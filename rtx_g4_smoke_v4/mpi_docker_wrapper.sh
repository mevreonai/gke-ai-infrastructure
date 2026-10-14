#!/bin/bash
LOCAL_RANK=${OMPI_COMM_WORLD_LOCAL_RANK:-0}
ENV_FILE=$(mktemp /tmp/mpi_env.XXXXXX)
env | grep -E '^(OMPI_|PMIX_|OPAL_)' > "$ENV_FILE"

exec docker run --rm --gpus all --ipc=host --net=host --pid=host \
  -v /tmp:/tmp \
  -v /home/user:/home/user \
  -e CUDA_VISIBLE_DEVICES="${LOCAL_RANK}" \
  --env-file "$ENV_FILE" \
  --entrypoint /bin/bash rtx-smoke:latest \
  -c "$HOME/rtx_g4_smoke/nccl-tests/build/all_reduce_perf $*"
