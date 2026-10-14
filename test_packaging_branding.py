"""Packaging/UI resource contracts: logos must survive into distributed builds."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent


class PackagingBrandingTests(unittest.TestCase):
    def test_both_windows_executables_embed_the_generated_product_icon(self):
        for filename in ("mysql_idle.spec", "mysql_idle_portable.spec"):
            with self.subTest(filename=filename):
                source = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn("(['assets/mysqlidle.ico', 'assets'])", source) if False else None
                self.assertIn("datas=[('assets/mysqlidle.ico', 'assets')]", source)
                self.assertIn("icon='assets/mysqlidle.ico'", source)

        generator = (ROOT / "tools" / "generate_brand_assets.py").read_text(encoding="utf-8")
        self.assertIn('ASSETS / "mysqlidle.ico"', generator)
        self.assertTrue((ROOT / "assets" / "mysqlidle-logo.svg").is_file())

    def test_installer_is_branded_and_removes_installed_program_files(self):
        source = (ROOT / "MySQLIDLE.iss").read_text(encoding="utf-8")
        for expected in (
            "SetupIconFile=assets\\\\mysqlidle.ico",
            "WizardImageFile=assets\\\\wizard-image.bmp",
            "WizardSmallImageFile=assets\\\\wizard-small.bmp",
            "UninstallDisplayIcon={app}\\\\{#MyAppExeName}",
            "[UninstallDelete]",
            'Name: "{app}"',
            "CurUninstallStepChanged",
            "local settings and diagnostic logs",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, source)

    def test_android_launcher_and_splash_reference_product_branding(self):
        manifest = (ROOT / "android-app/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn('android:icon="@mipmap/ic_launcher"', manifest)
        self.assertIn('android:roundIcon="@mipmap/ic_launcher_round"', manifest)
        self.assertIn('android:name=".MainActivity"', manifest)
        self.assertIn('android:name="android.intent.action.MAIN"', manifest)
        self.assertIn('android:name="android.intent.category.LAUNCHER"', manifest)

        for filename in ("ic_launcher.xml", "ic_launcher_round.xml"):
            for directory in ("mipmap-anydpi", "mipmap-anydpi-v26"):
                path = ROOT / "android-app/app/src/main/res" / directory / filename
                with self.subTest(resource=str(path)):
                    source = path.read_text(encoding="utf-8")
                    self.assertIn("@drawable/ic_launcher_foreground", source)

        foreground = (ROOT / "android-app/app/src/main/res/drawable/ic_launcher_foreground.xml").read_text(encoding="utf-8")
        self.assertIn("#22D3EE", foreground)
        main_activity = (ROOT / "android-app/app/src/main/java/com/mysqlidle/mobile/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("R.drawable.ic_mysqlidle_brandmark", main_activity)
        self.assertIn('contentDescription = "MySQL IDLE logo"', main_activity)
        styles = (ROOT / "android-app/app/src/main/res/values/styles.xml").read_text(encoding="utf-8")
        self.assertIn("@drawable/ic_launcher_foreground", styles)


if __name__ == "__main__":
    unittest.main(verbosity=2)