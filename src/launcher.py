"""The installed app's starting point (what PyInstaller builds; see packaging/).

Run from source, the app keeps a Terminal window open while it runs. An
installed app has no Terminal, so it shows a small window of its own instead:
it says the lookup page is open in the browser, can reopen it, and closing it
shuts the app down, after a warning if results haven't been downloaded yet.
The page itself works exactly as it does from source.

    launcher.py               the app
    launcher.py --no-browser  the app, without opening the page (for testing)
    launcher.py --self-test   loads the maps, looks up one public building, and
                              exits 0 if its districts come back right; the
                              build runs this on every finished app
"""

import sys
import threading
import time
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import about
import web
from layers import load_layers
from lookup import lookup_point

URL = f"http://{web.HOST}:{web.PORT}/"
# San José City Hall, where the Census geocoder places it (tests/conftest.py).
SELF_TEST_POINT = (37.338163163635, -121.886224209159)
# Districts only. Whatever follows an em dash is an officeholder's name
# ("3—Cm. Anthony Tordillos"), which an election changes; the maps don't.
SELF_TEST_EXPECTED = {"city": "San Jose", "council_district": "3",
                      "unified_trustee_area": "TA3", "scv_water_board_districts": "D2"}


def self_test() -> int:
    """Checks that a finished app carries everything it needs: the maps, the
    lookup, the page and the icon. Reports through the exit code, never by
    crashing: on Windows a crash pops up a dialog that would stall the build."""
    try:
        districts = lookup_point(load_layers(), *SELF_TEST_POINT)
        got = {column: (districts.get(column) or "").split("—")[0] for column in SELF_TEST_EXPECTED}
        ok = got == SELF_TEST_EXPECTED and "District Lookup" in web.PAGE and web.ICON_PATH.exists()
    except Exception as err:
        got, ok = repr(err), False
    print(f"District Lookup {about.VERSION} self-test {'passed' if ok else 'FAILED'}: {got}")
    return 0 if ok else 1


def open_page():
    # In a Chromebook's Linux, ChromeOS takes a moment to notice a new local
    # server and connect the Chromebook's own browser to it.
    if Path("/opt/google/cros-containers").exists():
        time.sleep(3)
    webbrowser.open(URL)


def show_error(message: str):
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("District Lookup", message)
        root.destroy()
    except Exception:  # no display, or no Tk: the message still reaches a terminal
        print(message, file=sys.stderr)


def run_window(server: web.Server):
    import tkinter as tk
    from tkinter import messagebox, ttk

    root = tk.Tk(className="district-lookup")  # matches StartupWMClass in the Linux .desktop file
    root.title("District Lookup")
    root.resizable(False, False)
    try:
        root.iconphoto(True, tk.PhotoImage(file=str(web.ICON_PATH)))
    except tk.TclError:
        pass

    frame = ttk.Frame(root, padding=(24, 20))
    frame.grid()
    ttk.Label(frame, text="District Lookup is running", font=("TkHeadingFont", 15, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w")
    ttk.Label(frame, justify="left", wraplength=340, text=(
        "Your lookup page opens in your web browser. Keep this window open while "
        "you use it; closing it shuts District Lookup down.")).grid(
        row=1, column=0, columnspan=2, sticky="w", pady=(6, 14))

    def quit_app():
        if web.busy() and not messagebox.askyesno(
                "District Lookup", "A lookup is still running. Quit anyway?", parent=root):
            return
        if web.unsaved_results() and not messagebox.askyesno(
                "District Lookup", "Your last results haven't been downloaded, and they aren't "
                "saved anywhere else. Quit anyway?", parent=root):
            return
        threading.Thread(target=server.shutdown, daemon=True).start()
        root.destroy()

    ttk.Button(frame, text="Open the lookup page",
               command=lambda: threading.Thread(target=webbrowser.open, args=(URL,), daemon=True).start()
               ).grid(row=2, column=0, sticky="w")
    ttk.Button(frame, text="Quit", command=quit_app).grid(row=2, column=1, sticky="e")
    ttk.Label(frame, text=f"Version {about.VERSION}", foreground="gray").grid(
        row=3, column=0, columnspan=2, sticky="w", pady=(14, 0))

    root.protocol("WM_DELETE_WINDOW", quit_app)
    if sys.platform == "darwin":
        root.createcommand("tk::mac::Quit", quit_app)  # the Dock's and menu's Quit
    root.mainloop()


def main():
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    try:
        server = web.start()
    except OSError as err:
        show_error(f"District Lookup couldn't start, because another program is using port "
                   f"{web.PORT} on this computer.\n\n({err})")
        sys.exit(1)
    show_page = "--no-browser" not in sys.argv
    if server is None:  # already running: just bring its page up again
        if show_page:
            open_page()
        return
    threading.Thread(target=server.serve_forever, daemon=True).start()
    if show_page:
        threading.Thread(target=open_page, daemon=True).start()
    try:
        run_window(server)
    except Exception:  # no display or no Tk: keep running the way the source version does
        print(f"District Lookup is running at {URL}. Press Control-C when you're done.")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
