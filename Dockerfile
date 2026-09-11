FROM vllm/vllm-tpu:v0.21.0

ENV VLLM_TARGET_DEVICE=tpu
ENV VLLM_XLA_CACHE_PATH=/data

USER root
RUN pip install --no-cache-dir -U \
  "https://s3-us-west-2.amazonaws.com/ray-wheels/master/75b85027a859439fae5634e49aa6443f6fbecfeb/ray-3.0.0.dev0-cp312-cp312-manylinux2014_x86_64.whl" && \
  pip install --no-cache-dir --no-deps "ray[llm]"

COPY serve_tpu_multihost.py /home/ray/serve_tpu_multihost.py
