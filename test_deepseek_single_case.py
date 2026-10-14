import subprocess

cmd = (
    "source /home/user/vllm_env/bin/activate && "
    "export CUDA_HOME=/usr/local/cuda && "
    "export PATH=/home/user/vllm_env/bin:/usr/local/cuda/bin:$PATH && "
    "cd /home/user/V9_FULL && "
    "python3 v9_core/run_single.py --model-profile configs/models/deepseek_v41_flash.json "
    "--matrix /home/user/v9_full_results/v9_full_production_20260930_090004/logs/V9_MATRIX.json "
    "--out /tmp/test_single_ds --case tp8_context_baseline --port 8000"
)

res = subprocess.run(["python", "run_ssh.py", "kimi-node-0", cmd], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
