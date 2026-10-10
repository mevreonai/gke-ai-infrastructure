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

async def capture_all():
    port = 9222
    # Start Chrome with remote debugging
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--window-size=1600,1050",
        "--hide-scrollbars",
        "--disable-gpu",
        URL
    ])
    
    time.sleep(2)
    
    # Query targets
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
        targets = json.loads(req.read().decode("utf-8"))
        ws_url = targets[0]["webSocketDebuggerUrl"]
        print(f"Connected to CDP: {ws_url}")
    except Exception as e:
        print(f"Failed to connect to Chrome: {e}")
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

        # Tasks to capture:
        tasks = [
            {
                "name": "proof_change1_key_discoveries_trust_strip.png",
                "js": """
                window.switchTab('keydiscoveries');
                window.scrollTo(0, 0);
                """
            },
            {
                "name": "proof_change2_profiler_wall_time_budget.png",
                "js": """
                window.switchTab('profiler');
                const el = document.getElementById('wall-time-budget-card') || document.querySelector('.profiler-card') || document.querySelector('section#profiler');
                if (el) el.scrollIntoView();
                window.scrollBy(0, -100);
                """
            },
            {
                "name": "proof_change3_evidence_stack_and_ledger.png",
                "js": """
                window.switchTab('evidence');
                const el = document.querySelector('.evidence-stack-banner') || document.getElementById('evidence-grid') || document.querySelector('section#evidence');
                if (el) el.scrollIntoView();
                window.scrollBy(0, -50);
                """
            },
            {
                "name": "proof_change4_long_context_fp8_offload_cards.png",
                "js": """
                window.switchTab('long');
                const el = document.getElementById('long') || document.querySelector('section#long');
                window.scrollTo(0, 450);
                """
            },
            {
                "name": "proof_change5_scaleout_15_12_layer_split.png",
                "js": """
                window.switchTab('scaleout');
                window.scrollTo(0, 500);
                """
            },
            {
                "name": "proof_change6_scheduler_ttft_advantage.png",
                "js": """
                window.switchTab('sched');
                window.scrollTo(0, 400);
                """
            },
            {
                "name": "proof_change7_evidence_modal_popup.png",
                "js": """
                window.switchTab('keydiscoveries');
                if (typeof window.openEvidenceModal === 'function') {
                    window.openEvidenceModal('EV-001', 'Dual-Node RTX 6000 Ada Baseline & Hardware Envelope');
                } else if (typeof window.openFindingSubPage === 'function') {
                    window.openFindingSubPage(1, '');
                }
                """
            }
        ]

        for task in tasks:
            print(f"Capturing {task['name']}...")
            await send("Runtime.evaluate", {"expression": task["js"]})
            await asyncio.sleep(1)
            shot_res = await send("Page.captureScreenshot", {"format": "png"})
            import base64
            img_bytes = base64.b64decode(shot_res.get("data", ""))
            out_path = os.path.join(OUT_DIR, task["name"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"Saved: {out_path} ({len(img_bytes)} bytes)")

    chrome_proc.terminate()

if __name__ == "__main__":
    asyncio.run(capture_all())
