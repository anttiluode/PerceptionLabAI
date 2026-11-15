"""Long-horizon 004 verification, same upstream WaveField and saved graph.

Goal: distinguish a brief alternating transient from long-lived mutual
regeneration; contrast gain 0.30/0.45 against 0.50, no-B feedback, and
swapped temporal/spatial identities.
"""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
import pathlib
import statistics
import sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("lab004",ROOT/"experiments"/"004_two_histories"/"run.py")
lab=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

def load_graph(stem):
    return json.loads((ROOT/"workflows"/stem).read_text())

def apply_strength(graph,value):
    g=copy.deepcopy(graph)
    found=False
    for e in g["edges"]:
        if e["from_node_id"]==2 and e["to_node_id"]==1 and e["from_port"]=="pulse":
            e["learned_weight"]=value
            found=True
    if not found:raise RuntimeError("A return pulse edge missing")
    return g

def window_counts(spikes,steps):
    bins={}
    for name,seq in spikes.items():
        bins[name]=[
            sum(lo<=t<hi for t in seq)
            for lo,hi in ((0,steps//4),(steps//4,steps//2),
                          (steps//2,3*steps//4),(3*steps//4,steps))
        ]
    return bins

def long_run(upstream,steps=1800):
    baseline=load_graph("004_two_fades_one_field.json")
    no_b=load_graph("004_weak_a_without_b_return.json")
    swapped_decay=load_graph("004_swap_decay.json")
    swapped_sites=load_graph("004_swap_sites.json")
    basecal=lab.calibrate(upstream,baseline)
    cases={
        "weak_0.30":(apply_strength(baseline,.30),basecal),
        "weak_0.45":(apply_strength(baseline,.45),basecal),
        "strong_0.50":(apply_strength(baseline,.50),basecal),
        "weak_0.30_without_B_return":(apply_strength(no_b,.30),basecal),
        "weak_0.30_swap_decay":(apply_strength(swapped_decay,.30),
                                 lab.calibrate(upstream,swapped_decay)),
        "weak_0.30_swap_sites":(apply_strength(swapped_sites,.30),
                                 lab.calibrate(upstream,swapped_sites)),
    }
    results={}
    for name,(g,cal) in cases.items():
        r=lab.run_case(upstream,g,cal,steps)
        r["quarter_spikes"]=window_counts(r["spike_times"],steps)
        results[name]=r
    return {"experiment":"004_long_horizon",
            "upstream":"PerceptionLab main, actual 96x96 WaveField",
            "steps":steps,"conditions":results,
            "interpretation":"Deterministic long-run intervention, not a robustness claim across seeds, biology, or learning."}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--upstream",default="PerceptionLab")
    p.add_argument("--steps",type=int,default=1800)
    p.add_argument("--out",default="results/004_two_histories_long.json")
    a=p.parse_args()
    result=long_run(pathlib.Path(a.upstream),a.steps)
    destination=ROOT/a.out
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({
        "experiment":result["experiment"],
        "steps":a.steps,
        "cases":{name:{
            "quarter_spikes":r["quarter_spikes"],
            "period_A":r["phase"]["a"]["mean_isi"],
            "period_B":r["phase"]["b"]["mean_isi"],
            "phase_R":r["phase"]["phase_concentration_r"],
            "interleaving":r["phase"]["interleaving_fraction"],
            "clip_frames":r["energy"]["saturated_frames"]
        } for name,r in result["conditions"].items()}
    },indent=2))
