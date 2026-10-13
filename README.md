# MySQL IDLE 3.0

A desktop SQL shell for MySQL/MariaDB with background query execution, disk-backed result streaming, CSV export, and an optional paired mobile companion.

## Download builds

Push a commit to `main` or open **Actions → Build EXE and APK → Run workflow** to build:
- Windows portable `MySQLIDLE_Portable.exe`
- Windows folder build (`mysql_idle.exe` plus its runtime folder)
- Windows installer `MySQLIDLE-Setup.exe` (Inno Setup)
- Android debug APK `MySQLIDLE-Mobile-debug.apk`

For a public GitHub Release, push a version tag such as `v3.0.1`. Release assets are attached automatically when the workflow succeeds. Debug APKs are installable for testing but are not Play Store release packages.

## Desktop setup from source

```powershell
py -m pip install -r requirements.txt
py mysql_idle.py
```

To build locally on Windows:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

The normal Windows user only needs the packaged `.exe` or installer; Python is required only to run from source or build the app.

## Android companion

The Android app is a small WebView client for the companion hosted by the desktop application. Start the companion in **Tools → Android / Mobile Companion** on the desktop, then enter the displayed LAN address in the Android app. Both devices should be on a trusted private network. The companion currently uses HTTP on the LAN, which is not encrypted; do not expose its port to the public internet. The APK does not embed your MySQL password or run a MySQL server on Android.

## Security and verification

Review `SECURITY.md`. Automated tests cover SQL parsing, result streaming and mobile endpoint logic; CI tests the source on Windows and builds both distributables. A successful GitHub Actions run is the authoritative check for the actual Windows and Android binaries.
