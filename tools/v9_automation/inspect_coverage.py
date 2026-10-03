import json

with open('v9_full_result/final_validation/coverage.json') as f:
    cov = json.load(f)

print(f"Total items in coverage.json: {len(cov)}")
from collections import Counter
status_counts = Counter(r.get('status') for r in cov)
print("Status counts:", status_counts)

print("\n=== SERVER_START_FAILED runs (Total: {}) ===".format(status_counts['SERVER_START_FAILED']))
for r in cov:
    if r.get('status') == 'SERVER_START_FAILED':
        print(f"Case: {r.get('case'):<25} | Bench: {r.get('bench'):<20} | tp={r.get('tp')} pp={r.get('pp')} ctx={r.get('context_tokens')}")

print("\n=== NOT_RUN runs (Total: {}) ===".format(status_counts['NOT_RUN']))
for r in cov:
    if r.get('status') == 'NOT_RUN':
        print(f"Case: {r.get('case'):<25} | Bench: {r.get('bench'):<20} | tp={r.get('tp')} pp={r.get('pp')} ctx={r.get('context_tokens')}")
