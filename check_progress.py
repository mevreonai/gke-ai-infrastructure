import subprocess
import json

def check():
    cmd = 'gcloud compute ssh ayu23@kimi-node-0 --zone=us-central1-b --tunnel-through-iap --command="python3 -c \\"import json, glob; files=sorted(glob.glob(\'/home/ayu23/v9_full_results/v9_test2_20260927_163750/vllm_single_node_v9_matrix/*/case_manifest.json\')); print(\'Found manifests:\', len(files)); [print(json.load(open(f))[\'name\'], \':\', json.load(open(f))[\'status\']) for f in files]\\""'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == '__main__':
    check()
