# Release signing setup

The workflow never publishes the debug APK or unsigned Windows files as a GitHub Release. A signed Android APK can be published on its own once all four Android secrets are configured. Windows release files are included only when the Windows signing secrets are configured and the signed Windows build succeeds.

## 1. Android release keystore

Create a long-lived Android signing key on a trusted computer. Back up the keystore securely; losing it means the existing self-managed APK cannot be updated in place with the same app identity. Do **not** commit the keystore to Git.

With a JDK installed, run:

```powershell
keytool -genkeypair -v -keystore mysqlidle-release.jks -alias mysqlidle -keyalg RSA -keysize 4096 -validity 10000
```

Use passwords you generate and store safely. When prompted for certificate identity, enter the publisher information you want embedded in the Android certificate. Keep the `.jks` file and both passwords backed up in a secure location separate from GitHub.

Convert the keystore to a single-line Base64 value in PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path .\mysqlidle-release.jks))) | Set-Clipboard
```

In the repository, open **Settings → Secrets and variables → Actions → New repository secret** and add these secrets:

| Secret name | Value |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | Clipboard value containing the Base64-encoded `.jks` |
| `ANDROID_KEYSTORE_PASSWORD` | The keystore/store password entered when you created or changed the `.jks` file |
| `ANDROID_KEY_ALIAS` | The exact key alias inside that keystore, e.g. `mysqlidle` if you used that alias |
| `ANDROID_KEY_PASSWORD` | The private-key password for that alias (it may be the same as the store password, but does not have to be) |

**Do not swap the two password secrets.** `ANDROID_KEYSTORE_PASSWORD` must open the keystore file; `ANDROID_KEY_PASSWORD` unlocks the private key inside it. If Gradle reports that the keystore password is incorrect, verify `ANDROID_KEYSTORE_PASSWORD` against the same keystore file you encoded. If the keystore and key use different passwords, keep the values separate.

Before Gradle packaging, CI now validates the store password, alias, and private-key password with `keytool`. Diagnostics name the failing secret variable but never print secret values. The completed APK is still checked with Android's `apksigner`.

## 2. Trusted Windows code-signing certificate

Obtain a **valid publicly trusted code-signing certificate** from a certificate authority or use Microsoft's Artifact Signing service. A self-signed certificate can create a cryptographic signature but does not establish trusted publisher identity for general Windows users and does not solve the SmartScreen trust issue. Microsoft notes that even signed new applications can still get SmartScreen warnings while reputation builds: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation.

For a PFX/P12 certificate file that includes its private key, create a single-line Base64 value in PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path .\publisher-code-signing.pfx))) | Set-Clipboard
```

Add these repository Actions secrets:

| Secret name | Value |
| --- | --- |
| `WINDOWS_CERTIFICATE_BASE64` | Base64 value for the trusted code-signing `.pfx`/ `.p12` file |
| `WINDOWS_CERTIFICATE_PASSWORD` | PFX password |

The certificate must be valid for code signing and include its private key. Do not send the PFX or passwords in chat or commit them to Git. The workflow uses SignTool with SHA-256 file digests and an RFC 3161 timestamp, signs the portable EXE, EXEs within the folder build, and installer, then verifies each signature before archiving/uploading.

## 3. Produce a signed release

After all four Android secrets are set, open **Actions → Build Windows EXE and Android APK → Run workflow** on `main`. The workflow will build and verify the release-signed Android APK and publish it as a prerelease. Windows assets remain excluded while Windows signing is on hold. Once both Windows secrets are configured and the Windows signatures verify, the release will also include the signed Windows binaries and installer.

Check the workflow run for successful signature-verification steps. The release APK will be named `MySQLIDLE-Mobile-release.apk`. Windows downloads keep their regular filenames, and Authenticode signatures must verify and identify your publisher certificate.

## 4. Important boundaries

- Android's release keystore and Windows' publisher certificate are distinct signing identities.
- This project currently uses application ID `com.mysqlidle.mobile`. If you later publish to Google Play, review Play App Signing and its upload-key model before your first release.
- Code signing is not malware scanning or an automatic guarantee that Windows SmartScreen will stop warning. Use a consistent trusted publisher identity and never modify signed files after signing.
- Do not upload signing credentials to workflow artifacts, commit them, or print them in CI logs.
