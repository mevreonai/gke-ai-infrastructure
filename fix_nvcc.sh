#!/bin/bash
sudo tee /usr/local/bin/nvcc > /dev/null << 'EOF'
#!/bin/bash
exec /opt/cuda-13.0/bin/nvcc "$@"
EOF
sudo chmod +x /usr/local/bin/nvcc
nvcc -c /tmp/test.cu -o /tmp/test_wrapper.o
ls -la /tmp/test_wrapper.o
