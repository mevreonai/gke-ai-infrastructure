with open('/home/ayu23/v8_additional_runs/20261009_104123/stage2/step_status.jsonl', 'w') as f:
    f.write('{"step":"s2_01_fp8_kv_rerun","rc":0,"start":1791579053,"end":1791579235}\n')
    f.write('{"step":"s2_01_fp8_summarize","rc":0,"start":1791579236,"end":1791579240}\n')
print("Successfully initialized step_status.jsonl for Stage 2")
