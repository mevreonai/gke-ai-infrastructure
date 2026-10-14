import subprocess

scp_cmd = 'gcloud compute scp ./apply_dg_patch.py kimi-node-1:~/apply_dg_patch.py --zone=us-central1-b --project=mevreon'
subprocess.run(scp_cmd, shell=True, check=True)

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-1', '/home/user/vllm_env/bin/python3 /home/user/apply_dg_patch.py'], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
