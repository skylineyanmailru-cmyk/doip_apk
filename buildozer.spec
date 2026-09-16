
[app]
title = Leapmotor DoIP Tester
package.name = leapmotordoip
package.domain = by.doip
source.dir = .
source.include_exts = py,txt
source.exclude_dirs = p4a-pinned,.git,.github,.buildozer,bin
version = 2.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
android.api = 33
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a

# python-for-android is pre-cloned by the CI workflow into ./p4a-pinned
# at tag v2024.01.21 (a known-good release, before newer releases
# (2026.05+) broke several built-in recipes — android, kivy, pyjnius —
# by migrating them to a "PyProjectRecipe" mechanism that wrongly tries
# to fetch them from PyPI, where Android-compatible builds don't exist).
# Pointing Buildozer straight at this local checkout is what actually
# forces the pinned version — relying on p4a.branch or a pre-installed
# pip package was not enough, Buildozer kept re-cloning the latest tag.
p4a.source_dir = ./p4a-pinned

[buildozer]
log_level = 2
warn_on_root = 1
