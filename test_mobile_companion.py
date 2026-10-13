"""End-to-end tests for the mobile companion using a synthetic MySQL server."""
import csv
import importlib.util
import io
import json
import sys
import types
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

# Let the source tests run without requiring a locally installed MySQL driver.
if "pymysql" not in sys.modules:
    try:
        _pymysql_spec = importlib.util.find_spec("pymysql")
    except (ImportError, ValueError):
        _pymysql_spec = None
    if _pymysql_spec is None:
        pymysql_stub = types.ModuleType("pymysql")
        pymysql_stub.cursors = types.SimpleNamespace(SSCursor=type("SSCursor", (), {}))
        pymysql_stub.__version__ = "test-stub"
        pymysql_stub.connect = lambda **kwargs: None
        sys.modules["pymysql"] = pymysql_stub

import mobile_companion


class FakeCursor:
    def __init__(self):
        self.description = None
        self.rowcount = -1
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql):
        if sql.strip().lower().startswith("select synthetic"):
            self.description = (("id",), ("payload",))
            self.offset = 0
        elif sql.strip().lower().startswith("select wide"):
            self.description = tuple((f"wide_{i}",) for i in range(70))
            self.offset = 0
        elif sql.strip().lower() == "select database()":
            self.description = (("DATABASE()",),)
        else:
            self.description = None
            self.rowcount = 1

    def fetchmany(self, size):
        if self.description and self.description[0][0] == "id":
            start = self.offset
            stop = min(start + size, 1100)
            self.offset = stop
            return [(i, "x" * 1000) for i in range(start, stop)]
        if self.description and self.description[0][0] == "wide_0" and self.offset == 0:
            self.offset = 1
            return [tuple(range(70))]
        return []

    def fetchone(self):
        return ("demo",)


class FakeConnection:
    def cursor(self, cursorclass=None):
        return FakeCursor()

    def get_server_info(self):
        return "8.0-test"

    def close(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass


class MobileCompanionHTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = mobile_companion.MobileCompanionServer(port=0, bind_host="127.0.0.1")
        self.server.start()
        self.base = f"http://127.0.0.1:{self.server.port}"

    def tearDown(self):
        self.server.stop()

    def request_json(self, path, payload=None, token=None, method=None):
        data = None if method == "GET" else json.dumps(payload or {}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        req = Request(self.base + path, data=data, headers=headers, method=method)
        with urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def pair(self):
        status, result = self.request_json("/api/pair", {"code": self.server.pairing_code})
        self.assertEqual(status, 200)
        return result["token"]

    def test_mobile_page_is_responsive_app(self):
        with urlopen(self.base + "/", timeout=5) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("Android companion", body)
            self.assertIn("viewport", body)
            self.assertIn("Run SQL", body)

    def test_pairing_code_authenticates_ephemeral_session(self):
        with self.assertRaises(HTTPError) as err:
            self.request_json("/api/pair", {"code": "wrong-code"})
        self.assertEqual(err.exception.code, 401)
        token = self.pair()
        status, state = self.request_json("/api/state", token=token, method="GET")
        self.assertEqual(status, 200)
        self.assertTrue(state["ok"])
        self.assertFalse(state["connected"])

    def test_large_query_preview_is_bounded_and_full_csv_is_exportable(self):
        original_connect = mobile_companion.pymysql.connect
        mobile_companion.pymysql.connect = lambda **kwargs: FakeConnection()
        token = self.pair()
        try:
            status, connected = self.request_json("/api/connect", {
                "host": "localhost", "port": 3306, "user": "tester", "password": "not-persisted",
                "database": "demo", "autocommit": True,
            }, token=token)
            self.assertEqual(status, 200)
            self.assertTrue(connected["ok"])

            status, result = self.request_json("/api/query", {"sql": "SELECT synthetic"}, token=token)
            self.assertEqual(status, 200)
            self.assertEqual(result["rowCount"], 1100)
            self.assertEqual(len(result["preview"]), mobile_companion.MAX_PREVIEW_ROWS)
            self.assertTrue(result["truncated"])
            self.assertLessEqual(len(result["preview"][0][1]), mobile_companion.MAX_PREVIEW_CELL_CHARS)

            req = Request(self.base + "/api/export", headers={"Authorization": "Bearer " + token})
            with urlopen(req, timeout=5) as response:
                csv_text = response.read().decode("utf-8-sig")
            rows = list(csv.reader(io.StringIO(csv_text)))
            self.assertEqual(rows[0], ["id", "payload"])
            self.assertEqual(len(rows) - 1, 1100)
            self.assertEqual(len(rows[1][1]), 1000)
        finally:
            mobile_companion.pymysql.connect = original_connect

    def test_wide_results_keep_preview_bounded_but_export_all_columns(self):
        original_connect = mobile_companion.pymysql.connect
        mobile_companion.pymysql.connect = lambda **kwargs: FakeConnection()
        token = self.pair()
        try:
            self.request_json("/api/connect", {"host": "localhost", "port": 3306, "user": "tester"}, token=token)
            status, result = self.request_json("/api/query", {"sql": "SELECT wide"}, token=token)
            self.assertEqual(status, 200)
            self.assertEqual(result["totalColumns"], 70)
            self.assertEqual(len(result["columns"]), mobile_companion.MAX_PREVIEW_COLUMNS)
            self.assertTrue(result["truncatedColumns"])
            req = Request(self.base + "/api/export", headers={"Authorization": "Bearer " + token})
            with urlopen(req, timeout=5) as response:
                header = next(csv.reader(io.StringIO(response.read().decode("utf-8-sig"))))
            self.assertEqual(len(header), 70)
        finally:
            mobile_companion.pymysql.connect = original_connect

    def test_host_header_rejects_unexpected_hostname(self):
        req = Request(self.base + "/", headers={"Host": "attacker.example"})
        with self.assertRaises(HTTPError) as err:
            urlopen(req, timeout=5)
        self.assertEqual(err.exception.code, 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
