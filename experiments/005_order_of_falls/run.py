"""005: can a future *unlabeled* population readout decode earlier AB vs BA?

The experiment loads real PerceptionLab source/WaveField/fade code and real
saved JSON edges. Stimuli have identical counts, timing slots, amplitude,
duration and site usage; ONLY which site fires first differs.
Train on one set of timing/amplitude perturbations, score unseen pairs.
Readout receives no teacher label or access to pulse-source states.
Passive-field and no-C-return controls avoid overclaiming recurrent memory.

The node probe is a read-only linear functional of 3 current fade traces and
3 decaying counts of recent spikes. Its short spike integrators are an
additional readout memory; interpret accordingly.
"""
from __future__ import annotations
import argparse
import copy
import json
import pathlib
import sys
import math

import numpy as np

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load

NAMES={
    "PulseSourceNode":"pulsesourcenode.py",
    "WaveFieldNode":"wavefieldnode.py",
    "FadingHistorySpikeNode":"fading_history_spike_node.py",
    "PopulationOrderReadoutNode":"population_order_readout_node.py",
    "SignalPlotterNode":"signalplotternode.py"
}
WPATH=ROOT/"workflows"
NODE_IDS=(3,4,5)
READOUT_ID=6
SNAPSHOTS=[160,240,360,520,650]
TRIAL_STEPS=660
# Parameters chosen before reading measurements. Same pair parameters for AB/BA.
TRAIN=[(j,g,a) for j,g,a in [
    (-3,30,.90),(-2,33,1.04),(-1,28,1.10),(0,32,1.00),
    (1,35,.94),(2,31,1.07),(3,29,.97),(-4,36,1.02)
]]
TEST=[(j,g,a) for j,g,a in [
    (4,29,.93),(-3,34,1.09),(2,37,.98),(0,28,1.06),
    (-1,34,.91),(3,32,1.03),(-4,30,1.11),(1,36,.96)
]]


def node_source(name,upstream):
    return (ROOT/"nodes"/NAMES[name]
            if name in ("FadingHistorySpikeNode","PopulationOrderReadoutNode")
            else pathlib.Path(upstream)/"nodes"/NAMES[name])


def instantiate(graph,upstream,fast_render=True):
    items={}
    for desc in graph["nodes"]:
        klass=load(node_source(desc["class_name"],upstream),desc["class_name"])
        unit=klass()             # EXACT host no-arg constructor
        config=copy.deepcopy(desc.get("config",{}))
        if hasattr(unit,"set_config_options"):
            unit.set_config_options(config)
        for key,val in config.items():
            if hasattr(unit,key):
                existing=getattr(unit,key)
                if existing != val:
                    setattr(unit,key,val)
        items[desc["id"]]=unit
    wave=items[2]
    if wave.field.shape!=(96,96):
        raise RuntimeError("The saved size was not applied: "+str(wave.field.shape))
    for edge in graph["edges"]:
        a=items[edge["from_node_id"]];b=items[edge["to_node_id"]]
        if edge["from_port"] not in a.outputs:
            raise RuntimeError("Output port missing: "+str(edge))
        if edge["to_port"] not in b.inputs:
            raise RuntimeError("Input port missing: "+str(edge))
        if a.outputs[edge["from_port"]] != b.inputs[edge["to_port"]]:
            raise RuntimeError("Port types differ: "+str(edge))
    if fast_render:
        # The simulation state update is untouched. Skip ONLY expensive
        # OpenCV drawing; the GUI still renders all four components.
        wave._render=lambda:None
        for i in NODE_IDS:
            items[i]._render=lambda *args:None
        for i in (0,1):
            items[i]._render=lambda:None
        items[READOUT_ID]._render=lambda:None
    return items


def read_graph(kind="feedback",order="AB"):
    suffix={"feedback":"","passive":"_no_return","no_C":"_slow_disconnected"}[kind]
    path=WPATH/("005_"+order+("_three_histories" if not suffix else suffix)+".json")
    g=json.loads(path.read_text())
    return g


def prepare_trial(graph,order,trial):
    """Paired perturbation: jitter, gap, amplitude identical in AB and BA."""
    jitter,gap,scale=trial
    if not (order in ("AB","BA") and 20<=gap<=50):
        raise ValueError("Invalid trial")
    g=copy.deepcopy(graph)
    early=40+jitter
    late=early+gap
    for i in (0,1):
        conf=next(n["config"] for n in g["nodes"] if n["id"]==i)
        conf["warmup"]=(early if (i==0)==(order=="AB") else late)
        conf["amplitude"]=.12*scale
    return g


def simulate(graph,upstream,steps=TRIAL_STEPS,
             reset_at=None,reset_kind=None):
    obj=instantiate(graph,upstream)
    active={i:obj[i] for i in range(7)}  # two stimuli, one wave, three fades, probe
    edges=[e for e in graph["edges"] if e["to_node_id"] in active]
    captures={}
    traces={i:[] for i in NODE_IDS}
    pulses={i:[] for i in NODE_IDS}
    maxfield=0.0
    clipframes=0
    peak_energy=0.0
    for tick in range(steps):
        if reset_at is not None and tick==reset_at:
            if reset_kind=="wave":
                obj[2].field[:]=0.
                obj[2].vel[:]=0.
                obj[2].read_values[:]=0.
                obj[2].energy_value=0.
            elif reset_kind=="traces":
                for i in NODE_IDS:
                    obj[i]._reset()
                obj[6].spike_memory[:]=0.
            else:
                raise ValueError("unknown reset kind")
        for n in active.values():
            n.pre_step()
        for e in edges:
            a=active[e["from_node_id"]]
            b=active[e["to_node_id"]]
            val=a.get_output(e["from_port"])
            if val is not None:
                b.set_input(e["to_port"],val,a.outputs[e["from_port"]],
                            e.get("learned_weight",1.0))
        for n in active.values():
            n.step()
        for i in NODE_IDS:
            traces[i].append(float(obj[i].trace))
            if obj[i].pulse:
                pulses[i].append(tick)
        fmax=float(np.max(np.abs(obj[2].field)))
        maxfield=max(fmax,maxfield)
        clipframes+=int(fmax>=3.9998)
        peak_energy=max(peak_energy,float(obj[2].energy_value))
        if tick in SNAPSHOTS:
            captures[tick]=[float(v) for v in obj[6].features]
    return {
        "features":captures,
        "spikes":{str(i):pulses[i] for i in NODE_IDS},
        "max_abs_field":round(maxfield,7),
        "clipped_frames":clipframes,
        "peak_energy":round(peak_energy,8),
        "trace_last":{str(i):round(traces[i][-1],8) for i in NODE_IDS}
    }


def calibrate(upstream):
    """One pooled, label-blind open-loop calibration, frozen for all variants."""
    peaks={str(i):0.0 for i in NODE_IDS}
    for order in ("AB","BA"):
        graph=prepare_trial(read_graph("passive",order),order,(0,32,1.0))
        obj=instantiate(graph,upstream)
        edges=[e for e in graph["edges"] if e["to_node_id"] in range(7)]
        for tick in range(240):
            for i in range(7):obj[i].pre_step()
            for e in edges:
                a=obj[e["from_node_id"]]
                b=obj[e["to_node_id"]]
                v=a.get_output(e["from_port"])
                if v is not None:b.set_input(e["to_port"],v,
                    a.outputs[e["from_port"]],e.get("learned_weight",1.))
            for i in range(7):obj[i].step()
            for i in NODE_IDS:
                peaks[str(i)]=max(peaks[str(i)],float(obj[i].trace))
    if min(peaks.values())<1e-8:
        raise RuntimeError("Some readouts did not receive open-loop pulses: "+str(peaks))
    return {str(i):{"trace_peak":peaks[str(i)],
                    "arm_threshold":.45*peaks[str(i)],
                    "release_threshold":.2*peaks[str(i)]}
            for i in NODE_IDS}


def calibrated_graph(kind,order,cal):
    g=read_graph(kind,order)
    for i in NODE_IDS:
        config=next(n["config"] for n in g["nodes"] if n["id"]==i)
        config.update({k:v for k,v in cal[str(i)].items() if k!="trace_peak"})
    return g


def dataset(upstream,kind,cal,trials,steps=TRIAL_STEPS):
    records={}
    for j,trial in enumerate(trials):
        for order in ("AB","BA"):
            g=prepare_trial(calibrated_graph(kind,order,cal),order,trial)
            x=simulate(g,upstream,steps)
            records[(j,order)]=x
    return records


FEATURE_SETS={
    "all_six":(0,1,2,3,4,5),
    "traces_only":(0,1,2),
    "spike_history_only":(3,4,5),
}

def fit_linear(train,checkpoint,feature_set="all_six"):
    """Ridge probe, training statistics ONLY. No leakage from test labels."""
    xs=[];labels=[]
    for (_,order),record in sorted(train.items()):
        xs.append([record["features"][checkpoint][i] for i in FEATURE_SETS[feature_set]])
        labels.append(1. if order=="AB" else -1.)
    X=np.asarray(xs,dtype=float); y=np.asarray(labels)
    avg=X.mean(axis=0)
    std=X.std(axis=0)
    std=np.maximum(std,1e-6)
    norm=(X-avg)/std
    coef=np.linalg.solve(norm.T@norm+0.25*np.eye(X.shape[1]),
                         norm.T@y)
    bias=float(y.mean()-coef@ (np.zeros_like(avg))) # normalized intercept
    raw_w=coef/std
    raw_b=bias-float(raw_w@avg)
    return {"feature_set":feature_set,
            "weights":[float(w) for w in raw_w],
            "bias":raw_b,
            "train_mean":[float(z) for z in avg],
            "train_std":[float(z) for z in std]}


def test_linear(test,model,checkpoint):
    w=np.array(model["weights"]);b=model["bias"]
    good=0;pairgood=0;pairs=sorted({j for j,_ in test})
    margins=[]
    for j in pairs:
        success=[]
        for order in ("AB","BA"):
            x=np.asarray([test[(j,order)]["features"][checkpoint][i]
                          for i in FEATURE_SETS[model["feature_set"]]])
            score=float(x@w+b)
            correct=(score>=0 if order=="AB" else score<0)
            success.append(bool(correct));good+=int(correct)
            margins.append((1 if order=="AB" else -1)*score)
        pairgood+=int(all(success))
    return {"balanced_accuracy":round(good/(2*len(pairs)),4),
            "both_orders_correct_pairs":pairgood,
            "pairs":len(pairs),
            "mean_labelled_margin":round(float(np.mean(margins)),6)}


def summarize_spikes(data):
    a=[r for (_,order),r in sorted(data.items())]
    n=len(a)
    return {str(i):{"mean_total_spikes":round(
        sum(len(x["spikes"][str(i)]) for x in a)/n,3),
        "mean_post_160_spikes":round(sum(sum(t>=160
          for t in x["spikes"][str(i)]) for x in a)/n,3)}
        for i in NODE_IDS}


def run(upstream,steps=TRIAL_STEPS):
    upstream=pathlib.Path(upstream)
    cal=calibrate(upstream)
    out={}
    for mode in ("feedback","passive","no_C"):
        train=dataset(upstream,mode,cal,TRAIN,steps)
        held=dataset(upstream,mode,cal,TEST,steps)
        if any(z["clipped_frames"] for z in list(train.values())+list(held.values())):
            raise RuntimeError("Wave clipping: calibration/energy need rechecking")
        stages={}
        for t in SNAPSHOTS:
            models={key:fit_linear(train,t,key) for key in FEATURE_SETS}
            stages[str(t)]={"test":test_linear(held,models["all_six"],t),
                            "training":test_linear(train,models["all_six"],t),
                            "ablation_readouts":{
                                key:test_linear(held,m,t)
                                for key,m in models.items()}}
            if t==360:stages[str(t)]["frozen_model"]=models["all_six"]
        out[mode]={
           "stages":stages,
           "train_pair_count":len(TRAIN),
           "heldout_pair_count":len(TEST),
           "source_energies_matched":True,
           "spikes":summarize_spikes(held),
           "max_abs_wave":max(x["max_abs_field"] for x in held.values()),
           "heldout_example_spikes":{
               order:held[(0,order)]["spikes"] for order in ("AB","BA")
           }
        }
    # Sanity: no stimulus = no event without a source or an initial trace.
    empty=calibrated_graph("feedback","AB",cal)
    for i in (0,1):
        next(n for n in empty["nodes"] if n["id"]==i)["config"]["amplitude"]=0.
    zero=simulate(empty,upstream,steps=steps)
    out["no_input"]={"spikes":zero["spikes"],"peak_energy":zero["peak_energy"]}
    result={
      "experiment":"005_order_of_falls",
      "upstream":"actual PerceptionLab 96x96 WaveField and PulseSource",
      "physics":"three Fade units; two distinct 2-frame source pulses with equal per-pair amplitudes, only order swapped",
      "timesteps":steps,
      "snapshots":SNAPSHOTS,
      "training_trial_parameters":TRAIN,
      "heldout_trial_parameters":TEST,
      "calibration":cal,
      "modes":out,
      "limits":"single deterministic simulator/parameter set; linear readout on fading states plus readout's own spike EMA; not learning in the recurrent medium. Passive condition has residual waves."
    }
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--upstream",default="PerceptionLab")
    p.add_argument("--out",default="results/005_order_of_falls.json")
    args=p.parse_args()
    result=run(pathlib.Path(args.upstream))
    path=ROOT/args.out
    path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(result,indent=2)+"\n")
    report={"experiment":result["experiment"],
        "calibration":result["calibration"],
        "no_input":result["modes"]["no_input"],
        "modes":{k:{
            "snapshots":{t:x["test"] for t,x in v["stages"].items()},
            "spikes":v["spikes"],"max_abs_wave":v["max_abs_wave"]}
            for k,v in result["modes"].items() if k!="no_input"}}
    print(json.dumps(report,indent=2))
