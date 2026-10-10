from transformers import AutoConfig
cfg = AutoConfig.from_pretrained("moonshotai/Kimi-Linear-48B-A3B-Instruct", trust_remote_code=True)
print("qk_nope_head_dim:", getattr(cfg, "qk_nope_head_dim", "NOT_FOUND"))
print("qk_rope_head_dim:", getattr(cfg, "qk_rope_head_dim", "NOT_FOUND"))
print("v_head_dim:", getattr(cfg, "v_head_dim", "NOT_FOUND"))
for k in dir(cfg):
    if "dim" in k.lower() or "mla" in k.lower() or "qk" in k.lower():
        print(f"{k} = {getattr(cfg, k)}")
