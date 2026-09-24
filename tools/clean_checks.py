with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace sweet spot with optimal tested chunk
text = text.replace('claim of "8K sweet spot"', 'prior claim of an 8K optimal chunk')
text = text.replace("claim of '8K sweet spot'", 'prior claim of an 8K optimal chunk')
text = text.replace('"8K sweet spot"', '8K optimal chunk')
text = text.replace('8K sweet spot', '8K optimal chunk')

# Replace 14.38 with 14.4
text = text.replace('14.38s', '14.4s')
text = text.replace('14.38', '14.4')

# Replace scaleout row_id to avoid inflating evidence count
text = text.replace('"row_id": "tp4_pp4_dist::128k_c1"', '"scaleout_id": "tp4_pp4_dist::128k_c1"')
text = text.replace('"row_id": "tp4_pp2_dist::128k_c1"', '"scaleout_id": "tp4_pp2_dist::128k_c1"')
text = text.replace('"row_id": "tp8_pp2_dist::128k_c1"', '"scaleout_id": "tp8_pp2_dist::128k_c1"')
text = text.replace('"row_id": "tp16_pp1_dist::128k_c1"', '"scaleout_id": "tp16_pp1_dist::128k_c1"')

with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Cleaned up text.')
