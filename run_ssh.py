import sys
import subprocess
import base64

def main():
    if len(sys.argv) < 3:
        print("Usage: python run_ssh.py <node> <command>", file=sys.stderr)
        sys.exit(1)
    node = sys.argv[1]
    cmd = " ".join(sys.argv[2:])
    
    zone = "us-central1-b"
    b64 = base64.b64encode(cmd.encode('utf-8')).decode('ascii')
    remote_cmd = f"echo {b64} | base64 -d | bash"
    full_cmd = f'gcloud compute ssh ayu23@{node} --zone={zone} --tunnel-through-iap --command="{remote_cmd}"'
    
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
