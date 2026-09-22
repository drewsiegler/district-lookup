"""The app window: a small page served to your own browser.

    python src/web.py

Everything stays on this machine — the server only listens on localhost, and
your list is never uploaded anywhere. The only thing that leaves your computer
is one address at a time going to the Census geocoder, exactly as the command
line version does.
"""

import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pipeline
from input_table import describe_roles, read_people
from layers import load_layers

HOST, PORT = "127.0.0.1", 8734
PAGE = (Path(__file__).resolve().parent / "web_page.html").read_text(encoding="utf-8")

state = {"status": "idle", "done": 0, "total": 0, "message": "", "summary": None, "error": None}
state_lock = threading.Lock()
layers_cache = []


def update(**changes):
    with state_lock:
        state.update(changes)


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

        def on_row(i, total, label, address):
            update(done=i - 1, total=total, message=f"{label or address}")

        outcome = pipeline.run(people, source_columns, roles, layers_cache, on_row=on_row)
        results_path, review_path = pipeline.write_outputs(outcome)
        update(status="done", done=len(people), message="", summary={
            "results": len(outcome["results"]),
            "review": len(outcome["review"]),
            "reasons": sorted({r["review_reason"] for r in outcome["review"]}),
            "results_path": str(results_path),
            "review_path": str(review_path),
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
        elif self.path == "/status":
            with state_lock:
                body = json.dumps(state).encode("utf-8")
            self.send(200, body, "application/json")
        elif self.path in ("/download/results", "/download/review"):
            path = pipeline.RESULTS_PATH if self.path.endswith("results") else pipeline.REVIEW_PATH
            if not path.exists():
                self.send(404, b"not generated yet", "text/plain")
                return
            self.send(200, path.read_bytes(), "text/csv", {
                "Content-Disposition": f'attachment; filename="{path.name}"',
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


def main():
    global layers_cache
    print("Loading district maps…")
    layers_cache = load_layers()
    print(f"Loaded {len(layers_cache)} layer(s).")

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"\nDistrict Lookup is running at {url}")
    print("Leave this window open while you use it. Press Control-C when you're done.\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
