import json
import subprocess
import time
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Run headless chrome to test v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html
target_file = os.path.abspath('v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html')
file_url = 'file:///' + target_file.replace('\\', '/')

print(f"Testing URL: {file_url}")

# Use node with puppeteer if available, or python script with webdriver, or inspect JS
# Let's check if puppeteer or playwright or selenium is installed
try:
    import selenium
    print("Selenium is available")
except ImportError:
    print("Selenium not installed")

# Let's check node
try:
    res = subprocess.run(["node", "-v"], capture_output=True, text=True)
    print("Node version:", res.stdout.strip())
except Exception as e:
    print("Node not available:", e)
