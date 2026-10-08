"""The app window: a small page served to your own browser.

    python src/web.py

Everything stays on this machine — the server only listens on localhost, and
your list is never uploaded anywhere. The only thing that leaves your computer
is the addresses, going to the Census geocoder exactly as the command line
version sends them, plus one question to GitHub when the window opens: is
there a newer version? (See about.py.)
"""

import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))

import about
import pipeline
from app_paths import ROOT
from input_table import describe_roles, read_people
from layers import load_layers

HOST, PORT = "127.0.0.1", 8734
PAGE = (ROOT / "src" / "web_page.html").read_text(encoding="utf-8")
ICON_PATH = ROOT / "assets" / "AppIcon.png"

state = {"status": "idle", "done": 0, "total": 0, "message": "", "summary": None, "error": None}
state_lock = threading.Lock()
layers_cache = []
# The finished rows live here and nowhere else: never written to disk, so a
# list of real people's addresses can't be left behind in the project folder
# (or committed by accident). Downloading is how you get them out.
last_outcome = {"results": None, "review": None}
# Which of those have been downloaded, so quitting can warn before losing them.
downloaded = set()
# Filled in by a background check when the app starts; the page asks for it.
update_info = {"checked": False, "update": None}


def update(**changes):
    with state_lock:
        state.update(changes)


def check_for_update():
    found = about.check_for_update()
    with state_lock:
        update_info.update(checked=True, update=found)


def run_job(filename: str, text: str):
    update(status="running", done=0, total=0, message="Reading your list…", summary=None, error=None)
    temp_path = None
    try:
        suffix = Path(filename).suffix.lower()
        with TemporaryDirectory() as tmp:
            # Written to a temp file so the same reader handles uploads, drops
            # and pasted text; deleted as soon as the rows are in memory.
            temp_path = Path(tmp) / f"input{suffix if suffix in ('.csv', '.txt') else '.txt'}"
            temp_path.write_text(text, encoding="utf-8")
            people, source_columns, roles = read_people(temp_path)

        update(total=len(people), message=describe_roles(roles))

        def on_progress(done, total):
            update(done=done, total=total, message="addresses looked up")

        outcome = pipeline.run(people, source_columns, roles, layers_cache, on_progress=on_progress)
        with state_lock:
            last_outcome["results"] = pipeline.csv_text(outcome, "results")
            last_outcome["review"] = pipeline.csv_text(outcome, "review")
            downloaded.clear()
        update(status="done", done=len(people), message="", summary={
            "results": len(outcome["results"]),
            "review": len(outcome["review"]),
            "reasons": outcome["reasons"],
        })
    except Exception as err:  # shown in the page rather than only the terminal
        message = str(err) or err.__class__.__name__
        if temp_path:  # the reader names the file it read; show theirs, not the temp copy
            message = message.replace(str(temp_path), filename)
        update(status="error", error=message)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # the page shows progress; keep the terminal quiet

    def send(self, code, body: bytes, content_type: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path == "/icon.png" and ICON_PATH.exists():
            self.send(200, ICON_PATH.read_bytes(), "image/png", {"Cache-Control": "max-age=86400"})
        elif self.path == "/status":
            with state_lock:
                body = json.dumps(state).encode("utf-8")
            self.send(200, body, "application/json")
        elif self.path == "/about":
            with state_lock:
                body = json.dumps({"version": about.VERSION, "donate_url": about.DONATE_URL,
                                   **update_info}).encode("utf-8")
            self.send(200, body, "application/json")
        elif self.path in ("/download/results", "/download/review"):
            which = "results" if self.path.endswith("results") else "review"
            with state_lock:
                text = last_outcome[which]
            if text is None:
                self.send(404, b"nothing to download yet", "text/plain")
                return
            with state_lock:
                downloaded.add(which)
            filename = "results.csv" if which == "results" else "needs_review.csv"
            self.send(200, text.encode("utf-8-sig"), "text/csv", {
                "Content-Disposition": f'attachment; filename="{filename}"',
            })
        else:
            self.send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/run":
            self.send(404, b"not found", "text/plain")
            return
        with state_lock:
            busy = state["status"] == "running"
        if busy:
            self.send(409, b'{"error": "a lookup is already running"}', "application/json")
            return
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"] or 0)) or b"{}")
        threading.Thread(
            target=run_job,
            args=(payload.get("filename", "pasted.txt"), payload.get("text", "")),
            daemon=True,
        ).start()
        self.send(200, b'{"started": true}', "application/json")


def busy() -> bool:
    with state_lock:
        return state["status"] == "running"


def unsaved_results() -> bool:
    """Results that exist only in memory and haven't been downloaded yet."""
    with state_lock:
        return last_outcome["results"] is not None and "results" not in downloaded


class Server(ThreadingHTTPServer):
    # Python marks its servers' ports as reusable, which on Windows would let a
    # second copy of the app listen on the same port alongside the first.
    allow_reuse_address = sys.platform != "win32"


def already_running(port: int = PORT) -> bool:
    """Whether the port is held by another copy of District Lookup."""
    try:
        with urlopen(f"http://{HOST}:{port}/about", timeout=2) as response:
            return "version" in json.loads(response.read())
    except (OSError, ValueError):
        return False


def start(port: int = PORT) -> Server | None:
    """Takes the port, loads the maps, and starts the update check. Returns None
    if another copy of the app already has the port, so the caller can just
    open that one's page; raises OSError if something else has it."""
    global layers_cache
    try:
        server = Server((HOST, port), Handler)
    except OSError:
        if already_running(port):
            return None
        raise
    print("Loading district maps…")
    layers_cache = load_layers()
    print(f"Loaded {len(layers_cache)} layer(s).")
    threading.Thread(target=check_for_update, daemon=True).start()
    return server


def main():
    url = f"http://{HOST}:{PORT}/"
    server = start()
    if server is None:
        print(f"District Lookup is already running at {url}; opening it.")
        webbrowser.open(url)
        return
    print(f"\nDistrict Lookup is running at {url}")
    print("Leave this window open while you use it. Press Control-C when you're done.\n")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
