"""Checks behind section 5 of Scripts_Review_v1.2.md: what the existing logs say about VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS.

Reads each log set in place (a folder or a .zip; .zip, .tgz and .tar.gz archives inside are read in memory). An optional
::<path prefix> keeps one part of an archive (for example one stage of a zip that holds two). Prints, per set:
  config  what the run records say the servers ran with: FlashInfer and nvcc packages, CUDA_HOME, the skip list, the MoE
          backend, split and pynccl variables, the autotune and eager flags in the saved commands, the Ray workers' library path
  C1      the MoE backend each logged server chose (its start-up line)
  C2      whether FlashInfer autotune ran, was turned off, or never came up (FlashInfer not usable); whether the skip list
          was applied (its start-up line, logged once per node); whether an autotune cache file was named (rank 0 logs it);
          C2b: whether every worker that ran the autotune step tuned the same operations (all or none tuned the two GEMMs)
  C3      the operations tuned; tuned results read from a cache file ('Config cache hit'); shapes no tuned result covers
  C4      autotuning time per worker (FlashInfer's start and end lines)
  C5      starts that may have stopped: an autotune line with nothing after it; worker logs that end before start-up is done
  C6      server start-up (start -> ready) per layout in launch order, first start of a set-up against later ones,
          whether each serving start kept a server log, and the starts that never became ready
  C7      MoE kernel time per call in each Nsight capture: the two main FlashInfer CUTLASS MoE kernels, or Triton's
  C8      worker start-up phases per capture: when its workers started, total (worker init to the JIT-monitor line),
          weights, autotune
  SPLIT   the same-session layer-split A/B (15/12 against vLLM's default), where a set holds one
and, across sets, the captures with the same name (C7 x) and each layout's first and later starts (C6 x).
Nothing is written. Paths under a home folder are masked. Standard library only.
Usage: python3 -I check_autotune_skip.py <name>=<folder or .zip>[::<path prefix>] [...]"""
import collections, csv, datetime as dt, io, json, os, re, statistics as st, sys, tarfile, zipfile

ANSI = re.compile(r"\x1b\[[0-9;]*m")
SRC = re.compile(r"(?:INFO|WARNING|DEBUG) \d\d-\d\d \d\d:\d\d:\d\d \[([a-z_0-9]+\.py:\d+)\] ([A-Za-z][^\n]{0,120})")
ARCH = (".zip", ".tgz", ".tar.gz", ".tar")
# folder and archive names that carry a version label or a model name are never printed
HIDE = re.compile("|".join(["v" + "8", "v" + "9", "ki" + "mi", "deep" + "seek", "mx" + "fp4", "moon" + "shot"]), re.I)
HOME = re.compile(r"/(?:home|Users)/[^/\s'\"]+")


def members(path, prefix=""):
    """Yield (name, bytes) for every file under a folder or in a zip, descending into nested zips and tarballs."""
    def from_bytes(name, data):
        if name.endswith(".zip"):
            try:
                z = zipfile.ZipFile(io.BytesIO(data))
            except zipfile.BadZipFile:
                return
            for i in z.infolist():
                if not i.is_dir() and not i.filename.startswith("__MACOSX/"):
                    yield from from_bytes(name + "!/" + i.filename, z.read(i))
        elif name.endswith((".tgz", ".tar.gz", ".tar")):
            try:
                tf = tarfile.open(fileobj=io.BytesIO(data))
            except tarfile.TarError:
                return
            with tf:
                for m in tf.getmembers():
                    if m.isfile():
                        f = tf.extractfile(m)
                        if f:
                            yield from from_bytes(name + "!/" + m.name, f.read())
        else:
            yield name, data
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for fn in files:
                p = os.path.join(root, fn)
                rel = os.path.relpath(p, path)
                if rel.startswith(prefix):
                    with open(p, "rb") as f:
                        yield from from_bytes(rel, f.read())
    else:
        with zipfile.ZipFile(path) as z:
            for i in z.infolist():
                if not i.is_dir() and not i.filename.startswith("__MACOSX/") and i.filename.startswith(prefix):
                    yield from from_bytes(i.filename, z.read(i))


def parts(name):
    """A path's folder names without archive names; any name that carries a label is shown as '…'."""
    return ["…" if HIDE.search(x) else x for x in name.replace("!/", "/").split("/") if x and not x.endswith(ARCH)]


def labels(keys, least=3):
    """The shortest path ending (at least `least` folders) that tells each key apart from the others."""
    p = {k: parts(k) for k in keys}
    out = {}
    for k, v in p.items():
        n = least
        while n < len(v) and sum(1 for w in p.values() if w[-n:] == v[-n:]) > 1:
            n += 1
        out[k] = "/".join(v[-n:])
    return out


def container(name):
    """The archive (or folder) a log came from, so that one worker's lines can be paired by pid."""
    return name.rsplit("!/", 1)[0] if "!/" in name else os.path.dirname(name)


PID = re.compile(r"\((?:Worker|EngineCore|APIServer|RayWorker)[A-Za-z_0-9]* pid=(\d+)")
VTS = re.compile(r"INFO (\d\d-\d\d \d\d:\d\d:\d\d) \[")                          # vLLM's own lines
FTS = re.compile(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) - INFO - autotuner")   # FlashInfer's autotuner lines
BACKEND = re.compile(r"Using (TRITON|FlashInfer CUTLASS|FlashInfer TRTLLM|BATCHED_TRITON|FLASHINFER_CUTLASS|FLASHINFER_TRTLLM) Unquantized MoE backend")
PHASES = [("weights loaded", "Loading weights took"),
          ("KV cache sized", "Available KV cache memory"), ("autotune started", "Running FlashInfer autotune"),
          ("graphs captured", "Graph capturing finished"), ("start-up done", "Kernel JIT monitor activated")]


def scan(path, prefix=""):
    S = dict(backend=collections.Counter(), at_run=0, at_off=0, at_skipops=collections.Counter(), backend_logs=0, backend_logs_no_fi=0,
             cache_file=0, cache_hit=collections.Counter(), no_cover=collections.Counter(),
             tuned_ops=collections.Counter(), workers=collections.defaultdict(dict), startups=[], env=[], freeze=collections.Counter(),
             ldpath=collections.Counter(), cmds=collections.Counter(), kern=collections.defaultdict(list), logdirs=set(),
             capstate=collections.defaultdict(set), split=collections.defaultdict(dict), failed=[], vllm_version=collections.Counter(),
             src=collections.defaultdict(set))
    manifests, runner_env = {}, {}
    for name, data in members(path, prefix):
        base = name.rsplit("/", 1)[-1]
        if base.endswith((".log", ".out", ".err", ".txt")) and b"INFO" in data:
            s = ANSI.sub("", data.decode("utf-8", "replace"))
            if "vllm" in s.lower():
                S["logdirs"].add(name.split("!/", 1)[0].rsplit("/", 1)[0])
            if "/node" in name:   # the capture this log belongs to: what its autotune step did
                cs = S["capstate"][name.split("/node")[0]]
                if re.search(r"Running FlashInfer autotune with \d+ tokens", s): cs.add("autotune ran")
                if "Skipping FlashInfer autotune because it is disabled" in s: cs.add("autotune off")
                if "Skipping FlashInfer autotuning for ops" in s: cs.add("skip list")
            m = BACKEND.search(s)
            if m:
                S["backend"][m.group(1).replace("FLASHINFER_", "FlashInfer ").replace("CUTLASS", "CUTLASS")] += 1; S["backend_logs"] += 1
                if not re.search(r"Running FlashInfer autotune|Skipping FlashInfer autotune", s): S["backend_logs_no_fi"] += 1
            S["at_run"] += bool(re.search(r"Running FlashInfer autotune with \d+ tokens", s))
            S["at_off"] += "Skipping FlashInfer autotune because it is disabled" in s
            S["cache_file"] += "Using FlashInfer autotune cache file:" in s
            for ops in re.findall(r"Skipping FlashInfer autotuning for ops (\(.*?\))", s): S["at_skipops"][ops] += 1
            for op in set(re.findall(r"Tuning (trtllm::fused_moe::gemm[12]|[a-z_]+::[a-z_:]+[a-z0-9]):", s)): S["tuned_ops"][op] += 1
            for op in set(re.findall(r"Config cache hit for (\S+) \(runner=", s)): S["cache_hit"][op] += 1
            for op in set(re.findall(r"No tuned config covers (\S+) input_shapes", s)): S["no_cover"][op] += 1
            for mm in SRC.finditer(s):
                key = re.sub(r"[0-9][0-9.:,x%-]*", "#", mm.group(2))[:60].strip()
                S["src"][key].add(mm.group(1))
            c = container(name)
            fp = PID.search(s)
            for line in s.splitlines():
                p = PID.search(line)
                if "Tuning trtllm::fused_moe::gemm" in line and (p or fp):
                    S["workers"][(c, (p or fp).group(1))]["tuned_gemm"] = True
                if not p: continue
                w = S["workers"][(c, p.group(1))]
                v, f = VTS.search(line), FTS.search(line)
                if v:
                    t = dt.datetime.strptime("2026-" + v.group(1), "%Y-%m-%d %H:%M:%S")
                    w["last"] = max(w.get("last", t), t)
                    if "world_size=" in line and "init" not in w: w["init"] = t
                    mm = re.search(r"Loading weights took ([0-9.]+) seconds", line)
                    if mm: w["weights_s"] = float(mm.group(1))
                    if "Running FlashInfer autotune with" in line: w["at_line"] = t
                    if "Kernel JIT monitor activated" in line: w["done"] = t
                    for k, (label, marker) in enumerate(PHASES):
                        if marker in line: w["phase"] = max(w.get("phase", -1), k)
                if f:
                    t = dt.datetime.strptime(f.group(1), "%Y-%m-%d %H:%M:%S,%f")
                    if "Autotuning process starts" in line: w.setdefault("at_start", t)
                    if "Autotuning process ends" in line: w["at_end"] = t
                    w["last_fi"] = t
        elif re.search(r"/(split_15_12|split_control_default)/(\w+)/\2/(\w+)/\3\.json$", name):
            m = re.search(r"/(split_15_12|split_control_default)/(\w+)/\2/(\w+)/\3\.json$", name)
            try:
                d = json.loads(data)
                S["split"][(m.group(2), m.group(3))][m.group(1)] = (d.get("completed"), d["mean_ttft_ms"], d["mean_tpot_ms"])
            except (ValueError, KeyError):
                pass
        elif base == "case_manifest.json":
            try: manifests[name] = json.loads(data)
            except ValueError: pass
        elif base.endswith("_manifest.json"):
            try:
                d = json.loads(data); e = d.get("environment") or {}
            except (ValueError, AttributeError):
                continue
            env = e.get("env") if isinstance(e, dict) else None
            if isinstance(env, dict):
                runner_env[os.path.dirname(name)] = env
                S["env"].append(env)
                cmds = e.get("commands") or {}
                for pk in set(re.findall(r"(flashinfer-[a-z-]+|nvidia-cuda-nvcc[a-z0-9-]*)==([0-9][0-9.a-z+]*)", json.dumps(cmds))): S["freeze"][pk] += 1
                vv = cmds.get("vllm_version") if isinstance(cmds, dict) else None
                vv = json.dumps(vv) if vv is not None else ""
                mv = re.search(r"\b(\d+\.\d+\.\d+[0-9a-z.+]*)", vv)
                S["vllm_version"][mv.group(1) if mv else "not recorded"] += 1
        elif base.endswith("RAY_NCCL_ENV_AUDIT.json"):
            try:
                for w in json.loads(data).get("workers", []):
                    lp = w.get("ld_library_path") or ""
                    S["ldpath"]["clean folder on the path" if "clean_nccl_libs" in lp else "no clean folder"] += 1
            except (ValueError, AttributeError):
                pass
        elif base == "cuda_gpu_kern_sum.csv":   # two-server captures (one per worker) and single-node ones
            root = name.split("/node")[0] if "_capture/worker_process_" in name and "/node" in name else os.path.dirname(name)
            S["kern"][root].append(data)
        if base == "SERVER_COMMAND.txt":
            t = data.decode("utf-8", "replace")
            for flag in ("--no-enable-flashinfer-autotune", "--enable-flashinfer-autotune", "--moe-backend", "--enforce-eager"):
                if re.search(re.escape(flag) + r"(\s|$|=)", t): S["cmds"][flag] += 1
            S["cmds"]["commands"] += 1
    for n, c in manifests.items():
        s0, r0 = c.get("server_start"), c.get("server_ready")
        if s0 and not r0:
            err = HOME.sub("/~", str(c.get("error") or "no error recorded"))
            S["failed"].append(dict(start=s0, secs=(c.get("server_end") or s0) - s0, layout=f"TP{c.get('tp')}/PP{c.get('pp', 1)}",
                                    error="…" if HIDE.search(err) else err[:80], case="/".join(parts(os.path.dirname(n))[-3:])))
        if not (s0 and r0): continue
        env = None; d = os.path.dirname(n)
        for _ in range(3):
            d = os.path.dirname(d)
            if d in runner_env: env = runner_env[d]; break
        cmd = c.get("server_command") or []
        cmd = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        case_dir = os.path.dirname(n)
        S["startups"].append(dict(start=s0, secs=r0 - s0, layout=f"TP{c.get('tp')}/PP{c.get('pp', 1)}", case="/".join(parts(case_dir)[-3:]),
                                  skip="?" if env is None else bool(env.get("VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS")),
                                  log=any(ld == case_dir or ld.startswith(case_dir + "/") for ld in S["logdirs"]),
                                  autotune="off" if "--no-enable-flashinfer-autotune" in cmd else ("on" if "--enable-flashinfer-autotune" in cmd else "level default")))
    return S


def kern_main(csv_blobs):
    """Across a capture's ranks: per kernel name (sum of time, sum of calls). For the two main CUTLASS MoE kernels, the serving
    variant (the one with the most calls; a capture that holds the autotune sweep also holds the variants it tried)."""
    t = collections.defaultdict(lambda: [0.0, 0])
    for b in csv_blobs:
        L = b.decode("utf-8", "replace").splitlines(); i = [k for k, x in enumerate(L) if x.startswith("Time")]
        if not i: continue
        for r in csv.DictReader(io.StringIO("\n".join(L[i[0]:]))):
            try: t[r["Name"]][0] += float(r["Total Time (ns)"]) / 1e9; t[r["Name"]][1] += int(r["Instances"])
            except (KeyError, ValueError): pass
    out = {}
    for fam, pre in (("fused MoE", "void fused_moe::run_global"), ("MoE FC GEMM", "void cutlass::Kernel<cutlass::gemm::kernel::MoeFCGemm")):
        c = [(v[1], n, v) for n, v in t.items() if n.startswith(pre)]
        if c:
            calls, n, v = max(c); out[fam] = dict(per_call_us=1e6 * v[0] / v[1], calls=v[1], variants=len(c))
    tri = [(v[1], v) for n, v in t.items() if n.startswith("fused_moe_kernel")]
    if tri: out["Triton fused_moe_kernel"] = dict(per_call_us=1e6 * sum(v[0] for _, v in tri) / sum(v[1] for _, v in tri), calls=sum(v[1] for _, v in tri), variants=len(tri))
    return out


def report(label, S):
    print(f"\n==================== {label}")
    envs = S["env"]
    print("config (run records)")
    print(f"   vLLM version label (records): {dict(S['vllm_version']) or 'none recorded'}")
    print(f"   packages in pip freeze (records listing each): {dict(sorted(S['freeze'].items())) or 'none recorded'}")
    for k in ("CUDA_HOME", "VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS", "VLLM_MOE_BACKEND", "VLLM_PP_LAYER_PARTITION", "VLLM_DISABLE_PYNCCL"):
        n = sum(1 for e in envs if e.get(k)); vals = sorted({HOME.sub("/~", str(e[k])) for e in envs if e.get(k)})
        print(f"   {k} set in {n} of {len(envs)}" + (f"  {vals}" if vals else ""))
    print(f"   saved server commands: {dict(S['cmds']) or 'none'}")
    print(f"   Ray workers audited: {dict(S['ldpath']) or 'no audits'}")
    print(f"C1 MoE backend start-up lines (logged once per node): {dict(sorted(S['backend'].items())) or 'none'}")
    print(f"C2 logs with 'Running FlashInfer autotune': {S['at_run']}; with 'autotune because it is disabled': {S['at_off']}; "
          f"backend line but neither (FlashInfer not usable): {S['backend_logs_no_fi']} of {S['backend_logs']}; "
          f"skip list applied ('Skipping FlashInfer autotuning for ops'): {dict(S['at_skipops']) or 'in no saved log'}; "
          f"autotune cache file named (rank 0): {S['cache_file']} logs")
    per = collections.defaultdict(lambda: [0, 0])
    for (c, pid), w in S["workers"].items():
        if "at_line" in w:
            r = per[c.split("/node")[0] if "/node" in c else c]; r[0] += 1; r[1] += bool(w.get("tuned_gemm"))
    mixed = sum(1 for a, b in per.values() if 0 < b < a)
    print(f"C2b workers that ran the autotune step, per capture: all or none tuned the two GEMMs in {len(per) - mixed} of {len(per)}"
          + "".join(f" [{b} of {a} tuned]" for a, b in per.values())
          + (f"; MIXED in {mixed}: ranks that tune different operations can deadlock FlashInfer's tuning" if mixed else "")
          + " (the skip-list line itself is logged once per node)")
    print(f"C3 operations tuned (logs naming each): {dict(sorted(S['tuned_ops'].items())) or 'none'}; "
          f"read from a cache file ('Config cache hit'): {dict(sorted(S['cache_hit'].items())) or 'none'}; no tuned config covers: {dict(sorted(S['no_cover'].items())) or 'none'}")
    ws = [w for w in S["workers"].values() if "at_start" in w and "at_end" in w]
    if ws:
        d = [(w["at_end"] - w["at_start"]).total_seconds() for w in ws]
        print(f"C4 autotuning per worker: {len(d)} workers, {min(d):.2f}-{max(d):.2f} s (median {st.median(d):.2f})")
    else:
        print("C4 autotuning per worker: no worker log with both autotuner marks")
    tuned = [w for w in S["workers"].values() if "at_line" in w]
    stuck = [w for w in tuned if "at_end" not in w and w.get("last", w["at_line"]) <= w["at_line"]]
    started = [w for w in S["workers"].values() if "init" in w]
    unfinished = collections.Counter(PHASES[w["phase"]][0] if w.get("phase", -1) >= 0 else "before weights" for w in started if "done" not in w)
    print(f"C5 worker logs that reached the autotune step: {len(tuned)}; with nothing logged after it: {len(stuck)}; "
          f"worker logs that start but end before 'Kernel JIT monitor activated': {sum(unfinished.values())} of {len(started)}"
          + (f" (last step logged: {dict(unfinished)})" if unfinished else ""))
    print("C6 start-up (server start -> ready) per layout in launch order; S = skip list in the run's environment; L = server log kept")
    by = collections.defaultdict(list)
    for x in sorted(S["startups"], key=lambda r: r["start"]): by[x["layout"]].append(x)
    for lay, v in sorted(by.items()):
        cells = " | ".join(f"{dt.datetime.fromtimestamp(x['start'], dt.timezone.utc).strftime('%m-%d %H:%M')} {x['secs']:.0f}s"
                           f"{' S' if x['skip'] is True else ''}{' L' if x['log'] else ''} (autotune {x['autotune']})" for x in v)
        print(f"   {lay:9s} {cells}")
    n_log = sum(1 for x in S["startups"] if x["log"])
    print(f"   serving starts that became ready: {len(S['startups'])}; with a server log kept: {n_log}")
    for x in sorted(S["failed"], key=lambda r: r["start"]):
        print(f"   never ready: {x['layout']} {dt.datetime.fromtimestamp(x['start'], dt.timezone.utc).strftime('%m-%d %H:%M')} ended after {x['secs']:.0f} s: {x['error']} ({x['case']})")
    sk = [x for x in S["startups"] if x["skip"] is True]
    if sk:
        print("   starts with the skip list in the run's environment: " + "; ".join(f"{x['layout']} {x['case']}" for x in sorted(sk, key=lambda r: r["start"])))
    print("C7 MoE kernels per call in each capture (Nsight, eager):")
    lab = labels(S["kern"].keys())
    S["c7"] = {}
    for root, blobs in sorted(S["kern"].items(), key=lambda kv: lab[kv[0]]):
        k = kern_main(blobs)
        if k:
            cs = S["capstate"].get(root, set())
            state = ("Triton" if "Triton fused_moe_kernel" in k else
                     "skip list" if "skip list" in cs else "autotune ran" if "autotune ran" in cs else "autotune off" if "autotune off" in cs else "no autotune line")
            S["c7"][root] = dict(label=lab[root], state=state, k=k)
            print(f"   {lab[root]:62s} [{state}] " + " · ".join(f"{f}: {v['per_call_us']:.1f} us/call ({v['calls']} calls, {v['variants']} variants)" for f, v in k.items()))
    if S["split"]:
        print("SPLIT the same-session layer-split A/B: 15/12 against the default (requests; mean first token ms; mean token time ms)")
        for (lay, pt), arms in sorted(S["split"].items()):
            if len(arms) == 2:
                (na, ta, pa), (nb, tb, pb) = arms["split_control_default"], arms["split_15_12"]
                print(f"   {lay:20s} {pt:8s} default n={na} {ta:.1f} / {pa:.3f} · 15/12 n={nb} {tb:.1f} / {pb:.3f} · first token {100 * (tb / ta - 1):+.2f}% · token time {100 * (pb / pa - 1):+.2f}%")
    print("C8 worker start-up phases per capture (worker logs with vLLM's init and JIT-monitor lines):")
    caps = collections.defaultdict(list)
    for (c, pid), w in S["workers"].items():
        if "init" in w and "done" in w: caps[c].append(w)
    lab = labels(caps.keys(), least=4)
    for c, v in sorted(caps.items(), key=lambda kv: lab[kv[0]]):
        tot = [(w["done"] - w["init"]).total_seconds() for w in v]; wt = [w["weights_s"] for w in v if "weights_s" in w]
        at = [(w["at_end"] - w["at_start"]).total_seconds() for w in v if "at_start" in w and "at_end" in w]
        rng = lambda x, f: f"{min(x):{f}}-{max(x):{f}} s" if x else "none"
        first = min(w["init"] for w in v).strftime("%m-%d %H:%M")
        print(f"   {lab[c]:72s} {first} · {len(v)} workers · start-up {rng(tot, '.0f')} · weights {rng(wt, '.2f')} · autotune {rng(at, '.1f')}")


def cross(sets):
    print("\n==================== across sets")
    print("C7 x  the same layout and prompt in several sets: CUTLASS captures whose autotune ran against those where it did not (us per call)")
    groups = collections.defaultdict(list)
    for lbl, S in sets:
        for root, e in S["c7"].items():
            groups[tuple(parts(root)[-2:])].append((lbl, e))
    for key, have in sorted(groups.items()):
        if len({lbl for lbl, _ in have}) < 2: continue
        tuned = [(l, e) for l, e in have if e["state"] == "autotune ran"]
        untuned = [(l, e) for l, e in have if e["state"] in ("autotune off", "skip list")]
        for (lt, t) in tuned:
            for (lu, u) in untuned:
                fams = [f for f in ("fused MoE", "MoE FC GEMM") if f in t["k"] and f in u["k"]]
                print(f"   {'/'.join(key)}: {lt} [{t['state']}] against {lu} [{u['state']}]: " + "; ".join(
                      f"{f} {t['k'][f]['per_call_us']:.1f} against {u['k'][f]['per_call_us']:.1f} ({100 * (t['k'][f]['per_call_us'] / u['k'][f]['per_call_us'] - 1):+.1f}%)" for f in fams)
                      + (f"; per layer (both kernels) {sum(t['k'][f]['per_call_us'] for f in fams):.1f} against {sum(u['k'][f]['per_call_us'] for f in fams):.1f}"
                         f" ({100 * (sum(t['k'][f]['per_call_us'] for f in fams) / sum(u['k'][f]['per_call_us'] for f in fams) - 1):+.1f}%)" if len(fams) == 2 else ""))
    print("C7 x  Triton against untuned CUTLASS, same layout and prompt, per MoE layer (Triton calls its kernel twice per layer: gate-up and down);"
          " only pairs whose captures hold the same layers (Triton calls = 2 x CUTLASS calls)")
    left_out = 0
    for key, have in sorted(groups.items()):
        tri = [(l, e) for l, e in have if e["state"] == "Triton"]
        cut = [(l, e) for l, e in have if e["state"] in ("autotune off", "skip list") and "fused MoE" in e["k"] and "MoE FC GEMM" in e["k"]]
        for (lt, t) in tri:
            for (lc, c) in cut:
                tk, ck = t["k"]["Triton fused_moe_kernel"], c["k"]
                ratio = tk["calls"] / ck["fused MoE"]["calls"]
                if abs(ratio - 2) > 0.01:
                    left_out += 1; continue
                tl, cl = 2 * tk["per_call_us"], ck["fused MoE"]["per_call_us"] + ck["MoE FC GEMM"]["per_call_us"]
                print(f"   {'/'.join(key)}: {lt} {t['label']} [Triton] against {lc} {c['label']} [{c['state']}]: calls {tk['calls']} against {ck['fused MoE']['calls']} "
                      f"(ratio {ratio:.2f}); per layer {tl:.1f} against {cl:.1f} us ({100 * (cl / tl - 1):+.1f}% for CUTLASS)")
    print(f"   ({left_out} pairs left out: their captures hold different numbers of layer calls)")
    print("BUILD log messages two sets both print, and how many come from other source lines (a different build under the same version label):")
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            (la, A), (lb, B) = sets[i], sets[j]
            common = [k for k in A["src"] if k in B["src"]]
            if common:
                other = [k for k in common if not (A["src"][k] & B["src"][k])]
                files = sorted({f.split(":")[0] for k in other for f in A["src"][k] | B["src"][k]})
                print(f"   {la} and {lb}: {len(common)} messages in both; {len(other)} from other source lines, in {len(files)} files")
    print("C6 x  first start of each layout against its later starts (s):")
    for lbl, S in sets:
        by = collections.defaultdict(list)
        for x in sorted(S["startups"], key=lambda r: r["start"]): by[x["layout"]].append(x)
        for lay, v in sorted(by.items()):
            later = [x["secs"] for x in v[1:]]
            print(f"   {lbl:9s} {lay:9s} first {v[0]['secs']:.0f}" + (f" · later {min(later):.0f}-{max(later):.0f} (median {st.median(later):.0f}, {len(later)} starts"
                  f"{', skip list on ' + str(sum(1 for x in v[1:] if x['skip'] is True)) if any(x['skip'] is True for x in v) else ''})" if later else " · no later start")
                  + (" · first start had the skip list" if v[0]["skip"] is True else ""))


if __name__ == "__main__":
    sets = []
    for arg in sys.argv[1:]:
        label, path = arg.split("=", 1)
        path, _, prefix = path.partition("::")
        S = scan(path, prefix)
        report(label, S)
        sets.append((label, S))
    cross(sets)
