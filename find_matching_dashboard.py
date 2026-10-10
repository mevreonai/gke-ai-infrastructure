import hashlib
import glob

def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

target = 'v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html'
target_hash = sha(target)
print(f"Target '{target}' SHA256: {target_hash}")

for f in sorted(glob.glob('*.html') + glob.glob('*/*/*.html') + glob.glob('*/*.html')):
    if f.replace('\\', '/') == target.replace('\\', '/'): continue
    h = sha(f)
    if h == target_hash:
        print(f"MATCH: {f}")
    else:
        # Check size similarity
        import os
        diff = abs(os.path.getsize(f) - os.path.getsize(target))
        if diff < 50000:
            print(f"Similar size ({diff} bytes diff): {f}")
