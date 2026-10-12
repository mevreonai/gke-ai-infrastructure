#!/usr/bin/env bash
set -e

PROJECT_ID="${PROJECT_ID:-mevreon}"
TARGET_CLUSTER="${CLUSTER_NAME:-}"
TARGET_REGION="${REGION:-}"

if [ -f "config.env" ]; then
    export $(grep -v '^#' config.env | xargs)
fi

echo -e "\033[1;31m========================================================\033[0m"
echo -e "\033[1;31m 🛑 COMPREHENSIVE MULTI-REGION TEARDOWN SCRIPT\033[0m"
echo -e "\033[1;31m========================================================\033[0m"

# 1. Kill local port forwards
pkill -f "kubectl port-forward" || true

# 2. Find and delete GKE clusters
echo "[INFO] Scanning for GKE clusters in project $PROJECT_ID..."
gcloud container clusters list --project "$PROJECT_ID" --format="csv[no-heading](name,location)" 2>/dev/null | while IFS=',' read -r cname cloc; do
    if [ -n "$cname" ]; then
        SHOULD_DELETE=false
        if [ -n "$TARGET_CLUSTER" ]; then
            if [ "$cname" = "$TARGET_CLUSTER" ]; then SHOULD_DELETE=true; fi
        else
            case "$cname" in
                *singlehost*|*ray*|*vllm*|*tpu*) SHOULD_DELETE=true ;;
            esac
        fi

        if [ "$SHOULD_DELETE" = "true" ]; then
            echo -e "\033[1;31m  -> Deleting cluster '$cname' in '$cloc'...\033[0m"
            gcloud container clusters delete "$cname" --location "$cloc" --project "$PROJECT_ID" --quiet || true
        else
            echo "  [SKIP] Retaining non-target cluster: $cname ($cloc)"
        fi
    fi
done

# 3. Check active VMs
echo "[INFO] Verifying active Compute Engine VMs in $PROJECT_ID..."
gcloud compute instances list --project "$PROJECT_ID" || true

echo -e "\033[1;32m========================================================\033[0m"
echo -e "\033[1;32m [SUCCESS] Multi-region cleanup completed.\033[0m"
echo -e "\033[1;32m========================================================\033[0m"
