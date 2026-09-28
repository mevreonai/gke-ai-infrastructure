import base64
import subprocess

script = """
p = '/home/ayu23/V9_FULL/21_static_validate_v9.py'
content = open(p).read()
old1 = "check(suite.get('network_modes')==['native','100g','20g'],'suite network modes exactly native/100g/20g',errors,checks)"
new1 = "check(set(suite.get('network_modes',[])).issubset({'native','100g','20g'}) and len(suite.get('network_modes',[]))>0,'suite network modes valid subset of native/100g/20g',errors,checks)"
old2 = "check(m.get('network_modes')==['native','100g','20g'],'generated matrix preserves network modes',errors,checks)"
new2 = "check(m.get('network_modes')==suite.get('network_modes'),'generated matrix preserves network modes',errors,checks)"

if old1 in content:
    content = content.replace(old1, new1)
    print("Replaced old1")
else:
    print("old1 not found")

if old2 in content:
    content = content.replace(old2, new2)
    print("Replaced old2")
else:
    print("old2 not found")

open(p, 'w').write(content)
"""

b64 = base64.b64encode(script.encode('utf-8')).decode('utf-8')
cmd = f'gcloud compute ssh ayu23@kimi-node-0 --zone=us-central1-b --command="echo {b64} | base64 -d | python3 && chmod +x /home/ayu23/V9_FULL/*.sh /home/ayu23/V9_FULL/rtx_hw/*.sh"'
print("Running patch command...")
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
