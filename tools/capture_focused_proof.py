import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = r"file:///C:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html"
OUT_DIR = r"C:\Users\ayu23\.gemini\antigravity-ide\brain\d789151d-6b04-46db-87e0-ca30f1fbc13a"

async def capture_focused():
    port = 9223
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--window-size=1600,1100",
        "--hide-scrollbars",
        "--disable-gpu",
        URL
    ])
    
    time.sleep(2)
    
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
        targets = json.loads(req.read().decode("utf-8"))
        ws_url = targets[0]["webSocketDebuggerUrl"]
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
        await asyncio.sleep(1)

        tasks = [
            {
                "name": "ss_part1_additional_runs_scaleout_rebalance.png",
                "js": """
                window.switchTab('scaleout');
                window.scrollTo(0, 650);
                """
            },
            {
                "name": "ss_part1_additional_runs_profiler_timings.png",
                "js": """
                window.switchTab('profiler');
                window.scrollTo(0, 800);
                """
            },
            {
                "name": "ss_part2_failed_runs_long_context_cards.png",
                "js": """
                window.switchTab('long');
                window.scrollTo(0, 500);
                """
            },
            {
                "name": "ss_part2_failed_runs_evidence_table.png",
                "js": """
                window.switchTab('evidence');
                window.scrollTo(0, 850);
                """
            }
        ]

        for t in tasks:
            print(f"Capturing {t['name']}...")
            await send("Runtime.evaluate", {"expression": t["js"]})
            await asyncio.sleep(1)
            shot_res = await send("Page.captureScreenshot", {"format": "png"})
            import base64
            img_bytes = base64.b64decode(shot_res.get("data", ""))
            out_path = os.path.join(OUT_DIR, t["name"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"Saved: {out_path} ({len(img_bytes)} bytes)")

    chrome_proc.terminate()

if __name__ == "__main__":
    asyncio.run(capture_focused())
