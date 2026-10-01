import subprocess
import sys

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    ip = "136.65.229.197"
    key = r"C:\Users\ayu23\.ssh\google_compute_engine"
    
    if cmd == "start":
        remote_cmd = "chmod +x /home/ayu23/run_scaleout_and_finish.sh && nohup /home/ayu23/run_scaleout_and_finish.sh > /home/ayu23/v9_full_results/v9_full_production_20260930_143117/logs/scaleout_finish.log 2>&1 &"
    elif cmd == "status":
        remote_cmd = "ps aux | grep -E 'run_scaleout|run_multi|vllm serve' | grep -v grep; echo '--- LOG TAIL ---'; tail -n 20 /home/ayu23/v9_full_results/v9_full_production_20260930_143117/logs/scaleout_finish.log 2>/dev/null || echo 'no log yet'"
    elif cmd == "tail":
        remote_cmd = "tail -n 30 /home/ayu23/v9_full_results/v9_full_production_20260930_143117/logs/scaleout_finish.log"
    else:
        remote_cmd = cmd

    ssh_cmd = [
        "ssh", "-i", key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=NUL",
        f"ayu23@{ip}",
        remote_cmd
    ]
    res = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if res.stdout:
        print(res.stdout.encode("ascii", errors="replace").decode("ascii"))
    if res.stderr and res.returncode != 0:
        print(res.stderr.encode("ascii", errors="replace").decode("ascii"), file=sys.stderr)

if __name__ == "__main__":
    main()
