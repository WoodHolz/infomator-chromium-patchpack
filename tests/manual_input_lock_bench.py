#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Human-verifiable bench for Input.setUserInputLocked.

  - Chrome window  : test page only (manual click / keyboard / hover / drag)
  - Native Tk panel: lock/unlock, steps, CDP simulator (NOT a browser tab)

The control panel is outside Chromium so kernel input lock on the test page
does not block your lock/CDP controls.

Usage:
  python tests/manual_input_lock_bench.py
  python tests/manual_input_lock_bench.py E:\\...\\out\\Default\\chrome.exe
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request
from pathlib import Path
from tkinter import scrolledtext, ttk
from typing import Any, Callable

try:
    import websocket  # type: ignore
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
    import websocket  # type: ignore

TEST_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Input Lock — Test Page</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: ui-sans-serif, system-ui, "Segoe UI", Arial; background: #0b1220; color: #e2e8f0; }
    .banner {
      padding: 10px 16px; background: #1e293b; border-bottom: 1px solid #334155;
      display: flex; justify-content: space-between; align-items: center; font-size: 14px;
    }
    .banner small { color: #94a3b8; }
    .lock-badge { padding: 4px 12px; border-radius: 999px; font-weight: 700; font-size: 13px; }
    .lock-badge.off { background: #78350f; color: #fcd34d; }
    .lock-badge.on { background: #14532d; color: #86efac; }
    .main { padding: 16px; display: grid; gap: 12px; grid-template-rows: auto 1fr auto; min-height: calc(100vh - 48px); }
    .metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
    .metric { background: #1f2937; border-radius: 8px; padding: 8px; font-size: 12px; }
    .metric b { display: block; font-size: 18px; margin-top: 4px; }
    .zones { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; min-height: 460px; }
    #clickZone {
      grid-column: 1 / span 2; border: 3px dashed #38bdf8; border-radius: 14px;
      display: flex; align-items: center; justify-content: center; font-size: 28px;
      background: rgba(56,189,248,0.08); user-select: none;
    }
    #hoverZone {
      border: 3px solid #f59e0b; border-radius: 14px; display: flex; align-items: center; justify-content: center;
      font-size: 18px; background: #422006; transition: background 0.12s, color 0.12s;
    }
    #hoverZone.hot { background: #15803d; border-color: #22c55e; color: #ecfccb; }
    .drag-col { display: flex; flex-direction: column; gap: 10px; }
    #dragSource {
      width: 120px; height: 56px; border-radius: 10px; background: #6366f1; color: #fff;
      display: flex; align-items: center; justify-content: center; cursor: grab; font-size: 14px;
    }
    #dropZone {
      flex: 1; min-height: 120px; border: 3px dashed #a78bfa; border-radius: 14px;
      display: flex; align-items: center; justify-content: center; font-size: 16px; background: rgba(167,139,250,0.08);
    }
    #dropZone.over { background: rgba(34,197,94,0.18); border-color: #22c55e; }
    #dropZone.done { background: rgba(34,197,94,0.28); border-style: solid; }
    #txt {
      width: 100%; height: 44px; border-radius: 8px; border: 1px solid #475569;
      background: #0f172a; color: #f8fafc; padding: 0 12px; font-size: 16px;
    }
  </style>
</head>
<body>
  <div class="banner">
    <div><strong>测试页</strong><small> — 只在这里做人工操作</small></div>
    <span id="lockBadge" class="lock-badge off">UNLOCKED</span>
  </div>
  <main class="main">
    <div class="metrics" id="metrics"></div>
    <div class="zones">
      <div id="clickZone">点击区域</div>
      <div id="hoverZone">Hover 区域（移入应变绿）</div>
      <div class="drag-col">
        <div id="dragSource" draggable="true">拖拽我</div>
        <div id="dropZone">拖放到这里</div>
      </div>
    </div>
    <input id="txt" placeholder="键盘测试：在此输入…" />
  </main>
  <script>
    window.__bench = {
      trustedClicks: 0, trustedKeydowns: 0, trustedHovers: 0, trustedDragStarts: 0, trustedDrops: 0,
      allClicks: 0, allKeydowns: 0, allHovers: 0, allDragStarts: 0, allDrops: 0,
      cdpClicks: 0, cdpKeys: 0, cdpHovers: 0,
    };
    const els = {
      metrics: document.getElementById("metrics"),
      lockBadge: document.getElementById("lockBadge"),
      hoverZone: document.getElementById("hoverZone"),
      dropZone: document.getElementById("dropZone"),
    };
    window.__setLockBanner = (locked) => {
      els.lockBadge.textContent = locked ? "LOCKED" : "UNLOCKED";
      els.lockBadge.className = "lock-badge " + (locked ? "on" : "off");
    };
    window.__resetZones = () => {
      els.hoverZone.classList.remove("hot");
      els.dropZone.classList.remove("over", "done");
      els.dropZone.textContent = "拖放到这里";
    };
    function renderMetrics() {
      const b = window.__bench;
      const items = [
        ["trustedClicks", b.trustedClicks], ["trustedKeys", b.trustedKeydowns],
        ["trustedHovers", b.trustedHovers], ["trustedDrops", b.trustedDrops],
        ["allClicks", b.allClicks], ["allKeys", b.allKeydowns],
        ["allHovers", b.allHovers], ["allDrops", b.allDrops],
        ["cdpClicks", b.cdpClicks], ["cdpKeys", b.cdpKeys], ["cdpHovers", b.cdpHovers],
      ];
      els.metrics.innerHTML = items.map(([k, v]) =>
        "<div class='metric'>" + k + "<b>" + v + "</b></div>"
      ).join("");
    }
    window.__markCdpHover = () => {
      window.__bench.cdpHovers += 1; window.__bench.allHovers += 1;
      els.hoverZone.classList.add("hot"); renderMetrics();
    };
    window.__markCdpClick = () => {
      window.__bench.cdpClicks += 1; window.__bench.allClicks += 1; renderMetrics();
    };
    window.__markCdpKey = () => {
      window.__bench.cdpKeys += 1; window.__bench.allKeydowns += 1; renderMetrics();
    };
    document.addEventListener("click", (e) => {
      window.__bench.allClicks += 1;
      if (e.isTrusted) window.__bench.trustedClicks += 1;
      renderMetrics();
    }, true);
    document.addEventListener("keydown", (e) => {
      window.__bench.allKeydowns += 1;
      if (e.isTrusted) window.__bench.trustedKeydowns += 1;
      renderMetrics();
    }, true);
    els.hoverZone.addEventListener("mouseenter", (e) => {
      window.__bench.allHovers += 1;
      if (e.isTrusted) window.__bench.trustedHovers += 1;
      els.hoverZone.classList.add("hot"); renderMetrics();
    });
    els.hoverZone.addEventListener("mouseleave", () => els.hoverZone.classList.remove("hot"));
    document.getElementById("dragSource").addEventListener("dragstart", (e) => {
      window.__bench.allDragStarts += 1;
      if (e.isTrusted) window.__bench.trustedDragStarts += 1;
      e.dataTransfer.setData("text/plain", "drag-token"); renderMetrics();
    });
    els.dropZone.addEventListener("dragover", (e) => { e.preventDefault(); els.dropZone.classList.add("over"); });
    els.dropZone.addEventListener("dragleave", () => els.dropZone.classList.remove("over"));
    els.dropZone.addEventListener("drop", (e) => {
      e.preventDefault(); window.__bench.allDrops += 1;
      if (e.isTrusted) window.__bench.trustedDrops += 1;
      els.dropZone.classList.remove("over"); els.dropZone.classList.add("done");
      els.dropZone.textContent = "Drop OK"; renderMetrics();
    });
    renderMetrics();
  </script>
</body>
</html>"""

STEPS: list[dict[str, Any]] = [
    {
        "title": "1) 未锁定基线",
        "guide": "点「解锁」，到 Chrome 测试页：点击、输入、hover、拖拽。\n预期：trusted* 增加。",
        "locked": False,
        "kind": "manual",
        "expect": lambda d: (
            d["trustedClicks"] > 0 and d["trustedKeydowns"] > 0
            and d["trustedHovers"] > 0 and d["trustedDrops"] > 0
        ),
        "pass": "PASS：未锁定时点击/键盘/hover/拖拽均可用。",
        "fail": "FAIL：未锁定时应能完成全部人工操作。",
    },
    {
        "title": "2) 锁定阻断人工输入",
        "guide": "点「锁定」，在测试页重复人工操作。\n预期：trusted* 不增；hover 不变绿；拖不进。",
        "locked": True,
        "kind": "manual",
        "expect": lambda d: (
            d["trustedClicks"] == 0 and d["trustedKeydowns"] == 0
            and d["trustedHovers"] == 0 and d["trustedDrops"] == 0
            and d["trustedDragStarts"] == 0
        ),
        "pass": "PASS：锁定后人工输入被阻断。",
        "fail": "FAIL：锁定后仍检测到 trusted 人工输入。",
    },
    {
        "title": "3) 锁定下 CDP 仍可用",
        "guide": "保持锁定，不要点测试页。在本 Tk 面板「CDP 模拟器」点按钮。\n预期：测试页 cdp* / all* 增加。",
        "locked": True,
        "kind": "cdp",
        "expect": lambda d: d["cdpHovers"] > 0 and d["cdpClicks"] > 0 and d["cdpKeys"] > 0,
        "pass": "PASS：锁定下 CDP 仍能驱动测试页。",
        "fail": "FAIL：CDP 未生效（请用本面板按钮，不要点测试页）。",
    },
    {
        "title": "4) 解锁后恢复",
        "guide": "点「解锁」，再到测试页做人工操作。\n预期：trusted* 恢复增长。",
        "locked": False,
        "kind": "manual",
        "expect": lambda d: (
            d["trustedClicks"] > 0 and d["trustedKeydowns"] > 0
            and d["trustedHovers"] > 0 and d["trustedDrops"] > 0
        ),
        "pass": "PASS：解锁后人工输入恢复。",
        "fail": "FAIL：解锁后 trusted 输入未恢复。",
    },
]


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_json(url: str, timeout: float = 30.0) -> Any:
    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as err:
            last_err = err
            time.sleep(0.2)
    raise RuntimeError(f"CDP endpoint not ready: {url} ({last_err})")


class Cdp:
    def __init__(self, ws_url: str):
        self._lock = threading.Lock()
        self.ws = websocket.create_connection(ws_url, timeout=20, origin="http://127.0.0.1")
        self._id = 0

    def send(self, method: str, params: dict | None = None) -> dict:
        with self._lock:
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

    def evaluate(self, expression: str) -> Any:
        result = self.send(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": False},
        )
        if result.get("exceptionDetails"):
            raise RuntimeError(result["exceptionDetails"])
        return result.get("result", {}).get("value")

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:
            pass


class BenchApp:
    def __init__(self, chrome: Path):
        self.chrome = chrome
        self.port = find_free_port()
        self.profile = Path(tempfile.mkdtemp(prefix="input-lock-bench-"))
        self.html_path = self.profile / "test.html"
        self.html_path.write_text(TEST_HTML, encoding="utf-8")
        self.proc: subprocess.Popen[Any] | None = None
        self.cdp: Cdp | None = None
        self.current_step = 0
        self.step_results: list[bool | None] = [None] * len(STEPS)
        self.step_baseline: dict[str, int] | None = None
        self.kernel_locked = False

        self.root = tk.Tk()
        self.root.title("Input Lock — Control Panel (Native)")
        self.root.geometry("460x780")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_ui()
        self.root.after(100, self.bootstrap)

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}
        frm = ttk.Frame(self.root, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="控制面板（原生窗口，不在 Chrome 内）", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, **pad)

        lock_frm = ttk.LabelFrame(frm, text="内核输入闸 Input.setUserInputLocked", padding=8)
        lock_frm.pack(fill=tk.X, **pad)
        row = ttk.Frame(lock_frm)
        row.pack(fill=tk.X)
        ttk.Button(row, text="🔒 锁定", command=lambda: self.set_lock(True)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(row, text="🔓 解锁", command=lambda: self.set_lock(False)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self.lock_label = ttk.Label(lock_frm, text="当前：UNLOCKED")
        self.lock_label.pack(pady=4)

        step_frm = ttk.LabelFrame(frm, text="验收步骤", padding=8)
        step_frm.pack(fill=tk.X, **pad)
        self.step_var = tk.StringVar(value=STEPS[0]["title"])
        self.step_combo = ttk.Combobox(
            step_frm, textvariable=self.step_var, values=[s["title"] for s in STEPS], state="readonly"
        )
        self.step_combo.pack(fill=tk.X)
        self.step_combo.bind("<<ComboboxSelected>>", self.on_step_selected)
        self.guide_label = ttk.Label(step_frm, text=STEPS[0]["guide"], wraplength=420, justify=tk.LEFT)
        self.guide_label.pack(fill=tk.X, pady=6)
        nav = ttk.Frame(step_frm)
        nav.pack(fill=tk.X)
        ttk.Button(nav, text="上一步", command=lambda: self.goto_step(self.current_step - 1)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(nav, text="下一步", command=lambda: self.goto_step(self.current_step + 1)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(step_frm, text="完成本步并判定", command=self.finish_step).pack(fill=tk.X, pady=4)
        self.verdict = scrolledtext.ScrolledText(step_frm, height=6, font=("Consolas", 9))
        self.verdict.pack(fill=tk.X)

        cdp_frm = ttk.LabelFrame(frm, text="CDP 模拟器（Agent 路径 → 测试页）", padding=8)
        cdp_frm.pack(fill=tk.X, **pad)
        ttk.Label(
            cdp_frm,
            text="在此点按钮 = 对 Chrome 测试页发 Input.dispatch*。\n不是把测试页人手点击变成 CDP。",
            wraplength=420,
        ).pack(anchor=tk.W)
        cdp_row = ttk.Frame(cdp_frm)
        cdp_row.pack(fill=tk.X, pady=4)
        ttk.Button(cdp_row, text="CDP Hover", command=self.cdp_hover).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(cdp_row, text="CDP Click", command=self.cdp_click).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(cdp_row, text="CDP Drag/Drop", command=self.cdp_drag).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        key_row = ttk.Frame(cdp_frm)
        key_row.pack(fill=tk.X, pady=4)
        self.key_entry = ttk.Entry(key_row)
        self.key_entry.insert(0, "a")
        self.key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        ttk.Button(key_row, text="CDP 发送键", command=self.cdp_key).pack(side=tk.RIGHT)

        ttk.Label(frm, text="测试页实时计数").pack(anchor=tk.W, **pad)
        self.metrics = scrolledtext.ScrolledText(frm, height=10, font=("Consolas", 9))
        self.metrics.pack(fill=tk.BOTH, expand=True)

    def log_verdict(self, text: str) -> None:
        self.verdict.delete("1.0", tk.END)
        self.verdict.insert(tk.END, text)

    def bootstrap(self) -> None:
        try:
            cmd = [
                str(self.chrome),
                f"--user-data-dir={self.profile}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-sync",
                "--window-size=1100,860",
                "--window-position=520,40",
                f"--remote-debugging-port={self.port}",
                "--remote-allow-origins=*",
                self.html_path.as_uri(),
            ]
            self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            targets = wait_json(f"http://127.0.0.1:{self.port}/json/list")
            page = next((t for t in targets if t.get("type") == "page"), None)
            if not page:
                raise RuntimeError("no page target")
            self.cdp = Cdp(page["webSocketDebuggerUrl"])
            self.cdp.send("Runtime.enable")
            for _ in range(50):
                if self.cdp.evaluate("document.getElementById('clickZone') ? true : false"):
                    break
                time.sleep(0.1)
            self.goto_step(0)
            self.poll_metrics()
        except Exception as err:
            self.log_verdict(f"启动失败: {err}")
            self.on_close()

    def require_cdp(self) -> Cdp:
        if not self.cdp:
            raise RuntimeError("CDP not connected")
        return self.cdp

    def snapshot(self) -> dict[str, int]:
        cdp = self.require_cdp()
        data = cdp.evaluate("JSON.parse(JSON.stringify(window.__bench))")
        if not isinstance(data, dict):
            raise RuntimeError("invalid bench snapshot")
        return {k: int(v) for k, v in data.items()}

    @staticmethod
    def delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
        return {k: after.get(k, 0) - before.get(k, 0) for k in after}

    def zone_center(self, selector: str) -> tuple[float, float]:
        cdp = self.require_cdp()
        pt = cdp.evaluate(
            f"""(() => {{
              const r = document.querySelector({json.dumps(selector)}).getBoundingClientRect();
              return {{ x: r.left + r.width / 2, y: r.top + r.height / 2 }};
            }})()"""
        )
        return float(pt["x"]), float(pt["y"])

    def set_lock(self, locked: bool) -> None:
        try:
            cdp = self.require_cdp()
            cdp.send("Input.setUserInputLocked", {"locked": locked})
            cdp.evaluate(f"window.__setLockBanner({json.dumps(locked)})")
            self.kernel_locked = locked
            self.lock_label.config(text=f"当前：{'LOCKED' if locked else 'UNLOCKED'}")
        except Exception as err:
            self.log_verdict(f"锁定失败: {err}")

    def reset_zones(self) -> None:
        self.require_cdp().evaluate("window.__resetZones()")

    def goto_step(self, index: int) -> None:
        if index < 0 or index >= len(STEPS):
            return
        self.current_step = index
        step = STEPS[index]
        self.step_var.set(step["title"])
        self.guide_label.config(text=step["guide"])
        try:
            self.reset_zones()
            self.step_baseline = self.snapshot()
            self.set_lock(bool(step["locked"]))
            hint = (
                "步骤已开始：请用下方 CDP 按钮（不要点测试页）。"
                if step["kind"] == "cdp"
                else "步骤已开始：请到 Chrome 测试页做人工操作。"
            )
            self.log_verdict(hint)
        except Exception as err:
            self.log_verdict(f"切换步骤失败: {err}")

    def on_step_selected(self, _event: object) -> None:
        title = self.step_var.get()
        for i, step in enumerate(STEPS):
            if step["title"] == title:
                self.goto_step(i)
                break

    def finish_step(self) -> None:
        step = STEPS[self.current_step]
        try:
            after = self.snapshot()
            before = self.step_baseline or after
            d = self.delta(before, after)
            expect: Callable[[dict[str, int]], bool] = step["expect"]
            ok = bool(expect(d))
            self.step_results[self.current_step] = ok
            msg = (step["pass"] if ok else step["fail"]) + "\n\n本步增量:\n" + json.dumps(d, indent=2)
            self.log_verdict(msg)
        except Exception as err:
            self.log_verdict(f"判定失败: {err}")

    def cdp_hover(self) -> None:
        try:
            cdp = self.require_cdp()
            x, y = self.zone_center("#hoverZone")
            cdp.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
            cdp.evaluate("window.__markCdpHover()")
        except Exception as err:
            self.log_verdict(f"CDP hover 失败: {err}")

    def cdp_click(self) -> None:
        try:
            cdp = self.require_cdp()
            x, y = self.zone_center("#clickZone")
            for etype in ("mousePressed", "mouseReleased"):
                cdp.send(
                    "Input.dispatchMouseEvent",
                    {"type": etype, "x": x, "y": y, "button": "left", "clickCount": 1},
                )
            cdp.evaluate("window.__markCdpClick()")
        except Exception as err:
            self.log_verdict(f"CDP click 失败: {err}")

    def cdp_key(self) -> None:
        key = self.key_entry.get() or "a"
        try:
            cdp = self.require_cdp()
            x, y = self.zone_center("#txt")
            for etype in ("mousePressed", "mouseReleased"):
                cdp.send(
                    "Input.dispatchMouseEvent",
                    {"type": etype, "x": x, "y": y, "button": "left", "clickCount": 1},
                )
            text = key if len(key) == 1 else ""
            params: dict[str, Any] = {"type": "keyDown", "key": key}
            if text:
                params["text"] = text
            cdp.send("Input.dispatchKeyEvent", params)
            if text:
                cdp.send("Input.dispatchKeyEvent", {"type": "char", "key": key, "text": text})
            cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": key})
            cdp.evaluate("window.__markCdpKey()")
        except Exception as err:
            self.log_verdict(f"CDP key 失败: {err}")

    def cdp_drag(self) -> None:
        try:
            cdp = self.require_cdp()
            sx, sy = self.zone_center("#dragSource")
            dx, dy = self.zone_center("#dropZone")
            data = {"items": [{"mimeType": "text/plain", "data": "drag-token"}], "dragOperationsMask": 1}
            cdp.send("Input.dispatchDragEvent", {"type": "dragEnter", "x": sx, "y": sy, "data": data})
            cdp.send("Input.dispatchDragEvent", {"type": "dragOver", "x": dx, "y": dy, "data": data})
            cdp.send("Input.dispatchDragEvent", {"type": "drop", "x": dx, "y": dy, "data": data})
        except Exception as err:
            self.log_verdict(f"CDP drag 失败: {err}")

    def poll_metrics(self) -> None:
        if self.cdp:
            try:
                snap = self.snapshot()
                self.metrics.delete("1.0", tk.END)
                self.metrics.insert(tk.END, json.dumps(snap, indent=2))
            except Exception:
                pass
        self.root.after(400, self.poll_metrics)

    def on_close(self) -> None:
        try:
            if self.cdp:
                self.cdp.send("Input.setUserInputLocked", {"locked": False})
                self.cdp.close()
        except Exception:
            pass
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    default = Path(r"E:\ungoogled-chromium-windows\build\src\out\Default\chrome.exe")
    chrome = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    if not chrome.is_file():
        print(f"FAIL: chrome.exe not found: {chrome}")
        return 1
    BenchApp(chrome).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
