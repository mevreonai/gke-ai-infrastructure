import subprocess
import json

def inspect():
    cmd = 'gcloud compute ssh ayu23@kimi-node-0 --zone=us-central1-b --tunnel-through-iap --command="cat /tmp/test_single_run/v9_single_manifest.json"'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        print("Cases in manifest:", len(data.get("cases", [])))
        for c in data.get("cases", []):
            print("Case:", c.get("name"), "Status:", c.get("status"))
            for b in c.get("benchmarks", []):
                print("  Benchmark:", b.get("name"), "Status:", b.get("status"), "Metrics:", b.get("metrics"))
    except Exception as e:
        print("Raw output:", res.stdout[:500])
        print("Error:", e)

if __name__ == '__main__':
    inspect()
