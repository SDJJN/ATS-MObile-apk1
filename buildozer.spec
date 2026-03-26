[app]

# (str) Title of your application
title = ATS Resume Analyzer

# (str) Package name
package.name = ats_analyzer

# (str) Package domain (needed for android duplication)
package.domain = org.ats.analyzer

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,html,css,js

# (list) List of directory to exclude (let empty to include all the directories)
source.exclude_dirs = tests, bin, venv, .git, .github

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3, kivy==2.3.0, flask, pdfplumber, python-docx, spacy, scikit-learn, pandas, numpy, requests, jinja2, click, werkzeug, itsdangerous, watchdog

# (str) Custom source folders for requirements
# (list) Garden requirements
# (str) Presplash of the application
# (str) Icon of the application
icon.filename = static/ats_app_icon.png

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) Permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Android API to use
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android build tool version to use
#android.build_tools_version = 33.0.0

# (bool) Use the PythonService on Android
#service.main = service.py

# (str) Python-for-android branch to use
p4a.branch = master

# (str) OUUTPUT (where the APK will be saved)
# (str) Path to a custom whitelist file
# (str) Path to a custom blacklist file

# (list) List of Java files to include for the android build
android.add_src = android_src

# (list) List of Java dependencies to include
# android.add_jars = foo.jar,bar.jar,baz.jar

# (list) List of Gradle dependencies to include
# android.add_libs = com.google.android.gms:play-services-ads:15.0.0

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (str) Android entry point
#android.entrypoint = org.kivy.android.PythonActivity

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = off, 1 = on)
warn_on_root = 1

# (str) Path to build directory (let empty to use default .buildozer)
#build_dir = ./.buildozer

# (str) Path to bin directory (let empty to use default ./bin)
#bin_dir = ./bin
