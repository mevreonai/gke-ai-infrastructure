with open('KEY_DISCOVERIES_STANDALONE_DASHBOARD.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="kd-map-details"')
print('Map details tag:', text[idx-20:idx+60].encode('ascii', errors='replace').decode('ascii'))
print('Has open attribute?:', 'open' in text[idx-10:idx+35])
print('Has Unfold 60-sec Map:', 'Unfold 60-sec Map' in text)
print('Has Fold 60-sec Map in listener:', 'Fold 60-sec Map' in text)

print('\nFinding 6 labels on canvas check (KEY_DISCOVERIES_STANDALONE_DASHBOARD.html):')
print('  TP4 / PP1 (93.2s) in text:', 'TP4 / PP1 (93.2s)' in text)
print('  TP4 / PP2 (52.5s) in text:', 'TP4 / PP2 (52.5s)' in text)
print('  TP4 / PP4 (28.6s) in text:', 'TP4 / PP4 (28.6s)' in text)
print('  TP8 / PP1 (74.7s) in text:', 'TP8 / PP1 (74.7s)' in text)
print('  TP8 / PP2 (41.5s) in text:', 'TP8 / PP2 (41.5s)' in text)
print('  TP16 / PP1 (68.2s) in text:', 'TP16 / PP1 (68.2s)' in text)
print('  frontierPointLabels plugin in text:', 'frontierPointLabels' in text)

with open('MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html', 'r', encoding='utf-8') as f:
    master_text = f.read()

idx_m = master_text.find('id="kd-map-details"')
print('\nMASTER Map details tag:', master_text[idx_m-20:idx_m+60].encode('ascii', errors='replace').decode('ascii'))
print('MASTER Has open attribute?:', 'open' in master_text[idx_m-10:idx_m+35])
print('\nFinding 6 labels on canvas check (MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html):')
print('  TP4 / PP1 (93.2s) in master:', 'TP4 / PP1 (93.2s)' in master_text)
print('  TP4 / PP2 (52.5s) in master:', 'TP4 / PP2 (52.5s)' in master_text)
print('  TP4 / PP4 (28.6s) in master:', 'TP4 / PP4 (28.6s)' in master_text)
print('  TP8 / PP1 (74.7s) in master:', 'TP8 / PP1 (74.7s)' in master_text)
print('  TP8 / PP2 (41.5s) in master:', 'TP8 / PP2 (41.5s)' in master_text)
print('  TP16 / PP1 (68.2s) in master:', 'TP16 / PP1 (68.2s)' in master_text)
print('  frontierPointLabels plugin in master:', 'frontierPointLabels' in master_text)
