import os, sys, re, json, glob

def parse_nccl_log(log_path):
    results = {}
    if not os.path.exists(log_path):
        return results
    
    # Regex to match size (bytes), time (us), algbw (GB/s), busbw (GB/s)
    # Header format: size count type redop root time algbw busbw #wrong time algbw busbw #wrong
    pattern = re.compile(r'^\s*(\d+)\s+\d+\s+\S+\s+\S+\s+-1\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)')
    # Pattern for sendrecv where root might be 0 or -1
    pattern_p2p = re.compile(r'^\s*(\d+)\s+\d+\s+\S+\s+\S+\s+[\d\-]+\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)')
    
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            m = pattern.match(line) or pattern_p2p.match(line)
            if m:
                sz = int(m.group(1))
                time_us = float(m.group(2))
                algbw = float(m.group(3))
                busbw = float(m.group(4))
                results[sz] = {
                    'time_us': time_us,
                    'time_ms': round(time_us / 1000.0, 4),
                    'algbw_gb_s': algbw,
                    'busbw_gb_s': busbw
                }
    return results

def find_first_existing(dir_path, filenames):
    for fn in filenames:
        p = os.path.join(dir_path, fn)
        if os.path.exists(p):
            return parse_nccl_log(p)
    return {}

def get_payload_label(bytes_val):
    kb = bytes_val / 1024.0
    mb = bytes_val / (1024.0 * 1024.0)
    if mb >= 1:
        return f"{int(mb) if mb.is_integer() else mb:.1f} MiB"
    return f"{int(kb) if kb.is_integer() else kb:.1f} KiB"

def get_milestone_desc(bytes_val):
    if bytes_val == 8192:
        return "Min Benchmark Floor (8 KiB)"
    elif bytes_val == 16384:
        return "Batch-1 Token Decode (16 KiB)"
    elif bytes_val == 131072:
        return "Small Activation (128 KiB)"
    elif bytes_val == 1048576:
        return "1 MiB Tensor"
    elif bytes_val == 16777216:
        return "16 MiB Activation"
    elif bytes_val == 67108864:
        return "64 MiB Chunk"
    elif bytes_val == 134217728:
        return "8K Prefill Chunk (128 MiB)"
    elif bytes_val == 268435456:
        return "Large Prefill (256 MiB)"
    return get_payload_label(bytes_val)

def generate_collective_csv(coll_name, data, out_dir):
    rates = ['NATIVE', '100', '50', '20', '10']
    
    # 1. TP16 vs TP8 Local
    tp16_csv = os.path.join(out_dir, f"tp16_vs_tp8_local_{coll_name}_comparison.csv")
    with open(tp16_csv, 'w', encoding='utf-8') as f:
        f.write("size_bytes,payload_label,description,tp8_local_latency_ms,tp8_local_algbw_gbs,"
                "tp16_native_175g_ms,tp16_native_algbw_gbs,tp16_100g_ms,tp16_100g_algbw_gbs,"
                "tp16_50g_ms,tp16_50g_algbw_gbs,tp16_20g_ms,tp16_20g_algbw_gbs,"
                "tp16_10g_ms,tp16_10g_algbw_gbs,tp16_native_vs_tp8_local,tp16_10g_vs_tp8_local\n")
        
        sizes = sorted(data['tp16']['NATIVE'].keys())
        for sz in sizes:
            lbl = get_payload_label(sz)
            desc = get_milestone_desc(sz)
            loc_t = data['tp8_local'].get(sz, {}).get('time_ms', 0)
            loc_bw = data['tp8_local'].get(sz, {}).get('algbw_gb_s', 0)
            
            row = [str(sz), lbl, f'"{desc}"', str(loc_t), str(loc_bw)]
            for r in rates:
                t = data['tp16'][r].get(sz, {}).get('time_ms', 0)
                bw = data['tp16'][r].get(sz, {}).get('algbw_gb_s', 0)
                row.extend([str(t), str(bw)])
            
            nat_t = data['tp16']['NATIVE'].get(sz, {}).get('time_ms', 0)
            t10 = data['tp16']['10'].get(sz, {}).get('time_ms', 0)
            r_nat = f"{(nat_t/loc_t):.2f}x" if loc_t > 0 else "-"
            r_10 = f"{(t10/loc_t):.2f}x" if loc_t > 0 else "-"
            row.extend([r_nat, r_10])
            f.write(",".join(row) + "\n")
    print(f"Generated: {tp16_csv}")

    # 2. TP8 Multi vs Local
    tp8_csv = os.path.join(out_dir, f"tp8_multinode_vs_local_{coll_name}_comparison.csv")
    with open(tp8_csv, 'w', encoding='utf-8') as f:
        f.write("size_bytes,payload_label,description,tp8_local_latency_ms,tp8_local_algbw_gbs,"
                "tp8_multi_native_175g_ms,tp8_multi_native_algbw_gbs,tp8_multi_100g_ms,tp8_multi_100g_algbw_gbs,"
                "tp8_multi_50g_ms,tp8_multi_50g_algbw_gbs,tp8_multi_20g_ms,tp8_multi_20g_algbw_gbs,"
                "tp8_multi_10g_ms,tp8_multi_10g_algbw_gbs,tp8_multi_native_vs_local,tp8_multi_10g_vs_local\n")
        for sz in sizes:
            lbl = get_payload_label(sz)
            desc = get_milestone_desc(sz)
            loc_t = data['tp8_local'].get(sz, {}).get('time_ms', 0)
            loc_bw = data['tp8_local'].get(sz, {}).get('algbw_gb_s', 0)
            row = [str(sz), lbl, f'"{desc}"', str(loc_t), str(loc_bw)]
            for r in rates:
                t = data['tp8'][r].get(sz, {}).get('time_ms', 0)
                bw = data['tp8'][r].get(sz, {}).get('algbw_gb_s', 0)
                row.extend([str(t), str(bw)])
            nat_t = data['tp8']['NATIVE'].get(sz, {}).get('time_ms', 0)
            t10 = data['tp8']['10'].get(sz, {}).get('time_ms', 0)
            r_nat = f"{(nat_t/loc_t):.2f}x" if loc_t > 0 else "-"
            r_10 = f"{(t10/loc_t):.2f}x" if loc_t > 0 else "-"
            row.extend([r_nat, r_10])
            f.write(",".join(row) + "\n")
    print(f"Generated: {tp8_csv}")

    # 3. TP4 Multi vs Local
    tp4_csv = os.path.join(out_dir, f"tp4_multinode_vs_local_{coll_name}_comparison.csv")
    with open(tp4_csv, 'w', encoding='utf-8') as f:
        f.write("size_bytes,payload_label,description,tp4_local_latency_ms,tp4_local_algbw_gbs,"
                "tp4_multi_native_175g_ms,tp4_multi_native_algbw_gbs,tp4_multi_100g_ms,tp4_multi_100g_algbw_gbs,"
                "tp4_multi_50g_ms,tp4_multi_50g_algbw_gbs,tp4_multi_20g_ms,tp4_multi_20g_algbw_gbs,"
                "tp4_multi_10g_ms,tp4_multi_10g_algbw_gbs,tp4_multi_native_vs_local,tp4_multi_10g_vs_local\n")
        for sz in sizes:
            lbl = get_payload_label(sz)
            desc = get_milestone_desc(sz)
            loc_t = data['tp4_local'].get(sz, {}).get('time_ms', 0)
            loc_bw = data['tp4_local'].get(sz, {}).get('algbw_gb_s', 0)
            row = [str(sz), lbl, f'"{desc}"', str(loc_t), str(loc_bw)]
            for r in rates:
                t = data['tp4'][r].get(sz, {}).get('time_ms', 0)
                bw = data['tp4'][r].get(sz, {}).get('algbw_gb_s', 0)
                row.extend([str(t), str(bw)])
            nat_t = data['tp4']['NATIVE'].get(sz, {}).get('time_ms', 0)
            t10 = data['tp4']['10'].get(sz, {}).get('time_ms', 0)
            r_nat = f"{(nat_t/loc_t):.2f}x" if loc_t > 0 else "-"
            r_10 = f"{(t10/loc_t):.2f}x" if loc_t > 0 else "-"
            row.extend([r_nat, r_10])
            f.write(",".join(row) + "\n")
    print(f"Generated: {tp4_csv}")

def generate_sendrecv_csv(sendrecv_data, out_dir):
    rates = ['NATIVE', '100', '50', '20', '10']
    csv_file = os.path.join(out_dir, "sendrecv_2node_vs_local_comparison.csv")
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("size_bytes,payload_label,description,local_intra_numa_ms,local_cross_numa_ms,"
                "p2p_native_175g_ms,p2p_native_algbw_gbs,p2p_100g_ms,p2p_100g_algbw_gbs,"
                "p2p_50g_ms,p2p_50g_algbw_gbs,p2p_20g_ms,p2p_20g_algbw_gbs,"
                "p2p_10g_ms,p2p_10g_algbw_gbs,p2p_native_vs_local_intra,p2p_10g_vs_local_intra\n")
        
        sizes = sorted(sendrecv_data['NATIVE'].keys())
        for sz in sizes:
            lbl = get_payload_label(sz)
            desc = get_milestone_desc(sz)
            intra_t = sendrecv_data['local_intra'].get(sz, {}).get('time_ms', 0)
            cross_t = sendrecv_data['local_cross'].get(sz, {}).get('time_ms', 0)
            row = [str(sz), lbl, f'"{desc}"', str(intra_t), str(cross_t)]
            for r in rates:
                t = sendrecv_data[r].get(sz, {}).get('time_ms', 0)
                bw = sendrecv_data[r].get(sz, {}).get('algbw_gb_s', 0)
                row.extend([str(t), str(bw)])
            nat_t = sendrecv_data['NATIVE'].get(sz, {}).get('time_ms', 0)
            t10 = sendrecv_data['10'].get(sz, {}).get('time_ms', 0)
            r_nat = f"{(nat_t/intra_t):.2f}x" if intra_t > 0 else "-"
            r_10 = f"{(t10/intra_t):.2f}x" if intra_t > 0 else "-"
            row.extend([r_nat, r_10])
            f.write(",".join(row) + "\n")
    print(f"Generated: {csv_file}")

def parse_full_suite(base_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rates = ['NATIVE', '100', '50', '20', '10']
    collectives = ['allreduce', 'allgather', 'reducescatter', 'alltoall']
    master_data = {}

    # 1. Parse SendRecv
    sr_dir = os.path.join(base_dir, "sendrecv")
    if os.path.exists(sr_dir):
        sendrecv_data = {
            'local_intra': find_first_existing(sr_dir, ["sendrecv_local_intra_numa.log", "local_intra.log"]),
            'local_cross': find_first_existing(sr_dir, ["sendrecv_local_cross_numa.log", "local_cross.log"]),
        }
        for r in rates:
            sendrecv_data[r] = find_first_existing(sr_dir, [f"sendrecv_2node_{r}.log", f"2node_{r}.log", f"{r}.log"])
        generate_sendrecv_csv(sendrecv_data, out_dir)
        master_data['sendrecv'] = sendrecv_data

    # 2. Parse Collectives
    for coll in collectives:
        c_dir = os.path.join(base_dir, coll)
        if not os.path.exists(c_dir):
            print(f"Directory {c_dir} not found, skipping...")
            continue
        coll_data = {
            'tp8_local': find_first_existing(c_dir, [f"tp8_local.log", f"{coll}_tp8_local.log", "tp8.log"]),
            'tp4_local': find_first_existing(c_dir, [f"tp4_local.log", f"{coll}_tp4_local.log", "tp4.log"]),
            'tp16': {},
            'tp8': {},
            'tp4': {}
        }
        for r in rates:
            coll_data['tp16'][r] = find_first_existing(c_dir, [f"tp16_{r}.log", f"{coll}_tp16_{r}.log"])
            coll_data['tp8'][r] = find_first_existing(c_dir, [f"tp8_{r}.log", f"{coll}_tp8_multi_{r}.log", f"{coll}_tp8_{r}.log"])
            coll_data['tp4'][r] = find_first_existing(c_dir, [f"tp4_{r}.log", f"{coll}_tp4_multi_{r}.log", f"{coll}_tp4_{r}.log"])
        
        generate_collective_csv(coll, coll_data, out_dir)
        master_data[coll] = coll_data

    # Save Master JSON
    json_path = os.path.join(out_dir, "master_benchmarks_all_collectives.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, indent=2)
    print(f"Master JSON generated: {json_path}")
    return master_data

if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else "rtx_g4_smoke_v4/results"
    out = sys.argv[2] if len(sys.argv) > 2 else "rtx_g4_smoke_v4/results"
    parse_full_suite(base, out)
