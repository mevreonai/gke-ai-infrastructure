import torch
from vllm.utils.deep_gemm import get_num_sms

device = torch.device("cuda:0")
props = torch.cuda.get_device_properties(0)
print("Device name:", props.name)
print("SM count (multi_processor_count):", props.multi_processor_count)
print("vllm get_num_sms():", get_num_sms())
