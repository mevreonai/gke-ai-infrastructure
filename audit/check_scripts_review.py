"""Checks behind Scripts_Review_v1.2.md: every finding about the Performance_Intelligence_Platform scripts, read from the scripts
themselves and from the vLLM 0.29.0 release wheel (read as a zip; nothing is imported). The scripts are never run. Eight small
experiments run in a scratch folder: vLLM's own partition function with the scripts' values, `pkill -f` called from a shell whose
command line holds the pattern, the master runner's run_step under `set -euo pipefail`, an unexported function, an unexported variable and `local`
inside `bash -c`, a `bash -c` body's exit status, and `source` of a missing file under `set -e`. The remote interface lookup is
replayed with awk on a typical `ip route get` line.
Since v1.2 it also reads the FlashInfer 0.6.18 wheel (as a zip) for the autotune skip-list facts.
Usage: python3 -I check_scripts_review.py <Performance_Intelligence_Platform dir> <vllm-0.29.0 wheel> <scratch dir> <the zip as shared> <flashinfer_python-0.6.18 wheel>"""
import ast, json, logging, os, re, subprocess, sys, types, zipfile
from pathlib import Path

ROOT, WHL, SCR, SHARED_ZIP, FI_WHL = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), sys.argv[4], sys.argv[5]
S = ROOT / "scripts"
SCR.mkdir(parents=True, exist_ok=True)
RES = []


def check(name, cond, detail=""):
    RES.append((name, bool(cond), detail))
    print(("ok   " if cond else "FAIL ") + name + (f" · {detail}" if detail else ""))


def text(p):
    return (p if isinstance(p, Path) else S / p).read_text(encoding="utf-8", errors="replace")


def lines_with(p, pat):
    return [i for i, l in enumerate(text(p).splitlines(), 1) if re.search(pat, l)]


z = zipfile.ZipFile(WHL)
WSRC = {n: z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith(".py")}
ALLW = "\n".join(WSRC.values())
M = "run_master_benchmark.sh"
ML = text(M).splitlines()
K = "Ki" + "mi"

# ---------------------------------------------------------------- the build
sn = text("setup_node_env.sh")
check("setup_node_env.sh installs an unpinned vLLM (vllm>=0.6.3) beside torch 2.5.1",
      '"vllm>=0.6.3"' in sn and "torch==2.5.1" in sn, f"lines {lines_with('setup_node_env.sh', 'vllm>=0.6.3')} and {lines_with('setup_node_env.sh', 'torch==2.5.1')}")
rb, rs = text(ROOT / "RUNBOOK_NEW_VM_SETUP.md"), text(ROOT / "README_SETUP_AND_OPERATIONS.md")
check("the runbook gives the same unpinned install; the setup manual pins vllm==0.29.0 with other companions",
      '"vllm>=0.6.3"' in rb and "vllm==0.29.0" in rs and "torch==2.13.0" in rs)
s0 = "\n".join(ML[388:399])
check("step 00 records vLLM's version string on node 0 only (node 1: nvidia-smi and env)",
      "vllm.__version__" in s0 and "node0_python_stack" in s0 and "node1_python_stack" not in s0 and "node1_nvidia_smi" in s0)
lib = text("v5_runner_lib.py")
check("the runners' environment record keeps `vllm --version` and pip freeze; its env filter leaves out LD_LIBRARY_PATH",
      '"vllm_version":[vllm,"--version"]' in lib and '"pip","freeze"' in lib and 'startswith(("NCCL_","CUDA_","VLLM_","RAY_","' + 'V' + '8_"))' in lib)

# ---------------------------------------------------------------- backend, autotune, pynccl
def reads(var):
    return [(n, i) for n, s in WSRC.items() for i, l in enumerate(s.splitlines(), 1) if re.search(r'["\']' + re.escape(var) + r'["\']', l)]
for var in ("VLLM_MOE_BACKEND", "MOE_BACKEND", "VLLM_FLASHINFER_AUTOTUNE"):
    check(f"vLLM 0.29.0 never reads {var}", reads(var) == [], f"set at {M}:{lines_with(M, 'export ' + var + '=')}")
check("vLLM 0.29.0 does read VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS and VLLM_PP_LAYER_PARTITION",
      reads("VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS") and reads("VLLM_PP_LAYER_PARTITION"))
check("the runner library passes --moe-backend only if the help text lists it (silently skipped otherwise), default flashinfer_cutlass",
      'add_if_supported(cmd, serve_help, "--moe-backend", str(moe_backend))' in lib and '"VLLM_MOE_BACKEND", "flashinfer_cutlass"' in lib)
direct = {"06_deep_kernel_and_torch_profiling/14_run_vllm_nsys_profile.sh": "SERVER_CMD=(vllm serve",
          "06_deep_kernel_and_torch_profiling/14c_run_vllm_torch_profile_batched.sh": "vllm serve",
          "06_deep_kernel_and_torch_profiling/14d_run_vllm_torch_profile_multi_node.sh": "vllm serve"}
check("the profile scripts launch `vllm serve` without --moe-backend (B1 decode, torch batched, two-server torch)",
      all(k in text(f) and "--moe-backend" not in text(f) for f, k in direct.items()))
s4 = "\n".join(ML[484:571])
check("step 04 (TP8 pinning) launches `vllm serve` without --moe-backend", "vllm serve" in s4 and "--moe-backend" not in s4)
uq = WSRC["vllm/model_executor/layers/fused_moe/oracle/unquantized.py"].splitlines()
check("with the backend left at auto, vLLM 0.29.0 tries FlashInfer TRT-LLM, then FlashInfer CUTLASS, then Triton (Hopper excepted), so the pick depends on the FlashInfer installed; setup installs flashinfer-python unpinned",
      [l.strip() for l in uq[68:72]] == ["UnquantizedMoeBackend.FLASHINFER_TRTLLM,", "UnquantizedMoeBackend.FLASHINFER_CUTLASS,", "UnquantizedMoeBackend.TRITON,", "UnquantizedMoeBackend.BATCHED_TRITON,"]
      and "pip install -q flashinfer-python" in sn)
cfgv = WSRC["vllm/config/vllm.py"].splitlines()
auto = [l.strip() for l in cfgv[250:330] if "enable_flashinfer_autotune" in l]
check("autotune: --enable-flashinfer-autotune exists in 0.29.0 and no script passes it; by default it follows the optimization level (off at O0, on at O1-O3; default O2)",
      "--enable-flashinfer-autotune" in ALLW and not any("enable-flashinfer-autotune" in text(p) for p in S.rglob("*") if p.is_file() and p.suffix in (".py", ".sh", ".json"))
      and auto == ['"enable_flashinfer_autotune": False,', '"enable_flashinfer_autotune": True,', '"enable_flashinfer_autotune": True,', '"enable_flashinfer_autotune": True,']
      and "optimization_level: OptimizationLevel = OptimizationLevel.O2" in WSRC["vllm/config/vllm.py"])
pn = WSRC["vllm/distributed/device_communicators/pynccl.py"].splitlines()
check("VLLM_DISABLE_PYNCCL=1 is set (master, multi-node runner, RUN_CONFIG example) and turns vLLM's own NCCL communicator off",
      lines_with(M, 'VLLM_DISABLE_PYNCCL="\\$\\{VLLM_DISABLE_PYNCCL:-1\\}"') and 'env["VLLM_DISABLE_PYNCCL"]="1"' in text("04_scaleout_distributed_network/12_run_vllm_multi_node.py")
      and 'export VLLM_DISABLE_PYNCCL="1"' in text("RUN_CONFIG.env.example") and "envs.VLLM_DISABLE_PYNCCL" in pn[92], f"pynccl.py line 93: {pn[92].strip()}")

# ---------------------------------------------------------------- the pipeline partition
check("the master exports VLLM_PP_LAYER_PARTITION=15,12 for every run unless set; the RUN_CONFIG example and the smoke test set 15,12; the cluster setup writes 7,7,7,6",
      ML[254].strip() == 'export VLLM_PP_LAYER_PARTITION="${VLLM_PP_LAYER_PARTITION:-15,12}"' and 'export VLLM_PP_LAYER_PARTITION="15,12"' in text("RUN_CONFIG.env.example")
      and 'export VLLM_PP_LAYER_PARTITION="15,12"' in text("run_smoke_test.sh") and 'export VLLM_PP_LAYER_PARTITION="7,7,7,6"' in text("setup_cluster_and_run_smoke.sh"))
du = WSRC["vllm/distributed/utils.py"]; fn = next(n for n in ast.parse(du).body if isinstance(n, ast.FunctionDef) and n.name == "get_pp_indices")
code = ast.get_source_segment(du, fn); out = {}
for part in ("15,12", "7,7,7,6"):
    ns = {"envs": types.SimpleNamespace(VLLM_PP_LAYER_PARTITION=part), "logger": logging.getLogger("x")}; exec(code, ns)
    for pp in (1, 2, 4):
        try: ns["get_pp_indices"](27, 0, pp); out[(part, pp)] = "ok"
        except ValueError as e: out[(part, pp)] = str(e)
check("vLLM 0.29.0's own get_pp_indices with 15,12: one-stage and four-stage servers raise ValueError, two-stage runs",
      out[("15,12", 1)].startswith("len(partitions)=2") and out[("15,12", 4)].startswith("len(partitions)=2") and out[("15,12", 2)] == "ok", out[("15,12", 1)])
check("and with 7,7,7,6 only four-stage servers start", out[("7,7,7,6", 4)] == "ok" and out[("7,7,7,6", 1)] != "ok" and out[("7,7,7,6", 2)] != "ok")
mdl = WSRC["vllm/models/" + K.lower() + "_k3/nvidia/model.py"]
check("the model builds its layers with make_layers, which calls get_pp_indices for every pipeline size",
      "self.start_layer, self.end_layer, self.layers = make_layers(" in mdl and "start_layer, end_layer = get_pp_indices(" in WSRC["vllm/model_executor/models/utils.py"])
check("step 11's 'default' control run does not clear the partition, so it also runs 15,12",
      "VLLM_PP_LAYER_PARTITION='15,12'" in ML[693] and "split_control_default" in ML[694] and "VLLM_PP_LAYER_PARTITION" not in ML[694] and "unset VLLM_PP_LAYER_PARTITION" not in text(M))

# ---------------------------------------------------------------- pkill -f vllm
pk = [i for i, l in enumerate(ML, 1) if "pkill -9 -f 'vllm'" in l or "pkill -9 -f vllm" in l]
check("the master calls `pkill -9 -f vllm` inside its `bash -c` steps (2, 19, 20) and in the remote clean-ups", pk == [425, 428, 435, 438, 446, 447, 454, 455, 462, 463, 918, 933], f"lines {pk}")
d14 = text("06_deep_kernel_and_torch_profiling/14d_run_vllm_torch_profile_multi_node.sh").splitlines()
check("14d's clean-up runs `pkill -9 -f \"vllm\"` and is called at start-up (its own path contains vllm)", 'pkill -9 -f "vllm"' in d14[54] and d14[67].strip() == "stop_ray_both")
pat = "zzq" + "mark" + "er_" + str(os.getpid())
r = subprocess.run(["bash", "-c", f"echo started {pat}; pkill -9 -f '{pat}'; sleep 1; echo survived"], capture_output=True, text=True, cwd=SCR)
check("experiment: a `bash -c` whose text holds the pattern is SIGKILLed by its own pkill -f", r.returncode in (137, -9) and "survived" not in r.stdout, f"exit {r.returncode}")
t = SCR / "run_step_test.sh"
t.write_text('#!/usr/bin/env bash\nset -euo pipefail\nrun_step() { local num="$1"; shift; local rc; set +e; "$@"; rc=$?; set -e; [[ "$rc" == 0 ]] && echo ok; return "$rc"; }\n'
             'if true; then run_step 2 bash -c "exit 137"; fi\necho reached_step_3\n')
r = subprocess.run(["bash", str(t)], capture_output=True, text=True, cwd=SCR)
check("experiment: the master's run_step under set -euo pipefail ends the whole run on the first failed step", r.returncode == 137 and "reached_step_3" not in r.stdout, f"exit {r.returncode}")

# ---------------------------------------------------------------- network shaping
rl = [i for i, l in enumerate(ML, 1) if "print \\\\\\$i+1" in l]
check("the remote interface lookup prints `$i+1` (the field plus one) in steps 10, 11 and 12; the local lookup prints `$(i+1)`",
      rl == [657, 689, 724] and "print \\$(i+1)" in ML[722], f"lines {rl}")
prog_remote = re.search(r"awk '(\{.*?\})'", ML[723]).group(1).replace("\\\\\\$", "$").replace('\\\\\\"', '"')
prog_local = re.search(r"awk '(\{.*?\})'", ML[722]).group(1).replace("\\$", "$").replace('\\"', '"')
sample = "10.128.0.12 via 10.128.0.1 dev ens3 src 10.128.0.11 uid 1000\n"
a_r = subprocess.run(["awk", prog_remote], input=sample, capture_output=True, text=True).stdout.strip()
a_l = subprocess.run(["awk", prog_local], input=sample, capture_output=True, text=True).stdout.strip()
check("replayed on a typical `ip route get` line: node 1's interface comes out as 1, node 0's as ens3", a_r == "1" and a_l == "ens3", f"remote program {prog_remote} -> {a_r!r}")
s10_12 = "\n".join(ML[641:791])
tcs = [l for l in s10_12.splitlines() for _ in re.findall(r"sudo -n tc (?:qdisc|class) ", l)]
tc_lines = [l for l in s10_12.splitlines() if "sudo -n tc " in l]
silenced = sum(len(re.findall(r"sudo -n tc (?:qdisc|class) [^\n]*?2>/dev/null \|\| true", l)) for l in tc_lines)
check("steps 10-12: all 18 tc commands silence their errors; no `tc -s qdisc show` and no iperf3",
      len(tcs) == 18 and silenced == 18 and "qdisc show" not in s10_12 and "iperf3" not in s10_12, f"{len(tcs)} tc commands, {silenced} silenced")
nm = text("04_scaleout_distributed_network/20_run_vllm_network_matrix.sh").splitlines()
check("the suite's own network matrix does it right (node 1's interface by $(i+1), tc errors not silenced, iperf3 both ways validated); the master does not call it",
      "print \\$(i+1)" in nm[24] and nm[36].strip().startswith("sudo -n tc qdisc replace") and "|| true" not in nm[36]
      and any("iperf3 -c" in l and "-R" in l for l in nm) and any("IPERF_VALIDATION" in l for l in nm)
      and "20_run_vllm_network_matrix" not in text(M))
mn = text("04_scaleout_distributed_network/12_run_vllm_multi_node.py")
cap_var = re.search(r'"configured_network_cap_gbps":os.environ.get\("([A-Z0-9_]+)"', mn).group(1)
check("step 12 sets the network-mode label but not the cap variable the multi-node runner records", cap_var not in "\n".join(ML[705:791]) and "NETWORK_MODE=\\\"capped\\\"" in "\n".join(ML[705:791]))

# ---------------------------------------------------------------- the NCCL library
pol = text("04_scaleout_distributed_network/20_nccl_policy.sh"); ini = text("01_preflight_and_diagnostics/00_init_gcp_config.sh")
check("the clean NCCL folder: the master makes it on node 0 only; node 1 gets it only from the init script when V5_FORCE_NCCL_SOCKET=1; the path is propagated",
      "mkdir -p /tmp/clean_nccl_libs" in "\n".join(ML[257:262]) and 'if [[ "$V5_FORCE_NCCL_SOCKET" == "1" ]]' in ini and "printf 'export LD_LIBRARY_PATH=%s; '" in pol)
check("no script records the NCCL library each worker mapped or the NCCL version",
      not any(re.search(r"/proc/[^ ]*/maps|nccl\.version\(\)|ncclGetVersion", text(p)) for p in S.rglob("*") if p.is_file() and p.suffix in (".py", ".sh")))
check("the README lists NCCL_ALGO=Tree and NCCL_PROTO=Simple as enforced; the master unsets both; NCCL_CROSS_NIC=1 stays in the RUN_CONFIG example",
      'export NCCL_ALGO="Tree"' in text(ROOT / "README.md") and ML[270].strip() == "unset NCCL_ALGO NCCL_PROTO || true" and 'export NCCL_CROSS_NIC="1"' in text("RUN_CONFIG.env.example"))
nt = text("04_scaleout_distributed_network/23_run_nccl_socket_tuning.sh")
check("the NCCL test sweeps socket-thread settings at a 16 KiB AllReduce and a 256 MiB SendRecv; no library-path arm",
      "-b 16K -e 16K" in nt and "-b 256M -e 256M" in nt and "clean_nccl_libs" not in nt)

# ---------------------------------------------------------------- coverage
code_files = [p for p in S.rglob("*") if p.is_file() and p.suffix in (".py", ".sh", ".json")]
check("expert parallel: --enable-expert-parallel exists in 0.29.0; no script or case uses it",
      ALLW.count("--enable-expert-parallel") > 0 and not any("expert-parallel" in text(p) or "expert_parallel" in text(p) for p in code_files))
check("no Nsight Compute capture anywhere", not any(re.search(r"\bncu\b|nsight.compute", text(p), re.I) for p in code_files))
mc = json.loads(text("master_benchmark_cases.json"))["cases"]; mc = list(mc.values()) if isinstance(mc, dict) else mc
rr = sorted({(c["name"], c["tp"], c.get("pp", 1)) for c in mc for b in c.get("benchmarks", []) if b.get("request_rate") is not None})
check("master cases: arrival-rate runs only in the TP4/PP1 Poisson sweep", rr == [("tp4_open_loop_poisson_sweep", 4, 1)])
cb = json.loads(text("continuous_batching_cases.json"))["cases"]; cb = list(cb.values()) if isinstance(cb, dict) else cb
b7 = sorted((c["tp"], c.get("pp", 1)) for c in cb if c.get("block") == 7 and any(b.get("request_rate") is not None for b in c.get("benchmarks", [])))
check("batching block 7 holds arrival-rate runs on all four two-server layouts", b7 == [(4, 2), (4, 4), (8, 2), (16, 1)], str(b7))
rc_py, rc_sh = text("run_continuous_batching.py"), text("run_continuous_batching.sh")
check("the batching runner asks for the Ray backend (pp > 1 or tp > 8) but never forms a two-node Ray cluster",
      'distributed=(case.get("pp", 1) > 1 or case.get("tp", 1) > 8)' in rc_py and not re.search(r"\bray\b|NODE1|ssh", rc_py + rc_sh, re.I))
check("step 17 (batching) is skipped unless CB_BLOCKS, --cb-blocks or -cb is given", 'CB_BLOCKS_SEL="${CB_BLOCKS_ARG:-${CB_BLOCKS:-none}}"' in text(M))
load = [c for c in mc if "scaleout_load" in c.get("groups", [])]
lay = sorted((c["tp"], c.get("pp", 1)) for c in load)
low = all(any(b["input"] in (1024, 8192) and b["concurrency"] == 1 for b in c["benchmarks"]) for c in load)
check("two-server load cases: TP4/PP2, TP8/PP2, TP4/PP4, TP16/PP1, each with 1K and 8K one at a time and 1K-1M up to 32 in flight",
      lay == [(4, 2), (4, 4), (8, 2), (16, 1)] and low and max(b["concurrency"] for c in load for b in c["benchmarks"]) == 32)
seqs = {c["name"]: c.get("max_num_seqs") for c in mc if c["name"] in ("tp4_pp1_baseline", "tp8_pp1_baseline") or "scaleout_load" in c.get("groups", [])}
check("admission caps differ: two-server load cases max_num_seqs 16, one-server baselines 32",
      all(v == 16 for k, v in seqs.items() if "dist_load" in k) and seqs["tp4_pp1_baseline"] == 32 and seqs["tp8_pp1_baseline"] == 32, json.dumps(seqs))
pc = text("06_deep_kernel_and_torch_profiling/18_run_vllm_multi_node_profile_case.py").splitlines()
mx = json.loads(text("06_deep_kernel_and_torch_profiling/18_multi_node_profile_matrix.json"))["profiles"]
dec = sorted({p["topology"] for p in mx if p["mode"] in ("decode_8k", "batched_decode_8k_c8")})
check("two-server decode profiles are written for all four layouts: the Nsight ones add --enforce-eager, the torch ones (14d) keep graphs on",
      pc[74].strip() == "if '--enforce-eager' in serve_help: server_cmd += ['--enforce-eager']" and dec == ["tp16_pp1_dist", "tp4_pp2_dist", "tp4_pp4_dist", "tp8_pp2_dist"]
      and "--optimization-level 2" in "\n".join(d14[100:108]) and "--enforce-eager" not in "\n".join(d14))
s18 = text("06_deep_kernel_and_torch_profiling/18_run_vllm_multi_node_profiles.sh")
check("step 14 asks the Nsight profile script for mode 'decode', which matches no profile exactly (decode_8k, batched_decode_8k_c8)",
      "PROFILE_MODE_FILTER=decode " in ML[834] and "if mode and p['mode'] != mode: continue" in s18 and "decode" not in {p["mode"] for p in mx})
reps = {c["name"]: max([sum(1 for y in c["benchmarks"] if {k: y[k] for k in y if k != "name"} == {k: x[k] for k in x if k != "name"}) for x in c["benchmarks"]] or [0]) for c in mc}
check("repeats: only the knee case repeats a benchmark (three times each at 8K c16 and 128K c4)", [k for k, v in reps.items() if v > 1] == ["tp4_knee_repeats"] and reps["tp4_knee_repeats"] == 3)
r2 = next(c for c in mc if c["name"] == "tp4_r2_agentic_prefix_cache_decay")
check("the R2 case uses 1K-4K prefixes on TP4/PP1: no 1M first-repeat arms, no retention interval",
      max(b.get("prefix", b.get("input", 0)) for b in r2["benchmarks"]) == 4096 and not any("retention" in text(p) for p in code_files))
sur = text("02_single_node_baseline_matrix/11_run_vllm_surrogate.py")
check("the one-server runner starts one server per case and runs every benchmark on it; the drain barrier is defined but never called",
      sur.count("start_server_with_timestamp_logging(") == 1 and "for bi,b in enumerate(benchmarks_to_run):" in sur
      and not any("drain_vram_barrier(" in text(p) for p in code_files if p.name != "v5_runner_lib.py"))
check("warm-up and measured run share a seed for the first benchmark of every case (bi*10 against bi)",
      "args.seed_base+ci*1000+bi*10" in sur and "args.seed_base+ci*1000+bi," in sur)
sm = text("run_smoke_test.sh")
check("the smoke test's end-to-end check writes a mock result (no server) and its runner check is a dry run, in which run_step executes nothing",
      '"mean_ttft_ms": 48.9' in sm and "run_master_benchmark.sh\" --dry-run" in sm and '[DRY-RUN] Simulating Step' in text(M))
check("step 15 runs tools/compile_canonical_data.py and tools/run_v1_4_verification.py, which the folder does not hold",
      "tools/compile_canonical_data.py" in text(M) and not (ROOT / "tools").exists())
ob = {c["name"]: sorted({(b["input"], b["concurrency"]) for b in c["benchmarks"]}) for c in mc if c["name"] in ("tp4_observer_overhead_test", "tp4_short_prompts")}
check("step 20 sets the minimal-telemetry case (8K) against the short-prompt case (1K/2K): different workloads",
      ob["tp4_observer_overhead_test"] == [(8192, 8), (8192, 32)] and all(i in (1024, 2048) for i, _ in ob["tp4_short_prompts"]))
check("two master runners with different case files (scripts/ and 07_master_campaign_orchestration/)",
      (S / "07_master_campaign_orchestration/run_master_benchmark.sh").exists() and text("07_master_campaign_orchestration/master_benchmark_cases.json") != text("master_benchmark_cases.json"))
check("the two-server serving runner brings back node 1's GPU telemetry only; the two-server profile script keeps Ray worker logs",
      "metrics_node1.jsonl" in mn and "Preserve Ray worker logs" in text("06_deep_kernel_and_torch_profiling/18_run_vllm_multi_node_profiles.sh"))
allb = [b for c in mc for b in c["benchmarks"]]
first_cold = sorted(c["name"] for c in mc if int(c["benchmarks"][0].get("warmups", 0) or 0) == 0)
check("warm-ups: 49 of 158 benchmarks have none, and every server's first measured run is warmed up except the offload case (128K first) and R2 (cold by design)",
      len(allb) == 158 and sum(1 for b in allb if int(b.get("warmups", 0) or 0) == 0) == 49
      and first_cold == ["tp4_native_offload_reuse_test", "tp4_r2_agentic_prefix_cache_decay"], str(first_cold))
check("the pause and stall screen runs over the whole campaign (step 16); it reads the per-request bench files, so it does not need the telemetry sampler",
      "pip_scan.py" in "\n".join(ML[866:875]) and (S / "pip_scan.py").exists() and (S / "pip_waves.py").exists()
      and 'all(k in d for k in ("ttfts", "start_times", "itls"))' in text("pip_scan.py"))

# ---------------------------------------------------------------- found by the independent check, verified here
fn_def = [i for i, l in enumerate(ML, 1) if l.startswith("topology_matches() {")]
calls = [i for i, l in enumerate(ML, 1) if "if topology_matches" in l and i >= 400]
check("topology_matches is a master-shell function, never exported, and steps 2 and 14 call it inside their `bash -c` bodies",
      fn_def == [296] and "export -f" not in text(M) and calls == [421, 430, 442, 450, 458, 822, 825, 841], f"calls at {calls}")
t = SCR / "unexported_fn_test.sh"
t.write_text('#!/usr/bin/env bash\nset -euo pipefail\ntopology_matches() { return 0; }\n'
             'bash -c "if topology_matches tp4 || topology_matches all; then echo capture_runs; fi; echo child_rc=\\$?"\n')
r = subprocess.run(["bash", str(t)], capture_output=True, text=True, cwd=SCR)
check("experiment: inside `bash -c` the unexported function is not found, the capture is skipped and the step exits 0 (marked done)",
      "capture_runs" not in r.stdout and "child_rc=0" in r.stdout and "command not found" in r.stderr and r.returncode == 0)
check("step 04 starts its server with `& local PID=$!` in a `bash -c` body, outside any function", "& local PID=\\$!" in ML[500] and "PID=\\$!" in ML[500])
r = subprocess.run(["bash", "-c", 'sleep 0.2 & local PID=$!; kill -0 "$PID" 2>/dev/null && echo alive || echo "server crashed (empty PID)"'], capture_output=True, text=True, cwd=SCR)
check("experiment: `local` outside a function fails, PID stays empty, and the readiness loop's `kill -0` fails at once (step 04 exits 3)",
      "can only be used in a function" in r.stderr and "server crashed (empty PID)" in r.stdout and 'kill -0 \\"\\$PID\\" 2>/dev/null || { echo \\"Server crashed on startup\\"; exit 3; }' in ML[515])
nt_l = nt.splitlines()
check("step 03's NCCL test runs under `set -euo pipefail` and returns 1 when nccl-tests is not built, so the master stops there",
      "set -euo pipefail" in nt_l[7] and any(l.strip() == "return 1" for l in nt_l) and 'echo "ERROR: nccl-tests binaries missing' in nt)
mns = text("04_scaleout_distributed_network/12_run_vllm_multi_node.sh").splitlines()
check("the two-server group runner stops at its first failed case (`set -euo pipefail`, the Python runner raises), skipping later cases and its `ray stop`",
      mns[3].strip() == "set -euo pipefail" and 'raise RuntimeError("Multi-node case execution failed with error")' in mn and mns[87].strip() == "ray stop -f || true"
      and [c["name"] for c in load][-1] == "tp16_pp1_dist_load")
rce = text("RUN_CONFIG.env.example")
lab = ["export " + "V" + "8_GCP_NETWORK_PROVENANCE_OVERRIDE=\"GCP_NATIVE\"", 'export GCP_NETWORK_PROVENANCE="GCP_NATIVE"', "export " + "V" + "8_VLLM_NETWORK_MODE=\"native\""]
check("the two-server runner re-reads RUN_CONFIG.env after taking the step's labels, and the example config sets them to native: every condition is recorded as native",
      all(x in rce for x in lab) and mns[8].startswith("CONFIG_CANDIDATES=") and "source" in mns[9] and "PROVENANCE_OVERRIDE:-" in mns[7])
rereads = {f: any("RUN_CONFIG.env" in l and ("source" in l or "CONFIG_FILE=" in l or "CONFIG_CANDIDATES" in l) for l in text(f).splitlines()[:25])
           for f in ("04_scaleout_distributed_network/12_run_vllm_multi_node.sh", "06_deep_kernel_and_torch_profiling/14d_run_vllm_torch_profile_multi_node.sh",
                     "06_deep_kernel_and_torch_profiling/18_run_vllm_multi_node_profiles.sh", "04_scaleout_distributed_network/23_run_nccl_socket_tuning.sh", "run_continuous_batching.sh")}
check("the four scripts the master calls directly that read RUN_CONFIG.env re-read it themselves (two-server runner, both two-server profile drivers, the NCCL test), so the 15,12 split must also come out of the config, not only the master",
      all(v for k, v in rereads.items() if k != "run_continuous_batching.sh") and "RUN_CONFIG" not in text("run_continuous_batching.py"), str(rereads))
sc = text("setup_cluster_and_run_smoke.sh")
check("the cluster set-up caps both nodes at 20 Gbit/s by default (SKIP_20G=0) and never removes the cap", "SKIP_20G=0" in sc and sc.count("htb rate 20gbit") == 2 and "qdisc del" not in sc)
nmx = "\n".join(nm)
check("the suite's network matrix validates only the forward iperf3 run, has no loss mode, and runs every case (--all)",
      'python3 - "$dir/iperf_forward.json"' in nmx and "iperf_reverse.json\" || true" in nmx and "netem" not in nmx and '12_run_vllm_multi_node.sh" --all' in nmx)
rd = text("01_preflight_and_diagnostics/22_readiness.py")
check("22_readiness.py already gates exact versions (vllm 0.29.0, torch 2.13.0, flashinfer-python 0.6.18, ray 2.58.0, triton 3.7.1, nvidia-nccl-cu13 2.29.7) and exits 2 on a mismatch; nothing calls it",
      all(f'"{k}": "{v}"' in rd for k, v in (("vllm", "0.29.0"), ("torch", "2.13.0"), ("flashinfer-python", "0.6.18"), ("ray", "2.58.0"), ("triton", "3.7.1"), ("nvidia-nccl-cu13", "2.29.7")))
      and "raise SystemExit(0 if payload['ok'] else 2)" in rd and not any("22_readiness" in text(p) for p in code_files if p.name != "22_readiness.py"))
meta = z.read([n for n in z.namelist() if n.endswith(".dist-info/METADATA")][0]).decode()
need = {k: re.search(r"^Requires-Dist: " + re.escape(k) + r"([=><]=?[^\s;]+)", meta, re.M) for k in ("torch", "flashinfer-python", "transformers", "safetensors")}
check("the 0.29.0 wheel pins torch==2.13.0 and flashinfer-python==0.6.18 and needs transformers>=5.10.4, safetensors>=0.6.2; the setup manual pins transformers 4.44.2 and safetensors 0.4.4, so its recipe cannot install",
      need["torch"].group(1) == "==2.13.0" and need["flashinfer-python"].group(1) == "==0.6.18" and need["transformers"].group(1) == ">=5.10.4" and need["safetensors"].group(1) == ">=0.6.2"
      and "transformers==4.44.2" in rs and "safetensors==0.4.4" in rs)
dm = text("run_demo_setup.sh")
check("two more install paths: the runbook adds FlashInfer from a torch-2.5 index, run_demo_setup.sh installs nightly torch and an unpinned vLLM; three venv paths",
      "flashinfer.ai/whl/cu124/torch2.5" in rb and "whl/nightly/cu128" in dm and re.search(r"uv pip install --python \S+ vllm ", dm)
      and 'VENV_PATH="${1:-$HOME/pip_vllm_env}"' in sn and ': "${VENV_DIR:=$HOME/vllm_env}"' in text(M) and "/opt/vllm-platform-env" in rs)
tb = next(n for n in WSRC if n.endswith("experts/trtllm_bf16_moe.py")); fc = next(n for n in WSRC if n.endswith("experts/flashinfer_cutlass_moe.py"))
check("on these GPUs (SM120) auto skips FlashInfer TRT-LLM (SM100 family only) and takes FlashInfer CUTLASS when its fused-MoE kernel imports, else Triton",
      "p.is_device_capability_family(100)" in WSRC[tb] and "is_device_capability_family(120)" not in WSRC[tb]
      and "p.is_device_capability_family(120)" in WSRC[fc] and "has_flashinfer_cutlass_fused_moe()" in WSRC[fc])
check("vLLM 0.29.0 warns 'Unknown vLLM environment variable detected' for VLLM_* names it does not know (a quick check in server.log)",
      'logger.warning("Unknown vLLM environment variable detected: %s", env)' in WSRC["vllm/envs.py"])
ns3 = text("01_preflight_and_diagnostics/03_run_network_sweep.sh")
check("the preflight network sweep already runs iperf3 both ways, SendRecv 16K-256M, cross-node AllReduce for TP2/TP8/TP16 from 16 KiB to 256 MiB, and records qdiscs on both nodes; the master does not call it",
      "DIRECTION=REVERSE" in ns3 and "for SIZE in 16K 128K 512K 64M 128M 256M" in ns3 and './build/all_reduce_perf -b 16K -e 256M -f 2' in ns3
      and 'for SPEC in "TP2:1" "TP8:4" "TP16:8"' in ns3 and "tc -s qdisc show" in ns3 and "03_run_network_sweep" not in text(M))
x10 = json.loads(text("05_long_context_1m_extensions/10d_1m_extended_cases.json"))["cases"]; x10 = list(x10.values()) if isinstance(x10, dict) else x10
pm = next(c for c in x10 if c["name"] == "tp4_prefix1m"); pb = pm["benchmarks"][0]
past = pb["prefix"] % 512 + pb["suffix"]
check("an unused 1M prefix case exists: 999,744-token prefix + 256 suffix, i.e. 576 tokens past the last whole block (the pilot's miss again); no whole-block arm, no retention arm; nothing runs the file",
      pb["prefix"] == 999744 and pb["suffix"] == 256 and past == 576 and pm.get("prefix_caching") is True
      and not any("10d_1m_extended_cases" in text(p) for p in code_files if p.suffix in (".sh", ".py")))
check("the RUN_CONFIG example sets CB_BLOCKS=all, so step 17 runs with the documented config", 'export CB_BLOCKS="all"' in rce)
one_or_four = sorted(c["name"] for c in cb if c.get("pp", 1) in (1, 4))
check("blocker 1 also stops the batching cases on one and four stages", len(one_or_four) == 20, f"{len(one_or_four)} of {len(cb)} cases")
check("the smoke test records PASSED on fallbacks (no GPUs, framework not loaded, tools missing, node 1 not reached)",
      all(x in sm for x in ('"gpu_hardware" "PASSED" "CPU surrogate fallback mode', '"ai_framework_stack" "PASSED" "Surrogate verified',
                            '"linux_systems_utilities" "PASSED" "Core utils present (missing non-critical', '"dual_node_16gpu_interconnect" "PASSED"')))

# ---------------------------------------------------------------- how far a default run gets; the shared config file
def step_body(n):
    i = next(k for k, l in enumerate(ML) if re.search(r'run_step ' + str(n) + r' "', l))
    j = next(k for k in range(i + 1, len(ML)) if ML[k].strip() == '"')
    return "\n".join(ML[i:j + 1])
byn = {c["name"]: c for c in mc}
one = {n: sorted({(byn[x]["tp"], byn[x].get("pp", 1)) for x in re.findall(r"--case (\w+)", step_body(n))}) for n in (1, 5, 6, 8, 9, 18, 20)}
one[19] = sorted({(byn[x]["tp"], byn[x].get("pp", 1)) for x in re.search(r"for seq_case in ([\w ]+); do", step_body(19)).group(1).split()})
grp = lambda g: [(c["tp"], c.get("pp", 1)) for c in mc if g in c.get("groups", [])]
check("with 15,12 only two-stage servers start: steps 1, 5, 6, 8, 9, 18, 19 and 20 use one-stage cases only; step 12's group is TP16/PP1 then TP4/PP4; step 10's group runs TP4/PP2, TP8/PP2, then TP4/PP4, which fails and stops the group before TP16/PP1; step 11 is PP2 only",
      all(v and all(p == 1 for _, p in v) for v in one.values()) and grp("r3_network_resilience") == [(16, 1), (4, 4)]
      and grp("scaleout_load") == [(4, 2), (8, 2), (4, 4), (16, 1)] and all(p == 2 for _, p in grp("pp2_split")),
      json.dumps({str(k): v for k, v in one.items()}))
p14 = step_body(14)
check("step 14's B1 decode and torch batched profiles are one-stage TP4 servers too (the scripts default TP to 4 and nothing clears the split)",
      "PROFILE_MODE=decode TP=4" in p14 and "14c_run_vllm_torch_profile_batched.sh' || true" in p14
      and ': "${TP:=4}"' in text("06_deep_kernel_and_torch_profiling/14c_run_vllm_torch_profile_batched.sh")
      and not any("PP_LAYER_PARTITION" in text("06_deep_kernel_and_torch_profiling/" + f) for f in ("14_run_vllm_nsys_profile.sh", "14c_run_vllm_torch_profile_batched.sh")))
b1 = step_body(1); b1_cmds = [l.strip() for l in b1.splitlines()[1:-1] if l.strip()]
summ = text("02_single_node_baseline_matrix/15_summarize_vllm.py")
check("step 1 is marked done even when both chunk servers fail: its `bash -c` body has no `set -e` and ends with the summarizer, which writes empty files and exits 0 when no case ran",
      "set -e" not in b1 and "15_summarize_vllm.py" in b1_cmds[-1] and 'raise RuntimeError("Case execution failed with error")' in sur
      and 'if not rows: path.write_text(""); return' in summ and not re.search(r"sys\.exit|raise SystemExit", summ))
r = subprocess.run(["bash", "-c", "false; true"], capture_output=True, text=True, cwd=SCR)
check("experiment: a `bash -c` body without `set -e` reports only its last command's status", r.returncode == 0, f"exit {r.returncode}")
dry = "\n".join(ML[366:375]); prof = text(M)[text(M).index("    --profile)"):text(M).index("    -h|--help)")]
readme = text(ROOT / "README.md"); i_dry = readme.find("bash run_master_benchmark.sh --dry-run"); i_smoke = readme.find("bash run_master_benchmark.sh --profile smoke")
check("resume is on by default and reuses the latest run id, a dry run marks every step it passes as done, and the profiles leave both alone; the README runs `--dry-run` first, so the real runs after it skip those steps",
      ': "${RESUME:=1}"' in text(M) and 'if [[ "$RESUME" == 1 && -f "$RUN_ID_FILE" && -z "${RUN_ID:-}" ]]; then' in text(M)
      and 'if [[ "$DRY_RUN" == 1 ]]; then' in dry and 'touch "$marker"' in dry and "RESUME=" not in prof and "RUN_ID=" not in prof
      and 0 <= i_dry < i_smoke and "--new-run" not in readme[i_dry:i_smoke])
helpers = {f: text(f) for f in ("setup_cluster_and_run_smoke.sh", "run_20min_tp4pp4_campaign.sh")}
check("two helpers overwrite scripts/RUN_CONFIG.env with the 7,7,7,6 split, a 20G network label and a TP4/PP4-only topology selection; the master and five scripts read that file, and the master's defaults do not override it",
      all('cat << EOF > "$SCRIPT_DIR/RUN_CONFIG.env"' in h and 'export VLLM_PP_LAYER_PARTITION="7,7,7,6"' in h and 'export TOPOLOGY_SELECTION="tp4_pp4"' in h
          and "NETWORK_BANDWIDTH_SELECTION=" in h for h in helpers.values())
      and 'elif [[ -f "$SUITE_ROOT/RUN_CONFIG.env" ]]; then source "$SUITE_ROOT/RUN_CONFIG.env"' in text(M)
      and 'if [[ -n "$SELECTED_TOPOLOGIES" && "$SELECTED_TOPOLOGIES" != "all" ]]; then' in text(M))
pcw = [c["name"] for f in ("master_benchmark_cases.json", "continuous_batching_cases.json")
       for c in (lambda d: list(d.values()) if isinstance(d, dict) else d)(json.loads(text(f))["cases"])
       if c.get("prefix_caching") and c.get("benchmarks") and int(c["benchmarks"][0].get("warmups", 0) or 0) > 0]
check("the shared warm-up seed is harmless today: no case with prefix caching on warms up its first benchmark", pcw == [], str(pcw))

check("the README promises a server restart between concurrency levels, which the runner does not do",
      "Between each concurrency level within a benchmark case, the `vllm serve` process" in text(ROOT / "README.md"))
check("the setup manual's ray 2.35.0 and triton 3.0.0 also disagree with the readiness gate (ray 2.58.0, triton 3.7.1)",
      "ray[default]==2.35.0" in rs and "triton==3.0.0" in rs and '"ray": "2.58.0"' in rd and '"triton": "3.7.1"' in rd)
cbl = {}
for c in cb: cbl.setdefault(c.get("block"), set()).add((c["tp"], c.get("pp", 1)))
check("batching blocks 1-4 (two long prompts, step budget, request cap, mixed traffic) go beyond TP4/PP1; block 7 runs 8K and 128K arrival rates",
      all(any(l != (4, 1) for l in cbl[k]) for k in (1, 2, 3, 4))
      and all({b.get("input") for b in c["benchmarks"] if b.get("request_rate") is not None} == {8192, 131072} for c in cb if c.get("block") == 7))

check("both helper-written configs also set NCCL_CROSS_NIC=1", all('export NCCL_CROSS_NIC="1"' in h for h in helpers.values()))

bsc = lib[lib.index("def build_server_cmd("):]; bsc = bsc[:bsc.index("\ndef ", 1)]
check("the runner library's server builder adds --moe-backend (case value, then MOE_BACKEND, then VLLM_MOE_BACKEND); the two-server runner, the two-server Nsight profiles and the batching runner all build their servers with it",
      'moe_backend = case.get("moe_backend") or os.environ.get("MOE_BACKEND") or os.environ.get("VLLM_MOE_BACKEND", "flashinfer_cutlass")' in bsc
      and '"--moe-backend"' in bsc and all("build_server_cmd(" in text(f) for f in ("04_scaleout_distributed_network/12_run_vllm_multi_node.py",
      "06_deep_kernel_and_torch_profiling/18_run_vllm_multi_node_profile_case.py", "run_continuous_batching.py")))
check("no Python file acts on VLLM_FLASHINFER_AUTOTUNE (only the SKIP_OPS variable is read)",
      not any(re.search(r"VLLM_FLASHINFER_AUTOTUNE(?!_)", text(p)) for p in S.rglob("*.py")))


# ---------------------------------------------------------------- found by the second independent check, verified here
zz = zipfile.ZipFile(SHARED_ZIP)
real_sh = [i for i in zz.infolist() if i.filename.endswith(".sh") and not i.filename.startswith("__MACOSX/")]
check("in the zip as shared, no .sh file has an exec bit (made on a Unix-like system, so the modes are recorded)",
      real_sh and all(i.create_system == 3 and not ((i.external_attr >> 16) & 0o111) for i in real_sh), f"{len(real_sh)} .sh files")
direct = [l for l in ML if re.search(r"""(['"]|\\")\$(NET_DIR|PROF_DIR)/[0-9][\w]*\.sh(['"]|\\")""", l) and " bash " not in l]
chm = re.findall(r"cd Performance_Intelligence_Platform/(scripts[\w/]*)\nchmod \+x \*\.sh", rs)
check("the master calls the subfolder .sh scripts directly, not through bash (steps 2, 3, 10-14); the setup manual's chmod lines cover scripts/, 01/, 02/ and 07/, never 04/ or 06/, which hold every script the master calls directly",
      len(direct) >= 15 and any("run_step 3" in l for l in direct) and any("run_step 13" in l for l in direct)
      and sorted(chm) == ["scripts", "scripts/01_preflight_and_diagnostics", "scripts/02_single_node_baseline_matrix", "scripts/07_master_campaign_orchestration"]
      and all(("$NET_DIR/" in l or "$PROF_DIR/" in l) for l in direct), str(sorted(chm)))
asg = {v: [i for i, l in enumerate(ML, 1) if re.match(r"\s*" + v + r"=", l)] for v in ("TP8_DIR", "NET_DIR", "CASES_FILE", "CAPPED_DIR", "OBS_DIR")}
esc = {v: [i for i, l in enumerate(ML, 1) if "\\$" + v in l] for v in asg}
check("these master variables are plain assignments, never exported, yet steps 4, 12 and 20 use them escaped (`\\$VAR`) inside `bash -c`, so the child sees them empty: TP8_DIR (step 4), NET_DIR, CASES_FILE and CAPPED_DIR (step 12), OBS_DIR (step 20)",
      all(asg[v] for v in asg) and not re.search(r"export (TP8_DIR|NET_DIR|CASES_FILE|CAPPED_DIR|OBS_DIR)\b|\bset -a\b|\bdeclare -x\b", text(M))
      and esc["TP8_DIR"][0] == 501 and min(esc["NET_DIR"]) >= 708 and max(esc["NET_DIR"]) <= 760 and esc["OBS_DIR"] == [939], json.dumps(esc))
r = subprocess.run(["bash", "-c", 'X=set; bash -c "echo [\\$X]"'], capture_output=True, text=True, cwd=SCR)
check("experiment: a plain (unexported) variable is empty inside a child `bash -c` when escaped", r.stdout.strip() == "[]", r.stdout.strip())
b12 = step_body(12)
check("so step 12 calls `/12_run_vllm_multi_node.sh` under every condition (not found) while still applying and removing caps on node 0, and ends with a report that exits 0: marked done with no case run",
      b12.count('\\"\\$NET_DIR/12_run_vllm_multi_node.sh\\"') == 4 and "apply_cap" in b12 and b12.rstrip().endswith('"') and "RESILIENCE_COMPARISON.json" in b12)
m02 = sorted(p.name for p in (S / "02_single_node_baseline_matrix").iterdir()); m06 = sorted(p.name for p in (S / "06_deep_kernel_and_torch_profiling").iterdir())
check("the main suite's single-node runner looks for 09_metrics_sampler.py beside itself, which its folder lacks, and sends the sampler's output to /dev/null: its runs record no samples, nothing fails, and only the summary's Metrics column says NOT_CAPTURED (the batching runner finds scripts/09_metrics_sampler.py)",
      "09_metrics_sampler.py" not in m02 and 'with_name("09_metrics_sampler.py")' in sur and "stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT" in sur
      and 'if not path.exists(): return {"peak_kv_usage":None' in lib and '"CAPTURED" if ps else "NOT_CAPTURED"' in summ
      and (S / "09_metrics_sampler.py").exists() and 'Path(__file__).with_name("09_metrics_sampler.py")' in rc_py)
s18l = text("06_deep_kernel_and_torch_profiling/18_run_vllm_multi_node_profiles.sh").splitlines()
p18 = text("06_deep_kernel_and_torch_profiling/18_run_vllm_multi_node_profile_case.py")
check("the two-server profile driver sources 20_nccl_policy.sh from its own folder at line 7 under `set -euo pipefail`; that folder also lacks 20_ray_nccl_env_audit.py, 09_metrics_sampler.py and 10b_vllm_multi_node_cases.json",
      s18l[4].strip() == "set -euo pipefail" and s18l[6].strip() == 'source "$SCRIPT_DIR/20_nccl_policy.sh"'
      and not any(f in m06 for f in ("20_nccl_policy.sh", "20_ray_nccl_env_audit.py", "09_metrics_sampler.py", "10b_vllm_multi_node_cases.json"))
      and "with_name('10b_vllm_multi_node_cases.json')" in p18)
t = SCR / "missing_source_test.sh"
t.write_text('#!/usr/bin/env bash\nset -euo pipefail\nsource "$(dirname "$0")/no_such_policy.sh"\necho reached_line_4\n')
r = subprocess.run(["bash", str(t)], capture_output=True, text=True, cwd=SCR)
check("experiment: under `set -euo pipefail`, `source` of a missing file ends the script (so step 13, called directly, stops the run)",
      r.returncode != 0 and "reached_line_4" not in r.stdout and "run_step 13" in "\n".join(ML[800:802]), f"exit {r.returncode}")
b4 = [c for c in cb if c.get("block") == 4]
check("batching block 4: every mixed-traffic stream lacks the `concurrency` field the bench builder reads, so all six cases raise KeyError before sending a request",
      len(b4) == 6 and all("concurrency" not in b[k] for c in b4 for b in c["benchmarks"] for k in ("short_stream", "long_stream"))
      and 'str(b["concurrency"])' in lib and 'build_bench_cmd(vllm, bench_help, model, args.port, b["short_stream"]' in rc_py)
mt = text(M); i_parse = mt.index('SELECTED_PROFILE="$2"'); i_src = mt.index('# Discover configuration')
check("the master parses --profile before it sources RUN_CONFIG.env, and the example resets the deep-profile switches to 0, so --profile deep-profile runs no step 18-20",
      i_parse < i_src and "RUN_POISSON_SWEEPS=1" in mt[i_parse:i_src] and all(f'export {v}="0"' in rce for v in ("RUN_POISSON_SWEEPS", "RUN_SCHEDULER_SWEEPS", "RUN_OBSERVER_OVERHEAD")))
heavy = [p for p in mx if p["topology"] == "tp16_pp1_dist" and p["mode"] == "long_prefill_512k"]
check("the two-server profile driver re-reads the config (line 9) before defaulting RUN_HEAVY_PROFILE (line 17), and the example sets it to 0; step 13's only profile is a heavy one, so it would be filtered out",
      "RUN_CONFIG.env" in s18l[8] and s18l[16].strip() == ': "${RUN_HEAVY_PROFILE:=1}"' and 'export RUN_HEAVY_PROFILE="0"' in rce
      and len(heavy) == 1 and heavy[0].get("optional_heavy") is True and "if p.get('optional_heavy') and not heavy: continue" in s18)
used = set(re.findall(r"--case (\w+)", text(M))) | set(re.search(r"for seq_case in ([\w ]+); do", text(M)).group(1).split())
ug = set(re.findall(r"--group (\w+)", text(M)))
run_c = [c for c in mc if c["name"] in used or ug & set(c.get("groups", []))]
one32 = sorted({c.get("max_num_seqs") for c in run_c if c["tp"] <= 8 and c.get("pp", 1) == 1 and any(b["concurrency"] == 32 for b in c["benchmarks"]) and "scheduler" not in c["name"]})
cbdef = json.loads(text("continuous_batching_cases.json"))["server_defaults"]["max_num_seqs"]
cb32 = sorted({c.get("max_num_seqs", cbdef) for c in cb if c["tp"] <= 8 and c.get("pp", 1) == 1 and any(b.get("concurrency") == 32 for b in c["benchmarks"])})
check("admission caps: the two-server load cases run up to 32 in flight with max_num_seqs 16 (so 16 queue); in the main case file the one-server cases run at 32 cap at 64, in the batching suite at 256; the 32-capped baselines are used by no step",
      all(c.get("max_num_seqs") == 16 and max(b["concurrency"] for b in c["benchmarks"]) == 32 for c in load) and one32 == [64] and cb32 == [256]
      and not ({"tp4_pp1_baseline", "tp8_pp1_baseline"} & {c["name"] for c in run_c}), f"main {one32}, batching {cb32}")
cold_cb = sorted(c["name"] for c in cb if int((c["benchmarks"][0].get("warmups") or (c["benchmarks"][0].get("short_stream") or {}).get("warmups") or 0)) == 0)
check("warm-ups outside the main suite: 10 of the 28 batching servers (blocks 4 and 7) start cold, and the profile runs send no warm-up",
      len(cold_cb) == 10 and {c.get("block") for c in cb if c["name"] in cold_cb} == {4, 7}
      and all("--num-warmups 0" in text("06_deep_kernel_and_torch_profiling/" + f) for f in ("14_run_vllm_nsys_profile.sh", "14c_run_vllm_torch_profile_batched.sh", "14d_run_vllm_torch_profile_multi_node.sh"))
      and "'warmups':0" in p18)
t14d = sorted(set(re.findall(r"TOPOLOGY=(\w+)", step_body(2))) | set(re.search(r"for topo in ([\w ]+); do", step_body(14)).group(1).split()))
check("the two-server torch profile (14d) is called for three layouts only (no TP4/PP2)", t14d == ["tp16_pp1_dist", "tp4_pp4_dist", "tp8_pp2_dist"], str(t14d))
ccl = WSRC["vllm/distributed/device_communicators/cuda_communicator.py"]; pyn = WSRC["vllm/distributed/device_communicators/pynccl.py"]
rs_body = ccl[ccl.index("    def reduce_scatter(self"):ccl.index("    def reduce_scatterv(")]
rsv_body = ccl[ccl.index("    def reduce_scatterv("):]; rsv_body = rsv_body[:rsv_body.index("\n    def ", 10)]
pr = pyn[pyn.index("    def reduce_scatter("):]; pr = pr[:pr.index("\n    def ", 10)]
vc = WSRC["vllm/config/vllm.py"]; a2a = WSRC["vllm/distributed/device_communicators/all2all.py"]; moec = WSRC["vllm/model_executor/layers/fused_moe/config.py"]
check("with VLLM_DISABLE_PYNCCL=1, vLLM's reduce-scatter still calls its own communicator, which returns without writing (uninitialised output, no error); its only user here would be the compile-time sequence-parallel pass, off for every model (IS_DENSE is the constant False)",
      "disabled" not in rs_body and "disabled" not in rsv_body and "pynccl_comm.reduce_scatter(output, input_tensor)" in rs_body
      and "if self.disabled:\n            return" in pr and "if pynccl_comm is None or pynccl_comm.disabled:" in ccl
      and vc.count('"enable_sp": IS_DENSE,') == 2 and "\nIS_DENSE = False\n" in vc)
mdl_sp = mdl[mdl.index("self.use_sequence_parallel = ("):][:400]
gv = ccl[ccl.index("    def all_gatherv("):]; gv = gv[:gv.index("\n    def ", 10)]
check("data-parallel expert parallelism (the default all-gather/reduce-scatter all-to-all) and this model's own sequence parallelism (expert parallel with DP>1) dispatch through all_gatherv, which asserts the communicator is on: with pynccl disabled they stop on their first forward pass instead of computing garbage",
      'all2all_backend: All2AllBackend = "allgather_reducescatter"' in WSRC["vllm/config/parallel.py"] and "gathered_tensors = dist_group.all_gatherv(" in a2a
      and "self.dp_size > 1 or self.pcp_size > 1 or self.is_sequence_parallel" in moec and "assert pynccl_comm is not None and not pynccl_comm.disabled" in gv
      and "parallel_config.enable_expert_parallel" in mdl_sp and "parallel_config.data_parallel_size > 1" in mdl_sp)

defs = [(m.start(), m.group(1)) for m in re.finditer(r"\n    def (\w+)\(", ccl)]
guard = {}
for k, (pos, name) in enumerate(defs):
    body = ccl[pos:(defs[k + 1][0] if k + 1 < len(defs) else len(ccl))]
    if "pynccl" in body and not name.startswith("_") and name not in ("__init__", "destroy"): guard[name] = ".disabled" in body
kind = {}
for k, (pos, name) in enumerate(defs):
    body = ccl[pos:(defs[k + 1][0] if k + 1 < len(defs) else len(ccl))]
    if name in guard:
        kind[name] = ("falls back" if ".disabled" in body and ("torch.distributed." in body or "return super()." in body) else
                      "raises" if ".disabled" in body and re.search(r"\braise\b|assert pynccl_comm is not None and not pynccl_comm.disabled", body) else "silent")
check("with pynccl disabled: all-reduce, all-gather and send/receive fall back to torch.distributed; broadcast, all-gatherv and batched send/receive raise; reduce-scatter and reduce-scatterv go silent",
      all(kind.get(n) == "falls back" for n in ("all_reduce", "all_gather", "send", "recv"))
      and all(kind.get(n) == "raises" for n in ("broadcast", "all_gatherv", "batch_isend_irecv"))
      and all(kind.get(n) == "silent" for n in ("reduce_scatter", "reduce_scatterv")), json.dumps(kind))

ps_ = text("pip_scan.py")
check("the pause screen treats any path containing 'profile' as a profiler capture and never counts its pauses; step 12 writes to step12_capped_profiles, so its runs would be skipped",
      'return "profile" in rl or "/workload/" in rl' in ps_ and "is_pause=pz[\"is_pause\"] and not is_profile(rel)" in ps_ and 'CAPPED_DIR="$MASTER_ROOT/step12_capped_profiles"' in text(M))
ns0 = {"envs": types.SimpleNamespace(VLLM_PP_LAYER_PARTITION=None), "logger": logging.getLogger("x")}; exec(code, ns0)
dflt = {pp: [ns0["get_pp_indices"](27, r, pp) for r in range(pp)] for pp in (1, 2, 4)}
dsz = {pp: [b - a for a, b in v] for pp, v in dflt.items()}
check("the two-server runner records the split as 'default_14_13' whenever the variable is unset, but vLLM's own default for 27 layers is 14/13 only at PP2 (7,7,7,6 at PP4, one stage at PP1); vLLM logs an uneven default split at start-up",
      '"pp_layer_partition":os.environ.get("VLLM_PP_LAYER_PARTITION", "default_14_13")' in mn and dsz == {1: [27], 2: [14, 13], 4: [7, 7, 7, 6]}
      and '"Hidden layers were unevenly partitioned: [%s]. "' in du, json.dumps(dsz))
row = summ[summ.index("row={"):summ.index("**pct_rel(completed)")]
check("the summarizer's rows carry neither the result folder nor the layer split, so step 11's two arms (same cases, two folders, one summary) come out as identically labelled pairs",
      "pp_layer_partition" not in row and "path" not in row and "split_15_12" in ML[693] and "split_control_default" in ML[694] and "15_summarize_vllm.py' '$PP2_DIR'" in ML[695])

# ---------------------------------------------------------------- v1.2: the autotune skip list and the agreed settings
FW = zipfile.ZipFile(FI_WHL)
FSRC = {n: FW.read(n).decode("utf-8", "replace") for n in FW.namelist() if n.endswith(".py")}
def wl(n): return WSRC[n].splitlines()
def fl(n): return FSRC[n].splitlines()
SKIP = 'export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"'
sk_at = {M: 254, "RUN_CONFIG.env.example": 114, "07_master_campaign_orchestration/RUN_CONFIG.env.example": 29, "run_smoke_test.sh": 146,
         "setup_cluster_and_run_smoke.sh": 140, "run_20min_tp4pp4_campaign.sh": 103, "04_scaleout_distributed_network/12_run_vllm_multi_node.sh": 22}
mns = text("04_scaleout_distributed_network/12_run_vllm_multi_node.sh").splitlines()
sur = text("02_single_node_baseline_matrix/11_run_vllm_surrogate.py").splitlines()
check("v1.2 the skip list (FlashInfer's two CUTLASS MoE GEMMs) is set unconditionally in seven places, exported again for node 1 after the policy exports (two-server runner line 34), and injected by the single-node runner when unset (line 58); the comments say 'to prevent Triton MoE hang'",
      all(text(f).splitlines()[n - 1].strip() == SKIP for f, n in sk_at.items())
      and '$(nccl_remote_v6_aligned_exports) export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS=\\"trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2\\"; export VLLM_DISABLE_PYNCCL=\\"1\\";' in mns[33]
      and 'env["VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS"]=os.environ.get("VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS", "trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2")' in sur[57]
      and "to prevent Triton MoE hang" in mns[20] and "to prevent Triton MoE hang" in sur[10])
pol = text("04_scaleout_distributed_network/20_nccl_policy.sh").splitlines()
check("v1.2 the NCCL policy exports the skip list, the split and VLLM_DISABLE_PYNCCL to node 1 whenever they are set, empty included (20_nccl_policy.sh lines 75-79)",
      all(v in pol[74] for v in ("VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS", "VLLM_PP_LAYER_PARTITION", "VLLM_DISABLE_PYNCCL")) and pol[75].strip() == 'if [[ -n "${!var+x}" ]]; then')
rso = text(ROOT / "README_SETUP_AND_OPERATIONS.md").splitlines(); pmr = text(ROOT / "PIP_MASTER_RESULTS_AND_BENCHMARKS.md").splitlines()
check("v1.2 the docs give the skip list as avoiding 'warmup hangs' (README_SETUP_AND_OPERATIONS.md line 1401) and a '45-minute JIT freeze' in Triton MoE warm-up (PIP_MASTER_RESULTS_AND_BENCHMARKS.md line 36), and 15,12 as '+27.58% TTFT' (line 1402)",
      "avoid warmup hangs" in rso[1400] and "Triton MoE JIT Warmup" in pmr[35] and "45-minute JIT freeze" in pmr[35] and "+27.58% TTFT" in rso[1401])
ev = wl("vllm/envs.py")
check("v1.2 vLLM reads the skip list as comma-separated names: unset, it skips fp4_gemm only with the CuTe-DSL NVFP4 linear kernel; set but empty, it skips nothing (envs.py 1712-1723)",
      'Unset: skip "fp4_gemm" when the' in ev[1712] and "Empty: skip nothing." in ev[1713] and '.split(",")' in ev[1719])
kw = wl("vllm/model_executor/warmup/kernel_warmup.py")
check("v1.2 vLLM runs FlashInfer autotune only when it is enabled, FlashInfer is usable and the GPU is SM90 or newer; otherwise it logs that it is disabled, or nothing (kernel_warmup.py 189-196)",
      kw[192].strip() == "if enable_flashinfer_autotune is False:" and "Skipping FlashInfer autotune because it is disabled." in kw[193]
      and kw[194].strip() == "elif has_flashinfer() and current_platform.has_device_capability(90):" and kw[195].strip() == "flashinfer_autotune(worker.model_runner)")
check("v1.2 a set skip list replaces vLLM's own choice; vLLM logs 'Skipping FlashInfer autotuning for ops' and passes it to FlashInfer's autotune (kernel_warmup.py 231-247, 299-305, 332)",
      kw[231].strip() == "if envs.VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS is not None:" and kw[232].strip() == "return set(envs.VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS) or None"
      and kw[245].strip() == 'return {"fp4_gemm"}' and kw[298].strip() == "skip_ops = _flashinfer_autotune_skip_ops(runner)"
      and '"Skipping FlashInfer autotuning for ops %s",' in kw[301] and kw[304].strip() == 'autotune_kwargs["skip_ops"] = skip_ops'
      and "fi_utils.autotune(tune_mode=True, **autotune_kwargs)," in kw[331] and 'logger.info("Running FlashInfer autotune with %d tokens.", num_tokens)' in kw[265])
fc = wl("vllm/model_executor/warmup/flashinfer_autotune_cache.py")
cf_ = ev[ev.index("    ignored_factors: set[str] = {"):]; cf_ = cf_[:cf_.index("    }")]
check("v1.2 the autotune cache: rank 0 names and reads the file, broadcasts it, every rank loads it before tuning, rank 0 saves it after (kernel_warmup.py 307-341); the file is VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR or the vLLM cache folder's flashinfer_autotune_cache, under a hash of the compile key (flashinfer_autotune_cache.py 19-41), which leaves out both autotune variables (envs.py 2257-2302)",
      'logger.info_once("Using FlashInfer autotune cache file: %s", cache_path)' in kw[308] and kw[317].strip() == "if is_leader and cache_path.exists():"
      and kw[320].strip() == "cached_results = world.broadcast_object(cached_results, src=0)" and kw[324].strip() == "tuner.load_configs(str(cache_path))"
      and kw[340].strip() == "tuner.save_configs(str(cache_path))" and fc[19].strip() == "factors = aot_compile_hash_factors(runner.vllm_config)"
      and fc[24].strip() == "override_dir = envs.VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR" and '"flashinfer_autotune_cache"' in fc[33] and fc[40].strip() == 'return output_dir / "autotune_configs.json"'
      and '        "VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR",' in cf_ and '        "VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS",' in cf_
      and "env_hash = hash_factors(envs.compile_factors())" in WSRC["vllm/compilation/caching.py"])
fu = wl("vllm/utils/flashinfer.py")
check("v1.2 vLLM counts FlashInfer as usable only with the flashinfer-cubin package or nvcc on PATH (flashinfer.py 68-83)",
      fu[67].strip() == "def has_flashinfer() -> bool:" and fu[76].strip() == 'if not has_flashinfer_cubin() and shutil.which("nvcc") is None:')
check("v1.2 the oracle moves both FlashInfer MoE kernels back on Hopper (unquantized.py 75-79) and CUTLASS also when data parallelism is above 1 (84-85); an explicit --moe-backend that cannot run stops the start with ValueError instead of falling back (271-297); the start-up line reads 'Using <backend> Unquantized MoE backend' (251-256)",
      uq[76].strip() == "if current_platform.is_device_capability_family(90):" and "UnquantizedMoeBackend.FLASHINFER_CUTLASS" in uq[78]
      and uq[83].strip() == "if moe_config.moe_parallel_config.dp_size > 1:" and "UnquantizedMoeBackend.FLASHINFER_CUTLASS" in uq[84]
      and uq[283].strip() == "raise ValueError(_make_log_unsupported(backend, reason))" and uq[288].strip() == 'if runner_backend not in ["auto", "humming"]:'
      and uq[296].strip() == "return _return_or_raise(requested_backend, moe_config, activation_format)" and 'f"Using {backend.value} Unquantized MoE backend out "' in uq[253])
fce = wl("vllm/model_executor/layers/fused_moe/experts/flashinfer_cutlass_moe.py"); fuj = "\n".join(fu)
check("v1.2 FlashInfer CUTLASS MoE runs only on SM90, SM100 or SM120 with FlashInfer usable (flashinfer_cutlass_moe.py 129-140, flashinfer.py 283-289 and 355-372); otherwise the oracle's support check fails, which with an explicit --moe-backend stops the start",
      fce[128].strip() == "def _supports_current_device() -> bool:" and "p.is_device_capability_family(120)" in fce[136] and fce[138].strip() == "and has_flashinfer_cutlass_fused_moe()"
      and fu[283].strip() == "def has_flashinfer_moe() -> bool:" and fu[286].strip() == "has_flashinfer()"
      and fu[355].strip() == "def has_flashinfer_cutlass_fused_moe() -> bool:" and fu[357].strip() == "if not has_flashinfer_moe():"
      and "if not cls._supports_current_device():" in WSRC["vllm/model_executor/layers/fused_moe/modular_kernel.py"])
rx = wl("vllm/v1/executor/ray_executor.py"); su = wl("vllm/utils/system_utils.py")
check("v1.2 vLLM copies every registered vLLM variable that is set on node 0 to all Ray workers and logs each overwrite; a variable unset on node 0 is not copied, so a worker keeps its own value (ray_executor.py 326-343, ray_env.py 88-98, system_utils.py 34-44)",
      rx[326].strip() == "env_vars_to_copy = get_env_vars_to_copy(" and rx[336].strip() == "if name in os.environ:" and rx[337].strip() == "args[name] = os.environ[name]"
      and wl("vllm/ray/ray_env.py")[88].strip() == "result = set(envs.environment_variables)" and su[35].strip() == "for k, v in envs_dict.items():"
      and "Overwriting environment variable" in su[38] and su[43].strip() == "os.environ[k] = v"
      and all(f'"{v}": lambda' in WSRC["vllm/envs.py"] for v in ("VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS", "VLLM_PP_LAYER_PARTITION", "VLLM_DISABLE_PYNCCL")))
fco = fl("flashinfer/fused_moe/core.py"); fat = fl("flashinfer/autotuner/autotuner.py")
check("v1.2 FlashInfer 0.6.18: trtllm::fused_moe::gemm1 and gemm2 are the two GEMMs its CUTLASS fused MoE tunes (fused_moe/core.py 891, 960-988)",
      fco[890].strip() == "def cutlass_fused_moe(" and fco[960].strip() == '"trtllm::fused_moe::gemm1",' and fco[976].strip() == '"trtllm::fused_moe::gemm2",'
      and "tuner.choose_one(" in fco[959] and "tuner.choose_one(" in fco[975])
check("v1.2 FlashInfer: a skipped operation is not profiled and gets the heuristic fallback tactic, and the skip applies only inside the tuning context (autotuner.py 1609-1621, 938-944, 988-992)",
      fat[1613].strip() == "if custom_op in self._effective_skip_ops:" and fat[1620].strip() == "return runners[0], -1"
      and fat[943].strip() == "skip_ops_stack.append(current | frozenset(skip_ops_set))" and fat[991].strip() == "skip_ops_stack.pop()")
check("v1.2 FlashInfer: tuned results loaded from the cache file are used in serving and logged as 'Config cache hit', and tuning checks the cache before profiling (autotuner.py 1430-1491, 1737-1744)",
      "2. User-loaded configs (via load_configs() or autotune(cache=...))" in fat[1431] and "# 2. User-loaded configs" in fat[1476]
      and '[Autotuner]: Config cache hit for {custom_op} ' in fat[1487] and "is_cache_hit, runner_id, tactic, _ = self.search_cache(" in fat[1736] and fat[1743].strip() == "if not is_cache_hit:")
check("v1.2 FlashInfer: every rank must tune the same operations against the same starting cache, since each tactic's time is all-reduced across ranks; a skip list that differs between ranks deadlocks the reduction (autotuner.py 1066-1072, 2187-2201); it logs 'Autotuning process starts' and 'ends' (972, 995)",
      "Caller contract: every rank must enter ``_profile_single_kernel`` the same" in fat[1065] and "``skip_ops`` (a skipped op returns before the tactic loop, doing zero" in fat[1068]
      and fat[2197].strip() == "dist.all_reduce(" and "Autotuning process starts" in fat[971] and "Autotuning process ends" in fat[994])
fjc, fje, fjm = fl("flashinfer/jit/core.py"), fl("flashinfer/jit/env.py"), fl("flashinfer/jit/fused_moe.py")
check("v1.2 FlashInfer builds its SM120 CUTLASS MoE module with nvcc on first use, unless a prebuilt copy loads, and keeps it in ~/.cache/flashinfer/<version>/<arch>/cached_ops (jit/core.py 300-321, jit/env.py 62 and 161-162, jit/fused_moe.py 63)",
      fjc[299].strip() == "def build_and_load(self) -> Any:" and fjc[300].strip() == "cached = self.try_load()" and fjc[319].strip() == "self.build()"
      and '".cache" / "flashinfer"' in fje[61] and fje[161].strip() == 'FLASHINFER_JIT_DIR: pathlib.Path = FLASHINFER_WORKSPACE_DIR / "cached_ops"'
      and fjm[62].startswith("def gen_cutlass_fused_moe_sm120_module("))
stt = text("run_smoke_test.sh").splitlines()
check("v1.2 the split elsewhere: the 20-minute script writes 7,7,7,6 (line 104), 07's example sets 15,12 (line 30), and the smoke test reports 'PP_SPLIT=15,12' as PASSED without testing the variable (lines 149-155); the two-server runner passes a set split to node 1 (lines 70-71)",
      text("run_20min_tp4pp4_campaign.sh").splitlines()[103].strip() == 'export VLLM_PP_LAYER_PARTITION="7,7,7,6"'
      and text("07_master_campaign_orchestration/RUN_CONFIG.env.example").splitlines()[29].strip() == 'export VLLM_PP_LAYER_PARTITION="15,12"'
      and "PP_SPLIT=15,12" in stt[154] and '"PASSED"' in stt[154] and not any("PP_LAYER_PARTITION" in l for l in stt[148:153])
      and mns[69].strip() == 'if [[ -n "${VLLM_PP_LAYER_PARTITION:-}" ]]; then' and "PP_EXPORT=\"export VLLM_PP_LAYER_PARTITION=" in mns[70]
      and "VLLM_PP_LAYER_PARTITION will affect the computation graph" in WSRC["vllm/compilation/caching.py"])
check("v1.2 VLLM_DISABLE_PYNCCL=1 is also set by both helpers (cluster set-up line 142, 20-minute script line 101), 07's example (line 31), the two-server runner for node 0 (line 23) and again for node 1 (line 34), so leaving it unset on node 0 alone would leave node 1's workers with 1",
      text("setup_cluster_and_run_smoke.sh").splitlines()[141].strip() == 'export VLLM_DISABLE_PYNCCL="1"' and text("run_20min_tp4pp4_campaign.sh").splitlines()[100].strip() == 'export VLLM_DISABLE_PYNCCL="1"'
      and text("07_master_campaign_orchestration/RUN_CONFIG.env.example").splitlines()[30].strip() == 'export VLLM_DISABLE_PYNCCL="1"'
      and mns[22].strip() == 'export VLLM_DISABLE_PYNCCL="1"' and 'export VLLM_DISABLE_PYNCCL=\\"1\\";' in mns[33] and ML[269].strip() == 'export VLLM_DISABLE_PYNCCL="${VLLM_DISABLE_PYNCCL:-1}"')

lg = wl("vllm/logger.py"); ps2 = wl("vllm/distributed/parallel_state.py")
check("v1.2 vLLM's info_once lines (the backend line, 'autotune because it is disabled', the skip-list line) log once per node: the default scope is 'local', the node's first rank (logger.py 102-105 and 127-134, parallel_state.py 2437-2445); 'Running FlashInfer autotune' is a plain info line on every rank",
      lg[101].strip() == 'if scope == "local":' and lg[104].strip() == "return is_local_first_rank()"
      and 'def info_once(self, msg: str, *args: Hashable, scope: LogScope = "local") -> None:' in lg[126]
      and ps2[2436].strip() == "def is_local_first_rank() -> bool:" and ps2[2444].strip() == "return _WORLD.local_rank == 0"
      and "logger.info_once(" in kw[300] and "logger.info_once(_make_log_backend(backend))" in uq[281] and kw[265].strip().startswith("logger.info("))
ec = wl("vllm/v1/engine/core.py"); gw = wl("vllm/v1/worker/gpu_worker.py")
check("v1.2 start-up order: the memory profiling run (the model's first forward) comes before the kernel warm-up that runs autotune (engine core.py 308, 343, 345; gpu_worker.py 513-557, 750-784)",
      "self.model_executor.determine_available_memory()" in ec[307] and "self.model_executor.compile_or_warm_up_model()" in ec[344]
      and gw[512].strip().startswith("def determine_available_memory(self)") and "self.model_runner.profile_run()" in gw[529]
      and gw[749].strip().startswith("def compile_or_warm_up_model(self)") and gw[783].strip() == "kernel_warmup(self)")
fcx = fl("flashinfer/jit/cpp_ext.py")
check("v1.2 FlashInfer builds the SM120 CUTLASS MoE module on the first call (fused_moe/core.py 585-598) and pipes the build output unless verbose, so the build logs nothing (jit/cpp_ext.py 353-377)",
      fco[584].strip() == "@functools.cache" and fco[585].startswith("def get_cutlass_fused_moe_module(") and "gen_cutlass_fused_moe_sm120_module(use_fast_build).build_and_load()" in fco[587]
      and fcx[352].startswith("def run_ninja(") and "stdout=None if verbose else subprocess.PIPE," in fcx[371])
check("v1.2 without nvcc on PATH, vLLM counts FlashInfer as usable only with the flashinfer-cubin package or VLLM_HAS_FLASHINFER_CUBIN=1 (flashinfer.py 56-64); FlashInfer's prebuilt modules come from the flashinfer-jit-cache package (jit/env.py 113-145)",
      fu[56].strip() == "def has_flashinfer_cubin() -> bool:" and fu[58].strip() == "if envs.VLLM_HAS_FLASHINFER_CUBIN:" and 'find_spec("flashinfer_cubin")' in fu[60]
      and fje[112].startswith("def _get_aot_dir():") and "import flashinfer_jit_cache" in fje[120])
prov = json.loads(text(S / "01_preflight_and_diagnostics" / (K.lower() + "_linear_provenance.json")))
fa1 = prov["config"]["linear_attn_config"]["full_attn_layers"]; nl = prov["config"]["num_hidden_layers"]
def fa_per_stage(sizes):
    out, a = [], 0
    for n in sizes:
        out.append(sum(1 for x in fa1 if a < x <= a + n)); a += n   # the list counts layers from 1
    return out
mix = {k: fa_per_stage(v) for k, v in {"14/13": dsz[2], "15/12": [15, 12], "7/7/7/6": dsz[4]}.items()}
check("v1.2 the oracle's other demotions do not apply here: FlashInfer kernels go back for the SWIGLUOAI activation (unquantized.py 87-93), LoRA takes its own path (222-236); this model's activation is SiLU (model provenance file)",
      uq[90].strip() == "if moe_config.activation == MoEActivation.SWIGLUOAI:" and uq[221].strip() == "if moe_config.is_lora_enabled:" and prov["config"].get("hidden_act") == "silu")
check("v1.2 full-attention layers per pipeline stage, from the model provenance file in 01_preflight_and_diagnostics (27 layers; full attention at 4, 8, 12, 16, 20, 24 and 27, counted from 1): 3/4 at 14/13, 3/4 at 15/12, 1/2/2/2 at 7/7/7/6",
      nl == 27 and fa1 == [4, 8, 12, 16, 20, 24, 27] and mix == {"14/13": [3, 4], "15/12": [3, 4], "7/7/7/6": [1, 2, 2, 2]}, json.dumps(mix))
check("v1.2 vLLM logs 'Hidden layers were unevenly partitioned' only for its own default and only when uneven, so a set split leaves no line (utils.py 143-167)",
      "if partition_list_str is not None:" in du and du.index("Hidden layers were unevenly partitioned") > du.index("    else:\n        layers_per_partition")
      and "if remaining_layers := num_hidden_layers % pp_size:" in du)
hs, h20 = text("setup_cluster_and_run_smoke.sh").splitlines(), text("run_20min_tp4pp4_campaign.sh").splitlines()
check("v1.2 the two helpers write their settings into RUN_CONFIG.env through an unquoted heredoc (cluster set-up 124-155, 20-minute script 91-115), so a ${...} there expands when the helper runs",
      hs[123].strip() == 'cat << EOF > "$SCRIPT_DIR/RUN_CONFIG.env"' and hs[154].strip() == "EOF" and h20[90].strip() == 'cat << EOF > "$SCRIPT_DIR/RUN_CONFIG.env"' and h20[114].strip() == "EOF"
      and all(124 < n < 155 for n in (140, 141, 142)) and all(91 < n < 115 for n in (101, 103, 104)))

n_ok = sum(1 for _, ok, _ in RES if ok)
print(f"{n_ok} of {len(RES)}")
sys.exit(0 if n_ok == len(RES) else 1)
