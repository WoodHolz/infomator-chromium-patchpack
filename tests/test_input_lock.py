#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runtime regression test for Input.setUserInputLocked.

Checks:
1) lock command exists
2) CDP click works while locked
3) OS click is blocked while locked
4) OS click recovers after unlock
"""

from __future__ import annotations

import ctypes
import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

try:
    import websocket  # type: ignore
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
    import websocket  # type: ignore

USER32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_json(url: str, timeout: float = 20.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"endpoint not ready: {url}")


class Cdp:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=20, origin="http://127.0.0.1")
        self._id = 0

    def send(self, method: str, params: dict | None = None):
        self._id += 1
        msg_id = self._id
        self.ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        while True:
            data = json.loads(self.ws.recv())
            if data.get("id") != msg_id:
                continue
            if "error" in data:
                raise RuntimeError(f"{method} failed: {data['error']}")
            return data.get("result") or {}

    def eval(self, js: str):
        return self.send("Runtime.evaluate", {"expression": js, "returnByValue": True})["result"]["value"]

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def os_click(x: int, y: int) -> None:
    USER32.SetCursorPos(int(x), int(y))
    time.sleep(0.05)
    USER32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)
    USER32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def main() -> int:
    default_chrome = Path(r"E:\ungoogled-chromium-windows\build\src\out\Default\chrome.exe")
    chrome = Path(sys.argv[1]) if len(sys.argv) > 1 else default_chrome
    if not chrome.exists():
        print(f"FAIL: missing chrome.exe: {chrome}")
        return 1

    html = """<!doctype html><meta charset="utf-8">
<button id="b" style="position:fixed;inset:0;font-size:40px">CLICK</button>
<script>
window.clicks=0; b.addEventListener('click',()=>window.clicks++);
</script>"""
    port = free_port()
    profile = Path(tempfile.mkdtemp(prefix="infomator-input-lock-"))
    page = profile / "index.html"
    page.write_text(html, encoding="utf-8")

    proc = subprocess.Popen(
        [
            str(chrome),
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            f"--remote-debugging-port={port}",
            "--remote-allow-origins=*",
            page.as_uri(),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cdp = None
    try:
        targets = wait_json(f"http://127.0.0.1:{port}/json/list")
        ws_url = next(t["webSocketDebuggerUrl"] for t in targets if t.get("type") == "page")
        cdp = Cdp(ws_url)
        cdp.send("Runtime.enable")

        cdp.send("Input.setUserInputLocked", {"locked": True})
        before = cdp.eval("window.clicks")

        cdp.send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 300, "y": 300, "button": "left", "clickCount": 1})
        cdp.send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 300, "y": 300, "button": "left", "clickCount": 1})
        after_cdp = cdp.eval("window.clicks")
        if after_cdp <= before:
            print("FAIL: CDP click did not land while locked")
            return 1

        os_click(300, 300)
        time.sleep(0.2)
        after_os_locked = cdp.eval("window.clicks")
        if after_os_locked != after_cdp:
            print("FAIL: OS click was not blocked while locked")
            return 1

        cdp.send("Input.setUserInputLocked", {"locked": False})
        os_click(300, 300)
        time.sleep(0.2)
        after_os_unlocked = cdp.eval("window.clicks")
        if after_os_unlocked <= after_os_locked:
            print("FAIL: OS click still blocked after unlock")
            return 1

        print("PASS: Input.setUserInputLocked behavior verified")
        return 0
    finally:
        if cdp:
            try:
                cdp.send("Input.setUserInputLocked", {"locked": False})
            except Exception:
                pass
            cdp.close()
        proc.terminate()


if __name__ == "__main__":
    sys.exit(main())

