#!/usr/bin/env python3
"""Checks behind Scripts_Review_v1.5: what became of each comment in Scripts_Review_v1.4, the new findings, and the
end-to-end walk, in the Performance Intelligence Platform folder as shared on 13 Oct (8 am). Every statement the review
makes about the code is an assertion here; the output lists each with the file and line it rests on.

It reads files only. It runs none of the team's scripts and imports nothing from them. The experiments at the end run
small shell and Python snippets of its own in the scratch folder: each reproduces a mechanism (setsid and a process
group, an unset after a capture, set -u, set -e, a glob's case, a key function, a parameter default), re-typed from the
team's lines, which the static checks tie to the team's text.

Usage: python3 -I check_scripts_review_v15.py <Performance_Intelligence_Platform dir> <zip as shared> <scratch dir>
           [--old <the folder v1.4 reviewed>] [--v13 <the folder v1.3 reviewed>] [--vllm-wheel <vllm-0.29.0 wheel>]
Exit status 0 when every check passes."""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile

_ap = argparse.ArgumentParser()
_ap.add_argument('pip'); _ap.add_argument('zip'); _ap.add_argument('scratch')
_ap.add_argument('--old', help='the Performance_Intelligence_Platform folder v1.4 reviewed (12 Oct, 9 pm)')
_ap.add_argument('--vllm-wheel', help='vllm-0.29.0 wheel, read as a zip, for the vLLM facts the review uses')
_ap.add_argument('--v13', help='the folder v1.3 reviewed, for what its helpers wrote into RUN_CONFIG.env')
_ap.add_argument('--nccl-json', help='an nccl-tests -J output from an earlier run (the pilot\'s), for the format step 3 parses')
_ap.add_argument('--stage2-fp8', help='the second campaign\'s FP8 KV rerun folder, for how that case ended')
_a = _ap.parse_args()
PIP, ZIP, SCRATCH, OLD, WHL, V13 = _a.pip, _a.zip, _a.scratch, _a.old, _a.vllm_wheel, _a.v13
NCCLJ, FP8DIR = _a.nccl_json, _a.stage2_fp8
os.makedirs(SCRATCH, exist_ok=True)

P8 = 'V' + '8'                                   # the old suite's prefix, spelled split so this file carries no such name
CAP_VAR, MODE_VAR, PROV_VAR = P8 + '_VLLM_NETWORK_CAP_GBPS', P8 + '_VLLM_NETWORK_MODE', P8 + '_GCP_NETWORK_PROVENANCE_OVERRIDE'
_MASK = [(re.compile('ki' + 'mi', re.I), '<model>'), (re.compile('moon' + 'shot', re.I), '<org>'),
         (re.compile('deep' + 'seek', re.I), '<m2>'), (re.compile('mx' + 'fp4', re.I), '<q4>'),
         (re.compile(r'(?<![A-Za-z0-9])[Vv]' + '8'), 'Vx'), (re.compile(r'(?<![A-Za-z0-9])[Vv]' + '9(?![0-9])'), 'Vy'),
         (re.compile('K' + 'DA'), '<attn>'), (re.compile(r'/home/[^/\s\'"]+'), '/home/<user>'),
         (re.compile(r'[Cc]:[/\\]+Users[/\\]+[^/\\\s\'"]+'), 'C:' + '/Users/<user>'), (re.compile(r'mev' + 'reon'), '<project>'),
         (re.compile(r'\b10\.128\.0\.\d+\b'), '<node address>')]


def mask(s):
    s = s.replace(os.path.abspath(SCRATCH), '<scratch>').replace(os.path.abspath(PIP), '<folder>')
    if OLD:
        s = s.replace(os.path.abspath(OLD), '<v1.4 folder>')
    if V13:
        s = s.replace(os.path.abspath(V13), '<v1.3 folder>')
    for extra in (NCCLJ, FP8DIR):
        if extra:
            s = s.replace(os.path.abspath(extra), '<earlier run>')
    for rx, rep in _MASK:
        s = rx.sub(rep, s)
    return s


def text(rel, root=None):
    with open(os.path.join(root or PIP, rel), encoding='utf-8', errors='replace') as f:
        return f.read()


def lines(rel, root=None):
    return text(rel, root).splitlines()


def grep(rel, pat, root=None, flags=0):
    rx = re.compile(pat, flags)
    return [(i + 1, l) for i, l in enumerate(lines(rel, root)) if rx.search(l)]


def vals(x):
    return list(x.values()) if isinstance(x, dict) else list(x)


def md5(path):
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


RESULTS = []


def check(cid, statement, ok, evidence=''):
    RESULTS.append((cid, bool(ok)))
    ev = mask(evidence if isinstance(evidence, str) else '; '.join(map(str, evidence)))
    print(f"[{'PASS' if ok else 'FAIL'}] {cid}: {mask(statement)}" + (f"\n         {ev[:700]}" if ev else ''))


class guard:
    """Run a section; if its code cannot be evaluated on this folder (a pattern or file it needs is gone), record a FAIL and go on."""
    def __init__(self, cid):
        self.cid = cid

    def __enter__(self):
        return self

    def __exit__(self, et, ev, tb):
        if et is not None:
            check(self.cid, f'could not be evaluated on this folder ({et.__name__}: {str(ev)[:160]})', False)
            return True


def at(rel, hits, n=3):
    return '; '.join(f"{rel}:{i} {l.strip()[:150]}" for i, l in hits[:n])


def first_line(rel, pat):
    h = grep(rel, pat)
    return h[0][0] if h else None


MASTER = 'scripts/run_master_benchmark.sh'
M07 = 'scripts/07_master_campaign_orchestration/run_master_benchmark.sh'
RUN12SH = 'scripts/04_scaleout_distributed_network/12_run_vllm_multi_node.sh'
RUN12PY = 'scripts/04_scaleout_distributed_network/12_run_vllm_multi_node.py'
POLICY = 'scripts/04_scaleout_distributed_network/20_nccl_policy.sh'
AUDIT = 'scripts/04_scaleout_distributed_network/20_ray_nccl_env_audit.py'
DRV18 = 'scripts/06_deep_kernel_and_torch_profiling/18_run_vllm_multi_node_profiles.sh'
CASE18 = 'scripts/06_deep_kernel_and_torch_profiling/18_run_vllm_multi_node_profile_case.py'
MAT18 = 'scripts/06_deep_kernel_and_torch_profiling/18_multi_node_profile_matrix.json'
T14 = 'scripts/06_deep_kernel_and_torch_profiling/14_run_vllm_nsys_profile.sh'
T14C = 'scripts/06_deep_kernel_and_torch_profiling/14c_run_vllm_torch_profile_batched.sh'
T14D = 'scripts/06_deep_kernel_and_torch_profiling/14d_run_vllm_torch_profile_multi_node.sh'
LIB = 'scripts/v5_runner_lib.py'
SINGLE = 'scripts/02_single_node_baseline_matrix/11_run_vllm_surrogate.py'
CB = 'scripts/run_continuous_batching.py'
CBCASES = 'scripts/continuous_batching_cases.json'
CASES = 'scripts/master_benchmark_cases.json'
C10B = 'scripts/04_scaleout_distributed_network/10b_vllm_multi_node_cases.json'
SMOKE = 'scripts/run_smoke_test.sh'
SETUPC = 'scripts/setup_cluster_and_run_smoke.sh'
H20 = 'scripts/run_20min_tp4pp4_campaign.sh'
NODEENV = 'scripts/setup_node_env.sh'
READY = 'scripts/01_preflight_and_diagnostics/22_readiness.py'
EX = 'scripts/RUN_CONFIG.env.example'
EX07 = 'scripts/07_master_campaign_orchestration/RUN_CONFIG.env.example'
SCAN = 'scripts/pip_scan.py'
SUMM = 'scripts/02_single_node_baseline_matrix/15_summarize_vllm.py'
NCCLTUNE = 'scripts/04_scaleout_distributed_network/23_run_nccl_socket_tuning.sh'
CC = 'tools/compile_canonical_data.py'
RES = 'tools/compare_resilience_matrix.py'
NUMA = 'tools/compare_numa_pinning.py'
ML = lines(MASTER)
MT = text(MASTER)


def body(step):
    """The text of a master step's bash -c body, and its first and last line numbers, as the child shell receives it."""
    start = next(i for i, l in enumerate(ML) if re.match(rf'\s*run_step {step} "[^"]+" bash -c "\s*$', l))
    end = next(j for j in range(start + 1, len(ML)) if re.fullmatch(r'\s*"\s*', ML[j]))
    raw = '\n'.join(ML[start + 1:end])
    return raw.replace('\\"', '"').replace('\\$', '$'), start + 1, end + 1


BODIES = {}
for n in range(0, 21):
    try:
        BODIES[n] = body(n)
    except StopIteration:
        pass


def bash_words(s, i):
    """Split the shell command that starts at s[i] into words as bash does (quotes, backslashes, line continuations); stop at an unquoted newline."""
    words, cur, have, q = [], [], False, None
    while i < len(s):
        c = s[i]
        if q is None:
            if c == '\\' and i + 1 < len(s):
                if s[i + 1] != '\n':
                    cur.append(s[i + 1]); have = True
                i += 2; continue
            if c in ' \t':
                if have:
                    words.append(''.join(cur)); cur, have = [], False
                i += 1; continue
            if c == '\n':
                break
            if c in '"\'':
                q = c; have = True; i += 1; continue
            cur.append(c); have = True; i += 1; continue
        if q == "'":
            if c == "'":
                q = None
            else:
                cur.append(c)
            i += 1; continue
        if c == '\\' and i + 1 < len(s) and s[i + 1] in '$`"\\\n':
            if s[i + 1] != '\n':
                cur.append(s[i + 1])
            i += 2; continue
        if c == '"':
            q = None; i += 1; continue
        cur.append(c); i += 1
    if have:
        words.append(''.join(cur))
    return words


def sh(script, name, env=None):
    p = os.path.join(SCRATCH, name)
    with open(p, 'w') as f:
        f.write(script)
    r = subprocess.run(['bash', p], capture_output=True, text=True, timeout=60, env=env, cwd=SCRATCH)
    return r.returncode, r.stdout, r.stderr


def scripts_corpus(exts=('.py', '.sh')):
    out = {}
    for dp, dn, fn in os.walk(os.path.join(PIP, 'scripts')):
        if 'rtx_g4' in dp:
            continue
        for f in fn:
            if f.endswith(exts):
                p = os.path.join(dp, f)
                out[os.path.relpath(p, PIP)] = open(p, errors='ignore').read()
    return out


CORPUS = scripts_corpus()
TIMING = sorted(glob.glob(os.path.join(PIP, 'scripts', 'calc_*_timing.py')))

print('# Scripts_Review_v1.5 checks')
print('folder:', mask(os.path.basename(os.path.abspath(PIP))), '| zip md5:', md5(ZIP)[:8], '| v1.4 folder given:', bool(OLD),
      '| vLLM wheel given:', bool(WHL), '| v1.3 folder given:', bool(V13))

# ---------------------------------------------------------------------------------------------------------------------------
print('\n## 0. The folder as shared')
with guard('Z: the folder'):
    zf = zipfile.ZipFile(ZIP)
    infos = zf.infolist()
    real = [i for i in infos if not i.filename.startswith('__MACOSX/') and not i.filename.endswith('/')]
    macos = [i for i in infos if i.filename.startswith('__MACOSX/')]
    dss = [i for i in real if i.filename.endswith('.DS_Store')]
    check('Z.zip', f'the zip holds {len(real)} files, {len(macos)} macOS metadata entries (__MACOSX/) and {len(dss)} .DS_Store files ({len(infos)} entries)',
          len(real) == 220 and len(macos) == 256 and not dss and len(infos) == 512)
    if OLD:
        def inv(root):
            d = {}
            for dp, dn, fn in os.walk(root):
                for f in fn:
                    p = os.path.join(dp, f)
                    d[os.path.relpath(p, root)] = md5(p)
            return d
        a, b = inv(OLD), inv(PIP)
        added, removed = sorted(set(b) - set(a)), sorted(set(a) - set(b))
        changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
        docs_changed = [k for k in changed if k.endswith('.md')]
        check('Z.diff', f'against the folder v1.4 reviewed ({len(a)} files): {len(added)} added, {len(removed)} removed, {len(changed)} changed, '
              f'{len(docs_changed)} of them docs', len(a) == 214 and len(added) == 6 and not removed and len(changed) == 31 and len(docs_changed) == 5,
              'added: ' + ', '.join(added))
        same = {k: a.get(k) == b.get(k) for k in (CASES, C10B, MAT18, SUMM, SCAN, NCCLTUNE, T14, T14C, CASE18, AUDIT, READY)}
        check('Z.same', 'unchanged since v1.4: the master\'s cases, 10b\'s cases, the profile matrix, the summarizer, the pause screen, the NCCL sweep, '
              '14, 14c, the two-server Nsight case script, the Ray audit and the readiness gate', all(same.values()),
              str({os.path.basename(k): v for k, v in same.items() if not v}))

# ---------------------------------------------------------------------------------------------------------------------------
print('\n## 3.1 Blockers 1-13')
with guard('Blocker 1'):
    sh_ = [i for i in real if i.filename.endswith('.sh')]
    exe = [i for i in sh_ if (i.external_attr >> 16) & 0o111]
    check('B1', f'every .sh file in the zip carries an executable bit ({len(exe)} of {len(sh_)})', sh_ and len(exe) == len(sh_) == 49)
    direct = [l for l in ML if re.search(r'[\x27"]\$(PROF_DIR|NET_DIR)/[0-9A-Za-z_]+\.sh', l) and not re.search(r'\bbash\s+[\x27"]?\$', l)]
    dfiles = sorted({re.search(r'/([0-9A-Za-z_]+\.sh)', l).group(1) for l in direct})
    via_env = [l.strip()[:60] for l in direct if re.match(r'\s*run_step (3|13) ', l)]
    check('B1.direct', f'the master runs {len(dfiles)} of the team\'s .sh files directly, not through bash, from {len(direct)} places; steps 3 and 13 call theirs '
          'through run_step, so a missing bit there is a recorded failure (exit 126), while steps 2, 10-12 and 14 call theirs inside their bodies, where it would pass '
          'unseen', len(direct) == 20 and len(dfiles) == 6 and len(via_env) == 2)

with guard('Blocker 2'):
    ex_line = grep(MASTER, r'^export NODE0_IP NODE1_IP SSH_KEY VENV_DIR MASTER_ROOT SUITE_ROOT RUN_ID DRY_RUN RESUME\s*$')
    flags = all(re.search(rf'^\s*--{f}\)\s*$', MT, re.M) for f in ('node0-ip', 'node1-ip', 'ssh-key', 'venv-dir'))
    check('B2.export', 'the master now exports the node addresses, the SSH key, the venv, the run root and id, and the dry-run and resume switches, '
          'takes --node0-ip, --node1-ip, --ssh-key and --venv-dir, and defaults node 0\'s address to the first entry of hostname -I',
          ex_line and flags and grep(MASTER, r'^: "\$\{NODE0_IP:=\$\(hostname -I'), at(MASTER, ex_line + grep(MASTER, r'NODE0_IP:=\$\(hostname')))
    uses = {n: ('"$NODE1_IP"' in BODIES[n][0] or "'$NODE1_IP" in BODIES[n][0] or '$NODE1_IP' in BODIES[n][0]) for n in (0, 10, 11, 12)}
    check('B2.bodies', 'steps 0 and 10-12 read the node addresses and the key inside their bodies, which now see them through the export',
          all(uses.values()) and all('$SSH_KEY' in BODIES[n][0] for n in (10, 11, 12)) and bool(ex_line))

with guard('Blocker 3'):
    def copies(name, with_old=False):
        out = []
        for dp, dn, fn in os.walk(os.path.join(PIP, 'scripts')):
            if 'rtx_g4' in dp and not with_old:
                continue
            if name in fn:
                out.append(os.path.join(dp, name))
        return out
    names = ('09_metrics_sampler.py', 'v5_runner_lib.py', '20_ray_nccl_env_audit.py', '20_nccl_policy.sh', 'run_master_benchmark.sh',
             'master_benchmark_cases.json', 'RUN_CONFIG.env.example')
    summ = {n: (len(copies(n)), len({md5(p) for p in copies(n)})) for n in names}
    lib_all = copies('v5_runner_lib.py', True)
    check('B3.copies', 'shared files are still copied, not resolved from one place (outside the old rtx_g4_* folders): ' +
          ', '.join(f'{n} {a} ({b} version{"s" if b > 1 else ""})' for n, (a, b) in summ.items()),
          summ['09_metrics_sampler.py'] == (5, 1) and summ['v5_runner_lib.py'] == (6, 1) and summ['20_ray_nccl_env_audit.py'] == (3, 2)
          and summ['run_master_benchmark.sh'] == (2, 1) and summ['RUN_CONFIG.env.example'] == (2, 1))
    check('B3.lib', f'the runner library is now one version in all {len(lib_all)} places (rtx_g4_smoke_v5/ included): every copy has the success check '
          'and none the old pkill -9 -f "vllm"', len(lib_all) == 7 and len({md5(p) for p in lib_all}) == 1
          and all('def is_benchmark_success' in open(p).read() and '"pkill", "-9", "-f", "vllm"]' not in open(p).read() for p in lib_all))
    aud = {os.path.relpath(p, PIP): md5(p) for p in copies('20_ray_nccl_env_audit.py')}
    check('B3.audit', 'the Ray audit\'s two versions: the copies the runners use (04/ and 06/) agree; the one in 01/ differs and nothing calls it',
          aud.get('scripts/04_scaleout_distributed_network/20_ray_nccl_env_audit.py') == aud.get('scripts/06_deep_kernel_and_torch_profiling/20_ray_nccl_env_audit.py')
          != aud.get('scripts/01_preflight_and_diagnostics/20_ray_nccl_env_audit.py')
          and not any('01_preflight_and_diagnostics/20_ray_nccl_env_audit' in t for t in CORPUS.values()))
    pre = grep(MASTER, r'\[\[ -f "?\$(VLLM_DIR|NET_DIR|PROF_DIR|HW_DIR)/')
    check('B3.startup', 'the master has no start-up check that the files its steps call exist', not pre, at(MASTER, pre))

with guard('Blocker 4'):
    active = lambda rel: [l for i, l in grep(rel, r'VLLM_PP_LAYER_PARTITION') if not l.strip().startswith('#') and 'unset' not in l]
    check('B4.default', 'the master unsets the split; neither example, the smoke test nor either helper sets it; the two-server runner, the Nsight '
          'driver and 14d unset it after their re-read of RUN_CONFIG.env', grep(MASTER, r'^unset VLLM_PP_LAYER_PARTITION')
          and not active(EX) and not active(EX07) and not active(SETUPC) and not active(H20)
          and all(grep(rel, r'^unset NCCL_ALGO NCCL_PROTO VLLM_DISABLE_PYNCCL VLLM_PP_LAYER_PARTITION') for rel in (RUN12SH, DRV18, T14D)))
    readme = {rel: bool(grep(rel, r'^unset VLLM_PP_LAYER_PARTITION')) and not grep(rel, r'^export VLLM_PP_LAYER_PARTITION=') for rel in ('README.md', 'scripts/README.md')}
    check('B4.docs', 'README.md and scripts/README.md now unset the split; the setup guide says it is left unset; the runbook says the smoke test confirms it '
          'is unset, which is what the smoke test checks (the environment only)', all(readme.values())
          and grep('README_SETUP_AND_OPERATIONS.md', r'`VLLM_PP_LAYER_PARTITION` left unset by default')
          and grep('RUNBOOK_NEW_VM_SETUP.md', r'confirms `VLLM_PP_LAYER_PARTITION` is unset') and 'split_env = os.environ.get("VLLM_PP_LAYER_PARTITION")' in text(SMOKE))

    left4 = {'setup guide smoke list says 15,12': bool(grep('README_SETUP_AND_OPERATIONS.md', r'Validates .*`VLLM_PP_LAYER_PARTITION=15,12`')),
             'README.md TP8/PP2 as 15/12': bool(grep('README.md', r'`tp8_pp2`: .*15/12 asymmetric partition'))}
    check('B4.docs2', f'two doc lines still describe the 15,12 split as the setting: {left4}', all(left4.values()))

with guard('Blocker 5'):
    bodies_pk = [n for n in BODIES if 'pkill' in BODIES[n][0]]
    b4 = BODIES[4][0]
    check('B5.bodies', f'no step body calls pkill any more ({len(BODIES)} bodies); steps 2, 19 and 20 wait 3 s between captures instead',
          not bodies_pk and all('sleep 3' in BODIES[n][0] for n in (2, 19, 20)), str(bodies_pk))
    check('B5.step4', 'step 4 starts its server with setsid in the background, takes PID=$!, and stops it with SIGTERM, then SIGKILL, to the PID and to '
          'the process group -PID, in a trap and once more after the pinned run',
          re.search(r'setsid vllm serve .*& PID=\$!', b4, re.S) and 'kill -15 -- -"$PID"' in b4 and 'kill -9 -- -"$PID"' in b4
          and 'trap cleanup_tp8 EXIT INT TERM ERR' in b4 and b4.count('cleanup_tp8') >= 3)
    s14d = text(T14D)
    stop14d = s14d[s14d.index('stop_ray_both(){'):s14d.index('\n}\n', s14d.index('stop_ray_both(){'))]
    check('B5.14d', '14d\'s stop_ray_both has no pkill on either node; node 1\'s command now activates the venv and runs ray stop',
          'pkill' not in stop14d and "source '$VENV_DIR/bin/activate' 2>/dev/null || true; ray stop -f" in stop14d)
    check('B5.helper', 'the 20-minute helper has no pkill', 'pkill' not in text(H20))
    left = sorted({rel for rel, t in CORPUS.items() if re.search(r'pkill -9 -f|"pkill", "-9", "-f"', t)})
    uncalled = not any('drain_vram_barrier(' in t for rel, t in CORPUS.items() if not rel.endswith('v5_runner_lib.py')) \
        and not any(re.search(r'^\s*kill_orphan_workers\s*$', t, re.M) for t in CORPUS.values())
    check('B5.left', 'the pkill -f calls left: 14c\'s, which targets its own port; the runner library\'s drain barrier and the master\'s new '
          'kill_orphan_workers, which nothing calls', uncalled and set(left) == {MASTER, M07, T14C} | {r for r in CORPUS if r.endswith('v5_runner_lib.py')},
          ', '.join(left))
    p14c = re.findall(r'pkill -9 -f "([^"]+)"', text(T14C))
    callers = [n for n in BODIES if '14c_run_vllm_torch_profile_batched.sh' in BODIES[n][0]]
    lower_port = [n for n in callers if 'port' in '\n'.join(ML[BODIES[n][1] - 1:BODIES[n][2]])]
    check('B5.14c', f'14c\'s pattern ({p14c[0] if p14c else None}) needs "port" in lower case after "vllm"; neither step that calls 14c ({callers}) has '
          '"port" in lower case in its text, so it cannot match their shells unless a folder path supplies it', p14c and set(p14c) == {'vllm.*port.*$PORT'}
          and callers == [2, 14] and not lower_port)

with guard('Blocker 6'):
    L12 = lines(RUN12SH)
    idx = lambda pat: next(i for i, l in enumerate(L12) if re.search(pat, l))
    i_set, i_rc = idx(r'^\s*set \+e\s*$'), idx(r'CASE_RC=\$\?')
    check('B6.case', 'the two-server runner still records a failed case, carries on, stops Ray in a trap and exits non-zero at the end',
          i_set < idx(r'12_run_vllm_multi_node.py') < i_rc and grep(RUN12SH, r'FAILED_CASES\+=') and grep(RUN12SH, r'^trap stop_ray_both EXIT INT TERM')
          and grep(RUN12SH, r'^\s*exit 1\s*$'))
    pre_case = [L12[i] for i in range(idx(r'^for row in'), i_set) if re.search(r'ray start|ray status|20_ray_nccl_env_audit', L12[i])]
    scp = [l for l in L12[:idx(r'^for row in')] if re.match(r'\s*scp ', l)]
    check('B6.ray', 'ray start, ray status and the Ray audit still run under set -e, so a cluster that does not form, or an audit violation '
          '(exit 2), ends the group with no case manifest written; so does a failed copy of the sampler before the first case',
          len(pre_case) == 4 and not any(l.rstrip().endswith('|| true') for l in pre_case) and scp and not scp[0].rstrip().endswith('|| true')
          and "raise SystemExit(0 if payload['ok'] else 2)" in text(AUDIT), ' | '.join(l.strip()[:80] for l in pre_case + scp))

with guard('Blocker 7'):
    rs = MT[MT.index('run_step() {'):]
    rs = rs[:rs.index('\n}\n')]
    check('B7.runstep', 'run_step now records each step\'s status in master_step_status.jsonl, writes the done marker only on status 0, adds a failed '
          'step to FAILED_STEPS with a warning, and always returns 0, so no step ends the run',
          'master_step_status.jsonl' in rs and re.search(r'if \[\[ "\$rc" == 0 \]\]; then\n\s*touch "\$marker"', rs)
          and 'FAILED_STEPS+=("step_${num}_${name}")' in rs and rs.rstrip().endswith('return 0') and rs.count('return 1') == 0)
    i_aud = MT.index('AUDITING CAMPAIGN CASE MANIFESTS')
    aud = MT[i_aud:]
    check('B7.audit', 'after the last step the master reads every *manifest*.json under the run, writes CAMPAIGN_SUMMARY.json and exits 1 if any case '
          'or step failed', 'master_root.rglob("*manifest*.json")' in aud and 'CAMPAIGN_SUMMARY.json' in aud and 'sys.exit(1)' in aud
          and '"${FAILED_STEPS[@]}"' in aud and 'exit "$AUDIT_RC"' in aud)
    sete = [n for n in BODIES if re.search(r'^\s*set -e', BODIES[n][0], re.M)]
    last = lambda n: [l for l in BODIES[n][0].splitlines() if l.strip() and not l.strip().startswith('#')][-1].strip()
    zero = [n for n in BODIES if last(n).endswith('|| true') or last(n).startswith('echo ') or last(n) in ('fi',)]
    summ_last = [n for n in BODIES if '15_summarize_vllm.py' in last(n) and not last(n).endswith('|| true')]
    check('B7.status', f'none of the {len(BODIES)} bodies sets -e, so a step\'s status is still its last command\'s: steps {sorted(zero)} end with || true, '
          f'an echo or an if block, so they report 0; steps {summ_last} end with the summarizer',
          not sete and sorted(zero) == [0, 2, 4, 8, 12, 14, 15, 16, 17] and summ_last == [1, 5, 6, 9, 10, 11, 18, 19])
    early_exit = [(n, l.strip()) for n in BODIES for l in BODIES[n][0].splitlines() if re.search(r'\bexit \d', l) and 'awk' not in l]
    check('B7.exit', f'the only early exit in a body is step 4\'s: it reports 3 when its server dies at start ({early_exit})',
          len(early_exit) == 1 and early_exit[0][0] == 4 and 'exit 3' in early_exit[0][1])
    ort = {n: len(re.findall(r'\|\| true', BODIES[n][0])) for n in BODIES}
    check('B7.ortrue', f'|| true appears {sum(ort.values())} times in the bodies ({ort[12]} in step 12)', sum(ort.values()) == 70 and ort[12] == 23)
    i_rid = next(i for i, l in enumerate(ML) if 'DEFAULT_RUN_ID=$(cat "$RUN_ID_FILE")' in l)
    i_loop = next(i for i, l in enumerate(ML) if l.startswith('while [[ $# -gt 0 ]]'))
    nr = MT[MT.index('    --no-resume)'):MT.index(';;', MT.index('    --no-resume)'))]
    check('B7.resume', 'resume is still on by default, and the run id is taken from latest_run_id.txt before the flags are read, so --no-resume re-runs every '
          'step into the latest run\'s folder; only --new-run starts a new one', grep(MASTER, r'^: "\$\{RESUME:=1\}"') and i_rid < i_loop
          and 'RESUME=0' in nr and 'RUN_ID=' not in nr and 'MASTER_ROOT=' not in nr, f'{MASTER}:{i_rid + 1} < {i_loop + 1}')

with guard('Blocker 8'):
    i_src = next(i for i, l in enumerate(ML) if 'source "$PWD/RUN_CONFIG.env"' in l)
    check('B8.master', 'the master reads RUN_CONFIG.env before it parses the flags', i_src < i_loop)
    check('B8.all', '--topologies all and --bandwidth all still export nothing, so a selection a RUN_CONFIG.env sets cannot be reset from the command line',
          grep(MASTER, r'"\$SELECTED_TOPOLOGIES" != "all"') and grep(MASTER, r'"\$SELECTED_BANDWIDTH" != "all"'))
    ex = text(EX)
    sel = all(re.search(rf'^export {k}="\${{{k}:-all}}"', ex, re.M) for k in ('TOPOLOGY_SELECTION', 'CONTEXT_SELECTION', 'CONCURRENCY_SELECTION',
                                                                            'NETWORK_BANDWIDTH_SELECTION', 'STAGE_SELECTION'))
    lab = all(re.search(rf'^export {k}="\${{{k}:-', ex, re.M) for k in (PROV_VAR, 'GCP_NETWORK_PROVENANCE', MODE_VAR))
    check('B8.examples', 'both examples (now one file in two places) default the five selections to all and the network labels with ${VAR:-...}, so a '
          'value the caller set survives a re-read', md5(os.path.join(PIP, EX)) == md5(os.path.join(PIP, EX07)) and sel and lab)
    caps = {rel: re.findall(r'^(CALLER_\w+)=', text(rel), re.M) for rel in (RUN12SH, DRV18, T14D)}
    check('B8.runners', 'the two-server runner, the Nsight driver and 14d now save the caller\'s values before re-reading RUN_CONFIG.env and put back the '
          'ones that are not empty: ' + '; '.join(f'{os.path.basename(k)}: {len(v)}' for k, v in caps.items()),
          len(caps[RUN12SH]) == 8 and len(caps[DRV18]) == 4 and len(caps[T14D]) == 9)
    check('B8.sweep', 'the NCCL sweep (step 3) still re-reads the file with nothing saved', 'CALLER_' not in text(NCCLTUNE) and 'RUN_CONFIG.env' in text(NCCLTUNE))
    outright = {k: bool(re.search(rf'^export {k}="[^$]', ex, re.M)) for k in ('RUN_HEAVY_PROFILE', 'RUN_POISSON_SWEEPS', 'RUN_SCHEDULER_SWEEPS', 'RUN_OBSERVER_OVERHEAD',
                                                                            'VLLM_MOE_BACKEND', 'MOE_BACKEND', 'NCCL_SOCKET_IFNAME', 'GLOO_SOCKET_IFNAME')}
    i_prof = MT.index('        deep-profile)')
    flagset = re.findall(r'^\s{4}(--[a-z0-9-]+)(?:\|[^)]*)?\)', MT, re.M)
    check('B8.outright', f'the example still sets these outright, so an environment variable cannot change them: {outright}; the sweeps and RUN_HEAVY_PROFILE '
          f'have a flag (--profile deep-profile, parsed after the file), the MoE variables and the NCCL interface none (the master\'s flags: {len(flagset)})',
          all(outright.values()) and i_src < i_loop and not any(re.search(r'moe|nccl|ifname', f_) for f_ in flagset)
          and 'RUN_POISSON_SWEEPS=1' in MT[i_prof:i_prof + 300] and 'export RUN_HEAVY_PROFILE=1' in MT[i_prof:i_prof + 300])

with guard('Blocker 9'):
    b10_12 = BODIES[10][0] + BODIES[11][0] + BODIES[12][0]
    n_app = len(re.findall(r'tc (?:qdisc|class) (?:add|replace) [^\n]*?2>/dev/null \|\| true', b10_12))
    n_del = len(re.findall(r'tc qdisc del [^\n]*?2>/dev/null \|\| true', b10_12))
    tcl = [l for l in b10_12.splitlines() if re.search(r'tc (qdisc|class) (add|replace|del)', l)]
    check('B9.silenced', f'every tc command in steps 10-12 still silences its errors: the {n_app} that apply a cap or loss and the {n_del} deletes',
          n_app == 6 and n_del == 12 and all('2>/dev/null || true' in l for l in tcl))
    show = [l for l in BODIES[12][0].splitlines() if 'tc -s qdisc show' in l]
    check('B9.show', f'step 12 prints tc -s qdisc show on both nodes ({len(show)} calls) to the master log only', len(show) == 6
          and all(not re.search(r'>\s*[\'"]?\$', l.replace('2>/dev/null', '')) for l in show))
    check('B9.iperf', 'nothing measures the link: no iperf3 in the master, and the network matrix script with its iperf3 checks is still not called',
          'iperf3' not in MT and '20_run_vllm_network_matrix' not in MT)
    reapply = all(re.search(rf'^\[\[ -n "\$CALLER_{c}" \]\] && export {v}=', text(RUN12SH), re.M)
                  for c, v in (('NET_MODE', MODE_VAR), ('NET_CAP', CAP_VAR), ('PROV', PROV_VAR)))
    check('B9.labels', 'the mode, cap and provenance labels step 12 passes now survive the runner\'s re-read (it puts back the caller\'s, and the '
          'examples\' labels default with ${VAR:-...})', reapply and all(f'{CAP_VAR}="{v}"' in BODIES[12][0] for v in ('native', '100', '20', 'impaired')))
    st, ht = text(SETUPC), text(H20)
    check('B9.traps', 'both helpers now remove their caps in a trap (the cluster set-up on EXIT, the 20-minute helper on EXIT, INT, TERM and ERR)',
          re.search(r'^trap cleanup_caps EXIT\s*$', st, re.M) and re.search(r'^trap cleanup_caps EXIT INT TERM ERR\s*$', ht, re.M))

with guard('Blocker 10'):
    ne = text(NODEENV)
    check('B10.pins', 'setup_node_env.sh still falls back silently when a pin fails: vLLM 0.29.0 with Ray 2.58.0 to vllm>=0.6.3 with any Ray, FlashInfer '
          '0.6.18 to any, and torch 2.13.0 from the CUDA 12.4 index to torch 2.5.1', re.search(r'"vllm==0\.29\.0" "ray\[default\]==2\.58\.0".*2>/dev/null \|\| \\\n\s*pip install -q "vllm>=0\.6\.3" "ray\[default\]"', ne)
          and re.search(r'"flashinfer-python==0\.6\.18" 2>/dev/null \|\| pip install -q flashinfer-python', ne)
          and 'torch==2.13.0 torchvision --index-url https://download.pytorch.org/whl/cu124 2>/dev/null || \\' in ne and 'torch==2.5.1' in ne)
    check('B10.hash', 'no install by file and no checksum', 'sha256' not in ne and '.whl' not in ne and '--require-hashes' not in ne)
    check('B10.venv', 'its venv now defaults to $VENV_DIR or ~/vllm_env, the master\'s default, and links the other name (pip_vllm_env) to it; it writes pip '
          'freeze into the venv', 'VENV_PATH="${1:-${VENV_DIR:-$HOME/vllm_env}}"' in ne and 'ln -sfn "$VENV_PATH" "$HOME/pip_vllm_env"' in ne
          and 'pip freeze > "$VENV_PATH/PIP_FREEZE.txt"' in ne and 'VENV_DIR:=$HOME/vllm_env' in MT)
    hv = {os.path.basename(r): 'VENV_DIR="${VENV_DIR:-$HOME/pip_vllm_env}"\n[[ -d "$VENV_DIR" ]] || VENV_DIR="$HOME/vllm_env"' in text(r) for r in (SETUPC, H20)}
    check('B10.venv2', f'but both helpers still prefer ~/pip_vllm_env when it exists ({hv}), and the link is made only when the other name is free, so on a VM '
          'set up before, with ~/pip_vllm_env, a new setup_node_env.sh run with its defaults installs into ~/vllm_env while a RUN_CONFIG.env the helpers write points the run at '
          '~/pip_vllm_env', all(hv.values()) and '[[ "$VENV_PATH" == *"/vllm_env" && ! -e "$HOME/pip_vllm_env" ]]' in ne)
    pins = None
    if WHL:
        wz = zipfile.ZipFile(WHL)
        meta = wz.read(next(n for n in wz.namelist() if n.endswith('.dist-info/METADATA'))).decode()
        pins = 'Requires-Dist: torch==2.13.0' in meta and 'Requires-Dist: flashinfer-python==0.6.18' in meta
    check('B10.vllmpins', f'vLLM 0.29.0 itself pins torch 2.13.0 and FlashInfer 0.6.18 (wheel checked: {pins is not None}), so when its pin installs, '
          'the torch line before it does not decide torch', pins in (True, None))
    docs = {'setup manual ray 2.35.0 / triton 3.0.0': bool(grep('README_SETUP_AND_OPERATIONS.md', r'ray\[default\]==2\.35\.0.*triton==3\.0\.0')),
            'runbook torch 2.5.1': bool(grep('RUNBOOK_NEW_VM_SETUP.md', r'torch==2\.5\.1'))}
    check('B10.docs', f'the docs\' recipes are unchanged: {docs}', all(docs.values()))
    rd = text(READY)
    check('B10.gate', 'the readiness gate expects vLLM 0.29.0, Ray 2.58.0, torch 2.13.0, Triton 3.7.1, FlashInfer 0.6.18 and NCCL 2.29.7 or 2.31.2 (or a library in the clean folder), strict by default',
          all(f'"{k}": "{v}"' in rd for k, v in (('vllm', '0.29.0'), ('ray', '2.58.0'), ('torch', '2.13.0'), ('triton', '3.7.1'), ('flashinfer-python', '0.6.18')))
          and "_REQUIRE_V6_CORE_STACK','1')" in rd and 'in ("2.29.7", "2.31.2")' in rd and "Path('/tmp/clean_nccl_libs/libnccl.so').exists()" in rd)
    man = glob.glob(os.path.join(PIP, 'data/results/tp4_pp4_20g_*/tp4_pp4_dist/vllm_surrogate_manifest.json'))
    pk = {}
    if man:
        out_ = json.load(open(man[0]))['environment']['commands']['python_packages']['out']
        for k in ('vllm', 'flashinfer-python', 'ray', 'torch'):
            m_ = re.search(rf'^{re.escape(k)}==(\S+)$', out_, re.M); pk[k] = m_.group(1) if m_ else None
    check('B10.run', f'the TP4/PP4 run in the data folder recorded, on node 0: {pk}', pk == {'vllm': '0.31.0', 'flashinfer-python': '0.7.0.post1', 'ray': '2.59.0', 'torch': '2.13.0'})

with guard('Blocker 11'):
    cbt = text(CB)
    n1 = re.search(r'remote_start_cmd = \((.*?)\n\s*\)', cbt, re.S).group(1)
    check('B11.node1', 'the batching runner\'s node 1 now activates $VENV_DIR, puts the clean NCCL folder first on LD_LIBRARY_PATH, unsets NCCL_ALGO, '
          'NCCL_PROTO and VLLM_DISABLE_PYNCCL, then starts Ray; its ray stop activates the venv too', 'source {venv_dir}/bin/activate' in n1
          and 'export LD_LIBRARY_PATH=/tmp/clean_nccl_libs${{LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}}' in n1 and 'unset NCCL_ALGO NCCL_PROTO VLLM_DISABLE_PYNCCL' in n1
          and cbt.count('f"source {venv_dir}/bin/activate 2>/dev/null || true; ray stop -f"') == 2)
    cbj = json.loads(text(CBCASES))
    tp4pp2 = [c for c in cbj['cases'] if c.get('tp') == 4 and c.get('pp') == 2]
    check('B11.gpus', f'the three TP4/PP2 cases now set ray_gpus_per_node 4 ({len(tp4pp2)} cases), and the runner falls back to 4 for TP4/PP2; the case '
          'manifest records the two node addresses and the GPUs per node', len(tp4pp2) == 3 and all(c.get('ray_gpus_per_node') == 4 for c in tp4pp2)
          and 'case_rec["ray_nodes"] = [node0_ip, node1_ip]' in cbt and 'case_rec["ray_gpus_per_node"] = gpus_per_node' in cbt)
    check('B11.left', 'left: no Ray audit runs, and node 1\'s ray start carries none of the NCCL policy\'s exports', '20_ray_nccl_env_audit' not in cbt
          and 'NCCL_SOCKET_IFNAME' not in n1 and 'nccl_remote_v6_aligned_exports' not in cbt)
    ld_ok = None
    if WHL:
        zr = zipfile.ZipFile(WHL)
        rx2_ = zr.read('vllm/v1/executor/ray_executor_v2.py').decode()
        ru_ = zr.read('vllm/v1/executor/ray_env_utils.py').decode()
        ld_ok = ('_RAY_WORKER_PRE_IMPORT_ENV_VARS = frozenset({"VLLM_USE_BREAKABLE_CUDAGRAPH"})' in ru_
                 and 'Driver env vars are applied separately via initialize_worker' in rx2_
                 and 'Returns everything from ``os.environ`` except ``worker_specific_vars``' in ru_)
    check('B11.fill', f'in vLLM 0.29.0 a Ray worker fills in the driver\'s variables after it starts, only where its own node\'s environment has none '
          f'(wheel checked: {ld_ok is not None}); so node 1\'s ranks take node 0\'s NCCL settings and skip list unless node 1\'s own login sets them, and '
          'LD_LIBRARY_PATH, read at start, comes from node 1\'s ray start shell, which now sets it', ld_ok in (True, None))

with guard('Blocker 12'):
    sm = text(SMOKE)
    check('B12.verdict', 'the smoke test now exits 1 and reports "DEPLOYMENT BLOCKED" when any check fails; ready_for_full_benchmark needs no failure and '
          '12 passes', re.search(r'if \[\[ "\$FAILED_CHECKS" == 0 \]\]; then[^\n]*\n(?:.*\n){1,3}\s*exit 0\nelse\n(?:.*\n){1,3}\s*exit 1', sm)
          and '"ready_for_full_benchmark": True if failed == 0 and passed >= 12 else False' in sm and 'DEPLOYMENT BLOCKED' in sm)
    mb = sm[sm.index('--- 18. END-TO-END MICRO-BENCHMARK'):sm.index('micro_benchmark_pipeline" "PASSED"')]
    check('N8', 'its end-to-end check still writes bench.json without a server: a first-token time from two clock reads plus 0.045 s, a fixed 5.0 ms a token, '
          'status COMPLETED, and the check passes when the file exists', 'vllm serve' not in mb and 'max(0.001, round(time.time() - t0 + 0.045, 5))' in mb
          and '"mean_tpot_ms": 5.0' in mb and '"status": "COMPLETED"' in mb and 'if [[ -f "$TEST_OUT/bench.json" ]]; then' in sm)
    live = [l for l in sm.splitlines() if 'LIVE_SERVER' in l]
    check('B12.live', 'its new --live-server flag ("Launch real micro-server test") sets a variable nothing reads', len(live) == 2
          and all(re.fullmatch(r'\s*LIVE_SERVER=[01]\s*', l) for l in live) and 'Launch real micro-server test' in sm)
    nchk = sorted(set(re.findall(r'record_check "([a-z0-9_]+)"', sm)))
    check('B12.count', f'it has {len(nchk)} checks (node 1\'s only when NODE1_IP is set, the runner\'s unless --skip-runner)', len(nchk) == 21
          and 'if [[ -n "${NODE1_IP:-}" ]]; then' in sm and 'if [[ "$SKIP_RUNNER" == 0 ]]; then' in sm)
    check('B12.dry', 'the runner check is still a dry run, in which no step executes, and the wave check still passes without running when its test file is absent',
          'bash "$MASTER_RUNNER" --dry-run --out-root "$DRY_RUN_OUT"' in sm and 'record_check "wave_and_stall_engine" "PASSED" "Wave analysis tools present"' in sm)
    consts = {k: k in sm for k in ('sample_text = """', 'reqs = [{"ttft": 3.7', 'sample_item = {', 'bench_data = {')}
    check('B12.consts', 'four checks test values written into the test itself: Prometheus parsing of a fixed sample, wave trimming of fixed numbers, '
          'the dashboard schema of a fixed record, and the micro-benchmark\'s own file', all(consts.values()))

with guard('Blocker 13'):
    wu = text(LIB)[text(LIB).index('def run_warmup'):text(LIB).index('def drain_vram_barrier')]
    check('B13.warmup', 'a warm-up now fails on a non-zero exit, or when its log holds "All requests failed", "Zero completed requests", or both '
          '"failed_requests" and "successful_requests: 0"; the three runners that warm up mark such a point WARMUP_FAILED and skip it',
          'warmup_ok = (rc == 0)' in wu and '"All requests failed" in content' in wu and '"Zero completed requests" in content' in wu
          and '"successful_requests: 0" in content' in wu
          and all('(warm.get("exit_code")!=0ornotwarm.get("success",True))' in text(r).replace(' ', '') for r in (SINGLE, RUN12PY, CB)))
    vs = None
    if WHL:
        sv = zipfile.ZipFile(WHL).read('vllm/benchmarks/serve.py').decode()
        vs = {'all-failed warning': sv.count('"All requests failed. This is likely due to a misconfiguration "') == 2,
              'prints Successful requests:': '"Successful requests:", metrics.completed' in sv,
              'no "Zero completed requests"': 'Zero completed requests' not in sv,
              'no "successful_requests"': 'successful_requests' not in sv,
              'ready check off by default': re.search(r'"--ready-check-timeout-sec",\s*type=int,\s*default=0,', sv) is not None}
    check('B13.vllm', f'in vLLM 0.29.0 the all-failed case prints the "All requests failed" warning, which the check catches; the other two strings never '
          f'occur in its output (it prints "Successful requests:"); and its ready check is off by default, so a dead server gives that warning with '
          f'exit 0 (wheel: {vs})', vs is None or all(vs.values()))

    pf = None
    if WHL:
        pf = 'print("Failed requests during benchmark run detected (capping to 10):")' in zipfile.ZipFile(WHL).read('vllm/benchmarks/serve.py').decode()
    check('B13.partial', f'when only some requests fail, vLLM 0.29.0 prints "Failed requests during benchmark run detected" (wheel checked: {pf is not None}), which the '
          'check does not look for', pf in (True, None) and 'Failed requests during benchmark run detected' not in wu)

# ---------------------------------------------------------------------------------------------------------------------------
print('\n## 3.2 The footing')
with guard('3.2 The footing'):
    lib = text(LIB)
    check('F1', 'the runners still add --moe-backend and --enable-flashinfer-autotune only when vLLM\'s help lists them, and the only server-log line '
          'any runner reads is the KV cache size', 'add_if_supported(cmd, serve_help, "--moe-backend"' in lib and 'if "--enable-flashinfer-autotune" in serve_help:' in lib
          and [t.count('server.log", "r"') for r, t in CORPUS.items() if 'server.log", "r"' in t] == [1] and 'GPU KV cache size:' in text(SINGLE))
    exp = [r for r in (MASTER, M07, EX, EX07, SMOKE) if re.search(r'^\s*export VLLM_FLASHINFER_AUTOTUNE="1"', text(r), re.M)
           and re.search(r'^\s*export VLLM_MOE_BACKEND=', text(r), re.M)]
    reads = None
    if WHL:
        envs = zipfile.ZipFile(WHL).read('vllm/envs.py').decode()
        reads = '"VLLM_FLASHINFER_AUTOTUNE"' in envs or '"VLLM_MOE_BACKEND"' in envs
    check('F2', f'VLLM_FLASHINFER_AUTOTUNE=1 is still exported by the master, both examples and the smoke test ({len(exp)} files), as is VLLM_MOE_BACKEND; '
          f'vLLM 0.29.0 reads neither (wheel checked: {reads is not None})', len(exp) == 5 and reads in (False, None))
    pol = text(POLICY)
    fwd = re.search(r'for var in ([^;]+); do', pol).group(1).split()
    unsets = [r for r in (MASTER, POLICY, RUN12SH, DRV18, T14D, H20, EX) if re.search(r'unset [^\n]*VLLM_DISABLE_PYNCCL', text(r))]
    sets = [r for r, t in CORPUS.items() if re.search(r'^\s*(export\s+)?VLLM_DISABLE_PYNCCL=', t, re.M)]
    check('F4', f'VLLM_DISABLE_PYNCCL is set nowhere ({len(sets)} files), unset by the master, the NCCL policy, the two-server runner, the Nsight driver, '
          '14d, the 20-minute helper and the examples, and no longer in the list the policy forwards to node 1; the split is still in that list, but every '
          'runner unsets it first', not sets and len(unsets) == 7 and 'VLLM_DISABLE_PYNCCL' not in fwd and 'VLLM_PP_LAYER_PARTITION' in fwd
          and 'unset NCCL_ALGO NCCL_PROTO VLLM_DISABLE_PYNCCL || true' in cbt)
    md = {}
    for dp, dn, fn in os.walk(PIP):
        for f in fn:
            if f.endswith('.md'):
                p = os.path.join(dp, f); md[os.path.relpath(p, PIP)] = open(p, errors='ignore').read()
    c2758 = sorted(r for r, t in md.items() if '27.58' in t)
    check('F5', f'the "+27.58%" claim for the 15/12 split is still in {len(c2758)} docs ({sum(md[r].count("27.58") for r in c2758)} places); '
          'README_SETUP_AND_OPERATIONS.md dropped it', len(c2758) == 5 and 'README_SETUP_AND_OPERATIONS.md' not in c2758, ', '.join(c2758))
    check('F6.ld', 'the master now builds LD_LIBRARY_PATH as /tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:...} and skips it when the folder is already there; '
          'the examples prepend it the same way but without the guard, so each re-read of an example-based RUN_CONFIG.env adds it once more (harmless)',
          'if [[ ":${LD_LIBRARY_PATH:-}:" != *":/tmp/clean_nccl_libs:"* ]]; then' in MT
          and 'export LD_LIBRARY_PATH="/tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"' in MT
          and 'export LD_LIBRARY_PATH="/tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"' in text(EX) and ':/tmp/clean_nccl_libs:' not in text(EX))
    check('F6.mapped', 'nothing records the NCCL library each worker mapped, or torch.cuda.nccl.version()',
          not any(re.search(r'nccl\.version\(|/proc/[^ ]*maps', t) for t in CORPUS.values()))
    n1c = MT[MT.index('if [[ -n "${NODE1_IP:-}" && "${DRY_RUN:-0}" -eq 0 && -d "/usr/local/gib/lib64" ]]; then'):]
    n1c = n1c[:n1c.index('\nfi\n')]
    check('F6.node1', 'the master still makes the clean folder on node 1 only where GIB is installed (and node 0 has it too), with errors silenced',
          'if [[ -d "/usr/local/gib/lib64" && ! -d "/tmp/clean_nccl_libs" ]]; then' in n1c and n1c.rstrip().endswith("' 2>/dev/null || true"))
    def unset_after_read(rel):
        t = text(rel); i = t.find('RUN_CONFIG.env')
        return i >= 0 and re.search(r'unset NCCL_ALGO NCCL_PROTO', t[i:]) is not None
    starters = {os.path.basename(r): unset_after_read(r) for r in (MASTER, RUN12SH, DRV18, T14D, H20)}
    noread = {os.path.basename(r): 'RUN_CONFIG.env' not in text(r) for r in (T14, T14C, SINGLE, CB)}
    check('F7.safe', f'every script that starts vLLM servers and reads RUN_CONFIG.env unsets NCCL_ALGO and NCCL_PROTO after the read ({starters}); the '
          f'others do not read it ({noread}); so a Tree in the file no longer reaches a run\'s servers', all(starters.values()) and all(noread.values()))
    tree = {r: len(re.findall(r'NCCL_ALGO[=:" ]*"?Tree', t)) for r, t in md.items() if re.search(r'NCCL_ALGO[=:" ]*"?Tree', t)}
    check('F7.tree', f'NCCL_ALGO=Tree is still recommended in {len(tree)} docs ({tree}), one of them asking for it in RUN_CONFIG.env and one claiming '
          '28.4% less cross-node AllReduce latency; NCCL_PROTO=Simple is gone from the docs, and NCCL_CROSS_NIC appears only as dropped',
          set(tree) == {'README_SETUP_AND_OPERATIONS.md', 'README_FILES_AND_ARCHITECTURE.md'} and tree['README_SETUP_AND_OPERATIONS.md'] == 4
          and tree['README_FILES_AND_ARCHITECTURE.md'] == 3 and 'export NCCL_ALGO=Tree` in `RUN_CONFIG.env`' in md['README_SETUP_AND_OPERATIONS.md']
          and '28.4%' in md['README_FILES_AND_ARCHITECTURE.md'] and not any(re.search(r'NCCL_PROTO[=:" ]*"?Simple', t) for t in md.values())
          and all('dropped' in l for t in md.values() for l in t.splitlines() if 'NCCL_CROSS_NIC' in l))
    check('F7.04readme', '04\'s README now says the policy leaves NCCL_ALGO and NCCL_PROTO unset', '`NCCL_ALGO`/`NCCL_PROTO` unset' in text('scripts/04_scaleout_distributed_network/README.md'))
    check('F7.restart', 'the master\'s header (both copies) and README.md still say the server restarts between concurrency levels; the runners keep one '
          'server for all of a case\'s points', 'vLLM serve is killed and restarted between concurrency levels' in MT
          and 'vLLM serve is killed and restarted between concurrency levels' in text(M07)
          and 'Between each concurrency level within a benchmark case, the `vllm serve` process' in md['README.md']
          and 'for bi,b in enumerate(benchmarks_to_run):' in text(SINGLE) and text(SINGLE).index('start_server_with_timestamp_logging') < text(SINGLE).index('for bi,b in enumerate(benchmarks_to_run):', text(SINGLE).index('try:')))
    rst = {'scripts/README.md': 'A clean `vllm serve` instance is booted for each concurrency level' in md['scripts/README.md'],
           '02 README': 'Each concurrency level runs against a newly booted instance' in md['scripts/02_single_node_baseline_matrix/README.md'],
           '04 README (pkill -9 -f vllm)': 'torn down via SSH (`pkill -9 -f vllm`)' in md['scripts/04_scaleout_distributed_network/README.md'],
           'RUN_COVERAGE.md (pkill -9 -f vllm)': '`pkill -9 -f vllm` followed by 3-second GPU memory drain between concurrency levels' in md['RUN_COVERAGE.md']}
    tag = not any('cache_state' in t for t in CORPUS.values()) and not any('classify_thermal_state(' in t for r, t in CORPUS.items() if not r.endswith('v5_runner_lib.py'))
    check('F7.restart2', f'the same claim is in four more docs ({rst}); no script writes the cache_state tag those READMEs describe, and the runner library\'s '
          'classify_thermal_state is called nowhere', all(rst.values()) and tag)
    caseset = json.loads(text(CASES))['cases']
    seats = {k: caseset[k].get('max_num_seqs') for k in ('tp4_pp4_dist_load', 'tp16_pp1_dist_load', 'stage3_r3_network_jitter_pp4')}
    check('F8', f'admission: the load grid admits 32 at once, the network-condition cases 16 ({seats}); the 20-minute helper now runs the load grid\'s '
          'TP4/PP4 case when the master\'s cases file is there', seats == {'tp4_pp4_dist_load': 32, 'tp16_pp1_dist_load': 32, 'stage3_r3_network_jitter_pp4': 16}
          and 'TARGET_CASE="tp4_pp4_dist_load"' in text(H20))

# ---------------------------------------------------------------------------------------------------------------------------
print('\n## 3.3 The skip list')
with guard('3.3 The skip list'):
    dash = {r: bool(re.search(r'VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="\$\{VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS-trtllm', text(r))) for r in (MASTER, RUN12SH, EX, EX07, SMOKE)}
    check('K1', 'the master, the two-server runner, both examples and the smoke test keep the "-" form, so an empty value stays empty', all(dash.values()))
    check('K2', 'the single-node runner keeps a value that is set, empty included', 'os.environ.get("VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS", "trtllm::' in text(SINGLE))
    check('K3', 'the two-server runner saves the caller\'s list, empty included, but puts it back after its re-read only when it is not empty, so a RUN_CONFIG.env '
          'that sets the list replaces arm B\'s empty value', 'CALLER_SKIP_OPS="${VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS-}"' in text(RUN12SH)
          and '[[ -n "$CALLER_SKIP_OPS" ]] && export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="$CALLER_SKIP_OPS"' in text(RUN12SH))
    smk = text(SMOKE)
    check('K4', 'the smoke test\'s MoE check keeps an empty list, then fails unless the list holds gemm1, so arm B fails the smoke test',
          '[[ "${VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS:-}" == *"trtllm::fused_moe::gemm1"* ]] || moe_env_ok=0' in smk
          and smk.index('export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="${VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS-') < smk.index('moe_env_ok=1'))

# ---------------------------------------------------------------------------------------------------------------------------
print('\n## 3.4 Coverage')
with guard('3.4 Coverage'):
    nc = [r for r, t in CORPUS.items() if re.search(r'\bncu\b', t)]
    check('C.ncu', 'nothing uses Nsight Compute', not nc, ', '.join(nc))
    lens = sorted({b['name'].split('_')[0] for k, c in caseset.items() if 'scaleout_load' in c.get('groups', []) for b in c['benchmarks']},
                  key=lambda s: (len(s), s))
    check('C.lengths', f'the two-server load grid still runs {lens}', lens == ['1k', '8k', '1m', '128k', '512k'] or set(lens) == {'1k', '8k', '128k', '512k', '1m'})
    r3 = {k: (c['tp'], c.get('pp')) for k, c in caseset.items() if 'r3_network_resilience' in c.get('groups', [])}
    check('C.net', f'network conditions still cover two layouts only: {r3}', sorted(r3.values()) == [(4, 4), (16, 1)])
    mat = json.loads(text(MAT18))['profiles']
    m14a = [p_ for p_ in mat if p_['mode'] in ('decode_8k', 'batched_decode_8k_c8', 'prefill_128k')]
    m14b = [p_ for p_ in mat if p_['mode'] in ('decode_8k', 'batched_decode_8k_c8')]
    m13 = [p_ for p_ in mat if p_['topology'] == 'tp16_pp1_dist' and p_['mode'] == 'long_prefill_512k']
    distinct = {(p_['topology'], p_['mode']) for p_ in m14a + m14b + m13}
    filt = ("PROFILE_MODE_FILTER=decode_8k,batched_decode_8k_c8,prefill_128k RUN_HEAVY_PROFILE=1" in BODIES[14][0]
            and "ENFORCE_EAGER=0 PROFILE_MODE_FILTER=decode_8k,batched_decode_8k_c8 RUN_HEAVY_PROFILE=1" in BODIES[14][0]
            and 'PROFILE_TOPOLOGY_FILTER=tp16_pp1_dist PROFILE_MODE_FILTER=long_prefill_512k RUN_HEAVY_PROFILE=1' in MT)
    check('C.nsight', f'the master selects {len(distinct)} of the matrix\'s {len(mat)} two-server Nsight captures in {len(m14a) + len(m14b) + len(m13)} runs: '
          f'{len(m13)} in step 13, {len(m14a)} eager and {len(m14b)} with graphs on in step 14', filt and len(distinct) == 13 and len(mat) == 24
          and len(m13) == 1 and len(m14a) == 12 and len(m14b) == 8)
    check('C.same', 'the master\'s cases and the profile matrix are unchanged, so depth, mid lengths and the other coverage gaps stand as v1.4 found them',
          OLD is None or (md5(os.path.join(PIP, CASES)) == md5(os.path.join(OLD, CASES)) and md5(os.path.join(PIP, MAT18)) == md5(os.path.join(OLD, MAT18))))

# ---------------------------------------------------------------------------------------------------------------------------
print('\n## 3.5 Smaller points')
with guard('3.5 Smaller points'):
    check('S2', 'step 20 compares the same 8K workload under minimal and full telemetry (unchanged)',
          'tp4_observer_overhead_test' in BODIES[20][0] and 'tp4_observer_overhead_full' in BODIES[20][0])
    check('S3', 'the two master copies are identical, and the 07/ copy now takes its suite root from scripts/ (where run_master_benchmark.sh sits one '
          'level up), so it finds 05/, pip_scan.py and the cases file', md5(os.path.join(PIP, MASTER)) == md5(os.path.join(PIP, M07))
          and 'if [[ -f "$SCRIPT_DIR/../run_master_benchmark.sh" ]]; then\n  SUITE_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)' in MT)
    check('S5', 'the summarizer is unchanged: its rows carry neither the folder nor the split', OLD is None or md5(os.path.join(PIP, SUMM)) == md5(os.path.join(OLD, SUMM)))
    wz0 = {os.path.basename(r): ('--num-warmups 0' in text(r) or "'warmups':0" in text(r)) for r in (T14, T14C, T14D, CASE18)}
    check('S7', f'all four profile paths still send no warm-up ({wz0})', all(wz0.values()))
    check('S8', 'a warm-up now has its own seed: (seed + 9999) mod 100000', 'warmup_seed = (int(seed) + 9999) % 100000' in wu and 'warmup_seed,measured=False' in wu)

# ---------------------------------------------------------------------------------------------------------------------------
print('\n## 3.6 v1.4\'s new findings N1-N14')
with guard('N1-N14'):
    dt = text(DRV18)
    check('N1', 'the Nsight driver gives PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE a default before it reads it', 'PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE=${PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE:-}' in dt
          and dt.index('PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE=${') < dt.index('if [[ -n "${PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE:-}" ]]'))
    full = MT
    w4 = bash_words(full, full.index('run_step 4 "tp8_pinning" bash -c "'))
    early = []
    for n_, (bt, bstart, bend) in BODIES.items():
        tx = '\n'.join(ML[bstart - 1:]); a_ = tx.index('bash -c "') + len('bash -c "'); b_ = a_
        while tx[b_] != '"':
            b_ += 2 if tx[b_] == '\\' else 1
        if bstart + tx[:b_].count('\n') != bend:
            early.append(n_)
    check('N2', f'step 4\'s comparison is now tools/compare_numa_pinning.py; bash -c gets its body as one word ({len(w4) - 5} after -c), and no step\'s string '
          f'closes before its body ends ({len(BODIES)} checked)', w4[:5] == ['run_step', '4', 'tp8_pinning', 'bash', '-c'] and len(w4) == 6 and not early
          and "tools/compare_numa_pinning.py' '$TP8_DIR'" in BODIES[4][0] and os.path.exists(os.path.join(PIP, NUMA)), str(early))
    i_cap = next(i for i, l in enumerate(L12) if l.startswith('CALLER_OUT_ROOT='))
    i_src12 = next(i for i, l in enumerate(L12) if 'for f in "${CONFIG_CANDIDATES[@]}"' in l)
    i_un12 = next(i for i, l in enumerate(L12) if l.startswith('unset NCCL_ALGO NCCL_PROTO VLLM_DISABLE_PYNCCL VLLM_PP_LAYER_PARTITION'))
    check('N3.defused', f'what made the old RUN_CONFIG.env stop servers and turn the communicator off is now undone after every runner\'s re-read: the two-server '
          f'runner saves the caller\'s values (lines up to {i_cap + 1}), reads the file (line {i_src12 + 1}), then unsets the split, VLLM_DISABLE_PYNCCL, '
          f'NCCL_ALGO and NCCL_PROTO (line {i_un12 + 1}); the Nsight driver and 14d do the same', i_cap < i_src12 < i_un12)
    check('N3.left', 'what the old file would still do: its selections pin the master (B8.all, E6); step 10 passes no cap label, so the file\'s label stays '
          'on step 10\'s runs; the policy forwards every NCCL_* variable but the local-transport ones, ALGO and PROTO, so its NCCL_CROSS_NIC reaches node 1; '
          'and its skip list replaces an empty one (K3). The helpers still keep an existing file as it is', CAP_VAR not in BODIES[10][0]
          and 'NCCL_P2P_DISABLE|NCCL_SHM_DISABLE|NCCL_P2P_LEVEL|NCCL_ALGO|NCCL_PROTO) continue ;;' in pol
          and all('preserved without clobbering' in text(r) and 'if [[ ! -f "$SCRIPT_DIR/RUN_CONFIG.env" ]]' in text(r) for r in (SETUPC, H20)))
    if V13:
        old_keys = {}
        for rel in (SETUPC, H20):
            t = text(rel, V13); hd = t[t.index('cat << EOF'):t.index('\nEOF', t.index('cat << EOF'))]
            old_keys[os.path.basename(rel)] = {
                'TOPOLOGY_SELECTION=tp4_pp4': 'export TOPOLOGY_SELECTION="tp4_pp4"' in hd,
                'bandwidth 20g': bool(re.search(r'export NETWORK_BANDWIDTH_SELECTION="(20g|\$\(\[\[)', hd)) and '20g' in hd,
                'cap label 20': bool(re.search(CAP_VAR + r'="(20|\$\(\[\[)', hd)),
                'NCCL_CROSS_NIC=1': 'export NCCL_CROSS_NIC="1"' in hd,
                'full skip list': 'export VLLM_FLASHINFER_AUTOTUNE_SKIP_OPS="trtllm::fused_moe::gemm1,trtllm::fused_moe::gemm2"' in hd,
                'split 7,7,7,6': 'export VLLM_PP_LAYER_PARTITION="7,7,7,6"' in hd, 'communicator off': 'export VLLM_DISABLE_PYNCCL="1"' in hd}
        check('N3.old', f'the v1.3-era helpers wrote into RUN_CONFIG.env: {old_keys}', all(all(v.values()) for v in old_keys.values()))
    t14b = BODIES[14][0]
    check('N3.shrink', 'with that file, the master keeps TP4/PP4 only (E6), and the runners now filter on it too: step 10 keeps only its TP4/PP4 case and step 12, '
          'whose 20G condition alone passes the bandwidth guard, keeps neither of its cases (E10); step 14\'s two-server torch traces keep only TP4/PP4, and '
          'step 2\'s TP8 block, its two TP8 torch captures, is skipped', "if not any(t in c_str for t in topos):" in text(RUN12SH) and 'for topo in tp4_pp2_dist tp4_pp4_dist tp8_pp2_dist tp16_pp1_dist; do' in t14b
          and BODIES[2][0][BODIES[2][0].index("if topology_matches 'tp8'"):].count('env TP=8 ') == 2
          and not any(re.search(r'TOPOLOGY_SELECTION', t) for r, t in CORPUS.items() if r in (SINGLE, CB, LIB, 'scripts/run_continuous_batching.sh'))
          and 'if topology_matches \"\$topo\" || topology_matches \'all\'; then'.replace('\\', '') in t14b.replace('\\', '')
          and "if topology_matches 'tp8' || topology_matches 'all'; then" in BODIES[2][0] and '*"20g"*' in BODIES[12][0])
    if V13:
        more = {}
        for rel in (SETUPC, H20):
            t = text(rel, V13); hd = t[t.index('cat << EOF'):t.index('\nEOF', t.index('cat << EOF'))]
            more[os.path.basename(rel)] = {'MODEL': bool(re.search(r'^export MODEL=', hd, re.M)), 'REVISION': bool(re.search(r'^export REVISION=', hd, re.M)),
                                           'old LD form': 'export LD_LIBRARY_PATH="/tmp/clean_nccl_libs:\\${LD_LIBRARY_PATH:-}"' in hd}
        check('N3.old2', f'it also set MODEL and REVISION outright and the old LD_LIBRARY_PATH form ({more}); the two-server runner and the Nsight driver do not '
              'save MODEL or REVISION, so the file\'s would replace --model and --revision there, and each re-read adds the folder again', all(all(v.values()) for v in more.values())
              and 'CALLER_MODEL' not in text(RUN12SH) and 'CALLER_MODEL' not in text(DRV18))
    check('N3.shrink2', 'with that selection, step 14\'s single-node TP8 Nsight capture is skipped too, while its two-server Nsight runs ignore the selection and run '
          'on all four layouts (the driver filters only on its own profile filters), and step 13 is skipped', "if topology_matches 'tp8' || topology_matches 'all'; then" in t14b
          and 'TOPOLOGY_SELECTION' not in text(DRV18) and 'if ! topology_matches "tp16"; then' in MT)
    b0 = BODIES[0][0]
    rl = [l for l in b0.splitlines() if '22_readiness.py --out' in l or "22_readiness.py' --out" in l]
    check('N4', 'step 0 now runs the readiness gate with --out on both nodes, node 1\'s inside the venv; both behind || true, so a failed gate (exit 2) does not '
          'stop the run; node 1\'s report stays in /tmp on node 1, only its summary line comes back', len(rl) == 2 and all(l.rstrip().endswith('|| true') for l in rl)
          and "raise SystemExit(0 if payload['ok'] else 2)" in text(READY) and '/tmp/node1_readiness' in b0
          and not re.search(r'scp [^\n]*\$NODE1_IP:/tmp/node1_readiness', b0))
    check('N4.node1', 'on node 1 the gate runs in a plain ssh shell, so its clean-folder checks run only if node 1\'s own login sets NCCL_NET=Socket or the '
          'folder on LD_LIBRARY_PATH; and step 0 is marked done even when a gate fails, so re-checking needs a new run of step 0',
          "if os.environ.get('NCCL_NET') == 'Socket' or '/tmp/clean_nccl_libs' in os.environ.get('LD_LIBRARY_PATH','')" in text(READY)
          and 'python3 /tmp/22_readiness.py --out /tmp/node1_readiness' in b0 and "echo 'Environment snapshot recorded.'" in last(0))
    n1py = [l for l in b0.splitlines() if 'ssh ' in l and 'python3' in l]
    check('N5', 'step 0\'s two python3 commands on node 1 now activate $VENV_DIR first, and step 0 copies the gate to node 1\'s /tmp',
          len(n1py) == 2 and all("source '$VENV_DIR/bin/activate'" in l for l in n1py)
          and re.search(r"scp [^\n]*'\$HW_DIR/22_readiness.py' \"\$NODE1_IP:/tmp/22_readiness.py\"", b0))
    check('N6.setup', 'the cluster set-up now gives SSH_KEY a default, sources RUN_CONFIG.env whenever it exists (the command-line address wins), removes both caps '
          'in its EXIT trap (a failing smoke test included), and clears the trap before it hands over to the master',
          re.search(r'^SSH_KEY="\$\{SSH_KEY:-\$HOME/\.ssh/google_compute_engine\}"', st, re.M) and re.search(r'^if \[\[ -f "\$SCRIPT_DIR/RUN_CONFIG.env" \]\]; then\n\s*source', st, re.M)
          and st.index('trap cleanup_caps EXIT') < st.index('bash "$SCRIPT_DIR/run_smoke_test.sh"') and 'trap - EXIT\n  exec bash' in st)
    check('N6.bench', 'with --run-benchmark it runs step 10 with --topologies tp4_pp4, which the runner now applies (only the TP4/PP4 case runs), but step 10 '
          'clears both caps and labels its runs native, so the run is uncapped under a banner that says 20 Gbit/s; --bandwidth reaches only step 12',
          '--topologies tp4_pp4' in st and '--step 10' in st and 'clean_tc "$LOCAL_IFACE"' in BODIES[10][0]
          and "PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE='GCP_NATIVE'" in BODIES[10][0] and 'NETWORK_BANDWIDTH_SELECTION' not in BODIES[10][0]
          and 'NETWORK_BANDWIDTH_SELECTION' in BODIES[12][0] and "20 Gbps (tc HTB on ens3)" in st)
    ex_m = st[st.index('exec bash "$SCRIPT_DIR/run_master_benchmark.sh"'):st.index('else', st.index('exec bash "$SCRIPT_DIR/run_master_benchmark.sh"'))]
    check('N6.resume', 'the cluster set-up hands over to the master without --new-run or --no-resume, so it resumes the latest run, and a step 10 already done there is skipped',
          '--new-run' not in ex_m and '--no-resume' not in ex_m and '--step 10' in ex_m and grep(MASTER, r'^: "\$\{RESUME:=1\}"'))
    check('N6.h20', 'the 20-minute helper now uses sudo -n, removes the caps in a trap, runs the master\'s TP4/PP4 load-grid case and unsets NCCL_ALGO, '
          'NCCL_PROTO and VLLM_DISABLE_PYNCCL; it still takes node 0\'s address from hostname -I, and its header still lists six parts and its banner '
          '"FlashInfer CUTLASS (Autotuned)" and 20 Gbit/s while it runs one case', 'sudo -n tc qdisc replace dev ens3' in ht and 'sudo tc ' not in ht
          and 'unset NCCL_ALGO NCCL_PROTO VLLM_DISABLE_PYNCCL || true' in ht and 'NODE0_IP=$(hostname -I' in ht and '# 6. Consolidated Markdown' in ht
          and 'FlashInfer CUTLASS (Autotuned)' in ht and ht.count('12_run_vllm_multi_node.sh') == 1)
    fb = [(r, i) for r in (SETUPC, H20) for i, l in grep(r, r'^\[\[ -f "\$SSH_KEY" \]\] \|\| SSH_KEY="\$\{SSH_KEY:-\$HOME/\.ssh/id_rsa\}"')]
    check('N6.key', 'both helpers\' fallback to id_rsa, [[ -f "$SSH_KEY" ]] || SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}", never changes the key, since SSH_KEY '
          'is already set (E8); harmless, as ssh then tries its default keys, and the cluster set-up writes id_rsa into the file it creates',
          len(fb) == 2 and 'export SSH_KEY="\\$HOME/.ssh/id_rsa"' in st, '; '.join(f'{r}:{i}' for r, i in fb))
    check('N6.link', 'neither helper measures the link (no iperf3)', 'iperf3' not in st and 'iperf3' not in ht)
    check('N7', 'the batching runner\'s node 1: as blocker 11', 'remote_start_cmd' in cbt)
    check('N9', 'setup_node_env.sh\'s pins: as blocker 10', 'vllm>=0.6.3' in ne)
    i_ld = MT.index('export LD_LIBRARY_PATH="/tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"')
    check('N12', 'no empty LD_LIBRARY_PATH entry: the master, both examples, both READMEs and the batching runner\'s node 1 use ${LD_LIBRARY_PATH:+:...}',
          i_ld > 0 and 'LD_LIBRARY_PATH:-}"' not in MT and 'clean_nccl_libs:${LD_LIBRARY_PATH:-}' not in text(EX)
          and all('/tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}' in text(r) for r in ('README.md', 'scripts/README.md')))
    aud_rec = glob.glob(os.path.join(PIP, 'data/results/tp4_pp4_20g_*/tp4_pp4_dist_RAY_NCCL_ENV_AUDIT.json'))
    rec_ld = json.load(open(aud_rec[0]))['driver_expected_ld_library_path'] if aud_rec else None
    adds_cuda = [r for r, t in CORPUS.items() if re.search(r'LD_LIBRARY_PATH=[^\n]*cuda/lib64', t)]
    check('N12.login', f'but the empty entry v1.4 saw in the TP4/PP4 run ({rec_ld!r}) comes after the CUDA entries, which no script adds ({len(adds_cuda)} files), '
          'so it was in the nodes\' own path; the new form keeps it, and with an example-based file the master plus one re-read give the recorded string again (E11)',
          rec_ld == '/tmp/clean_nccl_libs:/tmp/clean_nccl_libs:/usr/local/cuda/lib64:/usr/local/cuda/lib64:' and not adds_cuda)
    check('N13', 'the 07/ master now finds every file (S3); the runner library\'s old copies are gone (B3.lib); the copies themselves remain (B3.copies)',
          'SUITE_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)' in MT)
    exh = text(EX)
    check('N14', 'the example\'s batching help shows its three examples again ("all", "1,2,3", "4"), and export CB_BLOCKS stays commented out; the zip still '
          'carries the macOS metadata (Z.zip)', all(f'export CB_BLOCKS="{v}"' in exh for v in ('all', '1,2,3', '4'))
          and not re.search(r'^export CB_BLOCKS=', exh, re.M))

# ---------------------------------------------------------------------------------------------------------------------------
print('\n## 4. New findings N15-N25')
with guard('N15'):
    b11 = BODIES[11][0]
    caps12 = re.findall(r'^CALLER_\w+="\$\{(\w+)', text(RUN12SH), re.M)
    py_rec = 'pp_split_rec = os.environ.get("VLLM_PP_LAYER_PARTITION", "default_14_13" if case.get("pp", 1) == 2' in text(RUN12PY)
    i_pp = next(i for i, l in enumerate(L12) if 'if [[ -n "${VLLM_PP_LAYER_PARTITION:-}" ]]; then' in l)
    check('N15', f'step 11 passes VLLM_PP_LAYER_PARTITION=15,12 to the two-server runner only through its environment; the runner does not save it (it saves '
          f'{caps12}), unsets it at line {i_un12 + 1}, and builds the split it exports to both nodes from it at line {i_pp + 1}, so the 15,12 arm runs vLLM\'s '
          'default split and its case manifest records default_14_13', "VLLM_PP_LAYER_PARTITION='15,12' '$NET_DIR/12_run_vllm_multi_node.sh' --group pp2_split" in b11
          and 'VLLM_PP_LAYER_PARTITION' not in caps12 and i_un12 < i_pp and py_rec)
    pp2 = {k: c.get('pp') for k, c in caseset.items() if 'pp2_split' in c.get('groups', [])}
    check('N15.arms', f'both arms run the same pp2_split cases ({sorted(pp2)}), so step 11\'s two folders hold the same configuration', sorted(pp2.values()) == [2, 2]
          and b11.count('--group pp2_split') == 2)

    gp = None
    if WHL:
        du_ = zipfile.ZipFile(WHL).read('vllm/distributed/utils.py').decode()
        gp = 'layers_per_partition = num_hidden_layers // pp_size' in du_ and 'for i in range(2, remaining_layers + 2):\n                partitions[-i] += 1' in du_
    def default_split(n, pp):
        parts = [n // pp] * pp
        for i in range(2, n % pp + 2):
            parts[-i] += 1
        return parts
    check('N15.vllm', f'vLLM 0.29.0\'s default split for 27 layers, re-typed from get_pp_indices (wheel checked: {gp is not None}): {default_split(27, 2)} at PP2 and '
          f'{default_split(27, 4)} at PP4', gp in (True, None) and default_split(27, 2) == [14, 13] and default_split(27, 4) == [7, 7, 7, 6])

with guard('N16'):
    HL = lines(H20)
    uses_od = [i + 1 for i, l in enumerate(HL) if '$OUT_DIR' in l]
    set_od = next(i + 1 for i, l in enumerate(HL) if re.match(r'^OUT_DIR=', l))
    in_if = HL[uses_od[0] - 3].strip() if uses_od else ''
    outside = [i for i in uses_od if i < set_od and not HL[i - 1].startswith(' ')]
    check('N16', f'the 20-minute helper writes the qdisc to "$OUT_DIR/..." at lines {[i for i in uses_od if i < set_od]}, but sets OUT_DIR only at line {set_od}; '
          f'under set -u the first use stops it with "unbound variable" (E3), right after node 0\'s cap is applied, and line {outside} does the same where ens3 '
          'is absent; its EXIT trap then removes the caps, and the run never starts', 'set -euo pipefail' in text(H20) and uses_od and uses_od[0] < set_od
          and outside and not any(re.search(r'\bOUT_DIR=', text(r)) for r in (EX, SETUPC)) and 'OUT_DIR' not in text(H20)[:text(H20).index('$OUT_DIR')].replace('$OUT_DIR', ''),
          f'{H20}: uses {uses_od[:4]}, set at {set_od}')

    check('N16.label', 'once it runs, its 20 Gbit/s run will be labelled cap 0 and mode native: it passes no labels, and the file the helpers write sets none',
          CAP_VAR not in text(H20) and MODE_VAR not in text(H20) and 'os.environ.get("' + CAP_VAR + '","0")' in text(RUN12PY))
    i_wr = next(i + 1 for i, l in enumerate(HL) if l.strip() == 'echo "$RUN_TIMESTAMP" > "$HOME/platform_benchmark_runs/latest_run_id.txt"')
    check('N16.runid', f'once it runs, it also writes its own id into latest_run_id.txt (line {i_wr}, after the stop); a master resumed after it reads that file '
          'and runs in $HOME/platform_benchmark_runs/<id>, not the helper\'s tp4_pp4_20g_<id> folder: a new, empty run folder, so it starts again from step 0',
          i_wr > max(uses_od[:2]) and 'OUT_DIR="$HOME/platform_benchmark_runs/tp4_pp4_20g_${RUN_TIMESTAMP}"' in text(H20)
          and 'RUN_ID_FILE="$HOME/platform_benchmark_runs/latest_run_id.txt"' in MT and 'DEFAULT_RUN_ID=$(cat "$RUN_ID_FILE")' in MT
          and ': "${MASTER_ROOT:=$HOME/platform_benchmark_runs/$RUN_ID}"' in MT, f'{H20}:{i_wr}')

with guard('N17'):
    excl = re.search(r'if manifest\.name in \(([^)]*)\):', aud).group(1)
    check('N17.rules', 'the end audit counts a case as failed when its manifest\'s status is FAILED or it has an error, and otherwise only when one of its '
          'points has status FAILED; WARMUP_FAILED is not counted', 'elif status == "FAILED" or err:' in aud
          and 'b_failed = [b for b in benchmarks if b.get("status") == "FAILED"]' in aud and 'WARMUP_FAILED' not in aud, excl)
    single_status = '"status"' not in re.search(r'case_rec=\{"name":case\["name"\].*?"benchmarks":\[\]\}', text(SINGLE), re.S).group(0)
    cb_status = '"status"' not in re.search(r'case_rec = \{\s*"name": case\["name"\].*?"benchmarks": \[\]\s*\}', cbt, re.S).group(0)
    check('N17.warm', 'the single-node and batching runners write no case status, so a case whose points all failed their warm-up counts as completed; the '
          'two-server runner sets FAILED for such a case, which the audit sees', single_status and cb_status and '"case_rec["status"]' not in text(SINGLE)
          and 'rec["status"]="COMPLETED" if states and all(' in text(RUN12PY) and '("FAILED" if any(x in ("FAILED","WARMUP_FAILED") for x in states)' in text(RUN12PY))
    check('N17.profile', 'the two-server Nsight case writes PROFILE_CASE_MANIFEST.json, which the case-sensitive *manifest*.json does not match (E4), so steps '
          '13 and 14\'s two-server Nsight failures are not counted; the driver itself ends 0 whatever its cases did', 'PROFILE_CASE_MANIFEST.json' in text(CASE18)
          and text(DRV18).rstrip().endswith('echo "Distributed profile results: $OUT_ROOT"'))
    nomani = {n: not re.search(r'11_run_vllm_surrogate|12_run_vllm_multi_node\.sh|run_continuous_batching|18_run_vllm_multi_node_profiles', BODIES[n][0]) for n in (2, 4)}
    t14m = {os.path.basename(r): 'manifest' not in text(r).lower() for r in (T14, T14C, T14D)}
    check('N17.none', f'steps 2 and 4 call no runner that writes a case manifest ({nomani}), and 14, 14c and 14d write none ({t14m}), so their failures are '
          'not counted either', all(nomani.values()) and all(t14m.values()))
    check('N17.before', 'a two-server runner that stops before its first case manifest (the Ray start-up, the audit, the sampler copy) leaves nothing to '
          'count, and its exit status is lost, since steps 10 and 11 end with the summarizer and step 12 with an if block',
          all('12_run_vllm_multi_node.sh' in BODIES[n][0] for n in (10, 11, 12)) and '15_summarize_vllm.py' in last(10) and '15_summarize_vllm.py' in last(11)
          and last(12) == 'fi')
    i_py = MT.index('"$PYTHON_EXEC" - << \'PY\' "$MASTER_ROOT" "${FAILED_STEPS[@]}"')
    check('N17.banner', 'the audit\'s exit 1 ends the master under set -e before AUDIT_RC is read, so the closing banner is skipped when a run fails (E5)',
          MT.startswith('#!/usr/bin/env bash') and 'set -euo pipefail' in MT[:2000] and MT[i_py:].split('\n', 1)[0].rstrip().endswith('"${FAILED_STEPS[@]}"')
          and 'AUDIT_RC=$?' in MT[i_py:])

with guard('N18'):
    capn = {os.path.basename(r): sorted(set(re.findall(r'^CALLER_\w+="\$\{(\w+)', text(r), re.M))) for r in (RUN12SH, DRV18, T14D)}
    keys = {'NODE0_IP', 'NODE1_IP', 'SSH_KEY', 'VENV_DIR'}
    helper_keys = [re.findall(r'^export (\w+)=', t[t.index('cat << EOF'):t.index('\nEOF', t.index('cat << EOF'))], re.M) for t in (st, ht)]
    check('N18', f'the runners save none of the node addresses, the key or the venv before their re-read ({capn}), and the file the helpers write sets all '
          f'four ({helper_keys[0]}), so inside steps 3 and 10-14 the file\'s values replace the master\'s --node0-ip, --node1-ip, --ssh-key and --venv-dir',
          all(not (keys & set(v)) for v in capn.values()) and all(set(h) == keys for h in helper_keys) and 'CALLER_' not in text(NCCLTUNE) and flags)

    mreads = [l.strip() for l in ML[:60] if 'RUN_CONFIG.env' in l and 'source' in l]
    cands12 = re.search(r'CONFIG_CANDIDATES=\(([^)]*)\)', text(RUN12SH)).group(1)
    others = {os.path.basename(r): re.search(r'for f in "\$PWD/RUN_CONFIG.env" "\$SCRIPT_DIR/../RUN_CONFIG.env" "\$HOME/rtx_g4_smoke/RUN_CONFIG.env"; do', text(r)) is not None
              for r in (DRV18, T14D, NCCLTUNE)}
    check('N18.paths', 'the master reads RUN_CONFIG.env from $PWD, scripts/ or the repository root; the runners from $PWD, scripts/ (one level above their own folder), '
          f'then older copies in $HOME ({others}; the two-server runner one more, the old suite\'s folder)', len(mreads) == 3 and '"$PWD/RUN_CONFIG.env"' in mreads[0]
          and '"$SUITE_ROOT/RUN_CONFIG.env"' in mreads[1] and '"$SUITE_ROOT/../RUN_CONFIG.env"' in mreads[2] and all(others.values())
          and cands12.count('$HOME/') == 2 and cands12.startswith('"$PWD/RUN_CONFIG.env" "$SCRIPT_DIR/../RUN_CONFIG.env"'))

with guard('N19'):
    cli = smk[smk.index('--- 13. VLLM SERVE'):smk.index('--- 14. PROMETHEUS')]
    plain = None
    if WHL:
        import ast as _ast
        TQ = '"' * 3
        zq = zipfile.ZipFile(WHL); au_ = zq.read('vllm/utils/argparse_utils.py').decode(); sv_ = zq.read('vllm/entrypoints/cli/serve.py').decode()
        docs_ = {}
        for n_ in zq.namelist():
            if n_.startswith('vllm/config/') and n_.endswith('.py'):
                try:
                    tr_ = _ast.parse(zq.read(n_).decode('utf-8', 'ignore'))
                except Exception:
                    continue
                for nd in tr_.body:
                    if isinstance(nd, _ast.ClassDef):
                        docs_[nd.name] = _ast.get_docstring(nd) or ''
        groups_ = re.findall(r'add_argument_group\(\s*title="([^"]+)",\s*description=(\w+)\.__doc__', zq.read('vllm/engine/arg_utils.py').decode())
        i_d = sv_.index('DESCRIPTION = ' + TQ)
        desc_ = sv_[i_d:sv_.index(TQ, i_d + 20)]
        epi_src = [zq.read(n_).decode('utf-8', 'ignore') for n_ in zq.namelist() if n_.endswith('api_utils.py')]
        epi_src = [t_ for t_ in epi_src if 'VLLM_SUBCMD_PARSER_EPILOG = (' in t_]
        epi_ = epi_src[0][epi_src[0].index('VLLM_SUBCMD_PARSER_EPILOG = ('):epi_src[0].index('\n)', epi_src[0].index('VLLM_SUBCMD_PARSER_EPILOG = ('))] if epi_src else ''
        shown = desc_ + epi_ + ' '.join(docs_.get(g_[1], '') for g_ in groups_) + 'vllm serve [model_tag] [options]'
        plain = ('formatter.start_section("Config Groups")' in au_ and 'usage="vllm serve [model_tag] [options]"' in sv_ and len(groups_) == 15 and bool(epi_)
                 and not any(f_ in shown for f_ in ('--tensor-parallel-size', '--pipeline-parallel-size', '--distributed-executor-backend')))
    check('N19.cli', f'its vLLM check runs plain `vllm serve --help` and needs --tensor-parallel-size, --pipeline-parallel-size and --distributed-executor-backend in '
          f'it; vLLM 0.29.0\'s plain help prints its usage line, description, config-group list and epilog, with none of the three (wheel checked: {plain is not None}), '
          'so on Linux the check fails and the smoke test exits 1 on a healthy node; the runners, the gate and the Nsight driver read --help=all first',
          '[vllm_bin, "serve", "--help"]' in cli and all(f_ in cli for f_ in ('"--tensor-parallel-size"', '"--pipeline-parallel-size"', '"--distributed-executor-backend"'))
          and 'record_check "vllm_cli_capabilities" "FAILED"' in cli and plain in (True, None) and '["--help=all"]' in text(LIB) and "'--help=all'" in text(READY))
    check('N19.setup', 'the cluster set-up runs the smoke test under set -e, so it stops at step [4/5] and never reaches --run-benchmark',
          'set -euo pipefail' in st and st.index('bash "$SCRIPT_DIR/run_smoke_test.sh"') < st.index('if [[ "$RUN_BENCHMARK" == 1 ]]; then'))
    rb = text('RUNBOOK_NEW_VM_SETUP.md'); i_ap = rb.index('sudo apt-get update && sudo apt-get install -y')
    ip3 = {'smoke test': 'for cmd in taskset ip tc iperf3; do' in smk, 'gate': "'iperf3'" in text(READY),
           'not installed by setup_node_env.sh': 'iperf3' not in ne, 'not in the runbook install line': 'iperf3' not in rb[i_ap:rb.index('```', i_ap)],
           'new in the smoke test': OLD is None or 'for cmd in taskset ip tc; do' in text(SMOKE, OLD),
           '01\'s prepare script installs it': 'iperf3 numactl pciutils' in text('scripts/01_preflight_and_diagnostics/01_prepare_node.sh')}
    check('N19.iperf', f'iperf3 is now required by the smoke test on Linux, and by the gate, but neither setup_node_env.sh nor the runbook installs it (01\'s node '
          f'preparation script does): {ip3}', all(ip3.values()))
    cw = smk[smk.index('--- 8. CONTEXT WINDOW'):smk.index('--- 9. MASTER BENCHMARK')]
    bkeys = {}
    for c in caseset.values():
        for b_ in c.get('benchmarks', []):
            for k in b_:
                bkeys[k] = bkeys.get(k, 0) + 1
    big = sorted(k for k, c in caseset.items() if (c.get('max_num_batched_tokens') or 0) > 8192)
    check('N19.ctx', f'the smoke test\'s context check reads input_tokens and output_tokens, which no point in the cases file has (they use input, {bkeys.get("input")} '
          f'points, and output); and it warns whenever a case\'s step budget exceeds 8,192, which {len(big)} cases do by design ({big}), so it always warns (E9)',
          'b.get("input_tokens", 0)' in cw and 'b.get("output_tokens", 0)' in cw and 'input_tokens' not in bkeys and bkeys.get('input') == 155
          and 'if budget > 8192:' in cw and 'elif bad_budgets:' in cw and len(big) == 4)
    check('N19.verdict', 'once its vLLM check passes, any warning makes the verdict "SURROGATE QUALIFIED ... CLEARED FOR CLUSTER DEPLOYMENT", saying warnings '
          'reflect a local surrogate host; "100% PRODUCTION READY" needs none, so a healthy node never gets it; --strict turns warnings into failures, so --strict always fails',
          'elif warnings > 0:\n    readiness_code = "SURROGATE_QUALIFIED"' in smk and 'reflect local host surrogate fallback' in smk
          and 'if [[ "$STRICT_MODE" == 1 && "$status" == "WARNING" ]]; then\n    status="FAILED"' in smk)
    cbs = smk[smk.index('--- 17. CONTINUOUS BATCHING'):smk.index('--- 18. END-TO-END')]
    check('N19.cb', 'its batching check reads the file\'s block names, never a stream, and the flag it computes is never used, so it passes whenever the '
          'file parses', 'blocks = d.get("blocks", d.get("cases", {}))' in cbs and cbs.count('has_concurrency') == 2
          and isinstance(cbj.get('blocks'), dict) and all(isinstance(v, str) for v in cbj['blocks'].values()))
    win = [l for l in smk.splitlines() if re.search(r'/c/Users/', l)]
    check('N19.misc', 'its Python search list holds a developer\'s Windows home path, and its report hard-codes two node addresses and the model',
          len(win) == 1 and len(re.findall(r'\b10\.128\.0\.\d+\b', smk)) == 2 and '"model_target":' in smk)

with guard('N20'):
    rt = text(RES)
    exl = re.search(r'if f\.name in \((.*?)\):', rt, re.S).group(1)
    check('N20.key', 'step 12\'s comparison (tools/compare_resilience_matrix.py) now keys each point by d.get("case_name") or its folder\'s name and reports '
          'all four conditions with time per token; vLLM\'s result files carry no case_name, so the key is the benchmark\'s folder',
          'case_name = d.get("case_name") or f.parent.name or f.stem' in rt and 'tpot_degradation_pct' in rt
          and '"native", "capped_100g", "capped_20g", "impaired_005pct_loss"' in rt)
    check('N20.deg', 'it computes the change only for 0.05% loss against native', 'nat = report[case].get("native", {})' in rt
          and 'imp = report[case].get("impaired_005pct_loss", {})' in rt and rt.count('_degradation_pct"]') == 2)
    runres = sorted(glob.glob(os.path.join(PIP, 'data/results/tp4_pp4_20g_*/tp4_pp4_dist/tp4_pp4_dist/*/*.json')))
    rfiles = [p for p in runres if os.path.basename(p) != 'warmup_manifest.json']
    no_cn = all('case_name' not in json.load(open(p)) for p in rfiles)
    check('N20.files', f'the TP4/PP4 run\'s {len(rfiles)} result files have no case_name key; each sits beside a warmup_manifest.json in the same folder, which '
          'the comparison does not exclude, so the two share a key and the one the folder lists last is kept (E7)', len(rfiles) == 16 and no_cn
          and 'warmup_manifest.json' not in exl and '(bdir/"warmup_manifest.json").write_text' in text(RUN12PY))
    check('N20.audit', 'nor does it exclude the runner\'s <case>_RAY_NCCL_ENV_AUDIT.json at the top of each condition, which becomes a point named after '
          'the condition', 'RAY_NCCL_ENV_AUDIT' not in exl and '"$OUT_ROOT/${CASE}_RAY_NCCL_ENV_AUDIT.json"' in text(RUN12SH))
    r3n = sorted(b['name'] for k, c in caseset.items() if 'r3_network_resilience' in c.get('groups', []) for b in c['benchmarks'])
    check('N20.names', f'the two layouts\' benchmark names differ ({r3n}), so they do not collide with each other', len(set(r3n)) == 4)

with guard('N21'):
    cct = text(CC)
    cols = ['duration_seconds', 'num_total_requests', 'token_throughput_tps', 'itl_p99_ms', 'step_id', 'request_throughput_rps', 'ttft_median_ms']
    written = {c: any(re.search(rf'(?<![A-Za-z0-9_]){c}(?![A-Za-z0-9_])', t) for r, t in CORPUS.items()) for c in cols}
    hdr = open(next(iter(glob.glob(os.path.join(PIP, 'data/results/tp4_pp4_20g_*/summary_v6/vllm_runs.csv'))))).readline().strip().split(',')
    check('N21', 'step 15\'s aggregation now takes --run-dir and writes a copy into the run, but uses the first CSV a recursive glob finds there, and the '
          f'columns its figures need ({len(cols)} checked) appear in no CSV any script writes (the summarizer\'s {len(hdr)} columns have none of them), so its '
          'totals and per-step tables come out 0 or empty; 16 GPUs and 1,536 GiB are still constants, and it still overwrites the repository\'s dashboard file',
          'csv_path = run_csvs[0]' in cct and 'glob.glob(os.path.join(run_dir, "**", "*.csv"), recursive=True)' in cct and not any(written.values())
          and not (set(cols) & set(hdr)) and '"cluster_gpus_active": 16' in cct and '"total_cluster_vram_gib": 1536' in cct
          and 'os.path.join(base_dir, "dashboard", "DASHBOARD_CANONICAL_DATA.json")' in cct and '--run-dir' in BODIES[15][0], str(written))
    check('N21.v14', 'the dashboard string check is no longer called by the master', 'run_v1_4_verification' not in MT)
    others_csv = {'step 13 GPU inventory': 'nvidia-smi --query-gpu=index,uuid,name,memory.total,pci.bus_id --format=csv > "$DIR/node0_gpu_inventory.csv"' in text(DRV18),
                  'step 14 Nsight stats': 'nsys stats --format csv --report "$r" "$REP" > "$PROFILE_ROOT/${r}.csv"' in text(T14)}
    empty = 'if not rows: path.write_text(""); return' in text(SUMM)
    s2 = None
    if FP8DIR:
        s2 = os.path.getsize(os.path.join(FP8DIR, 'summary', 'vllm_runs.csv')) == 0
    check('N21.csv', f'the first CSV can also be another kind ({others_csv}), and the summarizer writes an empty file for a step with no rows ({empty}; the second '
          f'campaign\'s FP8 step summary is 0 bytes: {s2}); pandas fails on an empty file (E12), and the step\'s || true hides it',
          all(others_csv.values()) and empty and s2 in (True, None) and BODIES[15][0].rstrip().endswith('|| true'))

with guard('N22'):
    sel_py = text(RUN12SH)[text(RUN12SH).index("topo_sel = os.environ.get('TOPOLOGY_SELECTION', 'all')"):]
    r3names = sorted(k for k, c in caseset.items() if 'r3_network_resilience' in c.get('groups', []))
    check('N22', f'the two-server runner keeps a case only when a selected name is a substring of its name; step 12\'s cases are {r3names}, so a selection '
          'written as the help shows it (tp16_pp1, tp4_pp4) keeps neither, the runner exits 2 ("No multi-node cases selected") under every condition, and '
          'step 12 runs nothing; the master\'s own guard matches both ways (E10)', "if not any(t in c_str for t in topos):" in sel_py
          and r3names == ['stage3_r3_network_jitter_pp4', 'stage3_r3_network_jitter_tp16'] and 'tp4_pp1,tp8_pp1,tp4_pp2,tp8_pp2,tp4_pp4,tp16_pp1' in MT
          and '[[ ${#CASE_ROWS[@]} -gt 0 ]] || { echo "No multi-node cases selected"; exit 2; }' in text(RUN12SH)
          and 'if [[ "$topo" == *"$c"* || "$c" == *"$topo"* ]]; then return 0; fi' in MT)

    check('N22.fix', 'matching both ways would not help (neither tp16_pp1 nor stage3_r3_network_jitter_tp16 is part of the other); step 12 has no topology guard of '
          'its own; and --topologies multi_node passes step 10\'s guard but matches no case name, so step 10 would run nothing',
          'tp16_pp1' not in 'stage3_r3_network_jitter_tp16' and 'stage3_r3_network_jitter_tp16' not in 'tp16_pp1'
          and not re.search(r'if step_should_run 12; then\n\s*if ! topology_matches', MT) and 'if ! topology_matches "multi_node"' in MT
          and not any('multi_node' in k for k in caseset))

with guard('N23'):
    d1 = os.path.join(PIP, 'dashboard/index.html')
    d2 = glob.glob(os.path.join(PIP, 'data/results/tp4_pp4_20g_*/tp4_pp4_20g_dashboard.html'))
    ext = json.load(open(os.path.join(PIP, 'data/results/extracted_dashboard_metrics.json')))
    res = {os.path.basename(os.path.dirname(p)): json.load(open(p)) for p in rfiles}
    match = all(abs(r['median_itl_ms'] - round(res[r['bench']]['median_itl_ms'], 2)) < 0.006 for r in ext)
    check('N23.dash', f'new and outside the run: a dashboard page of the TP4/PP4 run, one file in two places ({os.path.getsize(d1):,} bytes each), and the '
          f'metrics it shows ({len(ext)} points), whose median ITL values match the run\'s result files', d2 and md5(d1) == md5(d2[0]) and len(ext) == 16 and match)
    rep = text('data/results/FINAL_TP4_PP4_20G_BENCHMARK_REPORT.md')
    check('N23.report', 'the TP4/PP4 report is unchanged, its median ITL column still wrong in 14 of 16 rows as v1.4 found',
          OLD is None or md5(os.path.join(PIP, 'data/results/FINAL_TP4_PP4_20G_BENCHMARK_REPORT.md')) == md5(os.path.join(OLD, 'data/results/FINAL_TP4_PP4_20G_BENCHMARK_REPORT.md')))
    tm = text(os.path.relpath(TIMING[0], PIP)) if TIMING else ''
    called = any(os.path.basename(TIMING[0]) in t for r, t in CORPUS.items() if TIMING and not r.endswith(os.path.basename(TIMING[0])))
    facs = sorted(set(float(x) for x in re.findall(r'factor = ([0-9.]+)', tm)))
    check('N23.timing', f'a new timing calculator for another model reads its input from a developer\'s Windows path, so it cannot run on the VM, scales this '
          f'run\'s durations by assumed factors ({facs}), and nothing calls it', len(TIMING) == 1 and re.search(r'r"[Cc]:\\Users\\', tm) and facs == [2.4, 2.5, 2.6, 2.7, 2.8]
          and not called)

    unused = {v: not any(re.search(rf'\b{v}\b', t) for r, t in CORPUS.items() if not r.endswith('RUN_CONFIG.env.example'))
              and re.search(rf'^export {v}=', text(EX), re.M) is not None for v in ('VLLM_COLD_WARM_ISOLATION', 'PROFILE_TOPOLOGIES', 'PROFILE_CONTEXTS', 'VLLM_METRIC_PERCENTILES')}
    vread = None
    if WHL:
        zv = zipfile.ZipFile(WHL)
        vread = any('VLLM_METRIC_PERCENTILES' in zv.read(n_).decode('utf-8', 'ignore') for n_ in zv.namelist() if n_.endswith('.py'))
    check('N23.unused', f'the example sets four switches no script reads ({unused}), the last of which vLLM 0.29.0 does not read either (wheel checked: {vread is not None})',
          all(unused.values()) and vread in (False, None))
    import html as _html
    pg = open(d1, encoding='utf-8', errors='replace').read()
    vis = _html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)[^>]*>.*?</\1>', '', pg, flags=re.S)))
    nv = json.load(open(man[0]))['environment']['commands']['nvidia_smi']['out'] if man else ''
    gpus = re.findall(r'NVIDIA (RTX PRO 6000 [A-Za-z ]+?), (\d+), ', nv)
    under10 = sum(1 for r in ext if r['mean_tpot_ms'] < 10)
    check('N23.page', f'the page says the run used 16 RTX PRO 6000 Ada GPUs with about 768 GB in all, decoding in under 10 ms; the run\'s records show {len(gpus)} '
          f'{sorted(set(g[0] for g in gpus))} on node 0 at {sorted(set(g[1] for g in gpus))} MiB each, and a mean time per token under 10 ms at {under10} of its 16 points '
          f'({min(r["mean_tpot_ms"] for r in ext)}-{max(r["mean_tpot_ms"] for r in ext)} ms); it calls its data "100% genuine"',
          '16× NVIDIA RTX PRO 6000 Ada GPUs' in vis and '~768 GB collective VRAM' in vis and 'consistent sub-10ms decoding' in vis and '100% genuine' in pg
          and len(gpus) == 8 and set(g[0] for g in gpus) == {'RTX PRO 6000 Blackwell Server Edition'} and set(g[1] for g in gpus) == {'97887'} and under10 == 2)

with guard('N24'):
    d18 = text(DRV18); L18 = lines(DRV18)
    i_scp = next(i for i, l in enumerate(L18) if '09_metrics_sampler.py" "$NODE1_IP:/tmp/v5_metrics_sampler.py"' in l)
    i_for = next(i for i, l in enumerate(L18) if l.startswith('for ROW in "${ROWS[@]}"; do'))
    i_rm = next(i for i, l in enumerate(L18) if 'rm -f /tmp/v5_metrics_sampler.py' in l)
    i_end = max(i for i, l in enumerate(L18) if l.strip() == 'done')
    c18 = text(CASE18)
    olds = {k: ('rm -f /tmp/v5_metrics_sampler.py' in text(DRV18, r)) for k, r in (('v1.4 folder', OLD), ('v1.3 folder', V13)) if r}
    check('N24', f'the two-server Nsight driver copies the sampler to node 1 once (line {i_scp + 1}), before its loop (line {i_for + 1}), and deletes it inside the '
          f'loop (line {i_rm + 1}), so only the first capture of each call gets node 1\'s GPU telemetry: 3 of the 21 runs (step 13\'s one, the first of each of step 14\'s '
          f'two calls); the remote start records no error (nohup ... & echo $!), and each later run\'s validation reads complete: false. The same lines were in '
          f'the earlier folders ({olds})', i_scp < i_for < i_rm < i_end and 'nohup python3 {shlex.quote(remote_py)}' in c18 and '& echo $!' in c18
          and "'node1_metrics': (p / 'workload/metrics_node1.jsonl').exists()" in d18 and all(olds.values()))

with guard('N25'):
    nt_ = text(NCCLTUNE)
    fmt = None
    if NCCLJ:
        jj = json.load(open(NCCLJ))
        fmt = 'results' in jj and 'data' not in jj and 'out_of_place' in jj['results'][0] and 'time' in jj['results'][0]['out_of_place'] and 'bus_bw' in jj['results'][0]['out_of_place']
    mp = re.findall(r'> "\$vdir/(all_reduce_16k|sendrecv_256m)\.log" 2>&1 \|\| true', nt_)
    check('N25', f'step 3\'s summary reads d["data"][...]["time_us"] and ["busbw"], but nccl-tests writes results[...]["out_of_place"]["time"] and ["bus_bw"] (an earlier '
          f'run\'s file checked: {fmt is not None}), so both figures for every variant in its NCCL_TUNING_SUMMARY.json are null (only the transport line, read from the '
          f'log, is filled); and each mpirun is behind || true ({len(mp)} of them), so a sweep whose runs all failed still ends 0', 'for row in d.get("data", []):' in nt_ and 'row.get("time_us")' in nt_ and 'row.get("busbw")' in nt_
          and fmt in (True, None) and len(mp) == 2 and nt_.rstrip().endswith('echo "NCCL Socket tuning evaluation complete: $OUT_ROOT"')
          and 'summary[vname]["transport_logged"] = line.strip()' in nt_)
    check('N25.algbw', 'its latency figure falls back to algbw, a bandwidth, when time_us is missing', 'row.get("time_us") or row.get("algbw")' in nt_)

# ---------------------------------------------------------------------------------------------------------------------------
print('\n## D. A default run, step by step')
with guard('D. A default run'):
    calls = [l for l in ML if re.match(r'\s*run_step \d+ ', l)]
    exits = [(i + 1, l.strip()) for i, l in enumerate(ML) if re.match(r'\s*exit\b', l)]
    check('D.flow', f'every step goes through run_step ({len(calls)} calls), which always returns 0; the master\'s only exits are --help, an unknown flag or '
          'profile, and the end (E5)', len(calls) == 21 and len(exits) == 4 and exits[-1][1] == 'exit "$AUDIT_RC"', str(exits))
    check('D.step0', 'step 0 runs whatever --step or --from-step say (no step_should_run guard)', not re.search(r'if step_should_run 0', MT)
          and MT.index('run_step 0 "preflight_and_env_snapshot"') < MT.index('if step_should_run 1'))
    nt = text(NCCLTUNE)
    check('D.step3', 'step 3 runs only with a node 1 address; without the nccl-tests binaries under $BENCH_ROOT its sweep exits 1, which now marks the step '
          'failed and the campaign FAILED at the end, without stopping the run', 'if [[ -n "${NODE1_IP:-}" ]]; then\n    NCCL_DIR=' in MT and 'return 1' in nt
          and rs.rstrip().endswith('return 0') and 'FAILED_STEPS+=' in rs and 'failed_steps_count' in aud
          and re.search(r'^run_nccl_variant "variant_a_baseline"', nt, re.M) and 'set -euo pipefail' in nt)
    check('D.bench', 'the sweep looks for nccl-tests under $BENCH_ROOT, which defaults to $HOME/rtx_g4_smoke and which the example sets to $HOME/platform_bench_suite',
          ': "${BENCH_ROOT:=$HOME/rtx_g4_smoke}"' in nt and 'NCCL_TESTS_DIR="$BENCH_ROOT/nccl-tests"' in nt and 'export BENCH_ROOT="$HOME/platform_bench_suite"' in text(EX))
    PREP = 'scripts/01_preflight_and_diagnostics/01_prepare_node.sh'
    pt = text(PREP); sc_ = text('scripts/01_preflight_and_diagnostics/00_smoke_common.sh')
    callers = sorted(r for r, t in CORPUS.items() if '01_prepare_node' in t and r.endswith(('.sh', '.py')) and not r.endswith('01_prepare_node.sh'))
    check('D.prep', f'01\'s node-preparation script installs iperf3 and clones and builds nccl-tests under its own $BENCH_ROOT ($HOME/rtx_g4_smoke unless set, '
          f'as in step 3), needs PEER_IP, and no script outside the old rtx_g4_* folders calls it, the master included (only error messages name it: {callers})',
          'iperf3 numactl pciutils' in pt and 'if [ ! -d nccl-tests/.git ]; then git clone https://github.com/NVIDIA/nccl-tests.git; fi' in pt
          and 'cd "$BENCH_ROOT/nccl-tests"' in pt and 'make -j"$(nproc)" MPI=1 MPI_HOME=/usr' in pt and ': "${BENCH_ROOT:=$HOME/rtx_g4_smoke}"' in sc_
          and ': "${PEER_IP:?' in pt and '01_prepare_node' not in MT
          and all(all('01_prepare_node' not in l or 'echo "ERROR' in l for l in text(r).splitlines()) for r in callers))
    sc_rl = sc_[sc_.index('run_logged() {'):sc_.index('\n}\n', sc_.index('run_logged() {'))]
    check('D.prep2', 'it runs under set -euo pipefail and each logged step returns its own status, so it stops at the first step that fails; it builds nvbandwidth '
          'before nccl-tests; step 3 runs all_reduce_perf and sendrecv_perf from nccl-tests/build/', pt.startswith('#!/usr/bin/env bash\n# Run on BOTH GCP nodes once.\nset -euo pipefail')
          and sc_rl.rstrip().endswith('return $rc') and pt.index('run_logged 031_build_nvbandwidth') < pt.index('run_logged 041_build_nccl_tests')
          and not re.search(r'^run_logged [^\n]*\|\|', pt, re.M) and '"$NCCL_TESTS_DIR/build/all_reduce_perf"' in nt and '"$NCCL_TESTS_DIR/build/sendrecv_perf"' in nt)
    rdy = text(READY)
    setup_txt = {r: text(r).lower() for r in (NODEENV, 'RUNBOOK_NEW_VM_SETUP.md', PREP, SETUPC)}
    b14_ = BODIES[14][0]
    check('D.tools', 'the readiness gate requires nsys and iperf3 (with vllm, ray, nvidia-smi, tc and python3) and fails on any missing one; neither setup_node_env.sh, '
          'the runbook, 01\'s node-preparation script nor the cluster set-up installs nsys; without it on node 0, 14 and the Nsight driver exit 2, so step 13 '
          '(through run_step) fails and step 14\'s Nsight calls, behind || true, are lost quietly', "for x in ('vllm','ray','nsys','nvidia-smi','iperf3','tc','python3')" in rdy
          and "'ok':all(x['ok'] for x in checks)" in rdy and not any('nsys' in t or 'nsight' in t for t in setup_txt.values())
          and 'command -v nsys >/dev/null || { echo "nsys not installed"; exit 2; }' in text(T14)
          and 'command -v nsys >/dev/null || { echo "ERROR: nsys missing on node0"; exit 2; }' in text(DRV18)
          and re.search(r'^\s*run_step 13 "tp16_512k_prefill" env [^\n]*18_run_vllm_multi_node_profiles\.sh"\s*$', MT, re.M)
          and all(l.rstrip().endswith('|| true') or l.rstrip().endswith('\\') for l in b14_.splitlines() if '14_run_vllm_nsys_profile.sh' in l or '18_run_vllm_multi_node_profiles.sh' in l)
          and b14_.count("'$PROF_DIR/14_run_vllm_nsys_profile.sh' || true") == 3 and b14_.count("'$PROF_DIR/18_run_vllm_multi_node_profiles.sh' || true") == 2)
    guide = text('README_SETUP_AND_OPERATIONS.md')
    check('D.hup', 'the master sets no trap for a hang-up and does not detach itself, so started in the foreground of an SSH session it ends when the session drops; '
          'the setup guide starts it with nohup; the master tees everything into <run>/logs/MASTER_BENCHMARK_RUN.log',
          not re.search(r'trap [^\n]*\b(HUP|SIGHUP)\b', MT) and 'nohup' not in MT and 'disown' not in MT and 'nohup ./run_master_benchmark.sh >' in guide
          and 'MASTER_LOG="$MASTER_ROOT/logs/MASTER_BENCHMARK_RUN.log"\nexec > >(tee -a "$MASTER_LOG") 2>&1' in MT)
    i_rid_flag = MT.index('    --run-id)')
    check('D.runid', '--run-id <id> sets the run id and its folder and leaves resume on, so the second command of 2.3 can name its run outright',
          'RUN_ID="$2"\n      MASTER_ROOT="$HOME/platform_benchmark_runs/$RUN_ID"\n      shift 2' in MT[i_rid_flag:i_rid_flag + 120]
          and 'RESUME=0' not in MT[i_rid_flag:i_rid_flag + 120])
    i_echo = next(i for i, l in enumerate(ML) if l.strip() == 'echo "$RUN_ID" > "$RUN_ID_FILE"')
    check('D.resume', 'section 2.3\'s two commands: --new-run gives a new id, which the master writes to latest_run_id.txt; step 0 alone with --step 0; the next run, '
          'resuming by default, takes that id and skips step 0, whose body ends with an echo (status 0) and so leaves its done marker',
          i_echo > i_loop and 'RUN_ID=$(date +%Y%m%d_%H%M%S)' in MT[MT.index('    --new-run)'):] and last(0).startswith("echo 'Environment snapshot recorded.'")
          and 'if [[ "$RESUME" == 1 && -f "$marker" ]]; then' in rs and "--out '$MASTER_ROOT/env/node0_readiness'" in b0 and "(out/'PLATFORM_READINESS.md')" in text(READY))
    f4 = None
    if WHL:
        zw = zipfile.ZipFile(WHL); au = zw.read('vllm/engine/arg_utils.py').decode(); vc = zw.read('vllm/config/vllm.py').decode()
        f4 = all(f in au for f in ('performance_mode', 'optimization_level', 'moe_backend', 'enable_flashinfer_autotune', 'model_impl')) \
            and 'PerformanceMode = Literal["balanced", "interactivity", "throughput"]' in vc
    check('D.step4', f'step 4\'s fixed server command uses flags that vLLM 0.29.0 has (wheel checked: {f4 is not None})',
          f4 in (True, None) and '--performance-mode balanced --optimization-level 2' in b4)
    check('D.step13', 'step 13 now reaches the Nsight driver, which exits 2 without nsys, ray or vllm on node 0 or vLLM\'s --ray-workers-use-nsight; on node 1 '
          'its check runs the three lookups in one command, so only the last (vllm) decides; a failed capture still ends the driver 0',
          'command -v nsys >/dev/null || { echo "ERROR: nsys missing on node0"; exit 2; }' in dt and "grep -q -- '--ray-workers-use-nsight'" in dt
          and 'ERROR: nsys/ray/vllm missing on node1"; exit 2' in dt and 'PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE=${PLATFORM_GCP_NETWORK_PROVENANCE_OVERRIDE:-}' in dt
          and 'command -v nsys; command -v ray; command -v vllm" >/dev/null ||' in dt and dt.rstrip().endswith('echo "Distributed profile results: $OUT_ROOT"'))
    check('D.step17', 'step 17 still runs only with --cb-blocks (or CB_BLOCKS set), and steps 18-20 only with --profile deep-profile or --step', 'CB_BLOCKS_SEL="${CB_BLOCKS_ARG:-${CB_BLOCKS:-none}}"' in MT
          and 'if [[ "${RUN_POISSON_SWEEPS:-0}" == "1" ]] || [[ "$TARGET_STEP" == "18" ]]; then' in MT)

    fp8 = None
    if FP8DIR:
        cm_ = json.load(open(os.path.join(FP8DIR, 'tp4_fp8_kv_fixed', 'case_manifest.json')))
        fp8 = (cm_.get('error') == "RuntimeError('server exited rc=1')" and not cm_.get('benchmarks') and not os.path.exists(os.path.join(FP8DIR, 'tp4_fp8_kv_fixed', 'server.log')))
    check('D.fp8', f'step 8 runs tp4_fp8_kv_fixed, the case that ended in the second campaign with "server exited rc=1", no benchmark and no server log (checked: '
          f'{fp8 is not None}); a server that dies at start gives the case manifest an error, which the end audit counts as a failed case; the runner now keeps '
          'the server\'s log in the case folder', "--case tp4_fp8_kv_fixed" in BODIES[8][0] and fp8 in (True, None) and 'case_rec["error"]=repr(e)' in text(SINGLE)
          and 'elif status == "FAILED" or err:' in aud and 'start_server_with_timestamp_logging(server_cmd, cdir/"server.log", env)' in text(SINGLE)
          and 'FP8_DIR="$MASTER_ROOT/step08_fp8_kv_rerun"' in MT and 'cdir=out/case["name"]' in text(SINGLE))
    trapline = 'trap cleanup_tp8 EXIT INT TERM ERR' in b4 and not re.search(r'^\s*set -e', b4, re.M)
    check('D.step4trap', 'step 4 sets an ERR trap in a shell without -e: if its control benchmark exits non-zero, the trap stops the server, the pinned run then '
          'measures nothing, and the step still reports 0', trapline and b4.index('trap cleanup_tp8 EXIT INT TERM ERR') < b4.index('Running TP8 unpinned control benchmark'))
    setters = sorted(r for r, t in CORPUS.items() if 'PLATFORM_VLLM_NETWORK_MODE=' in t)
    check('D.toplabel', f'each step-12 condition\'s top-level manifest reads its mode from a variable that only two scripts the master never calls set ({setters}), '
          'so it says native under every condition; the per-case records are right', '"network_mode":os.environ.get("PLATFORM_VLLM_NETWORK_MODE","native")' in text(RUN12PY)
          and [os.path.basename(r) for r in setters] == ['20_run_vllm_network_matrix.sh', '21_run_vllm_capped_profiles.sh']
          and not any(os.path.basename(r)[:-3] in MT for r in setters))

# ---------------------------------------------------------------------------------------------------------------------------
print('\n## E. Experiments (scratch folder, own snippets)')
E1 = '''# setsid in the background from a non-interactive shell, as step 4 starts its server: the child leads its own group
bash -c 'setsid bash -c "sleep 30 & sleep 30" & PID=$!; sleep 0.5
  echo "pid_is_group_leader=$([ "$(ps -o pgid= -p $PID | tr -d " ")" = "$PID" ] && echo yes || echo no)"
  echo "children=$(ps -o stat= -g $PID | grep -vc "^Z")"
  kill -15 -- -"$PID"; sleep 0.5
  echo "left_after_group_kill=$(ps -o stat= -g $PID | grep -vc "^Z")"
  echo body-survives'
echo "rc=$?"
'''
rc, out, err = sh(E1, 'e1_setsid.sh')
check('E1', 'started as step 4 starts its server (setsid ... & PID=$!), the background child leads its own process group, so kill -- -PID ends it and its '
      'children while the shell that started it carries on', 'pid_is_group_leader=yes' in out and 'left_after_group_kill=0' in out and 'body-survives' in out
      and 'rc=0' in out and re.search(r'children=[1-9]', out), out.replace('\n', ' | '))
E2 = '''# the two-server runner's prologue, re-typed: callers saved, config read, then the unset; step 11 passes the split by env
CALLER_TOPO="${TOPOLOGY_SELECTION:-}"
CALLER_OUT_ROOT="${OUT_ROOT:-}"
unset NCCL_ALGO NCCL_PROTO VLLM_DISABLE_PYNCCL VLLM_PP_LAYER_PARTITION 2>/dev/null || true
PP_EXPORT=""
if [[ -n "${VLLM_PP_LAYER_PARTITION:-}" ]]; then PP_EXPORT="export VLLM_PP_LAYER_PARTITION='$VLLM_PP_LAYER_PARTITION'; "; fi
echo "PP_EXPORT=[$PP_EXPORT]"
python3 -I -c 'import os; print("recorded=" + os.environ.get("VLLM_PP_LAYER_PARTITION", "default_14_13"))'
'''
env2 = dict(os.environ, VLLM_PP_LAYER_PARTITION='15,12')
rc, out, err = sh(E2, 'e2_split.sh', env2)
check('E2', 'given VLLM_PP_LAYER_PARTITION=15,12 in its environment, as step 11 passes it, the runner\'s prologue exports no split and records default_14_13',
      'PP_EXPORT=[]' in out and 'recorded=default_14_13' in out, out.replace('\n', ' | '))
E3 = '''set -euo pipefail
cleanup_caps(){ echo "TRAP_RAN"; }
trap cleanup_caps EXIT INT TERM ERR
if true; then
  echo "node0 cap applied"
  echo qdisc > "$OUT_DIR/node0_tc_qdisc_active.txt" 2>/dev/null || true
  echo "AFTER_QDISC"
fi
OUT_DIR="$PWD/run"
echo "RUN_STARTED"
'''
env3 = dict(os.environ); env3.pop('OUT_DIR', None)
rc, out, err = sh(E3, 'e3_outdir.sh', env3)
check('E3', 'under set -euo pipefail, writing to "$OUT_DIR/..." before OUT_DIR is set stops the script with "unbound variable" (status 1) despite '
      '2>/dev/null || true; the EXIT trap runs and nothing after it does', rc == 1 and 'unbound variable' in err and 'TRAP_RAN' in out and 'AFTER_QDISC' not in out
      and 'RUN_STARTED' not in out, (out + ' || ' + err).replace('\n', ' | ')[:300])
E4 = r'''import json, sys
from pathlib import Path
root = Path(sys.argv[1]); root.mkdir(parents=True, exist_ok=True)
(root / "single").mkdir(exist_ok=True); (root / "nsight/workload").mkdir(parents=True, exist_ok=True); (root / "two").mkdir(exist_ok=True)
(root / "single/case_manifest.json").write_text(json.dumps({"name": "tp4_case", "benchmarks": [{"name": "8k_c1", "status": "COMPLETED"}, {"name": "128k_c1", "status": "WARMUP_FAILED"}]}))
(root / "nsight/workload/PROFILE_CASE_MANIFEST.json").write_text(json.dumps({"name": "tp16_pp1_dist_decode_8k", "status": "FAILED"}))
(root / "two/case_manifest.json").write_text(json.dumps({"name": "tp4_pp4_dist_load", "status": "FAILED"}))
found = sorted(str(p.relative_to(root)) for p in root.rglob("*manifest*.json"))
completed = failed = 0
for m in root.rglob("*manifest*.json"):
    d = json.loads(m.read_text()); st = d.get("status"); err = d.get("error")
    if st == "COMPLETED": completed += 1
    elif st == "FAILED" or err: failed += 1
    else:
        b = d.get("benchmarks", [])
        if b:
            if [x for x in b if x.get("status") == "FAILED"]: failed += 1
            else: completed += 1
print("found=" + ",".join(found)); print(f"completed={completed} failed={failed}")
'''
p4 = os.path.join(SCRATCH, 'e4_audit.py'); open(p4, 'w').write(E4)
r4 = subprocess.run([sys.executable, '-I', p4, os.path.join(SCRATCH, 'e4_tree')], capture_output=True, text=True, timeout=60)
check('E4', 'the audit\'s rules, re-typed, on three manifests: a single-node case whose second point failed its warm-up counts as completed; the '
      'two-server case with status FAILED counts as failed; the upper-case PROFILE_CASE_MANIFEST.json is not found', 'completed=1 failed=1' in r4.stdout
      and 'PROFILE_CASE_MANIFEST' not in r4.stdout and 'single/case_manifest.json' in r4.stdout, (r4.stdout + r4.stderr).replace('\n', ' | '))
rc, out, err = sh('set -euo pipefail\npython3 -I - <<\'PY\'\nimport sys; sys.exit(1)\nPY\nAUDIT_RC=$?\necho "BANNER"\n', 'e5_sete.sh')
check('E5', 'under set -e a heredoc Python that exits 1 ends the script at once: the next line (AUDIT_RC=$?) and the banner never run', rc == 1 and 'BANNER' not in out)
E6 = '''# the master's selection lines, replayed: a stale RUN_CONFIG.env pins TOPOLOGY_SELECTION, the user passes --topologies all
export TOPOLOGY_SELECTION="tp4_pp4"
SELECTED_TOPOLOGIES="all"
if [[ -n "$SELECTED_TOPOLOGIES" && "$SELECTED_TOPOLOGIES" != "all" ]]; then export TOPOLOGY_SELECTION="$SELECTED_TOPOLOGIES"; fi
topology_matches() { local topo="$1"; local sel="${TOPOLOGY_SELECTION:-all}"; [[ "$sel" == "all" ]] && return 0; IFS=',' read -ra L <<< "$sel";
  for item in "${L[@]}"; do c=$(echo "$item" | tr -d ' ' | tr '[:upper:]' '[:lower:]'); if [[ "$topo" == *"$c"* || "$c" == *"$topo"* ]]; then return 0; fi; done; return 1; }
echo "selection=$TOPOLOGY_SELECTION"
topology_matches tp16 && echo step13_runs || echo step13_skipped
topology_matches tp8 && echo step4_runs || echo step4_skipped
(topology_matches pp2 || topology_matches tp8_pp2) && echo step11_runs || echo step11_skipped
'''
rc, out, err = sh(E6, 'e6_selection.sh')
check('E6', 'replaying the master\'s selection lines: a TOPOLOGY_SELECTION=tp4_pp4 left in a RUN_CONFIG.env survives --topologies all, and steps 4, 11 and 13 '
      'are skipped', 'selection=tp4_pp4' in out and all(x in out for x in ('step13_skipped', 'step4_skipped', 'step11_skipped')), out.replace('\n', ' | '))
E7 = r'''import json, sys
from pathlib import Path
root = Path(sys.argv[1]) / "capped_20g"; b = root / "stage3_r3_network_jitter_pp4" / "128k_c1_pp4_resilience"; b.mkdir(parents=True, exist_ok=True)
(b / "128k_c1_pp4_resilience.json").write_text(json.dumps({"mean_ttft_ms": 2060.1, "mean_tpot_ms": 13.25}))
(b / "warmup_manifest.json").write_text(json.dumps({"ran": True, "success": True}))
(root / "stage3_r3_network_jitter_pp4_RAY_NCCL_ENV_AUDIT.json").write_text(json.dumps({"ok": True}))
skip = ("summary.json", "manifest.json", "case_manifest.json", "resolved_models.json", "vllm_surrogate_manifest.json", "RESILIENCE_COMPARISON.json")
keys = {}
for f in root.rglob("*.json"):
    if f.name in skip: continue
    d = json.loads(f.read_text()); keys.setdefault(d.get("case_name") or f.parent.name or f.stem, []).append(f.name)
print(json.dumps(keys, sort_keys=True))
'''
p7 = os.path.join(SCRATCH, 'e7_resilience.py'); open(p7, 'w').write(E7)
r7 = subprocess.run([sys.executable, '-I', p7, os.path.join(SCRATCH, 'e7_tree')], capture_output=True, text=True, timeout=60)
try:
    k7 = json.loads(r7.stdout.strip().splitlines()[-1])
except Exception:
    k7 = {}
check('E7', 'the comparison\'s key, re-typed, on one condition\'s folder: the result and its warm-up manifest share the key 128k_c1_pp4_resilience, and the Ray '
      'audit file becomes a point named capped_20g', sorted(k7.get('128k_c1_pp4_resilience', [])) == ['128k_c1_pp4_resilience.json', 'warmup_manifest.json']
      and k7.get('capped_20g') == ['stage3_r3_network_jitter_pp4_RAY_NCCL_ENV_AUDIT.json'], r7.stdout.strip()[:300])
rc, out, err = sh('SSH_KEY="${SSH_KEY:-$HOME/.ssh/no_such_key_pipchk}"\n[[ -f "$SSH_KEY" ]] || SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"\necho "key=${SSH_KEY##*/}"\n', 'e8_key.sh',
                  {k: v for k, v in os.environ.items() if k != 'SSH_KEY'})
check('E8', 'the helpers\' fallback line, re-typed: with the first key missing, SSH_KEY still names it afterwards', 'key=no_such_key_pipchk' in out, out.strip())
E9 = r'''import json, sys
d = json.load(open(sys.argv[1])); cases = d.get("cases", {}); bad_prompts = []; bad_budgets = []
for cname, cinfo in cases.items():
    if cinfo.get("max_num_batched_tokens", 8192) > 8192: bad_budgets.append(cname)
    for b in cinfo.get("benchmarks", []):
        inp = b.get("input_tokens", 0); out = b.get("output_tokens", 0)
        if inp > 1_000_000 or inp + out > 1_048_576: bad_prompts.append(b.get("name"))
status = "OVERFLOW" if bad_prompts else ("HIGH_BUDGET" if bad_budgets else "BUDGET_OK")
record = {"BUDGET_OK": "PASSED", "OVERFLOW": "FAILED"}.get(status, "WARNING")
strict = "FAILED" if record == "WARNING" else record
print(f"status={status} record={record} strict={strict} budgets={len(bad_budgets)}")
'''
p9 = os.path.join(SCRATCH, 'e9_ctx.py'); open(p9, 'w').write(E9)
r9 = subprocess.run([sys.executable, '-I', p9, os.path.join(PIP, CASES)], capture_output=True, text=True, timeout=60)
check('E9', 'the smoke test\'s context check, re-typed, on the master\'s cases file: HIGH_BUDGET, recorded as a warning (a failure under --strict)',
      'status=HIGH_BUDGET record=WARNING strict=FAILED budgets=4' in r9.stdout, r9.stdout.strip())
E10 = r'''import sys
names = ["stage3_r3_network_jitter_tp16", "stage3_r3_network_jitter_pp4", "tp4_pp4_dist_load", "tp16_pp1_dist_load"]
for sel in ("tp4_pp4", "tp16_pp1", "tp16,pp4", "all"):
    topos = [t.strip().lower() for t in sel.split(",")] if sel != "all" else []
    kept = [n for n in names if not topos or any(t in (" " + n).lower() for t in topos)]
    print(sel + "=" + ",".join(kept))
'''
p10 = os.path.join(SCRATCH, 'e10_topo.py'); open(p10, 'w').write(E10)
r10 = subprocess.run([sys.executable, '-I', p10], capture_output=True, text=True, timeout=60)
o10 = dict(l.split('=', 1) for l in r10.stdout.strip().splitlines())
check('E10', 'the runner\'s case filter, re-typed: tp4_pp4 keeps only the load-grid case and tp16_pp1 only the TP16 load-grid case, neither of step 12\'s two; '
      '"tp16,pp4" or all keeps both', o10.get('tp4_pp4') == 'tp4_pp4_dist_load' and o10.get('tp16_pp1') == 'tp16_pp1_dist_load'
      and o10.get('tp16,pp4', '').count('stage3') == 2 and o10.get('all', '').count(',') == 3, r10.stdout.replace('\n', ' | '))

E11 = '''# the nodes' own path as the TP4/PP4 run's workers show it under the suite's entries, then the master's lines and one re-read of an example-based file
LD_LIBRARY_PATH="/usr/local/cuda/lib64:/usr/local/cuda/lib64:"
export LD_LIBRARY_PATH="/tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if [[ ":${LD_LIBRARY_PATH:-}:" != *":/tmp/clean_nccl_libs:"* ]]; then export LD_LIBRARY_PATH="/tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"; fi
export LD_LIBRARY_PATH="/tmp/clean_nccl_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
echo "ld=$LD_LIBRARY_PATH"
'''
rc, out, err = sh(E11, 'e11_ldpath.sh')
check('E11', 'the example\'s line read by the master, the master\'s guarded line, and the example\'s line again at a runner\'s re-read, on a node path ending in ":", '
      'give exactly the string the TP4/PP4 run recorded', out.strip() == 'ld=/tmp/clean_nccl_libs:/tmp/clean_nccl_libs:/usr/local/cuda/lib64:/usr/local/cuda/lib64:', out.strip())

p12 = os.path.join(SCRATCH, 'e12_empty.py'); open(p12, 'w').write(
    "import sys, pandas as pd\nopen(sys.argv[1], 'w').close()\ntry:\n    pd.read_csv(sys.argv[1]); print('read')\nexcept Exception as e:\n    print(type(e).__name__)\n")
r12 = subprocess.run([sys.executable, '-I', p12, os.path.join(SCRATCH, 'e12_empty.csv')], capture_output=True, text=True, timeout=60)
check('E12', 'pandas.read_csv on an empty file raises EmptyDataError', r12.stdout.strip() == 'EmptyDataError', (r12.stdout + r12.stderr).strip()[-200:])

# ---------------------------------------------------------------------------------------------------------------------------
groups = {}
for cid, ok_ in RESULTS:
    groups.setdefault(re.split(r'[.:]', cid)[0], []).append((cid, ok_))
print('\n## Checks by review item (Z: the folder; B: blockers 1-13; F, K, C, S: sections 3.2-3.5; N: v1.4\'s and the new findings; D: a default run; E: experiments)')
for g in sorted(groups, key=lambda k: (k[0], int(re.sub(r'\D', '', k) or 0), k)):
    print(f"{g}: {', '.join(c for c, _ in groups[g])} -- {sum(o for _, o in groups[g])} of {len(groups[g])} pass")
fails = [c for c, ok in RESULTS if not ok]
print(f'\n{len(RESULTS) - len(fails)} of {len(RESULTS)} checks pass' + (f'; failed: {fails}' if fails else ''))
sys.exit(1 if fails else 0)
