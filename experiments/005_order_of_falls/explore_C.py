"""Post-hoc 005 C-node recruitment scan. Exploratory; NOT used to tune original held-out result."""
import argparse
import importlib.util
import json
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("lab005",ROOT/"experiments"/"005_order_of_falls"/"run.py")
lab=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

C_DECAYS=[.70,.80,.86,.90,.93,.975]

def adapt(graph,decay,arm=None,release=None):
    node=next(n for n in graph["nodes"] if n["id"]==5)
    node["config"]["decay"]=float(decay)
    if arm is not None:
        node["config"]["arm_threshold"]=float(arm)
        node["config"]["release_threshold"]=float(release)
    return graph

def explore(upstream):
    report=[]
    for decay in C_DECAYS:
        # Pooled open-loop trace peak; no oscillator return pulses anywhere.
        peaks={}
        for order in ("AB","BA"):
            g=adapt(lab.read_graph("passive",order),decay)
            g=lab.prepare_trial(g,order,(0,32,1.))
            r=lab.simulate(g,upstream,steps=230)
            peaks[order]=r["trace_peaks"]["5"]
        maxpeak=max(peaks.values())
        arm=.45*maxpeak;release=.20*maxpeak
        cases={}
        for mode in ("feedback","no_C"):
            for order in ("AB","BA"):
                g=adapt(lab.read_graph(mode,order),decay,arm,release)
                g=lab.prepare_trial(g,order,(0,32,1.0))
                r=lab.simulate(g,upstream,steps=660)
                cases[mode+"_"+order]={
                    "all_spikes":{k:len(v) for k,v in r["spikes"].items()},
                    "late_spikes":{k:sum(t>=160 for t in v)
                                   for k,v in r["spikes"].items()},
                    "C_spike_times":r["spikes"]["5"],
                    "clipped_frames":r["clipped_frames"]
                }
        report.append({"decay":decay,"open_loop_C_peak":maxpeak,
                       "C_arm":arm,"C_release":release,
                       "conditions":cases})
    return {
        "study":"005_C_exploration",
        "status":"posthoc parameter scan, same wave and A/B parameters",
        "meaning":"Search whether third history node participates in spike trains; this data must not be reused as an independent held-out test.",
        "tested_decays":C_DECAYS,
        "results":report
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--upstream",default="PerceptionLab")
    p.add_argument("--out",default="results/005_C_recruitment.json")
    a=p.parse_args()
    d=explore(pathlib.Path(a.upstream))
    out=ROOT/a.out;out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(d,indent=2)+"\n")
    print("BEGIN_C005_RECEIPT")
    print(json.dumps(d,indent=2))
    print("END_C005_RECEIPT")
