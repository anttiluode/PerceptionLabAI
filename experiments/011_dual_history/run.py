"""011 — old wood, new history: *independent* first and second event orders.

Four crossed conditions AB->AB, AB->BA, BA->AB, BA->BA; 20+20
episodes; fixed 010 mechanism. The two readouts are fit only on
training body IDs, and the old one is frozen before second history.

Pre-result protocol / pass rule: see README committed before this file.
"""
from __future__ import annotations
import argparse
import json
import pathlib
import random
import statistics
import sys
import time
from multiprocessing import Pool
from importlib.util import spec_from_file_location, module_from_spec
import numpy as np

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tests"))

def _imp(name,path):
    s=spec_from_file_location(name,ROOT/path)
    m=module_from_spec(s)
    sys.modules[name]=m
    s.loader.exec_module(m)
    return m

r9=_imp("run009_011","experiments/009_morphology_as_memory/run.py")
r10=_imp("run010_011","experiments/010_hardening/run.py")
core=r9.core

FIRST_EPISODES=20
SECOND_EPISODES=20
CHECKPOINTS=(10,20)
TRAIN_IDS=8
HELDOUT_IDS=16
SEED=11011
SMOKE_SEED=771011
LABELS=("AB","BA")
CONDITIONS=("soft","use","age","frozen")
PRIMARY_OLD_MIN=.75
PRIMARY_NEW_MIN=.70
RIDGE=.25
T=r9.PRIMARY_SNAPSHOT

def init_worker(upstream,thresholds):
    # Explicit worker initialization for Windows 'spawn' compatibility;
    # the 009/010 source uses module-level paths/calibration.
    r9.UP=pathlib.Path(upstream)
    r9.TH=thresholds

def params_for(mode):
    if mode not in CONDITIONS:raise ValueError(mode)
    return r10.params("soft" if mode=="frozen" else mode)

def first_stage(job):
    bp,old,P,n_episodes=job
    rng=random.Random(bp["seed"])
    state=core.uniform_structure(P["budget"])
    clipped=0
    for _ in range(n_episodes):
        result=core.episode(state,r9.TH,r9.UP,old,
            bp["gap"]+rng.randint(-3,3),bp["scale"],
            r9.EP_STEPS,learn=1,params=P,jitter=rng.randint(-5,5))
        state=result["structure"]
        clipped+=result["clipped_frames"]
    return {"id":bp["id"],"old":old,"state":state,"clip":clipped}

def second_stage(job):
    bp,old,new,P,first,n_episodes,checkpoints=job
    state=first["state"]
    result={"id":bp["id"],"old":old,"new":new,"first":state,
            "after":{},"clip":0}
    rng=random.Random(bp["seed"] ^ 0x5F3759DF)
    for episode in range(1,n_episodes+1):
        r=core.episode(state,r9.TH,r9.UP,new,
            bp["gap"]+rng.randint(-3,3),bp["scale"],
            r9.EP_STEPS,learn=1,params=P,jitter=rng.randint(-5,5))
        state=r["structure"];result["clip"]+=r["clipped_frames"]
        if episode in checkpoints:
            result["after"][episode]=state
    return result

def probe_structure(state):
    # Fresh source + wave + fade units + spike EMA; no carry of fast state.
    # The unique stored object is structure (weights/alive/hardness).
    return r9.probe_body((state,"probe"))[T]

def measured(values,floors):
    return [0. if abs(float(v))<fl else float(v)
            for v,fl in zip(values,floors)]

def fit(train,dimension=6):
    """Ridge in standardized, TRAINING-only coordinates."""
    X=np.asarray([v for v,label in train],float)
    y=np.asarray([1. if label=="AB" else -1. for v,label in train],float)
    assert X.ndim==2 and X.shape[1]==dimension
    assert np.count_nonzero(y==1)==np.count_nonzero(y==-1)
    means=X.mean(0);stds=np.maximum(X.std(0),1e-6)
    Z=(X-means)/stds
    lam=RIDGE
    wy=np.linalg.solve(Z.T@Z+lam*np.eye(dimension),Z.T@(y-y.mean()))
    w=wy/stds
    bias=float(y.mean()-w@means)
    return {"weights":list(map(float,w)),"bias":bias,
            "ridge":RIDGE,"n_training":len(train)}

def score_features(model,values):
    return float(np.dot(values,model["weights"])+model["bias"])

def correct(model,features,label):
    v=score_features(model,features)
    return v>=0 if label=="AB" else v<0

def eval_first(model,features):
    pred={}
    for (idx,old),x in features.items():
        pred[f"{idx}:{old}"]=bool(correct(model,x,old))
    return {"correct":sum(pred.values()),"of":len(pred),
            "accuracy":round(sum(pred.values())/len(pred),4),
            "per_body":pred}

def eval_both(old_model,new_model,features):
    per={};oldcorrect=newcorrect=both=0
    for (idx,old,new),v in sorted(features.items()):
        oc=bool(correct(old_model,v,old))
        nc=bool(correct(new_model,v,new))
        key=f"{idx}:{old}:{new}"
        per[key]={"old":oc,"new":nc,"both":oc and nc}
        oldcorrect+=oc;newcorrect+=nc;both+=(oc and nc)
    total=len(per)
    return {
      "old_correct":oldcorrect,"new_correct":newcorrect,
      "joint_correct":both,"of":total,
      "old_accuracy":round(oldcorrect/total,4),
      "new_accuracy":round(newcorrect/total,4),
      "joint_accuracy":round(both/total,4),
      "per_body":per
    }

def paired(a,b,kind):
    A=a["per_body"];B=b["per_body"]
    assert A.keys()==B.keys()
    w=sum(A[k][kind] and not B[k][kind] for k in A)
    l=sum(B[k][kind] and not A[k][kind] for k in A)
    return {"first_only_correct":w,"second_only_correct":l,
            "two_sided_sign_p":r9.sign_p(w,l)}

def weight_distance(a,b):
    x=np.asarray(a["weights"],float)
    y=np.asarray(b["weights"],float)
    return float(np.abs(x-y).sum())

def living_count(st):
    return sum(sum(map(bool,row)) for row in st["alive"])

def prepare_ids(smoke):
    ntrain,ntest=(2,2) if smoke else (TRAIN_IDS,HELDOUT_IDS)
    ids=r9.body_params(SMOKE_SEED if smoke else SEED,ntrain+ntest)
    assert len({x["id"] for x in ids})==len(ids)
    return ids,{x["id"] for x in ids[:ntrain]},ntrain,ntest

def run(upstream,smoke=False,workers=4):
    upstream=pathlib.Path(upstream)
    start=time.time()
    cal=core.calibrate(upstream)
    th=cal["thresholds"]
    floors=[.01*x for x in cal["peaks"]]+[.001]*len(cal["peaks"])
    ids,train_ids,ntrain,ntest=prepare_ids(smoke)
    f_ep=2 if smoke else FIRST_EPISODES
    s_ep=2 if smoke else SECOND_EPISODES
    checks=(1,2) if smoke else CHECKPOINTS
    output={
       "experiment":"011_independent_dual_history",
       "smoke_not_scientific":smoke,
       "upstream":"Original 96x96 WaveFieldNode plus fading and GrowingReturn nodes",
       "design":"Four independent crosses AB/AB AB/BA BA/AB BA/BA",
       "first_episodes":f_ep,"second_episodes":s_ep,
       "checkpoints":checks,
       "n_training_ids":ntrain,"n_heldout_ids":ntest,
       "train_examples_per_condition":4*ntrain,
       "heldout_examples_per_condition":4*ntest,
       "calibration":cal,"floors":floors,
       "params":{"soft":params_for("soft"),
                 "use":params_for("use"),
                 "age":params_for("age"),
                 "frozen":params_for("frozen")},
       "old_reader_fit":"after first history, training IDs only, frozen thereafter",
       "new_reader_fit":"after SECOND history, training IDs only, untouched heldout",
       "decision_rule":"age old >=.75; new>=.70; joint age>soft with paired two-sided sign p<.05",
       "conditions":{},"paired":{}
    }
    with Pool(processes=workers,initializer=init_worker,
              initargs=(str(upstream),th)) as pool:
        for mode in CONDITIONS:
            p=params_for(mode)
            # Frozen and soft share exactly the same first stage.
            # Repeating it here would be redundant but the same histories
            # and deterministic seeds are used for all conditions.
            jobs=[(bp,old,p,f_ep) for bp in ids for old in LABELS]
            first=pool.map(first_stage,jobs)
            by_first={(r["id"],r["old"]):r for r in first}
            keys_first=sorted(by_first)
            X1=dict(zip(keys_first,pool.map(probe_structure,
                               [by_first[k]["state"] for k in keys_first])))
            X1={k:measured(v,floors) for k,v in X1.items()}
            trainold=[(X1[k],k[1]) for k in keys_first if k[0] in train_ids]
            old_model=fit(trainold)
            heldold={k:v for k,v in X1.items() if k[0] not in train_ids}
            old_initial=eval_first(old_model,heldold)
            print(f"{mode}: initial old {old_initial['correct']}/{old_initial['of']}",flush=True)

            crossed=[(bp,old,new) for bp in ids
                     for old in LABELS for new in LABELS]
            if mode=="frozen":
                # No learning during stage 2; after all fast resets,
                # its structure is EXACTLY the stage-1 structure.
                second=[{"id":bp["id"],"old":old,"new":new,
                    "first":by_first[(bp["id"],old)]["state"],
                    "after":{c:by_first[(bp["id"],old)]["state"]
                             for c in checks},"clip":0}
                    for bp,old,new in crossed]
            else:
                job2=[(bp,old,new,p,by_first[(bp["id"],old)],
                       s_ep,checks) for bp,old,new in crossed]
                second=pool.map(second_stage,job2)
            by_cross={(v["id"],v["old"],v["new"]):v for v in second}
            keys=sorted(by_cross)
            stages={}
            for checkpoint in checks:
                vals=pool.map(probe_structure,
                       [by_cross[k]["after"][checkpoint] for k in keys])
                stages[checkpoint]={k:measured(v,floors)
                        for k,v in zip(keys,vals)}
            end=stages[checks[-1]]
            trainnew=[(end[k],k[2]) for k in keys if k[0] in train_ids]
            new_model=fit(trainnew)
            bycheckpoint={}
            for checkpoint in checks:
                held={k:v for k,v in stages[checkpoint].items()
                      if k[0] not in train_ids}
                bycheckpoint[str(checkpoint)]=eval_both(old_model,new_model,held)
            change=statistics.mean(weight_distance(
                    v["first"],v["after"][checks[-1]]) for v in second)
            alive=statistics.mean(living_count(v["after"][checks[-1]])
                     for v in second)
            clips=sum(r["clip"] for r in first)+sum(r["clip"] for r in second)
            output["conditions"][mode]={
                "old_model":old_model,"new_model":new_model,
                "old_before_second":old_initial,
                "stage":bycheckpoint,
                "mean_absolute_weight_change":round(change,6),
                "living_branches_mean":round(alive,3),
                "clipped_frames":clips,
                "elapsed_seconds":round(time.time()-start,2)
            }
            last=bycheckpoint[str(checks[-1])]
            print(f"{mode}: after {checks[-1]} OLD {last['old_correct']}/{last['of']} "
                  f"NEW {last['new_correct']}/{last['of']} "
                  f"BOTH {last['joint_correct']}/{last['of']} "
                  f"change {change:.4f}; {time.time()-start:.1f}s",flush=True)
    c=output["conditions"]
    for other in ("soft","use","frozen"):
        output["paired"]["age_vs_"+other+"_joint_final"]=paired(
            c["age"]["stage"][str(checks[-1])],
            c[other]["stage"][str(checks[-1])],"both")
        output["paired"]["age_vs_"+other+"_old_final"]=paired(
            c["age"]["stage"][str(checks[-1])],
            c[other]["stage"][str(checks[-1])],"old")
        output["paired"]["age_vs_"+other+"_new_final"]=paired(
            c["age"]["stage"][str(checks[-1])],
            c[other]["stage"][str(checks[-1])],"new")
    f=c["age"]["stage"][str(checks[-1])]
    p=output["paired"]["age_vs_soft_joint_final"]["two_sided_sign_p"]
    output["prespecified_pass"]=bool(
        not smoke and f["old_accuracy"]>=PRIMARY_OLD_MIN and
        f["new_accuracy"]>=PRIMARY_NEW_MIN and
        f["joint_correct"]>c["soft"]["stage"][str(checks[-1])]["joint_correct"]
        and p<.05)
    output["total_seconds"]=round(time.time()-start,2)
    return output

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--upstream",default="PerceptionLab")
    ap.add_argument("--workers",type=int,default=4)
    ap.add_argument("--smoke",action="store_true")
    ap.add_argument("--out",default=None)
    args=ap.parse_args()
    outname=args.out or ("results/011_dual_history_smoke.json"
                 if args.smoke else "results/011_dual_history.json")
    result=run(args.upstream,args.smoke,args.workers)
    dest=ROOT/outname;dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+"\n")
    print("BEGIN_011_SUMMARY")
    print(json.dumps({
       "smoke":args.smoke,"prespecified_pass":result["prespecified_pass"],
       "stages":{key:{k:{"old":v["old_correct"],"new":v["new_correct"],
                            "joint":v["joint_correct"],"n":v["of"]}
                      for k,v in condition["stage"].items()}
                 for key,condition in result["conditions"].items()},
       "paired":result["paired"],"seconds":result["total_seconds"]
    },indent=2))
    print("END_011_SUMMARY")
