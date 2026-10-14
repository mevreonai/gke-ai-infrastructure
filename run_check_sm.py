import subprocess

scp_cmd = 'gcloud compute scp ./check_sm.py kimi-node-0:~/check_sm.py --zone=us-central1-b --project=mevreon'
subprocess.run(scp_cmd, shell=True, check=True)

res = subprocess.run(['python', 'run_ssh.py', 'kimi-node-0', '$HOME/vllm_env/bin/python3 $HOME/check_sm.py'], capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
