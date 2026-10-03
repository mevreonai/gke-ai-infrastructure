from pathlib import Path

for path in [Path("v9_full_result/MASTER_CHARACTERIZATION_DASHBOARD.html"), Path("v9_full_result/index.html")]:
    text = path.read_text(encoding="utf-8")
    
    # Replace [68.2, 28.57] with [133.64, 127.13]
    text = text.replace('"data": [\n                68.2,\n                28.57\n              ]', '"data": [\n                133.64,\n                127.13\n              ]')
    text = text.replace('"data":[68.2,28.57]', '"data":[133.64,127.13]')
    
    # Also update the labels if needed
    text = text.replace('"TP16 / PP1 (Cross-Node AllReduce)","TP4 / PP4 (Pipelined NUMA)"', '"TP8 / PP2 (Dual-Node Stage-Pipelined)","TP4 / PP2 (Dual-Node Intra-Socket)"')
    text = text.replace('TP16 / PP1 (Cross-Node AllReduce)', 'TP8 / PP2 (Dual-Node Stage-Pipelined)')
    text = text.replace('TP4 / PP4 (Pipelined NUMA)', 'TP4 / PP2 (Dual-Node Intra-Socket)')

    path.write_text(text, encoding="utf-8")

print("Updated discovery chart data points successfully.")
