from pathlib import Path

p = Path("/home/ayu23/v8_additional_runs_suite/rtx_g4_smoke_v5/20_ray_nccl_env_audit.py")
content = p.read_text()

old_code = """        if expected_ld is not None and r.get('ld_library_path') != expected_ld:
            violations.append({'type':'LD_LIBRARY_PATH_MISMATCH','node_id':r['node_id'],'hostname':r['hostname'],
                               'expected':expected_ld,'actual':r.get('ld_library_path')})"""

new_code = """        def _norm_ld(s):
            if not s: return ""
            return ":".join(dict.fromkeys(x for x in s.split(":") if x))
        if expected_ld is not None and _norm_ld(r.get('ld_library_path')) != _norm_ld(expected_ld):
            violations.append({'type':'LD_LIBRARY_PATH_MISMATCH','node_id':r['node_id'],'hostname':r['hostname'],
                               'expected':expected_ld,'actual':r.get('ld_library_path')})"""

if old_code in content:
    content = content.replace(old_code, new_code)
    p.write_text(content)
    print("Successfully patched 20_ray_nccl_env_audit.py")
else:
    print("Target code block not found in 20_ray_nccl_env_audit.py")
