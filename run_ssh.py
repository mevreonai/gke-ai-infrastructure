import sys
import subprocess

def main():
    if len(sys.argv) < 3:
        print("Usage: python run_ssh.py <node> <command>", file=sys.stderr)
        sys.exit(1)
    node = sys.argv[1]
    cmd = " ".join(sys.argv[2:])
    escaped_cmd = cmd.replace('"', '\\"')
    NODE_IPS = {
        'kimi-node-0': '136.65.229.197',
        'kimi-node-1': '136.64.217.143',
    }
    ip = NODE_IPS.get(node, node)
    full_cmd = f'ssh -i C:\\Users\\ayu23\\.ssh\\google_compute_engine -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL ayu23@{ip} "{escaped_cmd}"'
    try:
        res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=600)
        if res.stdout:
            sys.stdout.write(res.stdout)
        if res.stderr and res.returncode != 0:
            sys.stderr.write(res.stderr)
        sys.exit(res.returncode)
    except subprocess.TimeoutExpired:
        print(f"ERROR: Command timed out after 600s: {cmd}", file=sys.stderr)
        sys.exit(124)

if __name__ == "__main__":
    main()
