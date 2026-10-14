import json
cfg = json.load(open('$HOME/v8_additional_runs_suite/stage2_cases_multi_node_load.json'))
for c in cfg['cases']:
    print(c['name'], c.get('groups'))
