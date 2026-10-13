# MySQL IDLE 3.0

A desktop SQL shell for MySQL/MariaDB with background query execution, disk-backed result streaming, CSV export, and an optional paired mobile companion.

## Download builds

Push a commit to `main` or run the GitHub Actions workflow to compile and test the app. If release-signing secrets are not set, CI builds an Android debug APK and unsigned Windows files as test artifacts only; it deliberately does not publish them as release downloads.

To publish a release, configure the signing secrets in `SIGNING.md` first. The workflow then produces a release-signed Android APK, signs and verifies the Windows executable(s) and installer, and publishes those files. Android release signing and Windows publisher code signing use separate keys. A Windows signature does not guarantee SmartScreen warnings disappear immediately.

## Release signing

Follow [SIGNING.md](SIGNING.md) to configure the Android release keystore and trusted Windows code-signing certificate in GitHub Actions secrets. Private keys and passwords must never be committed to the repository. The release workflow will skip publication rather than publish unsigned release assets.

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

The Android app is a WebView client for the companion hosted by the desktop application. Start the companion in **Tools → Android / Mobile Companion** on the desktop, then enter the root LAN address in the Android app (for example, `http://192.168.1.20:8765`). The Android app rejects paths, query strings, fragments and embedded usernames so the saved URL matches the desktop service's root endpoint. Both devices must be on a trusted private network. The companion currently uses HTTP on the LAN, which is not encrypted; pairing codes, queries and database credentials cross that network in clear text. Do not use public Wi-Fi, router port forwarding or public exposure; for remote use, prefer a trusted VPN/private tunnel. The APK does not embed your MySQL password or run a MySQL server on Android.

## Security and verification

Review `SECURITY.md`. Automated tests cover SQL parsing, result streaming, request-size limits, host-header validation and mobile endpoint logic. CI runs the desktop helper tests on Windows, the mobile HTTP integration suite on Linux, and builds the Windows/Android packages. The release includes the Windows installer when the installer build succeeds. A successful GitHub Actions run is the authoritative check for the actual platform binaries.
