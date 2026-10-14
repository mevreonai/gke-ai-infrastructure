import subprocess

p = subprocess.run(['tail', '-n', '15', '/home/user/v9_full_production_execution.log'], capture_output=True, text=True)
print(p.stdout)