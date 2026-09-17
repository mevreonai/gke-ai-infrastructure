#!/bin/bash
exec docker run --rm --gpus all --ipc=host --net=host -v /home/ayu23:/home/ayu23 --entrypoint /bin/bash rtx-smoke:latest -c "/home/ayu23/rtx_g4_smoke/nccl-tests/build/all_reduce_perf $*"
