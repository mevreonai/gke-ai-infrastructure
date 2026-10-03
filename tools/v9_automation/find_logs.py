import glob, os

files = glob.glob('**/*tp4_pp4*', recursive=True)
print("Files matching tp4_pp4:", len(files))
for f in files[:10]:
    print(" ", f)

files_log = glob.glob('**/*server*.log', recursive=True) + glob.glob('**/*vllm*.log', recursive=True)
print("\nLog files found:", len(files_log))
for f in files_log[:10]:
    print(" ", f)
