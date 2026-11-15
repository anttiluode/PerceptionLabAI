"""005b: Held-out AB/BA order test after exploratory third-unit recruitment.

C=0.93 was chosen by a six-decay **post-hoc scan** on one AB and one BA
trial. Its result is NOT the preregistered 005. We lock C and all
thresholds first, then train/test on distinct trial perturbations.
"""
import argparse
import importlib.util
import json
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("lab005",ROOT/"experiments"/"005_order_of_falls"/"run.py")
lab=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

TRAIN=[(-3,30,.90),(-2,33,1.04),(-1,28,1.10),(0,32,1.00),
       (1,35,.94),(2,31,1.07),(3,29,.97),(-4,36,1.02)]
FRESH_TEST=[(5,34,.95),(-5,31,1.08),(2,40,.92),(0,37,1.13),
            (-2,42,1.00),(4,38,1.03),(-4,25,1.05),(1,43,.97)]
# Pooled open-loop calibration fixed from exploratory scan; no test labels.
CAL={
"3":{"trace_peak":.2766084566405938,"arm_threshold":.12447380548826721,
     "release_threshold":.05532169132811876},
"4":{"trace_peak":.22489778527827833,"arm_threshold":.10120400337522525,
     "release_threshold":.04497955705565567},
"5":{"trace_peak":.15069910639453591,"arm_threshold":.06781459787754025,
     "release_threshold":.030139821278906784}
}
OBSERVATION_TIMES=[160,240,360,520,650]

def graph(mode,order):
    if mode not in ("feedback","no_C","passive"):raise ValueError(mode)
    suffix="" if mode=="feedback" else "_"+mode
    path=ROOT/"workflows"/f"005_ABC093_{order}{suffix}.json"
    g=json.loads(path.read_text())
    for i in (3,4,5):
        n=next(n for n in g["nodes"] if n["id"]==i)
        assert abs(n["config"]["decay"]-[.86,.95,.93][i-3])<1e-8
        for k in ("arm_threshold","release_threshold"):
            assert abs(n["config"][k]-CAL[str(i)][k])<1e-8
    return g

def collect(upstream,mode,parameters):
    res={}
    for j,trial in enumerate(parameters):
        for order in ("AB","BA"):
            g=lab.prepare_trial(graph(mode,order),order,trial)
            res[(j,order)]=lab.simulate(g,upstream,steps=660)
    return res

def decode(train,test,t,feature_set,resolution=False):
    if resolution:
        floors=[.01*CAL[str(i)]["trace_peak"] for i in (3,4,5)]+[.001]*3
        train=lab.observed_resolution(train,floors)
        test=lab.observed_resolution(test,floors)
    model=lab.fit_linear(train,t,feature_set)
    return lab.test_linear(test,model,t),model

def run(upstream):
    modes={}
    for mode in ("feedback","no_C","passive"):
        train=collect(upstream,mode,TRAIN)
        held=collect(upstream,mode,FRESH_TEST)
        scores={}
        for t in OBSERVATION_TIMES:
            s={}
            for features in ("all_six","traces_only","spike_history_only"):
                raw,_=decode(train,held,t,features,False)
                robust,model=decode(train,held,t,features,True)
                s[features]={"raw":raw,"resolution_floor":robust}
                if t==360 and features=="all_six":
                    s[features]["frozen_model"]=model
            scores[str(t)]=s
        modes[mode]={
           "snapshots":scores,
           "heldout_spikes":lab.summarize_spikes(held),
           "examples":{order:held[(0,order)]["spikes"] for order in ("AB","BA")},
           "max_abs_field":max(z["max_abs_field"] for z in held.values()),
           "clipped_frames":sum(z["clipped_frames"] for z in held.values())
        }
    return {
      "experiment":"005b_C093_three_active_heldout",
      "status":"posthoc C-decay recruitment, independent new heldout examples",
      "source_scan":"results/005_C_recruitment.json",
      "train_pairs":TRAIN,"fresh_heldout_pairs":FRESH_TEST,
      "C_fixed_decay":.93,
      "calibration":CAL,"modes":modes,
      "caution":"posthoc model/parameter selection; small deterministic data; passive must be compared; no synaptic learning"
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--upstream",default="PerceptionLab")
    p.add_argument("--out",default="results/005b_three_active_heldout.json")
    a=p.parse_args()
    d=run(pathlib.Path(a.upstream))
    destination=ROOT/a.out;destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(d,indent=2)+"\n")
    print("BEGIN_005B_RECEIPT")
    print(json.dumps(d,indent=2))
    print("END_005B_RECEIPT")
