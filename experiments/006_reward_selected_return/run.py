"""006: reward-selected pruning of a return pathway in a real WaveField.

Question: can a feedback edge change across experiences to preserve which
past occurred (AB or BA), rather than being hand-pruned after 005b?

FACTS / important distinction:
- The physical path C -> PlasticReturnGateNode -> WaveField is real.
- The gate stores a bounded weight across separate trial episodes.
- An *external*, supervised trainer supplies a scalar reward-difference
  after comparing matched +/- weight trials (2-sided perturbation).
- AB/BA labels NEVER enter the graph, but they DO enter the utility
  evaluator. This is NOT local unsupervised biology.
- A fixed, separately trained, finite-resolution readout evaluates
  utility. Readout coefficients are frozen BEFORE gate plasticity.
- All training, testing and baseline graphs pass through the SAME gate
  node (same extra one-frame delay). Do not compare with 005b directly.
- A reduction in weight alone is NOT evidence of improved order memory.

Uses genuine upstream WaveField, PulseSource, workshop FadingHistorySpike,
PopulationOrderReadout and PlasticReturnGate nodes; no surrogate physics.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
import pathlib
import sys
import importlib.util
import statistics

import numpy as np

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load

spec=importlib.util.spec_from_file_location(
    "reference005",ROOT/"experiments"/"005_order_of_falls"/"run.py")
lab=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

CLASS_FILES={
 "PulseSourceNode":"pulsesourcenode.py",
 "WaveFieldNode":"wavefieldnode.py",
 "FadingHistorySpikeNode":"fading_history_spike_node.py",
 "PopulationOrderReadoutNode":"population_order_readout_node.py",
 "PlasticReturnGateNode":"plastic_return_gate_node.py",
}
WORKSHOP_CLASSES={
    "FadingHistorySpikeNode","PopulationOrderReadoutNode",
    "PlasticReturnGateNode"
}
TRAIN=[
 (-4,31,1.03),(-1,39,.96),(2,33,1.07),(0,37,1.00),
 (3,28,.94),(-2,42,1.08),(1,34,1.02),(-3,40,.98)
]
HELD_OUT=[
 (5,29,.97),(-5,34,1.05),(4,41,.92),(1,45,1.02),
 (-3,46,.99),(2,38,1.10),(0,27,1.06),(-1,44,.94)
]
FRAMES=660
OBSERVATION=650
INITIAL_WEIGHT=.5
DELTA=.1
LEARNING_RATE=.12
# Pooled open-loop calibration inherited from 005b and NEVER retuned
# for a label, the learned edge, or the held-out examples.
CAL={
"3":(.12447380548826721,.05532169132811876,.2766084566405938),
"4":(.10120400337522525,.04497955705565567,.22489778527827833),
"5":(.06781459787754025,.030139821278906784,.15069910639453591)
}
FLOOR=[.01*CAL[str(i)][2] for i in (3,4,5)]+[.001]*3


def base_graph(order="AB",kind="plastic"):
    return json.loads(
        (ROOT/"workflows"/f"006_{order}_{kind}_return.json").read_text())


def node_class(name,upstream):
    src=(ROOT/"nodes"/CLASS_FILES[name] if name in WORKSHOP_CLASSES
         else pathlib.Path(upstream)/"nodes"/CLASS_FILES[name])
    return load(src,name)


def instantiate(graph,upstream):
    obj={}
    for desc in graph["nodes"]:
        if desc["id"]>7:continue  # plotters only observe; not causal
        klass=node_class(desc["class_name"],upstream)
        n=klass()
        conf=copy.deepcopy(desc.get("config",{}))
        if hasattr(n,"set_config_options"):n.set_config_options(conf)
        for key,value in conf.items():
            if hasattr(n,key):
                existing=getattr(n,key)
                if existing!=value:setattr(n,key,value)
        if desc["id"] in (0,1,2,6,7):n._render=lambda *a:None
        if desc["id"] in (3,4,5):n._render=lambda *a:None
        obj[desc["id"]]=n
    if obj[2].field.shape!=(96,96):raise RuntimeError("Wave size mismatch")
    for e in graph["edges"]:
        if e["to_node_id"]>7:continue
        a=obj[e["from_node_id"]];b=obj[e["to_node_id"]]
        assert e["from_port"] in a.outputs, e
        assert e["to_port"] in b.inputs, e
        assert a.outputs[e["from_port"]]==b.inputs[e["to_port"]], e
    return obj


def trial_graph(order,params,retention,direction=0.0):
    g=lab.prepare_trial(base_graph(order),order,params)
    gate=next(n for n in g["nodes"] if n["id"]==7)
    gate["config"]["weight"]=float(retention)
    gate["config"]["exploration_direction"]=float(direction)
    # No supervised updates within the labelled episode.
    gate["config"]["learn_enabled"]=0
    return g


def simulate(graph,upstream,steps=FRAMES):
    obj=instantiate(graph,upstream)
    causal={i:obj[i] for i in range(8)}
    edges=[e for e in graph["edges"] if e["to_node_id"]<=7]
    snap={}
    spikes={"3":[],"4":[],"5":[]}
    last_energy=0.
    clipped=0
    max_abs_field=0.
    for tick in range(steps):
        for n in causal.values():n.pre_step()
        for e in edges:
            a=obj[e["from_node_id"]];b=obj[e["to_node_id"]]
            value=a.get_output(e["from_port"])
            if value is not None:b.set_input(e["to_port"],value,
                a.outputs[e["from_port"]],e.get("learned_weight",1.0))
        for n in causal.values():n.step()
        for i in (3,4,5):
            if obj[i].pulse>0:spikes[str(i)].append(tick)
        # No need to scan the whole field every tick; clipping is
        # detected at frame end (and upstream clips internally).
        if tick%20==0 or tick==steps-1:
            mag=float(np.max(np.abs(obj[2].field)))
            max_abs_field=max(max_abs_field,mag)
            clipped+=int(mag>=3.9998)
        if tick in (360,650):
            snap[tick]=[float(v) for v in obj[6].features]
        last_energy=float(obj[2].energy_value)
    return {"features":snap,"spikes":spikes,
        "max_abs_field":max_abs_field,"sampled_clipped_frames":clipped,
        "last_energy":last_energy,
        "gate_weight":float(obj[7].weight),
        "gate_effective_weight":float(obj[7].effective_weight)}


def collect(upstream,params,weight,delta_sign=0.,step_limit=FRAMES):
    data={}
    for j,trial in enumerate(params):
        for order in ("AB","BA"):
            g=trial_graph(order,trial,weight,delta_sign)
            data[(j,order)]=simulate(g,upstream,steps=step_limit)
    return data


def quantized(record):
    """Fixed sensor resolution: same as post-hoc 005 finite-floor choice."""
    return [0. if abs(v)<FLOOR[i] else float(v)
            for i,v in enumerate(record["features"][OBSERVATION])]


def model_on_pruned(upstream):
    # This is a downstream teacher/readout fitted *once* on training
    # pairs with C's return gated to ZERO. Never refit during plasticity.
    source=collect(upstream,TRAIN,0.0)
    observed=lab.observed_resolution(source,FLOOR)
    model=lab.fit_linear(observed,OBSERVATION,"all_six")
    return model,source


def reward(record,model,order):
    features=quantized(record)
    score=float(np.dot(features,model["weights"])+model["bias"])
    label=1. if order=="AB" else -1.
    margin=max(-20.,min(20.,label*score))
    # Higher utility when the frozen observer correctly reports the order.
    return -math.log1p(math.exp(-margin))


def paired_utility(upstream,params,weight,model,direction):
    scores=[];spk=[]
    for order in ("AB","BA"):
        g=trial_graph(order,params,weight,direction)
        r=simulate(g,upstream)
        scores.append(reward(r,model,order))
        spk.append(sum(len(ts) for ts in r["spikes"].values()))
    return statistics.mean(scores),statistics.mean(spk)


def make_trainer(initial=INITIAL_WEIGHT):
    # Persistent physical node; scalar reward comparison arrives through
    # BaseNode.set_input (same API as the GUI). No source label reaches it.
    trainer=node_class("PlasticReturnGateNode",upstream="")()
    trainer._render=lambda *a:None
    trainer.weight=initial
    trainer.perturbation=DELTA
    trainer.learning_rate=LEARNING_RATE
    trainer.resource_cost=0.0
    trainer.learn_enabled=1
    return trainer


def train(upstream,model,reverse_reward=False):
    trainer=make_trainer()
    ledger=[{"episode":-1,"weight":trainer.weight}]
    for j,params in enumerate(TRAIN):
        plus,sp_plus=paired_utility(upstream,params,trainer.weight,model,+1)
        minus,sp_minus=paired_utility(upstream,params,trainer.weight,model,-1)
        reward_difference=plus-minus
        if reverse_reward:reward_difference=-reward_difference
        before=trainer.weight
        trainer.pre_step()
        trainer.set_input("reward_difference",reward_difference,"signal",1)
        trainer.step()
        ledger.append({
          "episode":j,"trial":list(params),"w_before":before,
          "utility_plus":plus,"utility_minus":minus,
          "reward_difference_sent":reward_difference,
          "w_after":trainer.weight,"actual_update":trainer.last_update,
          "mean_spikes_plus":sp_plus,"mean_spikes_minus":sp_minus
        })
    return trainer.weight,ledger


def eval_model(model,observed):
    correct=0;pair_correct=0
    margins=[]
    for j in sorted({k for k,_ in observed}):
        pair=[]
        for order in ("AB","BA"):
            r=observed[(j,order)]
            v=quantized(r)
            score=float(np.dot(v,model["weights"])+model["bias"])
            label=1 if order=="AB" else -1
            ok=(score>=0 if order=="AB" else score<0)
            pair.append(ok);correct+=int(ok)
            margins.append(label*score)
        pair_correct+=int(all(pair))
    return {
        "correct":correct,"total":len(observed),"accuracy":round(correct/len(observed),4),
        "correct_full_pairs":pair_correct,
        "mean_margin":round(float(np.mean(margins)),5),
        "mean_total_spikes":{str(i):round(statistics.mean(
            len(r["spikes"][str(i)]) for r in observed.values()),3)
            for i in (3,4,5)},
        "max_abs_field":round(max(r["max_abs_field"] for r in observed.values()),6),
        "sampled_clip_frames":sum(r["sampled_clipped_frames"] for r in observed.values())
    }


def run(upstream):
    upstream=pathlib.Path(upstream)
    model,train_base=model_on_pruned(upstream)
    learned,history=train(upstream,model)
    opposite,negative=train(upstream,model,reverse_reward=True)
    baselines={"trained":learned,"initial_frozen":INITIAL_WEIGHT,
        "permanently_pruned":0.0,"inverted_reward":opposite}
    evals={}
    for name,weight in baselines.items():
        res=collect(upstream,HELD_OUT,weight)
        evals[name]={"weight":weight,**eval_model(model,res),
                     "example_AB":res[(0,"AB")]["spikes"],
                     "example_BA":res[(0,"BA")]["spikes"]}
    return {
        "experiment":"006_reward_selected_return",
        "research_question":"Does a physical C-return edge learn from supervised paired reward and improve unseen AB/BA readability?",
        "data_split":"8 matched training pairs; 8 disjoint heldout pairs; decoder frozen before gate training",
        "train":TRAIN,"heldout":HELD_OUT,
        "fixed_reader_origin":"fit ONCE on training pairs with gated-C return=0",
        "reader":model,
        "reader_train_baseline":lab.test_linear(
            lab.observed_resolution(train_base,FLOOR),model,OBSERVATION),
        "sensor_floors":FLOOR,
        "physical_gate_learning":"two-sided perturbation; gate weight updates via its own reward_difference port; per-episode reset of other dynamical state",
        "plasticity_params":{"initial":INITIAL_WEIGHT,"delta":DELTA,
                             "rate":LEARNING_RATE,"resource_cost":0.0},
        "learning_history":history,
        "inverted_reward_history":negative,
        "heldout_evaluation":evals,
        "scientific_limits":"Reward supplied by labelled external trainer; reward model was trained on a C-pruned network; bounded one-edge plasticity, not dendritic growth or local Hebbian learning. Single deterministic configuration. Timing delay through gate exists in ALL conditions."
    }


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--upstream",default="PerceptionLab")
    parser.add_argument("--out",default="results/006_reward_selected_return.json")
    args=parser.parse_args()
    result=run(args.upstream)
    out=ROOT/args.out
    out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("BEGIN_006_RECEIPT")
    print(json.dumps(result,indent=2))
    print("END_006_RECEIPT")
