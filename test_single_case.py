import subprocess

def run_test():
    cmd = (
        "cd /home/ayu23/V9_FULL && source /home/ayu23/vllm_env/bin/activate && "
        "python3 v9_core/run_single.py --model-profile configs/models/kimi_linear_48b.json "
        "--matrix /home/ayu23/v9_full_results/v9_test2_20260927_163750/logs/V9_MATRIX.json "
        "--out /tmp/test_single_run --case tp4_context_baseline --port 8000"
    )
    full_cmd = f'gcloud compute ssh ayu23@kimi-node-0 --zone=us-central1-b --tunnel-through-iap --command="{cmd}"'
    print("Testing single server launch with fixed code...")
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == '__main__':
    run_test()
