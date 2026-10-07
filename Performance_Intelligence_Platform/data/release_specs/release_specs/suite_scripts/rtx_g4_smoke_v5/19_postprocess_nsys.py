#!/usr/bin/env python3
"""Post-process every Nsight Systems report under a profile case.
Never equates aggregate GPU work with wall-clock critical path.
Tries version-specific NCCL reports opportunistically and records unsupported reports rather than failing.
"""
from __future__ import annotations
import argparse, csv, json, subprocess
from pathlib import Path

def run(cmd,timeout=600):
    try:
        p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,check=False)
        return p.returncode,p.stdout
    except Exception as e: return None,repr(e)

def csv_rows(p):
    try:
        with open(p,newline='') as f: return list(csv.DictReader(f))
    except Exception: return []

def fnum(v):
    try: return float(str(v).replace(',',''))
    except Exception: return 0.0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,default=None); a=ap.parse_args()
    root=a.root.resolve(); out=(a.out or root/'NSYS_ANALYSIS.json').resolve()
    reports=sorted(root.rglob('*.nsys-rep')); analyses=[]
    candidate_reports=['cuda_gpu_kern_sum','cuda_api_sum','nvtx_pushpop_sum','nccl_gpu_proj_sum','nccl_gpu_time_sum','nccl_op_sum']
    for rep in reports:
        rd=rep.parent/(rep.stem+'_processed'); rd.mkdir(exist_ok=True)
        rec={'report':str(rep),'size_bytes':rep.stat().st_size,'exports':{},'trace_role':'node1' if 'node1' in str(rep).lower() else 'node0_or_local'}
        sqlite=rd/(rep.stem+'.sqlite')
        rc,txt=run(['nsys','export','--type','sqlite','--output',str(sqlite),str(rep)])
        rec['sqlite']={'rc':rc,'path':str(sqlite),'exists':sqlite.exists(),'log':txt[-4000:]}
        for r in candidate_reports:
            cp=rd/(r+'.csv'); rc,txt=run(['nsys','stats','--format','csv','--report',r,str(rep)])
            if rc==0 and txt.strip(): cp.write_text(txt)
            rec['exports'][r]={'rc':rc,'path':str(cp),'exists':cp.exists(),'error_tail':None if rc==0 else txt[-1500:]}
        kern=csv_rows(rd/'cuda_gpu_kern_sum.csv')
        total_ns=sum(fnum(x.get('Total Time (ns)',0)) for x in kern)
        nccl=[x for x in kern if 'nccl' in (x.get('Name') or '').lower()]
        rec['kernel_rows']=len(kern); rec['aggregate_gpu_work_ms']=total_ns/1e6
        rec['nccl_kernel_rows']=len(nccl); rec['nccl_kernel_instances']=sum(int(fnum(x.get('Instances',x.get('Calls',0)))) for x in nccl)
        rec['warning']='aggregate_gpu_work_ms is summed GPU work across streams/devices, NOT wall-clock critical path'
        analyses.append(rec)
    manifests=list(root.rglob('PROFILE_CASE_MANIFEST.json'))
    status=[]
    for m in manifests:
        try: d=json.loads(m.read_text()); status.append({'path':str(m),'topology':d.get('topology'),'mode':d.get('mode'),'status':d.get('status'),'bench_exit_code':d.get('bench_exit_code')})
        except Exception as e: status.append({'path':str(m),'error':repr(e)})
    payload={'root':str(root),'nsys_report_count':len(reports),'reports':analyses,'profile_manifests':status,
             'trace_completeness':{'has_node0_report':any(x['trace_role']=='node0_or_local' for x in analyses),'has_node1_report':any(x['trace_role']=='node1' for x in analyses)},
             'guardrail':'Exact TP/PP/compute overlap attribution requires timeline/NVTX correlation. Do not sum per-rank kernel totals as request latency.'}
    out.write_text(json.dumps(payload,indent=2)); print(json.dumps({'out':str(out),'reports':len(reports)},indent=2))
if __name__=='__main__': main()
