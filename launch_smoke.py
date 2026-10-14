import subprocess

scp_cmd = 'gcloud compute scp ./run_live_token_test.sh kimi-node-0:~/run_live_token_test.sh --zone=us-central1-b --project=mevreon'
subprocess.run(scp_cmd, shell=True, check=True)

subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', 'chmod +x /home/user/run_live_token_test.sh'], check=True)

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', '/home/user/run_live_token_test.sh'], capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
