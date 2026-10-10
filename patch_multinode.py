target = '/home/ayu23/v8_additional_runs_suite/rtx_g4_smoke_v5/12_run_vllm_multi_node.sh'
content = open(target).read()

old_block = """  ray stop -f || true
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; ray stop -f || true"

  PP_EXPORT="" """

new_block = """  ray stop -f || true
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$NODE1_IP" "$REMOTE_V6_ENV unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; ray stop -f || true"
  sleep 4

  PP_EXPORT="" """

if old_block.strip() in content:
    open(target, 'w').write(content.replace(old_block.strip(), new_block.strip()))
    print("SUCCESS: Added sleep 4 after ray stop in 12_run_vllm_multi_node.sh")
else:
    print("Pattern not found, checking replacement...")
    old2 = 'ray stop -f || true"\n'
    new2 = 'ray stop -f || true"\n  sleep 4\n'
    if old2 in content:
        open(target, 'w').write(content.replace(old2, new2))
        print("SUCCESS: Replaced via fallback")
    else:
        print("Fallback pattern not found")
