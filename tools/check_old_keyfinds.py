import sys, re
dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"
with open(dash_path, "r", encoding="utf-8") as f:
    h = f.read()

# Let us check occurrences of "does not establish the allocator's exact sharding rule"
print("Found old TOP 10 text:", "does not establish the allocator's exact sharding rule" in h)
print("Found old TOP 3 text:", "not fully decomposed" in h)
