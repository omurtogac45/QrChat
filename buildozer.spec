[app]

# (str) Title of your application
title = QR Chat

# (str) Package name
package.name = qrchat

# (str) Package domain (reverse DNS)
package.domain = org.example

# (str) Source code where main.py lives
source.dir = .

# (str) Main Python file
source.main = main.py

# (list) Permissions
android.permissions = INTERNET

# (str) Icon
icon.filename = icon.png

# (list) Application requirements
requirements = python3,kivy,qrcode
version = 1.0

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0


[buildozer]

# (str) Application name
log_level = 2

warn_on_root = 1

# (str) Android NDK version
android.ndk = 25b

# (int) Android API to use
android.api = 31

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# (list) Supported architectures
android.archs = armeabi-v7a, arm64-v8a

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) Package format: apk, aab, or both
android.package_format = apk
