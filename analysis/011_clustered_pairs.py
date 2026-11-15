"""011 independent-seed audit; does NOT alter training or saved simulation.

Each held-out seed ID is reused across four crossed first/second histories.
Counting all 64 as independent replicates in a paired sign p-value would
be pseudoreplication. This audit aggregates the four paired outcomes per ID
and runs an EXACT two-sided sign test across the 16 independent seed IDs.

Added before the full 011 result was available. Displays per-example
accuracy and per-seed comparisons without re-fitting any reader.
"""
import argparse
import json
from collections import defaultdict
from math import comb
from pathlib import Path

def sign_p(w,l):
    n=w+l
    if n==0:return 1.0
    return min(1.,2*sum(comb(n,i) for i in range(min(w,l)+1))/2**n)

def cluster_compare(A,B,kind="both"):
    a=A["per_body"];b=B["per_body"]
    assert set(a)==set(b)
    by_seed=defaultdict(lambda:[0,0,0])
    for key in a:
        seed=int(key.split(":")[0])
        by_seed[seed][0]+=int(a[key][kind])
        by_seed[seed][1]+=int(b[key][kind])
        by_seed[seed][2]+=1
    assert all(n==4 for _,_,n in by_seed.values()),"Need four crosses/seed"
    aw=sum(i>j for i,j,_ in by_seed.values())
    bw=sum(j>i for i,j,_ in by_seed.values())
    return {"independent_seed_ids":len(by_seed),"first_wins":aw,
            "second_wins":bw,"ties":len(by_seed)-aw-bw,
            "cluster_sign_p":round(sign_p(aw,bw),8),
            "four_crosses_per_seed":True}

def analyse(result):
    assert result["experiment"]=="011_independent_dual_history"
    checkpoints=result["checkpoints"]
    stage=str(checkpoints[-1])
    conditions=result["conditions"]
    output={"readout_stage":stage,"smoke":result["smoke_not_scientific"],
            "final":{},"clustered_paired":{}}
    for mode,rec in conditions.items():
        v=rec["stage"][stage]
        output["final"][mode]={k:v[k] for k in
             ("old_correct","new_correct","joint_correct","of",
              "old_accuracy","new_accuracy","joint_accuracy")}
    for other in ("soft","use","frozen"):
        output["clustered_paired"]["age_vs_"+other]={kind:cluster_compare(
            conditions["age"]["stage"][stage],
            conditions[other]["stage"][stage],kind)
            for kind in ("both","old","new")}
    return output

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("receipt",nargs="?",default="results/011_dual_history.json")
    a=p.parse_args()
    data=json.loads(Path(a.receipt).read_text())
    print(json.dumps(analyse(data),indent=2))
