#!/usr/bin/env bash
set -e

echo "=== Configuring Clean CUDA Environment on $(hostname) ==="

# 1. Symlink CUDA root
sudo rm -rf /usr/local/cuda
sudo ln -sf /opt/cuda-13.0 /usr/local/cuda

# 2. Remove broken symlinks in /usr/local/bin
sudo rm -f /usr/local/bin/nvcc /usr/local/bin/nvcc.profile

# 3. Symlink all headers into system include paths
echo "Linking CUDA headers..."
sudo ln -sf /opt/cuda-13.0/targets/x86_64-linux/include/* /usr/local/include/ || true
sudo ln -sf /opt/cuda-13.0/targets/x86_64-linux/include/* /usr/include/ || true

# 4. System-wide environment profile
sudo tee /etc/profile.d/cuda.sh > /dev/null << 'EOF'
export CUDA_HOME=/usr/local/cuda
export PATH=/usr/local/cuda/bin:/usr/local/bin:$PATH
export CPATH=/usr/local/cuda/include:/usr/local/include:$CPATH
export LIBRARY_PATH=/usr/local/cuda/lib64:$LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
EOF
sudo chmod +x /etc/profile.d/cuda.sh

# 5. Inject into /etc/environment
if ! grep -q "CUDA_HOME" /etc/environment 2>/dev/null; then
    echo 'CUDA_HOME="/usr/local/cuda"' | sudo tee -a /etc/environment
fi

# 6. Inject into bashrc and vllm_env activate script
for target in /home/ayu23/.bashrc /home/ayu23/vllm_env/bin/activate; do
    if [ -f "$target" ]; then
        sed -i '/export CUDA_HOME/d' "$target"
        sed -i '/export PATH=\/usr\/local\/cuda/d' "$target"
        sed -i '/export CPATH=\/usr\/local\/cuda/d' "$target"
        sed -i '/export LIBRARY_PATH=\/usr\/local\/cuda/d' "$target"
        sed -i '/export LD_LIBRARY_PATH=\/usr\/local\/cuda/d' "$target"
        echo "export CUDA_HOME=/usr/local/cuda" >> "$target"
        echo "export PATH=/usr/local/cuda/bin:\$PATH" >> "$target"
        echo "export CPATH=/usr/local/cuda/include:\$CPATH" >> "$target"
        echo "export LIBRARY_PATH=/usr/local/cuda/lib64:\$LIBRARY_PATH" >> "$target"
        echo "export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH" >> "$target"
    fi
done

# 7. Test compilation with nvcc from PATH
echo "Testing nvcc from PATH..."
export PATH=/usr/local/cuda/bin:$PATH
export CUDA_HOME=/usr/local/cuda

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

which nvcc
nvcc /tmp/test_cuda.cu -o /tmp/test_cuda_bin
/tmp/test_cuda_bin

echo "=== Verification SUCCESS on $(hostname) ==="
