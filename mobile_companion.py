"""Authenticated, LAN-only mobile companion for MySQL IDLE.

The desktop app hosts this dependency-free HTTP service only after the user
explicitly enables it. The pairing secret is ephemeral and never persisted.
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import os
import secrets
import socket
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path

import pymysql

APP_NAME = "MySQL IDLE Mobile"
IDLE_TIMEOUT_SECONDS = 30 * 60
MAX_SESSIONS = 5
MAX_BODY_BYTES = 512 * 1024
MAX_SQL_BYTES = 256 * 1024
FETCH_BATCH_SIZE = 64
MAX_PREVIEW_ROWS = 150
MAX_PREVIEW_COLUMNS = 60
MAX_PREVIEW_CELL_CHARS = 200
PAIR_LOCKOUT_SECONDS = 60
MAX_PAIR_FAILURES = 8


MOBILE_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#101827"><meta name="color-scheme" content="dark">
<title>MySQL IDLE Mobile</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#111a2b;--line:#2a3850;--text:#edf3ff;--muted:#9eacc3;--accent:#61a8ff;--good:#66d9a7;--bad:#ff8f98}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(1000px 500px at 20% -10%,#1e3556 0%,var(--bg) 60%);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;min-height:100vh}
header{padding:18px 16px 12px;border-bottom:1px solid var(--line);position:sticky;top:0;background:#0b1020ed;backdrop-filter:blur(12px);z-index:3}header .sub{color:var(--muted);font-size:12px}h1{font-size:20px;margin:0;letter-spacing:.2px}.wrap{width:min(1100px,100%);margin:auto;padding:16px;display:grid;gap:14px}.panel{background:linear-gradient(180deg,#141f32,#101827);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 12px 32px #0002}.panel h2{font-size:16px;margin:0 0 12px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.field{display:flex;flex-direction:column;gap:5px;min-width:0}.field.wide{grid-column:1/-1}label{font-size:12px;color:var(--muted)}input,textarea,select{font:inherit;color:var(--text);background:#09111f;border:1px solid #34445e;border-radius:10px;padding:11px;width:100%;min-width:0;outline:none}input:focus,textarea:focus{border-color:var(--accent);box-shadow:0 0 0 2px #61a8ff22}textarea{font:13px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace;min-height:170px;resize:vertical;tab-size:4}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}button,.button{border:1px solid #3a4d69;border-radius:10px;padding:10px 14px;background:#192841;color:var(--text);font:600 14px system-ui;cursor:pointer;text-decoration:none}button.primary{background:#1d65c1;border-color:#2b81e9}button.danger{color:#ffc2c7;border-color:#78414d}button:disabled{opacity:.5;cursor:wait}.hint,.muted{color:var(--muted);font-size:12px}.status{padding:10px 12px;border-radius:10px;background:#15243a;color:var(--muted);white-space:pre-wrap;overflow-wrap:anywhere}.status.good{color:var(--good)}.status.bad{color:var(--bad)}.hidden{display:none!important}.rowhead{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}.table-wrap{overflow:auto;max-height:55vh;border:1px solid var(--line);border-radius:10px;margin-top:12px}table{border-collapse:separate;border-spacing:0;width:max-content;min-width:100%;font:12px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace}th,td{padding:8px 10px;border-bottom:1px solid #27364b;border-right:1px solid #27364b;text-align:left;vertical-align:top;max-width:340px;overflow-wrap:anywhere;white-space:pre-wrap}th{position:sticky;top:0;background:#1b2a40;color:#cfe3ff}td{background:#101a2a}tr:nth-child(even) td{background:#131f31}.null{color:#8190a8;font-style:italic}.metrics{display:flex;gap:12px;flex-wrap:wrap;color:var(--muted);font-size:12px}.metrics strong{color:var(--text)}footer{padding:0 16px 24px;color:var(--muted);font-size:11px;text-align:center}.badge{border:1px solid #36506f;border-radius:20px;padding:3px 8px;font-size:11px;color:#bddaff}
@media(min-width:850px){.wrap{grid-template-columns:340px minmax(0,1fr);align-items:start}.editor{grid-column:2;grid-row:1/3}.connection{grid-column:1;grid-row:1}.result{grid-column:1/-1}.grid{grid-template-columns:1fr 1fr}.field.wide{grid-column:1/-1}}
@media(max-width:420px){.wrap{padding:10px}.panel{padding:12px}.grid{grid-template-columns:1fr 1fr}.field.wide{grid-column:1/-1}header{padding:14px 12px 10px}}
</style></head><body>
<header><div class="rowhead"><div><h1>MySQL IDLE <span class="badge">Android companion</span></h1><div class="sub">Responsive SQL workspace · session-only credentials</div></div><div id="connectionBadge" class="badge">Not connected</div></div></header>
<main class="wrap">
<section id="pairPanel" class="panel"><h2>Pair with desktop</h2><p class="muted">In the desktop app, open Tools → Android / Mobile Companion and enter the 10-digit code shown there. Both devices must be on the same trusted Wi-Fi network.</p><div class="field"><label for="pairCode">Temporary pairing code</label><input id="pairCode" inputmode="numeric" pattern="[0-9]{10}" maxlength="10" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="10-digit code from desktop"></div><div class="actions"><button class="primary" id="pairBtn">Pair device</button></div><div id="pairStatus" class="status" style="margin-top:12px">Pairing expires when the desktop companion stops.</div></section>
<section id="connectionPanel" class="panel connection hidden"><div class="rowhead"><h2>MySQL connection</h2><button id="disconnectBtn" class="danger">Disconnect</button></div><div class="grid"><div class="field"><label for="host">Host (as seen by desktop)</label><input id="host" value="localhost" autocomplete="off"></div><div class="field"><label for="port">Port</label><input id="port" value="3306" inputmode="numeric"></div><div class="field"><label for="user">Username</label><input id="user" autocomplete="username"></div><div class="field"><label for="password">Password (not saved)</label><input id="password" type="password" autocomplete="current-password"></div><div class="field wide"><label for="database">Database (optional)</label><input id="database" autocomplete="off"></div><div class="field wide"><label><input id="autocommit" type="checkbox" checked style="width:auto;margin-right:8px"> Auto-commit each statement</label></div></div><div class="actions"><button class="primary" id="connectBtn">Connect to MySQL</button></div><div class="hint">The desktop computer connects to MySQL. For a local database on that computer, use localhost.</div><div id="dbStatus" class="status" style="margin-top:10px">Not connected</div></section>
<section id="editorPanel" class="panel editor hidden"><div class="rowhead"><h2>SQL editor</h2><span class="hint">Ctrl/⌘ + Enter to run</span></div><textarea id="sql" autocapitalize="off" autocomplete="off" spellcheck="false" aria-label="SQL editor" placeholder="SELECT VERSION();"></textarea><div class="actions"><button id="runBtn" class="primary">Run SQL</button><button id="clearBtn">Clear</button><button id="commitBtn">Commit</button><button id="rollbackBtn">Rollback</button></div><div id="queryStatus" class="status" style="margin-top:12px">Ready.</div></section>
<section id="resultPanel" class="panel result hidden"><div class="rowhead"><h2>Result</h2><button id="exportBtn" disabled>Export complete CSV</button></div><div id="metrics" class="metrics"></div><div id="resultTable" class="table-wrap"><div class="muted" style="padding:12px">Run a query to see results.</div></div></section>
</main><footer>Use only on a trusted private network. HTTP is not encrypted; never expose this port to the public internet.</footer>
<script>
(()=>{'use strict';
const $=id=>document.getElementById(id);let sessionToken=sessionStorage.getItem('mysqlIdleMobileSession')||'';let lastResult=false;
function status(id,msg,kind=''){const el=$(id);el.textContent=msg;el.className='status'+(kind?' '+kind:'');}
function showApp(show){$('pairPanel').classList.toggle('hidden',show);$('connectionPanel').classList.toggle('hidden',!show);$('editorPanel').classList.toggle('hidden',!show);$('resultPanel').classList.toggle('hidden',!show);}
async function api(path,data,method='POST'){const headers={'Content-Type':'application/json'};if(sessionToken)headers.Authorization='Bearer '+sessionToken;const response=await fetch(path,{method,headers,body:method==='GET'?undefined:JSON.stringify(data||{})});let json={};try{json=await response.json()}catch{}if(response.status===401){sessionToken='';sessionStorage.removeItem('mysqlIdleMobileSession');showApp(false);throw new Error(json.error||'Pairing expired. Pair again.')}if(!response.ok||json.ok===false)throw new Error(json.error||('Request failed ('+response.status+')'));return json;}
$('pairBtn').onclick=async()=>{const btn=$('pairBtn');btn.disabled=true;try{const r=await fetch('/api/pair',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:$('pairCode').value.trim()})});const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||'Pairing failed');sessionToken=j.token;sessionStorage.setItem('mysqlIdleMobileSession',sessionToken);showApp(true);status('dbStatus','Not connected');$('connectionBadge').textContent='Paired · not connected';status('pairStatus','Device paired. Connect to MySQL below.','good');}catch(e){status('pairStatus',e.message,'bad')}finally{btn.disabled=false}};
$('connectBtn').onclick=async()=>{const b=$('connectBtn');b.disabled=true;status('dbStatus','Connecting…');try{const r=await api('/api/connect',{host:$('host').value.trim(),port:$('port').value.trim(),user:$('user').value,password:$('password').value,database:$('database').value.trim(),autocommit:$('autocommit').checked});status('dbStatus','Connected to '+r.serverVersion,'good');$('connectionBadge').textContent='Connected · '+(r.database||'no database');$('password').value='';}catch(e){status('dbStatus',e.message,'bad');}finally{b.disabled=false}};
$('runBtn').onclick=async()=>{const sql=$('sql').value.trim();if(!sql){status('queryStatus','Enter a SQL statement first.');return}const b=$('runBtn');b.disabled=true;$('exportBtn').disabled=true;lastResult=false;status('queryStatus','Running query…');$('metrics').replaceChildren();$('resultTable').textContent='Query running…';$('resultPanel').classList.remove('hidden');try{const r=await api('/api/query',{sql});status('queryStatus',r.message||'Query completed.','good');if(r.database!==undefined)$('connectionBadge').textContent='Connected · '+(r.database||'no database');$('metrics').replaceChildren();[['Rows',r.rowCount],['Time',r.elapsed.toFixed(3)+' s'],['Mode',r.hasResult?'result set':'statement']].forEach(([k,v])=>{const span=document.createElement('span');span.innerHTML='';const strong=document.createElement('strong');strong.textContent=k+': ';span.append(strong,document.createTextNode(String(v)));$('metrics').append(span)});renderTable(r.columns||[],r.preview||[]);lastResult=!!r.hasResult;$('exportBtn').disabled=!lastResult;$('resultPanel').classList.remove('hidden');if(r.truncated||r.truncatedColumns){const notes=[];if(r.truncated)notes.push(`first ${r.preview.length} rows of ${r.rowCount}`);if(r.truncatedColumns)notes.push(`first ${r.columns.length} of ${r.totalColumns} columns`);status('queryStatus',`Preview limited to ${notes.join(' and ')}. Export contains the complete result.`,'good');}}catch(e){status('queryStatus',e.message,'bad')}finally{b.disabled=false}};
function renderTable(columns,rows){const wrap=$('resultTable');wrap.replaceChildren();if(!columns.length){wrap.textContent='Statement completed without a result set.';return}const table=document.createElement('table'),thead=document.createElement('thead'),hr=document.createElement('tr');columns.forEach(c=>{const th=document.createElement('th');th.textContent=c;hr.append(th)});thead.append(hr);table.append(thead);const body=document.createElement('tbody');rows.forEach(row=>{const tr=document.createElement('tr');row.forEach(v=>{const td=document.createElement('td');if(v===null){td.textContent='NULL';td.className='null'}else td.textContent=String(v);tr.append(td)});body.append(tr)});table.append(body);wrap.append(table);if(!rows.length){const p=document.createElement('div');p.className='muted';p.style.padding='12px';p.textContent='Empty result set.';wrap.append(p)}}
$('exportBtn').onclick=async()=>{try{const response=await fetch('/api/export',{headers:{Authorization:'Bearer '+sessionToken}});if(!response.ok)throw new Error('Export unavailable');const blob=await response.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='mysql_idle_result.csv';document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url)}catch(e){status('queryStatus',e.message,'bad')}};
async function txn(action){try{const r=await api('/api/transaction',{action});status('queryStatus',r.message,'good')}catch(e){status('queryStatus',e.message,'bad')}}
$('commitBtn').onclick=()=>txn('commit');$('rollbackBtn').onclick=()=>txn('rollback');
$('disconnectBtn').onclick=async()=>{try{await api('/api/disconnect',{});status('dbStatus','Disconnected');$('connectionBadge').textContent='Paired · not connected';lastResult=false;$('exportBtn').disabled=true;$('resultPanel').classList.add('hidden')}catch(e){status('dbStatus',e.message,'bad')}};
$('clearBtn').onclick=()=>{$('sql').value='';$('sql').focus()};$('sql').addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();$('runBtn').click()}});
if(sessionToken){api('/api/state',{},'GET').then(r=>{showApp(true);if(r.connected){$('connectionBadge').textContent='Connected · '+(r.database||'no database');status('dbStatus','Connected to '+r.serverVersion,'good')}else{$('connectionBadge').textContent='Paired · not connected'}}).catch(()=>{sessionToken='';showApp(false)})}else showApp(false);
})();</script></body></html>'''


def _json_default(value):
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode("utf-8", "replace")
    if isinstance(value, (_dt.datetime, _dt.date, _dt.time)):
        return value.isoformat(sep=" ") if isinstance(value, _dt.datetime) else value.isoformat()
    return str(value)


def _csv_value(value):
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode("utf-8", "replace")
    if isinstance(value, (_dt.datetime, _dt.date, _dt.time)):
        return _json_default(value)
    return value


def _preview_value(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    text = _json_default(value)
    if len(text) > MAX_PREVIEW_CELL_CHARS:
        return text[:MAX_PREVIEW_CELL_CHARS - 3] + "..."
    return text


def _local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # UDP connect selects a route; it does not send application data.
        sock.connect(("192.0.2.1", 9))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class _MobileSession:
    def __init__(self):
        self.created = time.monotonic()
        self.last_active = self.created
        self.lock = threading.RLock()
        self.conn = None
        self.current_db = None
        self.server_version = ""
        self.last_result_path = None
        self.last_result_columns = None

    def touch(self):
        self.last_active = time.monotonic()

    def close(self):
        with self.lock:
            if self.conn is not None:
                try:
                    self.conn.close()
                except Exception:
                    pass
            self.conn = None
            self.current_db = None
            result_path, self.last_result_path = self.last_result_path, None
            self.last_result_columns = None
            if result_path:
                try:
                    os.unlink(result_path)
                except OSError:
                    pass


class MobileCompanionServer:
    """Start/stop the mobile companion. Public-LAN access is never automatic."""

    def __init__(self, port=8765):
        self.pairing_code = f"{secrets.randbelow(10**10):010d}"
        self.sessions = {}
        self.sessions_lock = threading.RLock()
        self.attempts = {}
        self.attempts_lock = threading.Lock()
        self.temp_dir = tempfile.TemporaryDirectory(prefix="mysql_idle_mobile_")
        try:
            (Path(self.temp_dir.name) / ".owner_pid").write_text(str(os.getpid()), encoding="ascii")
        except OSError:
            pass
        self._running = False
        self._serve_thread = None
        self.port_requested = int(port)
        owner = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "MySQLIDLEMobile/1"
            sys_version = ""

            def setup(self):
                super().setup()
                self.connection.settimeout(15)

            def log_message(self, fmt, *args):
                # Never write client IPs, pairing data, SQL, or request metadata to console.
                return

            def _headers(self, content_type="application/json; charset=utf-8", length=None):
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
                if length is not None:
                    self.send_header("Content-Length", str(length))

            def _send_bytes(self, status, data, content_type="application/json; charset=utf-8", extra_headers=None):
                self.send_response(status)
                self._headers(content_type, len(data))
                for name, value in (extra_headers or {}).items():
                    self.send_header(name, value)
                self.end_headers()
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def _json(self, status, obj):
                body = json.dumps(obj, ensure_ascii=False, default=_json_default, separators=(",", ":")).encode("utf-8")
                self._send_bytes(status, body)

            def _host_allowed(self):
                host_header = self.headers.get("Host", "")
                host = host_header.rsplit(":", 1)[0].strip("[]").lower()
                return host in owner.allowed_hosts

            def _origin_allowed(self):
                origin = self.headers.get("Origin")
                if not origin:
                    return True
                parsed = urlparse(origin)
                host = (parsed.hostname or "").lower()
                try:
                    port = parsed.port or (443 if parsed.scheme == "https" else 80)
                except ValueError:
                    return False
                local_port = owner.httpd.server_address[1]
                return parsed.scheme == "http" and port == local_port and host in owner.allowed_hosts

            def _read_json(self):
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > MAX_BODY_BYTES:
                    raise ValueError("Request body is too large.")
                raw = self.rfile.read(length) if length else b"{}"
                obj = json.loads(raw.decode("utf-8"))
                if not isinstance(obj, dict):
                    raise ValueError("Request must be a JSON object.")
                return obj

            def _session(self, required=True):
                auth = self.headers.get("Authorization", "")
                token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
                if not token:
                    if required:
                        raise PermissionError("Pair this device first.")
                    return None
                with owner.sessions_lock:
                    session = owner.sessions.get(token)
                    if session and time.monotonic() - session.last_active > IDLE_TIMEOUT_SECONDS:
                        owner.sessions.pop(token, None)
                        session.close()
                        session = None
                    if session:
                        session.touch()
                    elif required:
                        raise PermissionError("Mobile session expired. Pair this device again.")
                    return session

            def do_GET(self):
                if not self._host_allowed():
                    self._json(403, {"ok": False, "error": "Unrecognized Host header."})
                    return
                path = urlparse(self.path).path
                if path == "/":
                    body = MOBILE_HTML.encode("utf-8")
                    self._send_bytes(200, body, "text/html; charset=utf-8")
                elif path == "/api/state":
                    try:
                        s = self._session()
                        with s.lock:
                            self._json(200, {"ok": True, "connected": s.conn is not None,
                                "database": s.current_db or "", "serverVersion": s.server_version})
                    except PermissionError as exc:
                        self._json(401, {"ok": False, "error": str(exc)})
                elif path == "/api/export":
                    try:
                        s = self._session()
                        with s.lock:
                            p = s.last_result_path
                            if not p or not os.path.isfile(p):
                                self._json(404, {"ok": False, "error": "No CSV result is available."})
                                return
                            self.send_response(200)
                            self._headers("text/csv; charset=utf-8", os.path.getsize(p))
                            self.send_header("Content-Disposition", 'attachment; filename="mysql_idle_result.csv"')
                            self.end_headers()
                            with open(p, "rb") as fh:
                                while True:
                                    chunk = fh.read(128 * 1024)
                                    if not chunk:
                                        break
                                    self.wfile.write(chunk)
                    except PermissionError as exc:
                        self._json(401, {"ok": False, "error": str(exc)})
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                else:
                    self._json(404, {"ok": False, "error": "Not found."})

            def do_POST(self):
                if not self._host_allowed() or not self._origin_allowed():
                    self._json(403, {"ok": False, "error": "Request origin rejected."})
                    return
                path = urlparse(self.path).path
                try:
                    data = self._read_json()
                except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    self._json(400, {"ok": False, "error": str(exc) or "Invalid JSON."})
                    return
                if path == "/api/pair":
                    self._pair(data)
                    return
                try:
                    session = self._session()
                except PermissionError as exc:
                    self._json(401, {"ok": False, "error": str(exc)})
                    return
                if path == "/api/connect":
                    self._connect(session, data)
                elif path == "/api/query":
                    self._query(session, data)
                elif path == "/api/transaction":
                    self._transaction(session, data)
                elif path == "/api/disconnect":
                    session.close()
                    self._json(200, {"ok": True, "message": "Disconnected."})
                else:
                    self._json(404, {"ok": False, "error": "Not found."})

            def _pair(self, data):
                if not owner._running:
                    self._json(503, {"ok": False, "error": "Mobile companion is stopped."})
                    return
                ip = self.client_address[0]
                now = time.monotonic()
                with owner.attempts_lock:
                    if ip not in owner.attempts and len(owner.attempts) >= 256:
                        owner.attempts.pop(next(iter(owner.attempts)))
                    failures, blocked_until = owner.attempts.get(ip, (0, 0.0))
                    if now < blocked_until:
                        self._json(429, {"ok": False, "error": "Too many pairing attempts. Try again in one minute."})
                        return
                code = str(data.get("code", ""))
                if not secrets.compare_digest(code, owner.pairing_code):
                    with owner.attempts_lock:
                        failures, _ = owner.attempts.get(ip, (0, 0.0))
                        failures += 1
                        owner.attempts[ip] = (failures, now + PAIR_LOCKOUT_SECONDS if failures >= MAX_PAIR_FAILURES else 0.0)
                    self._json(401, {"ok": False, "error": "Invalid pairing code."})
                    return
                with owner.sessions_lock:
                    owner._purge_expired_sessions()
                    if len(owner.sessions) >= MAX_SESSIONS:
                        self._json(429, {"ok": False, "error": "Maximum paired devices reached. Restart the companion to reset pairing."})
                        return
                    token = secrets.token_urlsafe(32)
                    owner.sessions[token] = _MobileSession()
                with owner.attempts_lock:
                    owner.attempts.pop(ip, None)
                self._json(200, {"ok": True, "token": token})

            def _connect(self, session, data):
                host = str(data.get("host", "localhost")).strip()[:255] or "localhost"
                user = str(data.get("user", "")).strip()[:128]
                password = str(data.get("password", ""))
                database = str(data.get("database", "")).strip()[:255] or None
                try:
                    port = int(data.get("port", 3306))
                    if not 1 <= port <= 65535:
                        raise ValueError
                    if not user:
                        raise ValueError("Username is required.")
                except ValueError as exc:
                    self._json(400, {"ok": False, "error": str(exc) if str(exc) else "Port must be 1–65535."})
                    return
                try:
                    conn = pymysql.connect(host=host, port=port, user=user, password=password,
                        database=database, charset="utf8mb4", autocommit=bool(data.get("autocommit", True)),
                        connect_timeout=8, read_timeout=90, write_timeout=15)
                    version = str(conn.get_server_info())
                except Exception as exc:
                    self._json(400, {"ok": False, "error": _database_error(exc)})
                    return
                with session.lock:
                    old = session.conn
                    old_result = session.last_result_path
                    session.conn = conn
                    session.current_db = database
                    session.server_version = version
                    session.last_result_path = None
                    session.last_result_columns = None
                    if old_result:
                        try:
                            os.unlink(old_result)
                        except OSError:
                            pass
                    if old is not None:
                        try:
                            old.close()
                        except Exception:
                            pass
                self._json(200, {"ok": True, "serverVersion": version, "database": database or ""})

            def _query(self, session, data):
                sql = data.get("sql")
                if not isinstance(sql, str) or not sql.strip():
                    self._json(400, {"ok": False, "error": "Enter a SQL statement."})
                    return
                if len(sql.encode("utf-8")) > MAX_SQL_BYTES:
                    self._json(413, {"ok": False, "error": "SQL statement exceeds the 256 KiB limit."})
                    return
                started = time.perf_counter()
                with session.lock:
                    if session.conn is None:
                        self._json(400, {"ok": False, "error": "Connect to MySQL first."})
                        return
                    previous = session.last_result_path
                    session.last_result_path = None
                    session.last_result_columns = None
                    if previous:
                        try:
                            os.unlink(previous)
                        except OSError:
                            pass
                    try:
                        with session.conn.cursor(pymysql.cursors.SSCursor) as cur:
                            cur.execute(sql)
                            if cur.description:
                                all_columns = [str(item[0]) for item in cur.description]
                                columns = all_columns[:MAX_PREVIEW_COLUMNS]
                                fd, path = tempfile.mkstemp(prefix="mobile_result_", suffix=".csv", dir=owner.temp_dir.name)
                                os.close(fd)
                                count = 0
                                preview = []
                                try:
                                    try:
                                        csv.field_size_limit(2**31 - 1)
                                    except OverflowError:
                                        csv.field_size_limit(2**30)
                                    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                                        writer = csv.writer(fh)
                                        writer.writerow(all_columns)
                                        while True:
                                            batch = cur.fetchmany(FETCH_BATCH_SIZE)
                                            if not batch:
                                                break
                                            for row in batch:
                                                writer.writerow([_csv_value(v) for v in row])
                                                if count < MAX_PREVIEW_ROWS:
                                                    preview.append([_preview_value(v) for v in row[:MAX_PREVIEW_COLUMNS]])
                                                count += 1
                                except Exception:
                                    try:
                                        os.unlink(path)
                                    except OSError:
                                        pass
                                    raise
                                session.last_result_path = path
                                session.last_result_columns = columns
                                elapsed = time.perf_counter() - started
                                self._json(200, {"ok": True, "hasResult": True, "columns": columns,
                                    "totalColumns": len(all_columns), "truncatedColumns": len(all_columns) > len(columns),
                                    "preview": preview, "rowCount": count, "database": session.current_db or "",
                                    "truncated": count > len(preview),
                                    "elapsed": elapsed, "message": f"{count} row(s) in {elapsed:.3f} sec."})
                            else:
                                affected = cur.rowcount
                                stripped = sql.strip().rstrip(";").strip()
                                if stripped.upper().startswith("USE "):
                                    # Ask the active connection for the actual current database.
                                    with session.conn.cursor() as meta:
                                        meta.execute("SELECT DATABASE()")
                                        value = meta.fetchone()
                                        session.current_db = value[0] if value else None
                                elapsed = time.perf_counter() - started
                                self._json(200, {"ok": True, "hasResult": False, "columns": [], "preview": [],
                                    "rowCount": max(0, affected), "database": session.current_db or "",
                                    "truncated": False, "elapsed": elapsed,
                                    "message": f"Statement completed; {affected} row(s) affected in {elapsed:.3f} sec."})
                    except Exception as exc:
                        self._json(400, {"ok": False, "error": _database_error(exc)})

            def _transaction(self, session, data):
                action = str(data.get("action", "")).lower()
                if action not in {"commit", "rollback"}:
                    self._json(400, {"ok": False, "error": "Action must be commit or rollback."})
                    return
                with session.lock:
                    if session.conn is None:
                        self._json(400, {"ok": False, "error": "Connect to MySQL first."})
                        return
                    try:
                        getattr(session.conn, action)()
                        self._json(200, {"ok": True, "message": action.capitalize() + " completed."})
                    except Exception as exc:
                        self._json(400, {"ok": False, "error": _database_error(exc)})

        try:
            self.httpd = ThreadingHTTPServer(("0.0.0.0", self.port_requested), Handler)
        except OSError:
            # Avoid a dead end if another app already uses the default port.
            self.httpd = ThreadingHTTPServer(("0.0.0.0", 0), Handler)
        self.httpd.daemon_threads = True
        self.httpd.block_on_close = False
        bound_port = self.httpd.server_address[1]
        self.port = bound_port
        local_ip = _local_ip()
        self.url = f"http://{local_ip}:{self.port}/"
        self.allowed_hosts = {"localhost", "127.0.0.1", local_ip.lower()}
        self._running = False
        self._closed = False

    def _purge_expired_sessions(self):
        now = time.monotonic()
        expired = [token for token, s in self.sessions.items() if now - s.last_active > IDLE_TIMEOUT_SECONDS]
        for token in expired:
            session = self.sessions.pop(token, None)
            if session:
                session.close()

    def start(self):
        if self._closed:
            raise RuntimeError("This mobile companion has already been stopped.")
        if self._running:
            return
        self._running = True
        self._serve_thread = threading.Thread(target=self.httpd.serve_forever, name="mysql-idle-mobile-http", daemon=True)
        self._serve_thread.start()

    def stop(self):
        if self._closed:
            return
        was_running = self._running
        self._running = False
        try:
            if was_running:
                self.httpd.shutdown()
        finally:
            self.httpd.server_close()
            with self.sessions_lock:
                for session in self.sessions.values():
                    session.close()
                self.sessions.clear()
            self.pairing_code = ""
            with self.attempts_lock:
                self.attempts.clear()
            try:
                self.temp_dir.cleanup()
            except OSError:
                pass
            self._closed = True

    @property
    def running(self):
        return self._running


def _database_error(exc):
    args = getattr(exc, "args", ())
    if len(args) >= 2 and isinstance(args[0], int):
        return f"MySQL error {args[0]}: {args[1]}"
    return str(exc)[:1000] or exc.__class__.__name__
