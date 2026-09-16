[app]
title = Leapmotor DoIP Tester
package.name = leapmotordoip
package.domain = by.doip

source.dir = .
source.include_exts = py,txt
version = 2.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

[app:android]
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

android.api = 36
android.minapi = 24
android.ndk = 28c

android.archs = arm64-v8a,armeabi-v7a

p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1