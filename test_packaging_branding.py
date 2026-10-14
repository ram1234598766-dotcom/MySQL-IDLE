"""Packaging/UI resource contracts: logos must survive into distributed builds."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent


class PackagingBrandingTests(unittest.TestCase):
    def test_both_windows_executables_embed_the_generated_product_icon(self):
        for filename in ("mysql_idle.spec", "mysql_idle_portable.spec"):
            with self.subTest(filename=filename):
                source = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn("assets/mysqlidle.ico", source)
                self.assertIn("icon='assets/mysqlidle.ico'", source)

        generator = (ROOT / "tools" / "generate_brand_assets.py").read_text(encoding="utf-8")
        self.assertIn('ASSETS / "mysqlidle.ico"', generator)
        self.assertTrue((ROOT / "assets" / "mysqlidle-logo.svg").is_file())

    def test_windows_mysql_connection_defaults_to_certificate_optional_tls(self):
        source = (ROOT / "mysql_idle.py").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_MYSQL_TLS_VERIFY = False", source)
        self.assertIn("defaults.get(\"tls_verify\", DEFAULT_MYSQL_TLS_VERIFY)", source)
        self.assertIn("params.get(\"tls_verify\", DEFAULT_MYSQL_TLS_VERIFY)", source)
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
        self.assertIn('UninstallDisplayIcon={app}\\assets\\mysqlidle.ico', source)
        self.assertIn('Name: "{autodesktop}\\MySQL IDLE"', source)
        self.assertIn('IconFilename: "{app}\\assets\\mysqlidle.ico"; IconIndex: 0', source)
        self.assertNotIn("Tasks: desktopicon", source)

    def test_shared_icon_uses_database_and_sql_prompt_visuals(self):
        generator = (ROOT / "tools" / "generate_brand_assets.py").read_text(encoding="utf-8")
        svg = (ROOT / "assets" / "mysqlidle-logo.svg").read_text(encoding="utf-8")
        self.assertIn("def _draw_database", generator)
        self.assertIn("MYSQL_BLUE", generator)
        self.assertIn("ORANGE", generator)
        self.assertIn('aria-label="MySQL IDLE database terminal app icon"', svg)
        self.assertIn("#4479A1", svg)
        self.assertIn("#F29111", svg)

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
                    references_shared_foreground = "@drawable/ic_launcher_foreground" in source
                    embeds_matching_brand_mark = (
                        "<vector" in source
                        and "#0F172A" in source
                        and "#22D3EE" in source
                        and "#2563EB" in source
                    )
                    self.assertTrue(references_shared_foreground or embeds_matching_brand_mark)

        foreground = (ROOT / "android-app/app/src/main/res/drawable/ic_launcher_foreground.xml").read_text(encoding="utf-8")
        self.assertIn("#22D3EE", foreground)
        main_activity = (ROOT / "android-app/app/src/main/java/com/mysqlidle/mobile/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn("R.drawable.ic_mysqlidle_brandmark", main_activity)
        self.assertIn('contentDescription = "MySQL IDLE logo"', main_activity)
        styles = (ROOT / "android-app/app/src/main/res/values/styles.xml").read_text(encoding="utf-8")
        self.assertIn("@drawable/ic_launcher_foreground", styles)


if __name__ == "__main__":
    unittest.main(verbosity=2)
