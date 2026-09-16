
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

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
android.api = 33
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a

# NOTE: python-for-android is pinned to v2024.1.21 via "pip install"
# in the CI workflow (.github/workflows/build-apk.yml), not here.
# Newer p4a releases (2026.05+) have a regression where several
# built-in recipes (android, kivy, pyjnius) are wrongly resolved via
# pip from PyPI instead of being built as recipes.

[buildozer]
log_level = 2
warn_on_root = 1
