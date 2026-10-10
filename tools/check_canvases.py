import asyncio, json, urllib.request, websockets, subprocess, time, tempfile

async def test():
    temp_dir = tempfile.mkdtemp()
    port = 9235
    proc = subprocess.Popen([
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        f"--user-data-dir={temp_dir}",
        f"--remote-debugging-port={port}",
        r"file:///C:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html"
    ])
    time.sleep(3)
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
        targets = json.loads(req.read().decode("utf-8"))
        page_targets = [t for t in targets if t.get("type") == "page"]
        ws_url = page_targets[0]["webSocketDebuggerUrl"]
        async with websockets.connect(ws_url) as ws:
            msg_id = 0
            async def call(expr):
                nonlocal msg_id
                msg_id += 1
                await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": expr, "returnByValue": True}}))
                while True:
                    r = await ws.recv()
                    data = json.loads(r)
                    if data.get("id") == msg_id:
                        return data.get("result", {}).get("result", {}).get("value")
            
            print("URL:", await call("window.location.href"), flush=True)
            print("Total Canvases:", await call("document.querySelectorAll('canvas').length"), flush=True)
            print("Canvas IDs:", await call("Array.from(document.querySelectorAll('canvas')).map(c => c.id).filter(id => id.includes('budget'))"), flush=True)
            print("Element budget-first-single-container:", await call("Boolean(document.getElementById('budget-first-single-container'))"), flush=True)
    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(test())
