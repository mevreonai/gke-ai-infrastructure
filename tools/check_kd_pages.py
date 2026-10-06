import re, json

with open('v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    h = f.read()

pos = h.find('KD_PAGES_DATA = [')
if pos != -1:
    end_pos = h.find(';\n', pos)
    data_str = h[pos + len('KD_PAGES_DATA = '):end_pos]
    try:
        data = json.loads(data_str)
        print(f"Parsed {len(data)} pages successfully!\n")
        for p in data:
            idx = p.get('id')
            title = p.get('title')
            print(f"=== Page {idx}: {title} ===")
            print("Confidence:", p.get("confidence"))
            print("Confidence note:", p.get("confidence_note"))
            print("Scope note:", p.get("scope_note"))
            takeaways = p.get("key_takeaways", [])
            print(f"Takeaways ({len(takeaways)}):")
            for t in takeaways:
                print("  -", t)
            meas = p.get("exact_measured_values", {})
            if "evidence_layers" in meas:
                print("Evidence layers:")
                for el in meas["evidence_layers"]:
                    print("   ", el)
            print()
    except Exception as e:
        print("JSON parse error:", e)
        # print snippet
        print(data_str[:500])
