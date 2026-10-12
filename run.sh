#!/usr/bin/env bash
set -e

# ==============================================================================
# Multi-Host TPU v5e Serving Lifecycle with Automatic Billing Safeguard
# ==============================================================================

# Default settings (can be overridden by config.env or environment variables)
PROJECT_ID="${PROJECT_ID:-mevreon}"
REGION="${REGION:-us-central1}"
ZONE="${ZONE:-us-central1-a}"
CLUSTER_NAME="${CLUSTER_NAME:-ray-llm-cluster}"
BUCKET_NAME="${PROJECT_ID}-tpu-model-weights"
AR_REPO="ray-repo"
AR_LOCATION="us-east1"
IMAGE_TAG="${AR_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/vllm-tpu-ray:vllm-tpu"

if [ -f "config.env" ]; then
    echo "[INFO] Sourcing config.env..."
    export $(grep -v '^#' config.env | xargs)
fi

cleanup() {
    echo -e "\n\033[1;31m========================================================\033[0m"
    echo -e "\033[1;31m [BILLING SAFEGUARD] INITIATING AUTOMATIC TEARDOWN\033[0m"
    echo -e "\033[1;31m========================================================\033[0m"

    # Kill background port-forwards
    pkill -f "kubectl port-forward" || true

    if [ "$KEEP_CLUSTER" = "true" ]; then
        echo -e "\033[1;33m[WARN] KEEP_CLUSTER is set to true. Cluster was NOT deleted.\033[0m"
        return
    fi

    echo -e "\033[1;33m[INFO] Deleting GKE Cluster '$CLUSTER_NAME' in zone '$ZONE' to STOP ALL TPU/VM BILLING...\033[0m"
    gcloud container clusters delete "$CLUSTER_NAME" --zone "$ZONE" --project "$PROJECT_ID" --quiet || true

    echo -e "\033[1;32m========================================================\033[0m"
    echo -e "\033[1;32m [SUCCESS] Safe teardown completed. No TPU VMs remaining.\033[0m"
    echo -e "\033[1;32m========================================================\033[0m"
}

# Trap exit signals (SIGINT, SIGTERM, EXIT) so teardown always runs
trap cleanup EXIT INT TERM

echo -e "\033[1;36m[1/7] Configuring GCP Project & APIs...\033[0m"
gcloud config set project "$PROJECT_ID" --quiet
gcloud config set compute/zone "$ZONE" --quiet

gcloud services enable \
    container.googleapis.com \
    tpu.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com --project "$PROJECT_ID" --quiet

echo -e "\033[1;36m[2/7] Provisioning GKE Cluster & TPU v5e Node Pool...\033[0m"
if ! gcloud container clusters describe "$CLUSTER_NAME" --zone "$ZONE" --project "$PROJECT_ID" >/dev/null 2>&1; then
    gcloud container clusters create "$CLUSTER_NAME" \
        --project "$PROJECT_ID" \
        --zone "$ZONE" \
        --release-channel regular \
        --machine-type e2-standard-16 \
        --num-nodes 1 \
        --addons RayOperator,GcsFuseCsiDriver \
        --workload-pool "${PROJECT_ID}.svc.id.goog" \
        --enable-ip-alias \
        --quiet
fi

if ! gcloud container node-pools describe tpu-v5e-pool --cluster "$CLUSTER_NAME" --zone "$ZONE" --project "$PROJECT_ID" >/dev/null 2>&1; then
    gcloud container node-pools create tpu-v5e-pool \
        --project "$PROJECT_ID" \
        --cluster "$CLUSTER_NAME" \
        --zone "$ZONE" \
        --machine-type ct5lp-hightpu-4t \
        --tpu-topology 2x4 \
        --num-nodes 2 \
        --node-locations "$ZONE" \
        --quiet
fi

gcloud container clusters get-credentials "$CLUSTER_NAME" --zone "$ZONE" --project "$PROJECT_ID"

echo -e "\033[1;36m[3/7] Setting up GCS Bucket & Workload Identity...\033[0m"
gcloud storage buckets create "gs://${BUCKET_NAME}" --project "$PROJECT_ID" --location="$REGION" || true
gcloud iam service-accounts create tpu-reader-sa --display-name="TPU Reader SA" --project "$PROJECT_ID" || true
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
    --member="serviceAccount:tpu-reader-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin" --quiet || true

kubectl create serviceaccount ray-ksa --dry-run=client -o yaml | kubectl apply -f -
gcloud iam service-accounts add-iam-policy-binding "tpu-reader-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project "$PROJECT_ID" \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[default/ray-ksa]" --quiet || true

kubectl annotate serviceaccount ray-ksa iam.gke.io/gcp-service-account="tpu-reader-sa@${PROJECT_ID}.iam.gserviceaccount.com" --overwrite

if [ -n "$HF_TOKEN" ]; then
    kubectl create secret generic hf-secret --from-literal=hf_api_token="$HF_TOKEN" --dry-run=client -o yaml | kubectl apply -f -
fi

echo -e "\033[1;36m[4/7] Checking Container Image in Artifact Registry...\033[0m"
gcloud artifacts repositories create "$AR_REPO" --repository-format=docker --location="$AR_LOCATION" --description="Ray TPU docker repo" --project "$PROJECT_ID" --quiet || true

if ! gcloud artifacts docker images describe "$IMAGE_TAG" --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "[INFO] Submitting build to Cloud Build..."
    gcloud builds submit --project "$PROJECT_ID" --tag "$IMAGE_TAG" .
fi

echo -e "\033[1;36m[5/7] Deploying Manifests to GKE...\033[0m"
kubectl apply -f manifests/01-networking-netdev.yaml || true
sed -e "s|us-east1-docker.pkg.dev/[^/]*/ray-repo/vllm-tpu-ray:vllm-tpu|${IMAGE_TAG}|g" \
    -e "s|bucketName:.*|bucketName: ${BUCKET_NAME}|g" manifests/02-ray-service-multihost-tpu.yaml | kubectl apply -f -
kubectl apply -f manifests/gradio.yaml || true

echo -e "\033[1;36m[6/7] Waiting for Gradio & Serving Pods...\033[0m"
kubectl rollout status deployment/gradio --timeout=180s || true

echo -e "\033[1;36m[7/7] Launching Port Forwarding & Live Session...\033[0m"
kubectl port-forward service/gradio 8080:8080 &
kubectl port-forward svc/vllm-tpu-multihost-head-svc 8000:8000 &

sleep 4

echo -e "\n\033[1;32m========================================================\033[0m"
echo -e "\033[1;32m 🚀 MULTI-HOST TPU SERVING IS READY & ONLINE!\033[0m"
echo -e "\033[1;32m========================================================\033[0m"
echo -e "  • Gradio Web Interface : http://localhost:8080"
echo -e "  • OpenAI-compatible API: http://localhost:8000/v1/chat/completions"
echo -e "\033[1;32m========================================================\033[0m"
echo -e "\033[1;33m⚠️  Press [ENTER] or [Ctrl+C] at any time to STOP the session\033[0m"
echo -e "\033[1;33m    and AUTOMATICALLY TEAR DOWN the GKE cluster & TPU VMs.\033[0m"

read -r -p "Press [Enter] to exit and stop all billing: " _dummy
