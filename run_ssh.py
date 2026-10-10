import sys
import subprocess
import base64

def main():
    if len(sys.argv) < 3:
        print("Usage: python run_ssh.py <node> <command>", file=sys.stderr)
        sys.exit(1)
    node = sys.argv[1]
    if node == "0":
        node = "kimi-node-0"
    elif node == "1":
        node = "kimi-node-1"
    cmd = " ".join(sys.argv[2:])
    
    zone = "us-central1-b"
    b64 = base64.b64encode(cmd.encode('utf-8')).decode('ascii')
    remote_cmd = f"echo {b64} | base64 -d | bash"
    full_cmd = f'gcloud compute ssh ayu23@{node} --zone={zone} --tunnel-through-iap --command="{remote_cmd}"'
    
    for attempt in range(3):
        try:
            res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
            if res.returncode == 0:
                if res.stdout:
                    sys.stdout.buffer.write(res.stdout.encode('utf-8', errors='replace'))
                sys.exit(0)
            if attempt == 2:
                if res.stdout:
                    sys.stdout.buffer.write(res.stdout.encode('utf-8', errors='replace'))
                if res.stderr:
                    sys.stderr.buffer.write(res.stderr.encode('utf-8', errors='replace'))
                sys.exit(res.returncode)
        except subprocess.TimeoutExpired:
            if attempt == 2:
                print(f"ERROR: Command timed out after 600s: {cmd}", file=sys.stderr)
                sys.exit(124)

if __name__ == "__main__":
    main()
