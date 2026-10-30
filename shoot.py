#!/usr/bin/env python3
"""用 headless Chrome 截圖檢查版面：python3 shoot.py [輸出資料夾]"""
import sys, subprocess, time, http.server, threading, functools
from pathlib import Path
from playwright.sync_api import sync_playwright
root = Path(__file__).resolve().parent / "docs"
out = Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/screenshots"); out.mkdir(parents=True, exist_ok=True)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = sys.argv[2] if len(sys.argv) > 2 else f"http://127.0.0.1:{port}/"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    for name, w, h, mob in (("mobile", 390, 844, True), ("desktop", 1280, 800, False)):
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2 if mob else 1, is_mobile=mob, has_touch=mob)
        errs = []; pg.on("console", lambda m: m.type == "error" and errs.append(m.text)); pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url, wait_until="networkidle")
        pg.screenshot(path=str(out / f"{name}.png"))
        pg.screenshot(path=str(out / f"{name}-full.png"), full_page=True)
        pg.click(".card .toggle"); pg.click(".card .more"); time.sleep(0.3)
        pg.screenshot(path=str(out / f"{name}-open.png"), full_page=True)
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(0.8)  # 讓 lazy 圖片載入後再檢查
        broken = pg.evaluate("[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src)")
        sw = pg.evaluate("document.documentElement.scrollWidth")
        print(name, "errors:", errs, "broken imgs:", broken, "scrollWidth:", sw)
    b.close()
srv.shutdown()
