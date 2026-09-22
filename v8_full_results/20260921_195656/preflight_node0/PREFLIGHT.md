# V5 preflight

- Host: `kimi-node-0`
- vLLM: `0.29.0`
- Required flags missing: `none`
- Ray: `/home/ayu23/vllm_env/bin/ray`
- Nsight Systems: `/usr/local/bin/nsys`

## GPU inventory
```
0, GPU-7ca702a0-5143-88bb-c6ff-6729e546bbb0, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:05:00.0
1, GPU-489ffba7-85db-e247-01da-c5f74d4dea68, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:06:00.0
2, GPU-fcbb3013-ff6c-bc47-80c8-714bc92101a8, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:0A:00.0
3, GPU-ec73c456-dfaa-11f5-1205-43bad849400f, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:0B:00.0
4, GPU-b11e0775-2d5b-bbe9-e0e7-e466122d59a5, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:84:00.0
5, GPU-3d29be65-8656-7fab-aa0a-ebb6ac6f0833, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:85:00.0
6, GPU-99c28e70-bc5e-9295-7005-08a631683901, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:89:00.0
7, GPU-cf61dfdc-19f1-d8a6-ef76-1af59b6301ce, NVIDIA RTX PRO 6000 Blackwell Server Edition, 97887, 00000000:8A:00.0
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
