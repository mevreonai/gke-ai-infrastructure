from vllm.v1.worker.utils import select_common_block_size
from vllm.v1.attention.backends.flashinfer import FlashInferBackend
from vllm.v1.attention.backends.mla.indexer import DeepseekV32IndexerBackend

class DummyBackend:
    @classmethod
    def get_supported_kernel_block_sizes(cls):
        return [16, 32, 64]

print("Test with 64 on FlashInfer:", select_common_block_size(64, [FlashInferBackend()]))
print("Test with 64 on Indexer:", select_common_block_size(64, [DeepseekV32IndexerBackend()]))
