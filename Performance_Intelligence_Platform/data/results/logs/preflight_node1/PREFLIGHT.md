# V5 preflight

- Host: `kimi-node-1`
- vLLM: `0.29.0`
- Required flags missing: `none`
- Ray: `/home/ayu23/vllm_env/bin/ray`
- Nsight Systems: `/usr/local/bin/nsys`

## GPU inventory
```
0, GPU-ee5e5809-7965-45fd-91e7-624021ecddd9, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:05:00.0
1, GPU-60979ab6-025f-2463-9c84-e7b731c702f8, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:06:00.0
2, GPU-0c83f5b1-4a0b-68b2-702f-8edf07f92a03, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:0A:00.0
3, GPU-e91c452b-5d94-1027-c4eb-08a8a031c827, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:0B:00.0
4, GPU-a3784865-0b4f-90e2-25bc-7c1d8d4756d8, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:84:00.0
5, GPU-f992898a-0664-6bd6-53df-fd914009c8ab, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:85:00.0
6, GPU-cf834e9c-dbfd-6fe1-27a6-688965f9d514, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:89:00.0
7, GPU-1d3657ff-0827-61fe-c22f-92181848cff7, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:8A:00.0
```

## Relevant packages
```
flashinfer-python==0.6.18
huggingface_hub==1.32.0
nccl4py==0.5.0
nvidia-nccl-cu13==2.29.7
ray==2.58.0
tokenspeed-triton==3.8.10.post20260906
torch==2.13.0
torch_c_dlpack_ext==0.1.5
torchaudio==2.11.0
torchcodec==0.16.0
torchvision==0.28.0
transformers==5.17.0
triton==3.7.1
vllm==0.29.0
```
