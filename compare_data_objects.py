import sys
import hashlib

def get_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

with open('MASTER_CHARACTERIZATION_DASHBOARD_V4_4thOct_2amIST_V8_KIMI48B.html', 'r', encoding='utf-8') as f:
    v8 = f.read()

with open('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    v9 = f.read()

import re

v8_can = re.search(r'CANONICAL_DASHBOARD_DATA\s*=\s*(\{.*?\});', v8, re.DOTALL)
v9_can = re.search(r'CANONICAL_DASHBOARD_DATA\s*=\s*(\{.*?\});', v9, re.DOTALL)

if v8_can and v9_can:
    print("CANONICAL_DASHBOARD_DATA identical:", v8_can.group(1) == v9_can.group(1))
    print("Lengths:", len(v8_can.group(1)), len(v9_can.group(1)))
else:
    print("CANONICAL_DASHBOARD_DATA regex failed:", bool(v8_can), bool(v9_can))

v8_kd = re.search(r'KD_PAGES_DATA\s*=\s*(\{.*?\});', v8, re.DOTALL)
v9_kd = re.search(r'KD_PAGES_DATA\s*=\s*(\{.*?\});', v9, re.DOTALL)

if v8_kd and v9_kd:
    print("KD_PAGES_DATA identical:", v8_kd.group(1) == v9_kd.group(1))
    print("Lengths:", len(v8_kd.group(1)), len(v9_kd.group(1)))
else:
    print("KD_PAGES_DATA regex failed:", bool(v8_kd), bool(v9_kd))

v8_pr = re.search(r'PROFILER_REGISTRY\s*=\s*(\{.*?\});', v8, re.DOTALL)
v9_pr = re.search(r'PROFILER_REGISTRY\s*=\s*(\{.*?\});', v9, re.DOTALL)

if v8_pr and v9_pr:
    print("PROFILER_REGISTRY identical:", v8_pr.group(1) == v9_pr.group(1))
    print("Lengths:", len(v8_pr.group(1)), len(v9_pr.group(1)))
else:
    print("PROFILER_REGISTRY regex failed:", bool(v8_pr), bool(v9_pr))
