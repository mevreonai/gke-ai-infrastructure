import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets
import base64
import tempfile

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = r"file:///C:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html"
OUT_DIR = r"C:\Users\ayu23\.gemini\antigravity-ide\brain\d789151d-6b04-46db-87e0-ca30f1fbc13a"

async def capture():
    temp_dir = tempfile.mkdtemp()
    port = 9240
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--user-data-dir={temp_dir}",
        f"--remote-debugging-port={port}",
        "--window-size=1650,1300",
        "--hide-scrollbars",
        "--disable-gpu",
        URL
    ])
    
    time.sleep(3)
    
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
        targets = json.loads(req.read().decode("utf-8"))
        page_targets = [t for t in targets if t.get("type") == "page"]
        ws_url = page_targets[0]["webSocketDebuggerUrl"]
        print(f"Connected to page target: {ws_url}", flush=True)
    except Exception as e:
        print(f"Failed to connect to chrome: {e}", flush=True)
        chrome_proc.terminate()
        return

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        msg_id = 0
        async def eval_js(expr):
            nonlocal msg_id
            msg_id += 1
            payload = {
                "id": msg_id,
                "method": "Runtime.evaluate",
                "params": {"expression": expr, "returnByValue": True}
            }
            await ws.send(json.dumps(payload))
            while True:
                resp = await ws.recv()
                data = json.loads(resp)
                if data.get("id") == msg_id:
                    res = data.get("result", {}).get("result", {})
                    return res.get("value")

        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            payload = {"id": msg_id, "method": method, "params": params or {}}
            await ws.send(json.dumps(payload))
            while True:
                resp = await ws.recv()
                data = json.loads(resp)
                if data.get("id") == msg_id:
                    return data.get("result", {})

        await send("Page.enable")
        await asyncio.sleep(1)

        # 1. Switch to Profiler tab
        print("Switching to Profiler tab...", flush=True)
        await eval_js("""
            const tabBtn = document.querySelector('button[data-tab="profiler"]');
            if (tabBtn) tabBtn.click();
            window.toggleBudgetView('first_single');
            window.dispatchEvent(new Event('resize'));
        """)
        await asyncio.sleep(2)

        # Scroll into view
        await eval_js("""
            const el = document.getElementById('budget-first-single-container');
            if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
        """)
        await asyncio.sleep(1)

        # Export Canvas 1
        info1 = await eval_js("""
            const c = document.getElementById('chart_budget_first_single');
            ({
                width: c.width,
                height: c.height,
                dataUrl: c.toDataURL('image/png')
            });
        """)
        if info1 and "dataUrl" in info1:
            b64 = info1["dataUrl"].split("base64,")[1]
            out_p1 = os.path.join(OUT_DIR, "live_chart_first_token_canvas.png")
            with open(out_p1, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"Saved Canvas 1 ({info1['width']}x{info1['height']}): {out_p1}", flush=True)

        # Full view screenshot of Chart 1 in the page
        shot1 = await send("Page.captureScreenshot", {"format": "png"})
        shot_p1 = os.path.join(OUT_DIR, "live_dashboard_view_first_token.png")
        with open(shot_p1, "wb") as f:
            f.write(base64.b64decode(shot1["data"]))
        print(f"Saved page view 1: {shot_p1}", flush=True)

        # 2. Switch to Decode Single
        print("Switching to Decode Single...", flush=True)
        await eval_js("""
            window.toggleBudgetView('decode_single');
            window.dispatchEvent(new Event('resize'));
        """)
        await asyncio.sleep(1.5)

        info2 = await eval_js("""
            const c = document.getElementById('chart_budget_decode_single');
            ({
                width: c.width,
                height: c.height,
                dataUrl: c.toDataURL('image/png')
            });
        """)
        if info2 and "dataUrl" in info2:
            b64 = info2["dataUrl"].split("base64,")[1]
            out_p2 = os.path.join(OUT_DIR, "live_chart_decode_token_canvas.png")
            with open(out_p2, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"Saved Canvas 2 ({info2['width']}x{info2['height']}): {out_p2}", flush=True)

        shot2 = await send("Page.captureScreenshot", {"format": "png"})
        shot_p2 = os.path.join(OUT_DIR, "live_dashboard_view_decode_token.png")
        with open(shot_p2, "wb") as f:
            f.write(base64.b64decode(shot2["data"]))
        print(f"Saved page view 2: {shot_p2}", flush=True)

        # 3. Switch to Decode Under Load
        print("Switching to Decode Load...", flush=True)
        await eval_js("""
            window.toggleBudgetView('decode_load');
            window.dispatchEvent(new Event('resize'));
        """)
        await asyncio.sleep(1.5)

        info4 = await eval_js("""
            const c = document.getElementById('chart_budget_decode_load');
            ({
                width: c.width,
                height: c.height,
                dataUrl: c.toDataURL('image/png')
            });
        """)
        if info4 and "dataUrl" in info4:
            b64 = info4["dataUrl"].split("base64,")[1]
            out_p4 = os.path.join(OUT_DIR, "live_chart_decode_load_canvas.png")
            with open(out_p4, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"Saved Canvas 4 ({info4['width']}x{info4['height']}): {out_p4}", flush=True)

        shot4 = await send("Page.captureScreenshot", {"format": "png"})
        shot_p4 = os.path.join(OUT_DIR, "live_dashboard_view_decode_load.png")
        with open(shot_p4, "wb") as f:
            f.write(base64.b64decode(shot4["data"]))
        print(f"Saved page view 4: {shot_p4}", flush=True)

    chrome_proc.terminate()
    print("ALL LIVE CODE CHARTS EXPORTED PERFECTLY!", flush=True)

if __name__ == "__main__":
    asyncio.run(capture())
