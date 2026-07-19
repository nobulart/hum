"""HUM Dashboard server (read-only).

Serves the built web UI (dashboard/web/dist) and a small JSON API that projects
the real HUM/DREAMS corpus through src/hum. Runs on Plato (MacBook). Pulls the
Hermes (Mac Studio) corpus via read-only rsync over SSH into a local cache.

Design constraints (from README/BUILD):
- READ-ONLY with respect to every HUM_DIR; the surfacing cron owns writes.
- CONFIG.YAML-INDEPENDENT: remote host is an env var, not a yaml edit.
- Minimal deps: stdlib http.server + SSE; no websockets, no FastAPI.

Env:
  HUM_DIR              local corpus dir        (default ~/.hermes/hum)
  HERMES_HOST          ssh host for Mac Studio (default mac-studio.local)
  HERMES_REMOTE_DIR    remote HUM_DIR          (default ~/.hermes/hum)
  HERMES_CACHE_DIR     local cache for pull    (default <repo>/dashboard/.cache/hum-studio)
  PORT                 listen port             (default 8650)
  BIND                 bind addr               (default 127.0.0.1)
"""
from __future__ import annotations

import json
import os
import sys
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "src"))  # so `import hum.dashboard` works
sys.path.insert(1, "/Users/craig/.hermes/hermes-agent/venv/lib/python3.11/site-packages")

from hum import dashboard as dash  # noqa: E402

PORT = int(os.environ.get("PORT", "8650"))
BIND = os.environ.get("BIND", "127.0.0.1")
HUM_DIR = os.environ.get("HUM_DIR") or dash.default_hum_dir()
HERMES_HOST = os.environ.get("HERMES_HOST", "mac-studio.local")
HERMES_REMOTE_DIR = os.environ.get("HERMES_REMOTE_DIR", "~/.hermes/hum")
HERMES_CACHE_DIR = os.environ.get(
    "HERMES_CACHE_DIR", os.path.join(HERE, ".cache", "hum-studio")
)
DIST_DIR = os.path.join(HERE, "web", "dist")

_model_cache: dict = {"ts": 0.0, "model": None, "mtimes": {}, "lock": threading.Lock()}
_sse_clients: set = set()
_sse_lock = threading.Lock()

ALL_FILES = [f"{l}.md" for l in dash.LAYERS] + ["DREAMS_PROTOCOL.md"]


def _mtime(path: str) -> float:
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def _corpus_mtime() -> float:
    latest = 0.0
    for base in (HUM_DIR, HERMES_CACHE_DIR):
        for fn in ALL_FILES:
            latest = max(latest, _mtime(os.path.join(base, fn)))
    return latest


def get_model(force: bool = False) -> dict:
    """Return the merged model, rebuilding only when a source file changes."""
    now = time.time()
    with _model_cache["lock"]:
        changed = _model_cache["mtimes"] and (
            _model_cache["mtimes"].get("corpus") != _corpus_mtime()
        )
        if _model_cache["model"] is not None and not force and not changed:
            return _model_cache["model"]
        plato = dash.build_machine_model(HUM_DIR, "plato", "macbook-pro.local")
        hermes = None
        if os.path.isdir(HERMES_CACHE_DIR):
            hermes_pulled = _mtime(os.path.join(HERMES_CACHE_DIR, "DREAMS.md"))
            pulled_at: "str | None" = None
            if hermes_pulled:
                pulled_at = time.strftime(
                    "%Y-%m-%dT%H:%M:%S%z", time.localtime(hermes_pulled)
                )
            hermes = dash.build_machine_model(
                HERMES_CACHE_DIR, "hermes", HERMES_HOST, pulled_at=pulled_at
            )
        model = dash.build_merged(plato, hermes)
        model["sources"] = {
            "hum_dir": HUM_DIR,
            "hermes_host": HERMES_HOST,
            "hermes_cache_dir": HERMES_CACHE_DIR,
            "hermes_available": hermes is not None,
        }
        _model_cache["model"] = model
        _model_cache["mtimes"] = {"corpus": _corpus_mtime()}
        _model_cache["ts"] = now
        return model


def broadcast(event: dict) -> None:
    msg = f"data: {json.dumps(event)}\n\n"
    dead = []
    with _sse_lock:
        for q in list(_sse_clients):
            try:
                q.put(msg)
            except Exception:
                dead.append(q)
        for q in dead:
            _sse_clients.discard(q)


def do_pull() -> dict:
    ok, msg = dash.pull_hermes(HERMES_HOST, HERMES_REMOTE_DIR, HERMES_CACHE_DIR)
    model = get_model(force=True)
    broadcast({"type": "model", "model": model})
    return {"ok": ok, "message": msg, "hermes_available": model["sources"]["hermes_available"]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # quiet (override BaseHTTPRequestHandler)
        pass

    def _send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, path: str):
        rel = path.lstrip("/")
        if rel in ("", "index.html"):
            rel = "index.html"
        fpath = os.path.normpath(os.path.join(DIST_DIR, rel))
        if not fpath.startswith(DIST_DIR) or not os.path.isfile(fpath):
            # SPA fallback
            fpath = os.path.join(DIST_DIR, "index.html")
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".json": "application/json",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
            ".woff2": "font/woff2",
        }.get(os.path.splitext(fpath)[1], "application/octet-stream")
        try:
            with open(fpath, "rb") as fh:
                body = fh.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/hum":
            return self._send_json(get_model())
        if u.path == "/api/health":
            return self._send_json({"ok": True, "hermes_host": HERMES_HOST,
                                    "hermes_available": get_model()["sources"]["hermes_available"]})
        if u.path == "/api/stream":
            return self._serve_sse()
        # static
        return self._serve_static(u.path)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/api/pull":
            return self._send_json(do_pull())
        self.send_error(404)

    def _serve_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        import queue
        q: "queue.Queue[str]" = queue.Queue()
        with _sse_lock:
            _sse_clients.add(q)
        # push current model immediately
        try:
            self.wfile.write(f"data: {json.dumps({'type': 'model', 'model': get_model()})}\n\n".encode())
            while True:
                msg = q.get()
                self.wfile.write(msg.encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with _sse_lock:
                _sse_clients.discard(q)


def main():
    os.makedirs(DIST_DIR, exist_ok=True)
    # Warm the model once at startup (and trigger an initial pull if cache empty).
    if not os.path.isdir(HERMES_CACHE_DIR):
        print(f"[hum-dashboard] no Hermes cache yet at {HERMES_CACHE_DIR}; "
              f"run POST /api/pull (or click refresh) to fetch from {HERMES_HOST}.")
    get_model(force=True)
    srv = ThreadingHTTPServer((BIND, PORT), Handler)
    print(f"[hum-dashboard] http://{BIND}:{PORT}  (local={HUM_DIR}, hermes={HERMES_HOST})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
