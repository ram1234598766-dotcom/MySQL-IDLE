# MySQL IDLE 3.0

A desktop SQL shell for MySQL/MariaDB with background query execution, disk-backed result streaming, CSV export, and an optional paired mobile companion.

## Download builds

Push a commit to main or run the GitHub Actions workflow to build and test both platforms. Pull requests build the desktop apps and an Android debug APK for testing. Release publication requires all four Android signing secrets described in SIGNING.md; CI verifies the release APK signature before publishing it.

Windows EXE, installer, and folder-archive assets are published whenever the Windows build succeeds. If a trusted Windows signing certificate is configured, CI signs and verifies the Windows executables and installer. Otherwise, those Windows files are explicitly marked UNSIGNED in WINDOWS-SIGNING-STATUS.txt. Windows and Android use separate signing identities. A signature does not guarantee SmartScreen warnings disappear immediately. Every published bundle includes a SHA256SUMS manifest for integrity verification.

## App branding

The exact supplied MySQL IDLE logo image is the shared visual source for Windows and Android. It is stored at assets/mysqlidle-logo.png and copied byte-for-byte into Android's drawable-nodpi resource. The Windows ICO, wizard artwork, and shortcut icon are generated from that image by tools/generate_brand_assets.py. The installer adapts to Windows light/dark appearance and always creates a desktop shortcut that points to the packaged icon. CI verifies the shared logo source, desktop shortcut target/icon, application launch, and uninstall cleanup.

## Release signing

Follow SIGNING.md to configure Android release signing and optional trusted Windows code signing in GitHub Actions secrets. Private keys and passwords must never be committed. A debug APK is used only for CI/testing, never as a published release APK; unsigned Windows release files are allowed but clearly labelled.

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

## Build smoke tests

CI now launches both packaged Windows executables and checks they stay alive through startup. It installs the Windows setup package into an isolated temporary directory, starts the installed application, runs the uninstaller, then verifies the installation folder and Start Menu shortcut are removed. On Android, CI boots an API 35 emulator, installs the exact release APK when signing is configured (otherwise the CI debug APK), launches MainActivity, confirms its process stays alive, and checks that the branded connection screen and logo are visible.

The interactive Windows uninstaller uses the standard progress animation while removing the installed application and shortcuts. It asks separately whether to remove this Windows account's MySQL IDLE settings and logs; selecting No preserves preferences. Silent uninstall keeps user settings by default. This cleanup never removes MySQL databases or files outside the application's own settings paths.

## Android companion

The Android app is a WebView client for the desktop-hosted companion. Start **Tools → Android / Mobile Companion** on the desktop and enter the HTTPS LAN address into the Android app (for example, `https://192.168.1.20:8765`). Before connecting, compare the complete SHA-256 certificate fingerprint shown by the desktop with the fingerprint typed into the phone. The companion uses a short-lived self-signed certificate; the Android app only accepts that exact certificate after checking the fingerprint and rejects public/non-private hosts. The fingerprint changes when the desktop companion restarts, so verify and enter it again for a new session. Never accept a fingerprint that differs from the value shown on the desktop.

The companion binds to one selected private IPv4 interface, refuses wildcard/public binds, restricts request origins, limits concurrent request handlers, caps JSON request size and aborts result exports above 512 MiB. Stop the companion when it is not being used. Do not use public Wi-Fi, router port forwarding or public exposure; use a trusted VPN/private tunnel for remote access. The APK does not embed your MySQL password or run a MySQL server on Android.

The Windows **Connect to MySQL** dialog defaults to certificate-optional TLS for compatibility with localhost and self-signed MySQL servers. With PyMySQL 1.2+, it attempts encrypted TLS when the server supports it but does not verify the server's certificate or identity; this is less resistant to man-in-the-middle attacks. For managed servers, enable **Verify MySQL server certificate** and provide a trusted CA PEM file when required. The Android companion's MySQL connection form still requires verified TLS by default. Its HTTPS connection to the desktop remains protected by a manually verified SHA-256 certificate fingerprint.

The mobile SQL editor includes previous/next query history (at most 50 entries in page memory, cleared on disconnect or session expiry) and quick templates for server version, current database, database/table lists, and server time. Mobile query history is never written to persistent browser storage. On Windows, SQL history remains in memory by default and is only persisted after setting `MYSQLIDLE_SAVE_HISTORY=1` before starting the app. Review templates before execution; SQL runs with the connected MySQL account's permissions.

## Feature Governance

MySQL IDLE now has a shared local policy engine for the Windows SQL worker and paired Android companion. Open **Tools → Feature Governance** on Windows to configure the session policy and review recent decisions.

- **Guarded mode** is the default. High-impact SQL such as destructive DDL, administrative/file-related SQL, and `UPDATE` or `DELETE` without a `WHERE` clause requires explicit one-time approval.
- **Read-only mode** blocks statements classified as mutations or administration. The SQL is checked before queueing and checked again at the Windows execution boundary; the mobile server checks policy before using the database cursor.
- **Mobile step-up approval** uses a short-lived, random, single-use challenge bound to the exact SQL digest and paired session. A declined, expired, replayed, or mismatched approval is rejected.
- **Privacy-preserving audit** keeps at most 256 events in memory. Entries include time, decision, risk category, reason and a truncated SHA-256 statement fingerprint; they do not retain SQL text, literals, passwords or connection credentials.
- Policies are saved with other local app preferences. The environment variable `MYSQLIDLE_READ_ONLY=1` forces read-only mode, and `MYSQLIDLE_DISABLE_MOBILE=1` disables the mobile companion. Environment-enforced restrictions cannot be switched off in the UI.

The governor uses conservative lexical SQL classification, not a full MySQL parser, and is defense-in-depth rather than a replacement for least-privilege database accounts, backups, transactions and server-side permissions. SQL running under the connected MySQL account still has the permissions granted by that server.

## Security and verification

Review `SECURITY.md`. Automated tests cover SQL parsing, result streaming, HTTPS certificate handling, request-size/resource limits, Host/Origin validation, TLS connection settings and mobile endpoint behavior. CI runs desktop helper tests on Windows, the mobile HTTPS integration suite on Linux, and builds the Windows/Android packages. A successful GitHub Actions run is the authoritative check for the actual platform binaries. Windows assets are not code-signed unless a trusted Windows signing certificate is configured.
