import sys

path = '/home/ayu23/V9_FULL/v9_core/run_single.py'
with open(path, 'r') as f:
    content = f.read()

old_block = """        finally:
            rec['server_end']=time.time()
            if sampler_proc: stop_proc(sampler_proc)
            kill_process_group(server_proc); slog.close(); (cdir/'case_manifest.json').write_text(json.dumps(rec,indent=2)); top['cases'].append(rec)"""

new_block = """        finally:
            rec['server_end']=time.time()
            if sampler_proc: stop_proc(sampler_proc)
            try:
                kill_process_group(server_proc)
            finally:
                slog.close()
                cdir.mkdir(parents=True, exist_ok=True)
                (cdir/'case_manifest.json').write_text(json.dumps(rec, indent=2))
                top['cases'].append(rec)"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(path, 'w') as f:
        f.write(content)
    print('SUCCESS: Patched run_single.py')
else:
    print('ERROR: Old block not found in run_single.py')
    sys.exit(1)
