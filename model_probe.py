#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,platform,subprocess,sys,time
from pathlib import Path
from config import load_json

def capture(cmd):
    try:
        p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120,check=False)
        return {'cmd':cmd,'rc':p.returncode,'out':p.stdout}
    except Exception as e:return {'cmd':cmd,'rc':None,'error':repr(e)}

def flatten_config(cfg):
    """Capture architecture fields without assuming a flat HF config.

    Multimodal/model-wrapper configs (for example DeepSeek V4.1) expose the
    language model under ``text_config``.  We preserve top-level provenance,
    then merge non-null text fields for serving-matrix decisions.  Nothing is
    synthesized when a field is absent.
    """
    keys=['model_type','architectures','hidden_size','num_hidden_layers','num_attention_heads','num_key_value_heads',
          'max_position_embeddings','model_max_length','torch_dtype','dtype','n_routed_experts','num_experts','num_local_experts',
          'num_experts_per_tok','num_experts_per_token','moe_intermediate_size','index_n_heads','index_head_dim','index_topk',
          'q_lora_rank','o_lora_rank','head_dim','sliding_window','expert_dtype','kv_lora_rank','qk_nope_head_dim','qk_rope_head_dim','v_head_dim']
    out={}
    def add_from(obj,prefix=None):
        if obj is None: return
        for k in keys:
            v=getattr(obj,k,None)
            if v is None: continue
            key=k if prefix is None or k not in out else f'{prefix}.{k}'
            try: json.dumps(v); out[key]=v
            except Exception: out[key]=str(v)
    add_from(cfg)
    text_cfg=getattr(cfg,'text_config',None)
    if text_cfg is not None:
        # Language-model fields are the serving fields.  Keep wrapper identity
        # but let text_config fill fields missing at top level.
        for k in keys:
            if k in out: continue
            v=getattr(text_cfg,k,None)
            if v is None: continue
            try: json.dumps(v); out[k]=v
            except Exception: out[k]=str(v)
        out['has_text_config']=True
    qc=getattr(cfg,'quantization_config',None)
    if qc is not None:
        try: qcd=qc if isinstance(qc,dict) else qc.to_dict()
        except Exception: qcd={'raw':str(qc)}
        out['quantization_config']=qcd
        if isinstance(qcd,dict) and qcd.get('expert_dtype') is not None and out.get('expert_dtype') is None:
            out['expert_dtype']=qcd['expert_dtype']
    # Record the resolved HF snapshot when transformers exposes it.  This is
    # provenance only and is never used to fabricate a revision.
    ch=getattr(cfg,'_commit_hash',None)
    if ch: out['resolved_commit_hash']=str(ch)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--model-profile',required=True); ap.add_argument('--out',required=True); ap.add_argument('--local-files-only',action='store_true'); a=ap.parse_args()
    profile,_=load_json(a.model_profile); outp=Path(a.out); outp.parent.mkdir(parents=True,exist_ok=True)
    rec={'schema_version':2,'time':time.time(),'model':profile['model'],'revision':profile.get('revision'),'profile_id':profile['profile_id'],'precision_label':profile.get('precision_label'),'host':platform.node(),'python':sys.version,'expected_config':profile.get('expected_config',{}),'checks':{},'actual_config':{},'status':'UNKNOWN'}
    rec['commands']={'nvidia_smi':capture(['nvidia-smi','--query-gpu=index,name,memory.total,compute_cap','--format=csv,noheader,nounits']), 'vllm_version':capture(['vllm','--version'])}
    try:
        cfg = None
        try:
            from vllm.transformers_utils.config import get_config
            cfg = get_config(profile['model'], revision=profile.get('revision'), trust_remote_code=bool(profile.get('trust_remote_code')))
        except Exception:
            from transformers import AutoConfig
            cfg=AutoConfig.from_pretrained(profile['model'],revision=profile.get('revision'),trust_remote_code=bool(profile.get('trust_remote_code')),local_files_only=a.local_files_only)
        
        actual=flatten_config(cfg); rec['actual_config']=actual
        failures=[]; warnings=[]
        for k,v in (profile.get('expected_config') or {}).items():
            av=actual.get(k)
            if av is None: warnings.append(f'{k}: not exposed by AutoConfig')
            elif av!=v: failures.append(f'{k}: expected {v!r}, got {av!r}')
        maxpos=actual.get('max_position_embeddings')
        if maxpos is not None and int(profile['max_model_len'])>int(maxpos): failures.append(f"profile max_model_len={profile['max_model_len']} exceeds model max_position_embeddings={maxpos}")
        rec['checks']={'expected_config_failures':failures,'warnings':warnings}; rec['status']='PASS' if not failures else 'FAIL'
    except Exception as e:
        rec['status']='PROBE_FAILED'; rec['error']=repr(e)
    outp.write_text(json.dumps(rec,indent=2,default=str)+'\n'); print(json.dumps({'status':rec['status'],'out':str(outp)},indent=2))
    if rec['status']!='PASS': raise SystemExit(2)
if __name__=='__main__': main()
