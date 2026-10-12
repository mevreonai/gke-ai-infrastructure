#!/usr/bin/env bash
set -e

echo "=== Applying CUDA Environment and Header Fix on $(hostname) ==="

# 1. Symlink CUDA root
sudo rm -rf /usr/local/cuda
sudo ln -sf /opt/cuda-13.0 /usr/local/cuda

# 2. Link all headers into system include paths
echo "Linking CUDA headers to /usr/local/include and /usr/include..."
sudo ln -sf /opt/cuda-13.0/targets/x86_64-linux/include/* /usr/local/include/ || true
sudo ln -sf /opt/cuda-13.0/targets/x86_64-linux/include/* /usr/include/ || true

# 3. Create persistent profile.d script
sudo tee /etc/profile.d/cuda.sh > /dev/null << 'EOF'
export CUDA_HOME=/usr/local/cuda
export PATH=/usr/local/cuda/bin:/usr/local/bin:$PATH
export CPATH=/usr/local/cuda/include:/usr/local/include:$CPATH
export LIBRARY_PATH=/usr/local/cuda/lib64:$LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
EOF
sudo chmod +x /etc/profile.d/cuda.sh

# 4. Inject into bashrc and vllm_env activate script
for target in /home/ayu23/.bashrc /home/ayu23/vllm_env/bin/activate; do
    if [ -f "$target" ]; then
        if ! grep -q "CUDA_HOME=/usr/local/cuda" "$target"; then
            echo "" >> "$target"
            echo "export CUDA_HOME=/usr/local/cuda" >> "$target"
            echo "export PATH=/usr/local/cuda/bin:\$PATH" >> "$target"
            echo "export CPATH=/usr/local/cuda/include:\$CPATH" >> "$target"
            echo "export LIBRARY_PATH=/usr/local/cuda/lib64:\$LIBRARY_PATH" >> "$target"
            echo "export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH" >> "$target"
        fi
    fi
done

# 5. Fix nvcc binary wrapper and profile
sudo rm -f /usr/local/bin/nvcc
sudo tee /usr/local/bin/nvcc > /dev/null << 'EOF'
#!/bin/bash
export CUDA_HOME=/usr/local/cuda
export PATH=/usr/local/cuda/bin:$PATH
export CPATH=/usr/local/cuda/include:$CPATH
exec /opt/cuda-13.0/bin/nvcc "$@"
EOF
sudo chmod +x /usr/local/bin/nvcc
sudo cp /opt/cuda-13.0/bin/nvcc.profile /usr/local/bin/nvcc.profile || true

# 6. Verify compilation of test CUDA kernel
echo "Verifying nvcc compilation..."
cat << 'EOF' > /tmp/test_cuda.cu
#include <cuda_runtime.h>
#include <stdio.h>
__global__ void k() {}
int main() {
    k<<<1,1>>>();
    cudaError_t err = cudaDeviceSynchronize();
    if (err == cudaSuccess) {
        printf("CUDA_KERNEL_SUCCESS\n");
        return 0;
    }
    return 1;
}
EOF

nvcc /tmp/test_cuda.cu -o /tmp/test_cuda_bin
/tmp/test_cuda_bin

echo "=== Verification SUCCESS on $(hostname) ==="
