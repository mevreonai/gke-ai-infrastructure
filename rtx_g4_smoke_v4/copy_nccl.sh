#!/bin/bash
set -euo pipefail

docker run --rm --entrypoint /bin/bash rtx-smoke:latest -c 'tar -cf - $(ldd /home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf | grep libnccl | awk "{print \$3}")' | tar -xvf - -C /opt/cuda-13.0/
# Move any extracted libnccl files directly to /opt/cuda-13.0/lib64
find /opt/cuda-13.0 -name "libnccl*" -exec cp -a {} /opt/cuda-13.0/lib64/ \;
ldconfig
ldd /home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf
