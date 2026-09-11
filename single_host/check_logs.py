import subprocess
res = subprocess.run(["gcloud.cmd", "logging", "read", 'timestamp >= "2026-09-07T11:46:00Z" AND severity >= WARNING', "--limit=10", "--format=yaml(timestamp,severity,protoPayload.status.message,protoPayload.methodName,textPayload)"], capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
