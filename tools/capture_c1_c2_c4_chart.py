import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = r"file:///C:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html"
OUT_DIR = r"C:\Users\ayu23\.gemini\antigravity-ide\brain\d789151d-6b04-46db-87e0-ca30f1fbc13a"

async def capture_conc_chart():
    port = 9222
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--window-size=1600,1050",
        "--hide-scrollbars",
        "--disable-gpu",
        URL
    ])
    time.sleep(2.0)
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
        targets = json.loads(req.read().decode("utf-8"))
        page_targets = [t for t in targets if t.get("type") == "page"]
        ws_url = page_targets[0]["webSocketDebuggerUrl"]
    except Exception as e:
        print(f"Failed to connect: {e}")
        chrome_proc.terminate()
        return

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        msg_id = 0
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
        await send("Runtime.enable")
        await asyncio.sleep(0.5)

        js_script = """
        (() => {
            if (typeof window.switchTab === 'function') {
                window.switchTab('scaleout');
            }
            const el = document.getElementById('scaleout-concurrency-charts-container');
            if (el) {
                el.scrollIntoView();
                window.scrollBy(0, -60);
            } else {
                window.scrollTo(0, 1500);
            }
        })();
        """
        await send("Runtime.evaluate", {"expression": js_script})
        await asyncio.sleep(1.0)

        shot_res = await send("Page.captureScreenshot", {"format": "png"})
        img_bytes = base64.b64decode(shot_res.get("data", ""))
        out_path = os.path.join(OUT_DIR, "ss_c1_vs_c2_vs_c4_concurrency_charts.png")
        with open(out_path, "wb") as f:
            f.write(img_bytes)
        print(f"Saved: {out_path} ({len(img_bytes)} bytes)")

    chrome_proc.terminate()

if __name__ == "__main__":
    asyncio.run(capture_conc_chart())
