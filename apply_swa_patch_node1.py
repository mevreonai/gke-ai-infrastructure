import subprocess

scp_cmd = 'gcloud compute scp ./patch_swa_block_size.py kimi-node-1:~/patch_swa_block_size.py --zone=us-central1-b --project=mevreon'
subprocess.run(scp_cmd, shell=True, check=True)

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-1', '$HOME/vllm_env/bin/python3 $HOME/patch_swa_block_size.py'], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
