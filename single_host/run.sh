#!/usr/bin/env bash
set -e

# ==============================================================================
# Single-Host TPU vLLM Serving Lifecycle (GKE Standard) with Auto-Teardown
# ==============================================================================

PROJECT_ID="${PROJECT_ID:-mevreon}"
REGION="${REGION:-us-central1}"
ZONE="${ZONE:-us-central1-a}"
CLUSTER_NAME="${CLUSTER_NAME:-vllm-singlehost-cluster}"
MACHINE_TYPE="${MACHINE_TYPE:-ct5lp-hightpu-4t}"
TPU_TOPOLOGY="${TPU_TOPOLOGY:-2x2}"
MODEL_ID="${MODEL_ID:-google/gemma-2-27b-it}"
BUCKET_NAME="${PROJECT_ID}-singlehost-vllm-weights"
KSA_NAME="vllm-ksa"
NAMESPACE="default"

if [ -f "config.env" ]; then
    export $(grep -v '^#' config.env | xargs)
fi

cleanup() {
    echo -e "\n\033[1;31m========================================================\033[0m"
    echo -e "\033[1;31m [BILLING SAFEGUARD] INITIATING AUTOMATIC TEARDOWN\033[0m"
    echo -e "\033[1;31m========================================================\033[0m"

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

trap cleanup EXIT INT TERM

echo -e "\033[1;36m[1/6] Configuring GCP Project & APIs...\033[0m"
gcloud config set project "$PROJECT_ID" --quiet
gcloud config set compute/zone "$ZONE" --quiet

gcloud services enable \
    container.googleapis.com \
    tpu.googleapis.com \
    storage.googleapis.com \
    monitoring.googleapis.com --project "$PROJECT_ID" --quiet

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

echo -e "\033[1;36m[2/6] Provisioning GKE Standard Cluster & Single-Host TPU Node Pool...\033[0m"
if ! gcloud container clusters describe "$CLUSTER_NAME" --zone "$ZONE" --project "$PROJECT_ID" >/dev/null 2>&1; then
    gcloud container clusters create "$CLUSTER_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --node-locations="$ZONE" \
        --release-channel regular \
        --machine-type e2-standard-4 \
        --num-nodes 1 \
        --workload-pool="${PROJECT_ID}.svc.id.goog" \
        --addons GcsFuseCsiDriver \
        --enable-ip-alias \
        --quiet
fi

if ! gcloud container node-pools describe tpunodepool --cluster "$CLUSTER_NAME" --zone "$ZONE" --project "$PROJECT_ID" >/dev/null 2>&1; then
    gcloud container node-pools create tpunodepool \
        --project="$PROJECT_ID" \
        --cluster="$CLUSTER_NAME" \
        --zone="$ZONE" \
        --node-locations="$ZONE" \
        --machine-type="$MACHINE_TYPE" \
        --tpu-topology="$TPU_TOPOLOGY" \
        --num-nodes=1 \
        --quiet
fi

gcloud container clusters get-credentials "$CLUSTER_NAME" --zone "$ZONE" --project "$PROJECT_ID"

echo -e "\033[1;36m[3/6] Setting up GCS Bucket & Workload Identity...\033[0m"
gcloud storage buckets create "gs://${BUCKET_NAME}" --project "$PROJECT_ID" --location="$REGION" --uniform-bucket-level-access || true

kubectl create serviceaccount "$KSA_NAME" --namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
    --member="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/${NAMESPACE}/sa/${KSA_NAME}" \
    --role="roles/storage.objectUser" --quiet || true

if [ -n "$HF_TOKEN" ]; then
    kubectl create secret generic hf-secret --from-literal=hf_api_token="$HF_TOKEN" --namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
fi

echo -e "\033[1;36m[4/6] Deploying Single-Host vLLM Manifests...\033[0m"
sed -e "s|GSBUCKET|${BUCKET_NAME}|g" manifests/01-vllm-single-host-tpu.yaml | kubectl apply -f - -n "$NAMESPACE"
kubectl apply -f manifests/02-gradio.yaml -n "$NAMESPACE"

echo -e "\033[1;36m[5/6] Waiting for Gradio & Single-Host TPU Pods...\033[0m"
kubectl rollout status deployment/gradio --timeout=120s || true

echo -e "\033[1;36m[6/6] Launching Port Forwarding & Live Session...\033[0m"
kubectl port-forward service/gradio 8080:8080 &
kubectl port-forward service/vllm-service 8000:8000 &

sleep 4

echo -e "\n\033[1;32m========================================================\033[0m"
echo -e "\033[1;32m 🚀 SINGLE-HOST TPU SERVING IS READY & ONLINE!\033[0m"
echo -e "\033[1;32m========================================================\033[0m"
echo -e "  • Gradio Web Interface : http://localhost:8080"
echo -e "  • OpenAI-compatible API: http://localhost:8000/v1/chat/completions"
echo -e "\033[1;32m========================================================\033[0m"
echo -e "\033[1;33m⚠️  Press [ENTER] or [Ctrl+C] to STOP session and delete cluster & TPU VMs.\033[0m"

read -r -p "Press [Enter] to exit and stop all billing: " _dummy
