# Multi-Host TPU v5e Serving on GKE (End-to-End Replication Guide)

This guide contains the exact steps and commands to reproduce the deployment of **Google Gemma-2-27B-IT** on a **Multi-Host TPU v5e** pod slice on **Google Kubernetes Engine (GKE)** using **Ray Serve** and **vLLM**.

---

## 📋 Prerequisites & Architecture Overview

- **GCP Project:** `mevreon` (or your target project ID)
- **Region & Zone:** `us-central1-a` (TPU v5e is readily available here)
- **TPU Machine Type:** `ct5lp-hightpu-4t` (4 chips per VM, 2 VMs = 8 TPU v5e chips total)
- **TPU Topology:** `2x4` (Multi-Host Pod Slice)
- **Model:** `google/gemma-2-27b-it` (54.48 GB, 8-way Tensor Parallelism)
- **Software Stack:** vLLM v0.21.0 + Ray Serve 3.0.0.dev0 + PyTorch XLA

---

## ⚡ Quickstart: One-Command Run with Automatic Billing Protection

To provision everything, deploy the model, open the Gradio UI, and **automatically delete the GKE cluster and TPU VMs when you finish (to avoid unexpected billing)**:

### On Windows (PowerShell):
```powershell
# 1. Run full lifecycle with auto-teardown on exit:
.\run.ps1 -ProjectId "mevreon" -HfToken "your_huggingface_token"

# Or if you have already built the Docker image:
.\run.ps1 -ProjectId "mevreon" -SkipBuild
```
*When you press `[Enter]` or `Ctrl+C`, the script immediately deletes the GKE cluster & TPU node pool so no hourly charges accumulate.*

### Emergency / Standalone Manual Teardown:
```powershell
.\cleanup.ps1 -ProjectId "mevreon"
```

### On Linux / Cloud Shell (Bash):
```bash
./run.sh
# Emergency cleanup:
./cleanup.sh
```

---

## 🛠️ Step 1: Environment Setup & GCP APIs

```powershell
# Set variables
$PROJECT_ID = "mevreon"
$REGION = "us-central1"
$ZONE = "us-central1-a"
$CLUSTER_NAME = "ray-llm-cluster"
$BUCKET_NAME = "${PROJECT_ID}-tpu-model-weights"
$HF_TOKEN = "your_huggingface_token"

gcloud config set project $PROJECT_ID
gcloud config set compute/zone $ZONE

# Enable required Google Cloud APIs
gcloud services enable `
    container.googleapis.com `
    tpu.googleapis.com `
    artifactregistry.googleapis.com `
    cloudbuild.googleapis.com `
    storage.googleapis.com
```

---

## 🏗️ Step 2: Create GKE Cluster & TPU Node Pool

### 2.1 Create the Base GKE Cluster
```powershell
gcloud container clusters create $CLUSTER_NAME `
    --zone $ZONE `
    --release-channel regular `
    --machine-type e2-standard-16 `
    --num-nodes 1 `
    --addons RayOperator,GcsFuseCsiDriver `
    --workload-pool "${PROJECT_ID}.svc.id.goog" `
    --enable-ip-alias
```

### 2.2 Create the Multi-Host TPU v5e Node Pool
```powershell
gcloud container node-pools create tpu-v5e-pool `
    --cluster $CLUSTER_NAME `
    --zone $ZONE `
    --machine-type ct5lp-hightpu-4t `
    --tpu-topology 2x4 `
    --num-nodes 2 `
    --node-locations $ZONE
```

### 2.3 Connect `kubectl` to the Cluster
```powershell
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE
```

---

## 📦 Step 3: Cloud Storage, IAM & Hugging Face Secret

### 3.1 Create Bucket & IAM Binding for GCSFuse
```powershell
# Create Cloud Storage bucket for weights
gcloud storage buckets create "gs://${BUCKET_NAME}" --location=$REGION

# Create IAM Service Account and bind Workload Identity
gcloud iam service-accounts create tpu-reader-sa --display-name="TPU Reader SA"

gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" `
    --member="serviceAccount:tpu-reader-sa@${PROJECT_ID}.iam.gserviceaccount.com" `
    --role="roles/storage.objectAdmin"

# Create Kubernetes Service Account and annotate it
kubectl create serviceaccount ray-ksa --default

gcloud iam service-accounts add-iam-policy-binding "tpu-reader-sa@${PROJECT_ID}.iam.gserviceaccount.com" `
    --role="roles/iam.workloadIdentityUser" `
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[default/ray-ksa]"

kubectl annotate serviceaccount ray-ksa `
    iam.gke.io/gcp-service-account="tpu-reader-sa@${PROJECT_ID}.iam.gserviceaccount.com" --overwrite
```

### 3.2 Create Hugging Face Kubernetes Secret
```powershell
kubectl create secret generic hf-secret `
    --from-literal=hf_api_token=$HF_TOKEN `
    --dry-run=client -o yaml | kubectl apply -f -
```

---

## 📥 Step 4: Pre-stage Model Weights into Cloud Storage

Running a Kubernetes Job with GCSFuse to download model weights directly into `gs://${BUCKET_NAME}` ensures fast local streaming and avoids container restart download delays:

```powershell
kubectl apply -f manifests/model-downloader-job.yaml
```

*Wait for completion:*
```powershell
kubectl wait --for=condition=complete job/model-downloader --timeout=1800s
```

---

## 🐳 Step 5: Build & Push the Multi-Host Container Image

```powershell
# Create Artifact Registry repo if not already existing
gcloud artifacts repositories create ray-repo `
    --repository-format=docker `
    --location=us-east1 `
    --description="Ray TPU docker repo"

# Submit build via Cloud Build (no local Docker required)
gcloud builds submit --tag "us-east1-docker.pkg.dev/${PROJECT_ID}/ray-repo/vllm-tpu-ray:vllm-tpu" .
```

---

## 🚀 Step 6: Deploy Networking, RayService & Gradio

### 6.1 Apply Dynamic Resource Allocation (DRA) Network Claim
```powershell
kubectl apply -f manifests/01-networking-netdev.yaml
```

### 6.2 Apply Multi-Host RayService Manifest
```powershell
kubectl apply -f manifests/02-ray-service-multihost-tpu.yaml
```

### 6.3 Deploy Gradio Web Interface
```powershell
kubectl apply -f manifests/gradio.yaml
```

---

## ⚡ Step 7: Apply Runtime Multi-Host Placement Group & Assertion Patch

Because Ray LLM standard node initialization expects single-node placement groups unless explicitly configured with per-host bundles, ensure `serve_tpu_multihost.py` defines the multi-host bundle config:

```python
placement_group_config={
    "bundles": [
        {"TPU": 4, "CPU": 1},
        {"TPU": 4, "CPU": 1}
    ],
    "strategy": "PACK"
}
```

Copy and run `patch_init.py` into all Ray pods:
```powershell
$code = [System.IO.File]::ReadAllText("patch_init.py")
$b64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($code))

$pods = (kubectl get pods -l ray.io/node-type -o jsonpath='{.items[*].metadata.name}').Split(' ')
foreach ($p in $pods) {
    if ($p) {
        if ($p -match "head") {
            kubectl exec $p -c ray-head -- python -c "import base64; exec(base64.b64decode('$b64').decode())"
        } else {
            kubectl exec $p -c ray-worker -- python -c "import base64; exec(base64.b64decode('$b64').decode())"
        }
    }
}
```

---

## 🔍 Step 8: Verify Deployment Status

Check that the Ray Serve applications have transitioned to `HEALTHY / RUNNING`:
```powershell
$headPod = kubectl get pod -l ray.io/node-type=head -o jsonpath='{.items[0].metadata.name}'
kubectl exec $headPod -c ray-head -- serve status
```

Expected output:
```yaml
applications:
  llm:
    status: RUNNING
    deployments:
      LLMServer:google--gemma-2-27b-it:
        status: HEALTHY
      OpenAiIngress:
        status: HEALTHY
```

---

## 🎮 Step 9: Run the Live Demo on Call

### Option A: Gradio Web Chat UI
1. In a terminal, start port forwarding:
   ```powershell
   kubectl port-forward service/gradio 8080:8080
   ```
2. Open browser: **`http://localhost:8080`**
3. Chat live with **Gemma 2 27B**!

### Option B: PowerShell CLI Test
1. In a separate terminal, forward the Ray Serve port:
   ```powershell
   kubectl port-forward svc/vllm-tpu-multihost-head-svc 8000:8000
   ```
2. Run in PowerShell:
   ```powershell
   $body = @{
       model = "google/gemma-2-27b-it"
       messages = @(
           @{
               role = "user"
               content = "Explain why multi-host TPU serving on GKE is ideal for Gemma 2 27B in 2 bullet points."
           }
       )
       max_tokens = 128
   } | ConvertTo-Json -Depth 5

   $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/chat/completions" -Method Post -ContentType "application/json" -Body $body
   $response.choices[0].message.content
   ```
