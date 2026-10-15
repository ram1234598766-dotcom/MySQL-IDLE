"""Packaging/UI resource contracts for the shared product logo."""
from pathlib import Path
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parent


class PackagingBrandingTests(unittest.TestCase):
    def test_both_windows_executables_embed_the_generated_product_icon(self):
        for filename in ("mysql_idle.spec", "mysql_idle_portable.spec"):
            with self.subTest(filename=filename):
                source = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn("assets/mysqlidle.ico", source)
                self.assertIn("icon='assets/mysqlidle.ico'", source)

        generator = (ROOT / "tools" / "generate_brand_assets.py").read_text(encoding="utf-8")
        self.assertIn('LOGO_SOURCE = ASSETS / "mysqlidle-logo.png"', generator)
        self.assertTrue((ROOT / "assets" / "mysqlidle-logo.png").is_file())

    def test_windows_mysql_connection_defaults_to_certificate_optional_tls(self):
        source = (ROOT / "mysql_idle.py").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_MYSQL_TLS_VERIFY = False", source)
        self.assertIn('defaults.get("tls_verify", DEFAULT_MYSQL_TLS_VERIFY)', source)
        self.assertIn('params.get("tls_verify", DEFAULT_MYSQL_TLS_VERIFY)', source)
        self.assertIn("tls_verify=DEFAULT_MYSQL_TLS_VERIFY", source)
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("PyMySQL>=1.2.3,<2.0", requirements)

    def test_installer_is_branded_and_removes_installed_program_files(self):
        source = (ROOT / "MySQLIDLE.iss").read_text(encoding="utf-8")
        for expected in (
            "SetupIconFile=",
            "WizardImageFile=",
            "WizardSmallImageFile=",
            "UninstallDisplayIcon=",
            "[Files]",
            "recursesubdirs createallsubdirs",
            "CurUninstallStepChanged",
            "InitializeUninstallProgressForm",
            "npbstMarquee",
            "UninstallSilent",
            "local settings, SQL history",
            "MB_YESNO or MB_DEFBUTTON2",
            "DelTree(DataDir, True, True, True)",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, source)
        self.assertNotIn('[UninstallDelete]\nType: filesandordirs; Name: "{app}"', source)
        self.assertNotIn("WizardSilent", source)

    def test_windows_startup_requires_master_password_and_android_uses_same_verifier(self):
        desktop = (ROOT / "mysql_idle.py").read_text(encoding="utf-8")
        companion = (ROOT / "mobile_companion.py").read_text(encoding="utf-8")
        self.assertIn('MASTER_PASSWORD_PATH = APP_DATA_DIR / "master_password.json"', desktop)
        self.assertIn("if not _authenticate_startup(root):", desktop)
        self.assertIn("password_record=password_record", desktop)
        self.assertIn("from password_auth import is_password_record, verify_password", companion)
        self.assertIn('master_password = data.get("masterPassword", "")', companion)
        self.assertIn("password_valid = verify_password(master_password, owner.password_record)", companion)
        self.assertIn("Invalid master password or pairing code.", companion)

    def test_installer_creates_desktop_shortcut_with_explicit_shared_icon(self):
        source = (ROOT / "MySQLIDLE.iss").read_text(encoding="utf-8")
        self.assertIn("WizardStyle=modern dynamic polar includetitlebar", source)
        self.assertIn('UninstallDisplayIcon={app}\\_internal\\assets\\mysqlidle.ico', source)
        self.assertIn('Name: "{autodesktop}\\MySQL IDLE"', source)
        self.assertIn('IconFilename: "{app}\\_internal\\assets\\mysqlidle.ico"; IconIndex: 0', source)
        self.assertNotIn("Tasks: desktopicon", source)

    def test_user_supplied_logo_is_the_shared_windows_and_android_source(self):
        generator = (ROOT / "tools" / "generate_brand_assets.py").read_text(encoding="utf-8")
        logo = ROOT / "assets" / "mysqlidle-logo.png"
        android_logo = ROOT / "android-app/app/src/main/res/drawable-nodpi/ic_mysqlidle_logo.png"
        self.assertIn('LOGO_SOURCE = ASSETS / "mysqlidle-logo.png"', generator)
        self.assertTrue(logo.is_file())
        self.assertTrue(android_logo.is_file())
        self.assertEqual(logo.read_bytes(), android_logo.read_bytes())
        with Image.open(logo) as image:
            self.assertEqual(image.size, (96, 96))
            self.assertEqual(image.convert("RGBA").getpixel((0, 0))[3], 0)

    def test_android_launcher_and_splash_use_the_supplied_logo(self):
        manifest = (ROOT / "android-app/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn('android:icon="@mipmap/ic_launcher"', manifest)
        self.assertIn('android:roundIcon="@mipmap/ic_launcher_round"', manifest)
        self.assertIn('android:name=".MainActivity"', manifest)
        self.assertIn('android:name="android.intent.action.MAIN"', manifest)
        self.assertIn('android:name="android.intent.category.LAUNCHER"', manifest)

        for filename in ("ic_launcher.xml", "ic_launcher_round.xml"):
            legacy = ROOT / "android-app/app/src/main/res/mipmap-anydpi" / filename
            adaptive = ROOT / "android-app/app/src/main/res/mipmap-anydpi-v26" / filename
            with self.subTest(resource=str(legacy)):
                self.assertIn("@drawable/ic_mysqlidle_logo", legacy.read_text(encoding="utf-8"))
            with self.subTest(resource=str(adaptive)):
                self.assertIn("@drawable/ic_launcher_foreground", adaptive.read_text(encoding="utf-8"))

        foreground = (ROOT / "android-app/app/src/main/res/drawable/ic_launcher_foreground.xml").read_text(encoding="utf-8")
        self.assertIn("@drawable/ic_mysqlidle_logo", foreground)
        main_activity = (ROOT / "android-app/app/src/main/java/com/mysqlidle/mobile/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("R.drawable.ic_mysqlidle_logo", main_activity)
        self.assertIn('contentDescription = "MySQL IDLE logo"', main_activity)
        styles = (ROOT / "android-app/app/src/main/res/values/styles.xml").read_text(encoding="utf-8")
        self.assertIn("@drawable/ic_launcher_foreground", styles)


    def test_android_api_36_configuration_and_edge_to_edge_insets(self):
        app_build = (ROOT / "android-app/app/build.gradle.kts").read_text(encoding="utf-8")
        root_build = (ROOT / "android-app/build.gradle.kts").read_text(encoding="utf-8")
        activity = (ROOT / "android-app/app/src/main/java/com/mysqlidle/mobile/MainActivity.kt").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/build-exe-apk.yml").read_text(encoding="utf-8")
        self.assertIn("compileSdk = 36", app_build)
        self.assertIn("targetSdk = 36", app_build)
        self.assertRegex(root_build, r'id\("com\.android\.application"\) version "\d+\.\d+\.\d+" apply false')
        self.assertIn("gradle-version: \"9.8.1\"", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn('build-tools;36.0.0', workflow)
        self.assertIn("APK must target Android API level 36 or higher.", workflow)
        self.assertIn("winget install 9NQ7512CXL7T", workflow)
        self.assertIn('exec -3.15 -c "import sys; print(sys.executable)"', workflow)
        self.assertIn("MYSQLIDLE_PYTHON=$pythonExecutable", workflow)
        self.assertIn('shell: cmd', workflow)
        self.assertIn('"%MYSQLIDLE_PYTHON%" -m unittest -v', workflow)
        self.assertNotIn("MYSQLIDLE_PYMANAGER exec -3.15 .\\run_ci_tests.py", workflow)
        self.assertIn("bash tools/setup_python_3_15_linux.sh", workflow)
        linux_setup = (ROOT / "tools/setup_python_3_15_linux.sh").read_text(encoding="utf-8")
        self.assertIn('version="3.15.0"', linux_setup)
        self.assertIn('archive="${RUNNER_TEMP:?}/Python-${version}.tar.xz"', linux_setup)
        self.assertIn("ba4bed1ba346b916890b76d9e320451420aa69f6408997d33c66482eeae3d575", linux_setup)
        self.assertIn("python3.15", linux_setup)
        self.assertNotIn('python-version: "3.14.8"', workflow)
        windows_builder = (ROOT / "build_windows.ps1").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("py -3.15", windows_builder)
        self.assertIn("pyinstaller==6.22.3 pillow==12.3.0", windows_builder)
        self.assertIn("Python 3.15", readme)
        self.assertIn("WindowInsets.Type.systemBars()", activity)
        self.assertIn("applySystemBarInsets(scroll)", activity)
        self.assertIn("applySystemBarInsets(page)", activity)
        self.assertIn("Privacy Policy", activity)
        self.assertIn("https://github.com/ram1234598766-dotcom/MySQL-IDLE/blob/main/PRIVACY_POLICY.md", activity)
        privacy = (ROOT / "PRIVACY_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("# Privacy Policy — MySQL IDLE Mobile", privacy)
        self.assertIn("contact", privacy.lower())



if __name__ == "__main__":
    unittest.main(verbosity=2)
