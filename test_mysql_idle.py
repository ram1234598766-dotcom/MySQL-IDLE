"""Focused regression tests for MySQL IDLE's pure parsing and streaming helpers."""
import csv
import json
import importlib
import logging
import os
import time
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from pathlib import Path


# Keep these helper tests runnable on systems where PyMySQL is not installed.
if importlib.util.find_spec("pymysql") is None:
    pymysql_stub = types.ModuleType("pymysql")
    cursors_stub = types.SimpleNamespace(SSCursor=type("SSCursor", (), {}))
    pymysql_stub.cursors = cursors_stub
    pymysql_stub.__version__ = "test-stub"
    pymysql_stub.connect = lambda **kwargs: None
    sys.modules["pymysql"] = pymysql_stub

import mysql_idle


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.offset = 0
        self.description = None
        self.rowcount = -1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql):
        sql = sql.strip().lower()
        if sql.startswith("select synthetic"):
            self.description = (("id",), ("payload",))
            self.rows = [(i, b"x" * 1000) for i in range(1100)]
            self.offset = 0
        elif sql.startswith("select database()"):
            self.description = (("DATABASE()",),)
            self.rows = [("demo",)]
            self.offset = 0
        else:
            self.description = None
            self.rowcount = 1
            self.rows = []
            self.offset = 0

    def fetchone(self):
        batch = self.fetchmany(1)
        return batch[0] if batch else None

    def fetchmany(self, size):
        batch = self.rows[self.offset:self.offset + size]
        self.offset += len(batch)
        return batch


class FakeConnection:
    def ping(self, reconnect=False):
        return None

    def thread_id(self):
        return 456

    def cursor(self, cursorclass=None):
        return FakeCursor([])


class SplitSQLTests(unittest.TestCase):
    def test_semicolons_inside_quotes_and_comments(self):
        sql = "SELECT 'a;b'; SELECT \"x;y\"; SELECT `t;z`; -- ; ignore\nSELECT 4;"
        statements, rest = mysql_idle.split_sql(sql)
        self.assertEqual(len(statements), 4)
        self.assertEqual(rest, "")

    def test_doubled_quote_escape(self):
        statements, rest = mysql_idle.split_sql("SELECT 'it''s; fine'; SELECT 2;")
        self.assertEqual(len(statements), 2)
        self.assertEqual(statements[0], "SELECT 'it''s; fine'")
        self.assertEqual(rest, "")

    def test_incomplete_statement_is_preserved(self):
        statements, rest = mysql_idle.split_sql("SELECT 1; SELECT 'unfinished")
        self.assertEqual(statements, ["SELECT 1"])
        self.assertEqual(rest, " SELECT 'unfinished")

    def test_config_save_never_persists_password(self):
        with tempfile.TemporaryDirectory(prefix="mysql_idle_config_test_") as tmp:
            target = Path(tmp) / "settings.json"
            with patch.object(mysql_idle, "CONFIG_PATH", target):
                mysql_idle.save_config({
                    "last_connection": {
                        "host": "localhost", "user": "tester", "password": "never-save-me"
                    },
                    "history": ["SELECT 1;"],
                })
            saved = target.read_text(encoding="utf-8")
            self.assertNotIn("never-save-me", saved)
            self.assertNotIn('"password"', saved)

    def test_legacy_settings_are_migrated_and_secret_removed(self):
        with tempfile.TemporaryDirectory(prefix="mysql_idle_migrate_test_") as tmp:
            root = Path(tmp)
            legacy = root / "old.json"
            target = root / "app" / "settings.json"
            legacy.write_text(json.dumps({
                "last_connection": {"host": "localhost", "user": "tester", "password": "legacy-secret"},
                "history": ["SELECT 1;"],
            }), encoding="utf-8")
            with patch.object(mysql_idle, "CONFIG_PATH", target), patch.object(mysql_idle, "LEGACY_CONFIG_PATH", legacy):
                cfg = mysql_idle.load_config()
            self.assertTrue(target.is_file())
            self.assertFalse(legacy.exists())
            self.assertEqual(cfg["last_connection"]["user"], "tester")
            self.assertNotIn("password", cfg["last_connection"])
            self.assertNotIn("legacy-secret", target.read_text(encoding="utf-8"))


class RuntimeBootstrapTests(unittest.TestCase):
    def test_runtime_setup_creates_per_user_log_directory(self):
        logger = logging.getLogger()
        original_handlers = list(logger.handlers)
        with tempfile.TemporaryDirectory(prefix="mysql_idle_bootstrap_test_") as tmp:
            root = Path(tmp)
            try:
                with patch.object(mysql_idle, "APP_DATA_DIR", root / "app"), patch.object(mysql_idle, "LOG_DIR", root / "app" / "logs"), patch.object(mysql_idle.tempfile, "gettempdir", return_value=tmp):
                    mysql_idle.setup_runtime_environment()
                    self.assertTrue((root / "app" / "logs" / "application.log").is_file())
                    self.assertIn("Application version:", mysql_idle.runtime_diagnostics())
                    live = root / "mysql_idle_mobile_live_test"
                    stale = root / "mysql_idle_mobile_stale_test"
                    live.mkdir()
                    (live / ".owner_pid").write_text(str(os.getpid()), encoding="ascii")
                    stale.mkdir()
                    os.utime(live, (time.time() - 8 * 86400, time.time() - 8 * 86400))
                    os.utime(stale, (time.time() - 8 * 86400, time.time() - 8 * 86400))
                    mysql_idle.setup_runtime_environment()
                    self.assertTrue(live.exists(), "an active process's spool must never be deleted")
                    self.assertFalse(stale.exists(), "old unowned spools should be cleaned up")
            finally:
                # Close the test-created file handler before TemporaryDirectory cleanup (Windows).
                for handler in list(logger.handlers):
                    if handler not in original_handlers:
                        logger.removeHandler(handler)
                        handler.close()


class ResultStreamingTests(unittest.TestCase):
    def test_result_is_spooled_and_preview_is_bounded(self):
        events = __import__("queue").Queue()
        worker = mysql_idle.DatabaseWorker.__new__(mysql_idle.DatabaseWorker)
        worker.events = events
        worker.conn = FakeConnection()
        worker.conn_info = {"host": "localhost", "port": 3306, "user": "tester"}
        worker.current_db = "demo"
        worker.identifiers = set()
        worker._credentials = None
        worker._active_lock = __import__("threading").Lock()
        worker._active_thread_id = None
        with tempfile.TemporaryDirectory(prefix="mysql_idle_test_") as tmp:
            worker._temp_dir = types.SimpleNamespace(name=tmp)
            self.assertTrue(worker._execute_statement("SELECT synthetic"))
            kind, columns, preview, count, elapsed, path = events.get_nowait()
            self.assertEqual(kind, "result")
            self.assertEqual(columns, ["id", "payload"])
            self.assertEqual(count, 1100)
            self.assertEqual(len(preview), mysql_idle.MAX_DISPLAY_ROWS)
            self.assertLessEqual(len(preview[0][1]), mysql_idle.MAX_CELL_WIDTH)
            self.assertTrue(os.path.exists(path))
            with open(path, "r", newline="", encoding="utf-8-sig") as fh:
                reader = csv.reader(fh)
                header = next(reader)
                rows = list(reader)
            self.assertEqual(header, columns)
            self.assertEqual(len(rows), 1100)
            self.assertEqual(len(rows[0][1]), 1000)  # full data remains exportable


if __name__ == "__main__":
    unittest.main(verbosity=2)
