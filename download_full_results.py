import subprocess
import os
import tarfile

def download_and_extract():
    remote_archive = "/home/ayu23/V9_TEST2_RESULTS_v9_test2_20260927_163750.tar.gz"
    local_archive = r"c:\Users\ayu23\OneDrive\Desktop\tpu\V9_TEST2_RESULTS_v9_test2_20260927_163750.tar.gz"
    extract_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\v9_test2_results"
    
    print(f"Downloading {remote_archive} -> {local_archive}...")
    cmd = f'gcloud compute scp ayu23@kimi-node-0:{remote_archive} {local_archive} --zone=us-central1-b --tunnel-through-iap'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("SCP STDOUT:\n", res.stdout)
    print("SCP STDERR:\n", res.stderr)
    
    if os.path.exists(local_archive) and os.path.getsize(local_archive) > 1000000:
        print(f"SUCCESS: Downloaded archive size: {os.path.getsize(local_archive):,} bytes")
        os.makedirs(extract_dir, exist_ok=True)
        print(f"Extracting to {extract_dir}...")
        with tarfile.open(local_archive, "r:gz") as tar:
            tar.extractall(path=extract_dir)
        print("Extraction complete!")
    else:
        print("Download failed or file incomplete.")

if __name__ == '__main__':
    download_and_extract()
