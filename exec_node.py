import sys
import subprocess
import base64

def run_on_node(node, script_text, as_python=False):
    b64 = base64.b64encode(script_text.encode('utf-8')).decode('ascii')
    interpreter = "python3" if as_python else "bash"
    remote_cmd = f"echo {b64} | base64 -d | {interpreter}"
    full_cmd = f'gcloud compute ssh ayu23@{node} --zone=us-central1-b --tunnel-through-iap --command="{remote_cmd}"'
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=600)
    return res.returncode, res.stdout, res.stderr

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python exec_node.py <node> <command_or_python_code> [--py]")
        sys.exit(1)
    node = sys.argv[1]
    as_py = "--py" in sys.argv
    text = " ".join([arg for arg in sys.argv[2:] if arg != "--py"])
    rc, out, err = run_on_node(node, text, as_python=as_py)
    if out: sys.stdout.write(out)
    if err and rc != 0: sys.stderr.write(err)
    sys.exit(rc)
