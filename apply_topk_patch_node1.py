import subprocess

scp_cmd = 'gcloud compute scp c:/Users/ayu23/OneDrive/Desktop/tpu/patch_topk_1152.py kimi-node-1:/home/ayu23/patch_topk_1152.py --zone=us-central1-b --project=mevreon'
subprocess.run(scp_cmd, shell=True, check=True)

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-1', '/home/ayu23/vllm_env/bin/python3 /home/ayu23/patch_topk_1152.py && rm -rf /home/ayu23/.cache/flashinfer'], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
