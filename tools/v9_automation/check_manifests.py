import json, os, glob

# Check case_manifest.json files
manifests = glob.glob('**/*manifest*.json', recursive=True)
print(f"Total manifest files found: {len(manifests)}")

cases_status = {}
for m in manifests:
    if 'case_manifest.json' in m:
        try:
            with open(m, 'r', encoding='utf-8') as f:
                data = json.load(f)
                case_name = data.get('case_name') or data.get('case') or os.path.basename(os.path.dirname(m))
                status = data.get('status') or data.get('state')
                cases_status[m] = {'case': case_name, 'status': status, 'optional': data.get('optional_capability_probe')}
        except Exception as e:
            pass

print("\n--- Case Manifests Summary ---")
for path, info in sorted(cases_status.items()):
    print(f"{info['case']:<30} | Status: {str(info['status']):<15} | Optional: {info.get('optional')} | Path: {path}")
