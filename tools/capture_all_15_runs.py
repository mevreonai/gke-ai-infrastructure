import asyncio
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
import websockets

sys.stdout.reconfigure(encoding='utf-8')

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = r"file:///C:/Users/ayu23/OneDrive/Desktop/tpu/v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html"
OUT_DIR = r"C:\Users\ayu23\.gemini\antigravity-ide\brain\d789151d-6b04-46db-87e0-ca30f1fbc13a"

RUNS_CONFIG = [
    # --- PART 1: 8 ADDITIONAL RUNS ---
    {
        "id": "run_add_1",
        "file": "ss_add_run1_chunk_budget_8448.png",
        "desc": "Additional Run 1: 8K Chunk Budget A/B Test (8192 vs 8448 fix)",
        "tab": "executive",
        "scroll_y": 0
    },
    {
        "id": "run_add_2",
        "file": "ss_add_run2_graphs_on_torch_profiler.png",
        "desc": "Additional Run 2: Graphs-On Torch Profiler under Load (8K c=8, c=32)",
        "tab": "profiler",
        "scroll_y": 800
    },
    {
        "id": "run_add_3",
        "file": "ss_add_run3_pp2_15_12_layer_split.png",
        "desc": "Additional Run 3: PP2 15/12 Layer Split Optimization (+1.18% speedup)",
        "tab": "scaleout",
        "scroll_y": 650
    },
    {
        "id": "run_add_4",
        "file": "ss_add_run4_8gpu_kv_pool_audit.png",
        "desc": "Additional Run 4: 8-GPU KV Pool Log Audit (8.14M vs 8.21M tokens)",
        "tab": "sched",
        "scroll_y": 300
    },
    {
        "id": "run_add_5",
        "file": "ss_add_run5_interactive_sub8k_short_prompts.png",
        "desc": "Additional Run 5: Sub-8K Short Prompts & Collective Overhead",
        "tab": "scaleup",
        "scroll_y": 450
    },
    {
        "id": "run_add_6",
        "file": "ss_add_run6_tp16_512k_prefill_recapture.png",
        "desc": "Additional Run 6: TP16 512K Prefill Re-Capture (Profiler View)",
        "tab": "profiler",
        "scroll_y": 600
    },
    {
        "id": "run_add_7",
        "file": "ss_add_run7_nccl_provider_socket_threads.png",
        "desc": "Additional Run 7: NCCL Provider Plugin & Socket Threads (173.58 Gb/s Native Fabric)",
        "tab": "evidence",
        "scroll_y": 180
    },
    {
        "id": "run_add_8",
        "file": "ss_add_run8_closed_loop_wave_trimming.png",
        "desc": "Additional Run 8: Closed-Loop Wave 1 & Drain Trimming (Steady-State Throughput)",
        "tab": "executive",
        "scroll_y": 250
    },

    # --- PART 2: 7 FAILED APPLICATION RUNS ---
    {
        "id": "run_fail_1",
        "file": "ss_failed_run1_fp8_128k_c1.png",
        "desc": "Failed Run 1: tp4_fp8_kv 128k_c1 (EV-055) Assertion Guarded",
        "tab": "evidence",
        "selector": "#ev-row-EV-055",
        "scroll_y": -120
    },
    {
        "id": "run_fail_2",
        "file": "ss_failed_run2_fp8_128k_c4.png",
        "desc": "Failed Run 2: tp4_fp8_kv 128k_c4 (EV-056) Assertion Guarded",
        "tab": "evidence",
        "selector": "#ev-row-EV-056",
        "scroll_y": -120
    },
    {
        "id": "run_fail_3",
        "file": "ss_failed_run3_fp8_512k_c1.png",
        "desc": "Failed Run 3: tp4_fp8_kv 512k_c1 (EV-057) Assertion Guarded",
        "tab": "evidence",
        "selector": "#ev-row-EV-057",
        "scroll_y": -120
    },
    {
        "id": "run_fail_4",
        "file": "ss_failed_run4_fp8_1m_c1.png",
        "desc": "Failed Run 4: tp4_fp8_kv_1m 1m_c1 (EV-074) & FP8 Root Cause Card",
        "tab": "long",
        "scroll_y": 750
    },
    {
        "id": "run_fail_5",
        "file": "ss_failed_run5_offload_128k_c1.png",
        "desc": "Failed Run 5: tp4_native_offload_pressure 128k_c1 (EV-058) Memory Rejection",
        "tab": "evidence",
        "selector": "#ev-row-EV-058",
        "scroll_y": -120
    },
    {
        "id": "run_fail_6",
        "file": "ss_failed_run6_offload_512k_c1.png",
        "desc": "Failed Run 6: tp4_native_offload_pressure 512k_c1 (EV-059) Memory Rejection",
        "tab": "evidence",
        "selector": "#ev-row-EV-059",
        "scroll_y": -120
    },
    {
        "id": "run_fail_7",
        "file": "ss_failed_run7_offload_1m_c1.png",
        "desc": "Failed Run 7: tp4_native_offload_pressure 1m_c1 (EV-060) & DDR5 Offload Penalty Card",
        "tab": "long",
        "scroll_y": 500
    }
]

async def main():
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
        if not page_targets:
            print("No page target found!")
            chrome_proc.terminate()
            return
        ws_url = page_targets[0]["webSocketDebuggerUrl"]
        print(f"Connected to Chrome page at {ws_url}", flush=True)
    except Exception as e:
        print(f"Failed to connect: {e}", flush=True)
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

        for item in RUNS_CONFIG:
            print(f"Processing: {item['desc']} -> {item['file']}", flush=True)
            sel = item.get("selector")
            js_script = f"""
            (() => {{
                if (typeof window.switchTab === 'function') {{
                    window.switchTab('{item['tab']}');
                }}
                
                document.querySelectorAll('.active-highlight-trace').forEach(el => {{
                    el.style.outline = '';
                    el.style.backgroundColor = '';
                    el.classList.remove('active-highlight-trace');
                }});

                const sel = '{sel or ''}';
                let el = null;
                if (sel) {{
                    el = document.querySelector(sel);
                }}
                if (el) {{
                    el.scrollIntoView();
                    window.scrollBy(0, {item['scroll_y']});
                    el.classList.add('active-highlight-trace');
                    el.style.outline = '3px solid #f59e0b';
                    el.style.backgroundColor = 'rgba(245, 158, 11, 0.2)';
                }} else {{
                    window.scrollTo(0, {item['scroll_y']});
                }}
            }})();
            """
            await send("Runtime.evaluate", {"expression": js_script})
            await asyncio.sleep(0.5)

            shot_res = await send("Page.captureScreenshot", {"format": "png"})
            img_bytes = base64.b64decode(shot_res.get("data", ""))
            out_path = os.path.join(OUT_DIR, item["file"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
    chrome_proc.terminate()
    print("ALL 15 SCREENSHOTS CAPTURED SUCCESSFULLY!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
