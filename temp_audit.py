import subprocess

p = subprocess.run(['tail', '-n', '15', '/home/ayu23/v9_full_production_execution.log'], capture_output=True, text=True)
print(p.stdout)