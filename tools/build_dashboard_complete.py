import json
import csv
import os
import re
import datetime

print("Running tools/build_dashboard_complete.py...")

# 1. Load data
with open('data/evidence.json', 'r', encoding='utf-8') as f:
    ev_full = json.load(f)
meta = ev_full['meta']
rows = ev_full['rows']
missing = ev_full['missing_configured_cases']

with open('data/scaleout.json', 'r', encoding='utf-8') as f:
    scaleout_rows = json.load(f)['rows']

ev_map = {(r['case'], r['bench']): r for r in rows}

# Pre-fetch key rows for convenience
q_tp4_8k_c1 = ev_map[('tp4_qualification', '8k_c1')]
q_tp4_8k_c8 = ev_map[('tp4_qualification', '8k_c8')]
q_tp4_128k_c1 = ev_map[('tp4_qualification', '128k_c1')]
q_tp4_512k_c1 = ev_map[('tp4_qualification', '512k_c1')]

q_tp8_8k_c1 = ev_map[('tp8_qualification', '8k_c1')]
q_tp8_8k_c8 = ev_map[('tp8_qualification', '8k_c8')]
q_tp8_128k_c1 = ev_map[('tp8_qualification', '128k_c1')]
q_tp8_512k_c1 = ev_map[('tp8_qualification', '512k_c1')]

cl8_c1 = ev_map[('tp4_closedloop_8k', 'c1')]
cl8_c4 = ev_map[('tp4_closedloop_8k', 'c4')]
cl8_c8 = ev_map[('tp4_closedloop_8k', 'c8')]
cl8_c16 = ev_map[('tp4_closedloop_8k', 'c16')]
cl8_c32 = ev_map[('tp4_closedloop_8k', 'c32')]

cl128_c1 = ev_map[('tp4_closedloop_128k', 'c1')]
cl128_c4 = ev_map[('tp4_closedloop_128k', 'c4')]
cl128_c8 = ev_map[('tp4_closedloop_128k', 'c8')]
cl128_c16 = ev_map[('tp4_closedloop_128k', 'c16')]

cl512_c1 = ev_map[('tp4_closedloop_512k', 'c1')]
cl512_c2 = ev_map[('tp4_closedloop_512k', 'c2')]
cl512_c4 = ev_map[('tp4_closedloop_512k', 'c4')]

cl1m_c1 = ev_map[('tp4_closedloop_1m', 'c1')]
cl1m_c2 = ev_map[('tp4_closedloop_1m', 'c2')]
cl1m_c4 = ev_map[('tp4_closedloop_1m', 'c4')]

b_tp4_8k = ev_map[('tp4_context_baseline', '8k_c1')]
b_tp4_128k = ev_map[('tp4_context_baseline', '128k_c1')]
b_tp4_512k = ev_map[('tp4_context_baseline', '512k_c1')]
b_tp4_1m = ev_map[('tp4_context_baseline', '1m_c1')]

b_tp8_8k = ev_map[('tp8_context_baseline', '8k_c1')]
b_tp8_128k = ev_map[('tp8_context_baseline', '128k_c1')]
b_tp8_512k = ev_map[('tp8_context_baseline', '512k_c1')]
b_tp8_1m = ev_map[('tp8_context_baseline', '1m_c1')]

ch4k = ev_map[('tp4_chunk4k', '1m_c1')]
ch8k = ev_map[('tp4_chunk8k', '1m_c1')]
ch16k = ev_map[('tp4_chunk16k', '1m_c1')]

p128 = ev_map[('tp4_prefix128k', 'prefix128k')]
p512 = ev_map[('tp4_prefix512k', 'prefix512k')]

m4 = ev_map[('tp4_512k_maxseq4', '512k_c4')]
m8 = ev_map[('tp4_512k_maxseq8', '512k_c4')]
m16 = ev_map[('tp4_512k_maxseq16', '512k_c4')]

print("Data mappings pre-fetched successfully.")
