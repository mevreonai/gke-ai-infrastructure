"""The coverage table behind section 6 of Scripts_Review_v1.3.md: for each layout, what the master runner would run (prompt
length x requests in flight, by master step or batching block), which cases no step runs, the points vLLM would refuse
("refused": prompt plus output longer than the server's max_model_len), and which profiles the master selects, with each
profile script's defaults filled in and the two-server Nsight driver's mode filter and eager setting read from its scripts.
Reads the case files, the profile matrix, the profile scripts and the master runner as shared; runs nothing and imports
nothing from them. Every step's topology guard is taken as matching, and batching blocks count only when --cb-blocks or
CB_BLOCKS selects them. Re-run it after any change to those files to see the new coverage.
Usage: python3 -I coverage_matrix.py <Performance_Intelligence_Platform dir>"""
import collections, itertools, json, re, sys
from pathlib import Path

S = Path(sys.argv[1]) / "scripts"
M = (S / "run_master_benchmark.sh").read_text(errors="replace")
cases = json.loads((S / "master_benchmark_cases.json").read_text())["cases"]
cases = cases if isinstance(cases, dict) else {c["name"]: c for c in cases}
cb = json.loads((S / "continuous_batching_cases.json").read_text())
blocks = cb.get("blocks", {})
LIM_MAIN = json.loads((S / "master_benchmark_cases.json").read_text())["server_defaults"]["max_model_len"]
LIM_CB = cb["server_defaults"]["max_model_len"]
REF = set()   # (layout, source, prompt length, in flight) that the server would refuse
def over(b, c, lim): return b["input"] + b.get("output", 0) > c.get("max_model_len", lim)
mx = json.loads((S / "06_deep_kernel_and_torch_profiling/18_multi_node_profile_matrix.json").read_text())["profiles"]
ORDER = ["TP4/PP1", "TP8/PP1", "TP4/PP2", "TP16/PP1", "TP8/PP2", "TP4/PP4"]
GPUS = {"TP4/PP1": 4, "TP8/PP1": 8, "TP4/PP2": 8, "TP16/PP1": 16, "TP8/PP2": 16, "TP4/PP4": 16}
OPTIONAL = {17: "batching, only with CB_BLOCKS", 18: "deep-profile only", 19: "deep-profile only", 20: "deep-profile only"}


def lay(c): return f"TP{c['tp']}/PP{c.get('pp', 1)}"
def size(n): return "1M" if n in (1000000, 1048576) else (f"{n // 1024}K" if n >= 1024 else str(n))


# which master step runs which case: --case, --group and the scheduler loop
steps = [(int(m.group(1)), m.start()) for m in re.finditer(r"# STEP (\d+):", M)]
step_of = collections.defaultdict(set)
for i, (st, pos) in enumerate(steps):
    body = M[pos:steps[i + 1][1] if i + 1 < len(steps) else len(M)]
    for name in re.findall(r"--case (\w+)", body): step_of[name].add(st)
    for g in re.findall(r"--group (\w+)", body):
        for name, c in cases.items():
            if g in c.get("groups", []): step_of[name].add(st)
    loop = re.search(r"for seq_case in ([\w ]+); do", body)
    if loop:
        for name in loop.group(1).split(): step_of[name].add(st)

serving = collections.defaultdict(lambda: collections.defaultdict(set))
for name, c in cases.items():
    for st in step_of.get(name, ()):
        for b in c["benchmarks"]:
            if b.get("input"):
                src = f"step {st}" + (" (deep-profile only)" if st in (18, 19, 20) else "")
                serving[lay(c)][(b["input"], b["concurrency"])].add(src)
                if over(b, c, LIM_MAIN): REF.add((lay(c), src, b["input"], b["concurrency"]))
for c in cb["cases"]:
    for b in c["benchmarks"]:
        streams = [b] if "input" in b else [v for v in b.values() if isinstance(v, dict) and "input" in v]
        for s in streams:
            rate = s.get("request_rate") is not None or b.get("request_rate") is not None
            key = (s["input"], ("rate" + (f" (cap c{s['concurrency']})" if s.get("concurrency") else "")) if rate else s.get("concurrency"))
            src = f"batching block {c['block']} ({blocks.get(str(c['block']), '?')})"
            serving[lay(c)][key].add(src)
            if over(s, c, LIM_CB): REF.add((lay(c), src) + key)

print("SERVING RUNS (prompt length: requests in flight; 'rate' = arrivals at a set rate; batching blocks run in step 17 only when --cb-blocks or CB_BLOCKS selects them)")
# step 4 starts its own TP8 server inline (no case): 8K one at a time, 12 requests, unpinned then pinned
s4 = M[M.index("# STEP 04:"):M.index("# STEP 05:")]
if "--tensor-parallel-size 8" in s4 and "--random-input-len 8192" in s4 and "--max-concurrency 1" in s4 and "--num-prompts 12" in s4:
    serving["TP8/PP1"][(8192, 1)].add("step 4 (inline server; unpinned, then pinned)")
for L in ORDER:
    print(f"  {L} · {GPUS[L]} GPUs")
    pts = serving.get(L, {})
    by_src = collections.defaultdict(lambda: collections.defaultdict(set))
    for (inp, conc), srcs in pts.items():
        for s in srcs: by_src[s][inp].add(conc)
    for src in sorted(by_src, key=lambda s: (not s.startswith("step"), int(re.search(r"\d+", s).group()))):
        cells = "; ".join(f"{size(i)} " + "/".join((("c" + str(x)) if not isinstance(x, str) else x) + (" refused" if (L, src, i, x) in REF else "")
                                                   for x in sorted(v, key=lambda x: (isinstance(x, str), str(x) if isinstance(x, str) else x)))
                          for i, v in sorted(by_src[src].items()))
        print(f"      {src:58s} {cells}")
    if not pts: print("      none")
print("  defined, but no master step runs them: " + ", ".join(f"{n} ({lay(c)})" for n, c in sorted(cases.items()) if not step_of.get(n)))

print("PROFILES THE MASTER SELECTS (every step's topology guard taken as matching)")
PD = S / "06_deep_kernel_and_torch_profiling"
case_py = (PD / "18_run_vllm_multi_node_profile_case.py").read_text(errors="replace")
drv = (PD / "18_run_vllm_multi_node_profiles.sh").read_text(errors="replace")
nsys = (PD / "14_run_vllm_nsys_profile.sh").read_text(errors="replace")
t14c = (PD / "14c_run_vllm_torch_profile_batched.sh").read_text(errors="replace")
t14d = (PD / "14d_run_vllm_torch_profile_multi_node.sh").read_text(errors="replace")
# the two-server Nsight captures run eager when the case script adds --enforce-eager unconditionally
ALWAYS_EAGER = re.search(r"^\s*if '--enforce-eager' in serve_help: server_cmd \+= \['--enforce-eager'\]\s*$", case_py, re.M) is not None
GATE = re.search(r"ENFORCE_EAGER['\"]\s*,\s*['\"](\d)['\"]", case_py)          # a switch such as os.environ.get('ENFORCE_EAGER', '1')
def eager2(d):
    if ALWAYS_EAGER: return "eager"
    if GATE: return "eager" if d.get("ENFORCE_EAGER", GATE.group(1)) == "1" else "graphs on"
    return "eager or graphs on (see the case script)"
EXACT = "if mode and p['mode'] != mode: continue" in drv            # the driver's mode filter: one exact name
def dflt(txt, var, fb="?"):
    m = re.search(r"\$\{" + var + r":=([^}]*)\}", txt); return m.group(1) if m else fb
def mode_dflt(mode, var, fb="?"):
    m = re.search(r"^\s*" + mode + r"\)(.*?);;", nsys, re.M)
    v = m and re.search(var + r"=\$\{" + var + r":-(\d+)\}", m.group(1)); return v.group(1) if v else fb
def kv(line): return {k: v.strip("'\"\\") for k, v in re.findall(r"\b([A-Z][A-Z0-9_]*)=(\\?\"[^\"]*\"|'[^']*'|[^\s;'\"]+)", line)}
def sz(x): return size(int(x)) if str(x).isdigit() else str(x)
sel, out = [], []
for i, (st, pos) in enumerate(steps):
    body = re.sub(r"\\\s*\n\s*", " ", M[pos:steps[i + 1][1] if i + 1 < len(steps) else len(M)])
    loop = re.search(r"for topo in ([\w ]+); do", body)
    for line in body.splitlines():
        d = kv(line)
        if "14_run_vllm_nsys_profile.sh" in line:
            mode = d.get("PROFILE_MODE", dflt(nsys, "PROFILE_MODE"))
            eager = d.get("ENFORCE_EAGER", dflt(nsys, "ENFORCE_EAGER", "0")) == "1"
            out.append((st, "single-node Nsight", f"TP{d.get('TP', dflt(nsys, 'TP'))} {mode} {sz(d.get('INPUT_LEN', mode_dflt(mode, 'INPUT_LEN')))} "
                        f"c{d.get('CONCURRENCY', mode_dflt(mode, 'CONCURRENCY'))} {'eager' if eager else 'graphs on'}"))
        elif "14c_run_vllm_torch_profile_batched.sh" in line:
            out.append((st, "torch", f"TP{d.get('TP', dflt(t14c, 'TP'))} {sz(d.get('INPUT_LEN', dflt(t14c, 'INPUT_LEN')))} c{d.get('CONCURRENCY', dflt(t14c, 'CONCURRENCY'))} "
                        + ("eager" if "--enforce-eager" in t14c else "graphs on")))
        elif "14d_run_vllm_torch_profile_multi_node.sh" in line:
            topo = d.get("TOPOLOGY", dflt(t14d, "TOPOLOGY"))
            for t in (loop.group(1).split() if topo == "$topo" and loop else [topo]):
                out.append((st, "two-server torch", f"{t} {sz(d.get('INPUT_LEN', dflt(t14d, 'INPUT_LEN')))} c{d.get('CONCURRENCY', dflt(t14d, 'CONCURRENCY'))} "
                            + ("eager" if "--enforce-eager" in t14d else "graphs on")))
        elif "18_run_vllm_multi_node_profiles.sh" in line:
            topo = d.get("PROFILE_TOPOLOGY_FILTER"); modes = [m for m in d.get("PROFILE_MODE_FILTER", "").split(",") if m]
            heavy = d.get("RUN_HEAVY_PROFILE", dflt(drv, "RUN_HEAVY_PROFILE", "1")) == "1"
            if len(modes) > 1 and EXACT:
                out.append((st, "two-server Nsight", f"filter '{','.join(modes)}' is one name to the driver, which takes one exact mode (it selects nothing)")); continue
            hit = [q for q in mx if (heavy or not q.get("optional_heavy")) and (not topo or q["topology"] == topo) and (not modes or q["mode"] in modes)]
            sel += hit
            out += [(st, "two-server Nsight", f"{q['topology']} {q['mode']} {eager2(d)}") for q in hit]
            if modes and not hit:
                out.append((st, "two-server Nsight", f"filter mode '{','.join(modes)}' matches none of the matrix's modes"))
for (st, kind), grp in itertools.groupby(out, key=lambda r: (r[0], r[1])):
    print(f"  step {st}: {kind}: " + "; ".join(r[2] for r in grp))
modes = collections.Counter(q["topology"] for q in mx)
print("  two-server Nsight captures the server would refuse (prompt + output longer than max_model_len): "
      + (", ".join(sorted({f"{q['mode']} ({q['input']:,} + {q['output']})" for q in mx if q["input"] + q["output"] > LIM_MAIN})) or "none"))
print(f"  the two-server Nsight matrix defines {len(mx)} captures ({', '.join(f'{t} {n}' for t, n in sorted(modes.items()))}); the master selects {len(sel)}")
