import os
import subprocess
import sys
import time

model_id = "deepseek-ai/DeepSeek-V4.1-Flash"
local_dir = "/opt/models/DeepSeek-V4.1-Flash"
gcs_dest = "gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash"

print(f"[{time.ctime()}] Starting snapshot_download for {model_id} (16 workers)...", flush=True)
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id=model_id,
    local_dir=local_dir,
    max_workers=16
)

print(f"[{time.ctime()}] Hugging Face download finished! Syncing to GCS: {gcs_dest}...", flush=True)
subprocess.run(["gcloud", "storage", "rsync", "-r", local_dir, gcs_dest], check=True)

print(f"[{time.ctime()}] Transfer verified and complete! Self-terminating worker VM to protect costs...", flush=True)
zone = subprocess.check_output([
    "curl", "-s", "-H", "Metadata-Flavor: Google",
    "http://metadata.google.internal/computeMetadata/v1/instance/zone"
]).decode().strip().split("/")[-1]

name = subprocess.check_output([
    "curl", "-s", "-H", "Metadata-Flavor: Google",
    "http://metadata.google.internal/computeMetadata/v1/instance/name"
]).decode().strip()

subprocess.run(["gcloud", "compute", "instances", "delete", name, f"--zone={zone}", "-q"])
