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
        self.assertIn("PyMySQL>=1.2.0,<2.0", requirements)

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

    def test_installer_creates_desktop_shortcut_with_explicit_shared_icon(self):
        source = (ROOT / "MySQLIDLE.iss").read_text(encoding="utf-8")
        self.assertIn("WizardStyle=modern dynamic polar includetitlebar", source)
        self.assertIn('UninstallDisplayIcon={app}\\\\_internal\\\\assets\\\\mysqlidle.ico', source)
        self.assertIn('Name: "{autodesktop}\\\\MySQL IDLE"', source)
        self.assertIn('IconFilename: "{app}\\\\_internal\\\\assets\\\\mysqlidle.ico"; IconIndex: 0', source)
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
            self.assertEqual(image.size, (256, 256))
            self.assertIn("A", image.getbands())

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
