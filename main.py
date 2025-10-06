import io
import time
import webbrowser
from urllib.parse import quote_plus
from threading import Thread, Event

from kivy.clock import mainthread
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.filemanager import MDFileManager

import cv2
import qrcode
from PIL import Image as PILImage
from pyzbar import pyzbar


class SmartQRApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Dark"

        self.history = []
        self.qr_image_data = None
        self.cam_thread = None
        self.stop_cam = Event()
        self.manager_open = False

        root = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Mesaj kutusu
        self.msg_input = MDTextField(
            hint_text="Mesaj yaz...",
            multiline=True,
            mode="outlined",
            size_hint_y=None,
            height="100dp",
            line_color_focus=(0.16, 0.5, 0.9, 1),
            line_color_normal=(0.7, 0.7, 0.7, 1),
        )

        # Telefon kutusu
        self.phone_input = MDTextField(
            hint_text="(İsteğe bağlı) Telefon numarası: örn 905555555555",
            mode="outlined",
            size_hint_y=None,
            height="50dp",
            line_color_focus=(0.16, 0.5, 0.9, 1),
            line_color_normal=(0.7, 0.7, 0.7, 1),
        )

        # Üst butonlar
        btn_box = BoxLayout(size_hint_y=None, height="60dp", spacing=10)
        btn_box.add_widget(Button(text="QR Oluştur", on_release=self.generate_qr))
        btn_box.add_widget(Button(text="QR'u Oku (Dosya)", on_release=self.open_file))
        btn_box.add_widget(Button(text="Kamera ile Tara", on_release=self.toggle_camera))

        # QR Görseli
        self.qr_img = Image(size_hint_y=0.5)

        # Alt butonlar
        send_box = BoxLayout(size_hint_y=None, height="60dp", spacing=10)
        send_box.add_widget(Button(text="WhatsApp ile Gönder", on_release=self.send_whatsapp))
        send_box.add_widget(Button(text="Kaydet", on_release=self.save_qr))

        # Geçmiş listesi
        self.history_list = BoxLayout(orientation="vertical", size_hint_y=None)
        self.history_list.bind(minimum_height=self.history_list.setter('height'))

        scroll = MDScrollView()
        scroll.add_widget(self.history_list)

        # Ekrana ekleme
        root.add_widget(self.msg_input)
        root.add_widget(self.phone_input)
        root.add_widget(btn_box)
        root.add_widget(self.qr_img)
        root.add_widget(send_box)
        root.add_widget(scroll)

        return root

    def generate_qr(self, *args):
        text = self.msg_input.text.strip()
        if not text:
            self.show_popup("Uyarı", "Lütfen QR oluşturmak için mesaj girin.")
            return

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(text)
        qr.make(fit=True)

        pil_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
        self.qr_image_data = pil_img

        self.show_qr_image(pil_img)
        self.add_to_history(f"QR oluşturuldu: {text[:40]}")

    @mainthread
    def show_qr_image(self, pil_img):
        data = io.BytesIO()
        pil_img.save(data, format="PNG")
        data.seek(0)
        self.qr_img.texture = CoreImage(data, ext="png").texture

    def open_file(self, *args):
        self.file_manager = MDFileManager(
            select_path=self.decode_qr_from_file,
            exit_manager=self.close_file_manager,
        )
        self.file_manager.show("/")
        self.manager_open = True

    def close_file_manager(self, *args):
        self.manager_open = False
        self.file_manager.close()

    def decode_qr_from_file(self, path):
        try:
            img = cv2.imread(path)
            decoded = pyzbar.decode(img)
            if not decoded:
                self.show_popup("Bilgi", "Resimde QR bulunamadı.")
                return
            text = decoded[0].data.decode("utf-8")
            self.msg_input.text = text
            self.add_to_history(f"Resimden okundu: {text[:40]}")
            self.show_popup("Başarılı", f"QR mesajı: {text}")
        except Exception as e:
            self.show_popup("Hata", str(e))
        self.close_file_manager()

    def toggle_camera(self, *args):
        if self.cam_thread and self.cam_thread.is_alive():
            self.stop_cam.set()
            self.cam_thread = None
            self.show_popup("Bilgi", "Kamera durduruldu.")
        else:
            self.stop_cam.clear()
            self.cam_thread = Thread(target=self.camera_loop, daemon=True)
            self.cam_thread.start()
            self.show_popup("Bilgi", "Kamera başlatıldı, QR taramak için kameraya gösterin.")

    def camera_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.show_popup("Hata", "Kamera açılamadı.")
            return

        while not self.stop_cam.is_set():
            ret, frame = cap.read()
            if not ret:
                continue
            decoded = pyzbar.decode(frame)
            if decoded:
                text = decoded[0].data.decode("utf-8")
                self.stop_cam.set()
                self.update_msg_from_qr(text)
            small = cv2.resize(frame, (480, 360))
            self.update_cam_view(small)
        cap.release()

    @mainthread
    def update_cam_view(self, frame):
        data = io.BytesIO()
        PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).save(data, format="PNG")
        data.seek(0)
        self.qr_img.texture = CoreImage(data, ext="png").texture

    @mainthread
    def update_msg_from_qr(self, text):
        self.msg_input.text = text
        self.add_to_history(f"Kameradan okundu: {text[:40]}")
        self.show_popup("QR Okundu", text)

    def send_whatsapp(self, *args):
        text = self.msg_input.text.strip()
        if not text:
            self.show_popup("Uyarı", "Gönderilecek mesaj yok.")
            return

        phone = self.phone_input.text.strip()
        base = "https://wa.me/"
        if phone:
            url = f"{base}{phone}?text={quote_plus(text)}"
        else:
            url = f"{base}?text={quote_plus(text)}"

        webbrowser.open(url)
        self.add_to_history(f"WhatsApp gönderildi: {text[:40]}")

    def save_qr(self, *args):
        if not self.qr_image_data:
            self.show_popup("Uyarı", "Kaydedilecek QR yok.")
            return

        fname = f"qr_{int(time.time())}.png"
        self.qr_image_data.save(fname)
        self.show_popup("Kaydedildi", f"QR '{fname}' olarak kaydedildi.")
        self.add_to_history(f"Kaydedildi: {fname}")

    def add_to_history(self, text):
        self.history.insert(0, text)
        self.history_list.clear_widgets()
        for item in self.history[:10]:
            self.history_list.add_widget(
                MDListItem(
                    headline_text=item
                )
            )

    def show_popup(self, title, message):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(MDLabel(
            text=message,
            halign="center"
        ))
        btn = Button(
            text="Kapat",
            on_release=lambda x: popup.dismiss(),
            background_color=(0.16, 0.5, 0.9, 1),
            color=(1, 1, 1, 1)
        )
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        popup.open()


if __name__ == "__main__":
    SmartQRApp().run()
