import subprocess
import time

def harvest():
    print("Waiting 10s for sshd...")
    time.sleep(10)
    cmd = (
        'tail -n 80 /home/ayu23/v9_test2_execution.log; '
        'echo === PHASE_STATUS ===; '
        'cat /home/ayu23/v9_full_results/v9_test2_20260927_163750/logs/phase_status.jsonl; '
        'echo === ARCHIVES ===; '
        'ls -la /home/ayu23/V9_TEST2* /home/ayu23/v9_full_results/*.tar.gz'
    )
    full_cmd = f'gcloud compute ssh ayu23@kimi-node-0 --zone=us-central1-b --tunnel-through-iap --command="{cmd}"'
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == '__main__':
    harvest()
