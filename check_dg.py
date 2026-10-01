import subprocess

# SCP using gcloud.cmd with shell=True
scp_cmd = 'gcloud compute scp c:/Users/ayu23/OneDrive/Desktop/tpu/test_deepgemm_adapter.py kimi-node-0:/home/ayu23/test_deepgemm_adapter.py --zone=us-central1-b --project=mevreon'
subprocess.run(scp_cmd, shell=True, check=True)

# Run test script via run_ssh.py
res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', '/home/ayu23/vllm_env/bin/python3 /home/ayu23/test_deepgemm_adapter.py'], capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
