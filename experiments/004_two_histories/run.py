"""004 - Two fading-history emitters within ONE upstream WaveField.

Scientific claim kept narrow: measure timing/phase relations, and identify
which changes follow rate, spatial site, or return-wire connectivity.

No new wave simulator and no surrogate logic. The exact PerceptionLab host
constructor/config/edge-transfer schedule is reproduced on saved graphs.
The host GUI itself is not run in CI.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
import pathlib
import statistics
import sys

import numpy as np

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load

CLASS_FILES={
    "PulseSourceNode":"pulsesourcenode.py",
    "WaveFieldNode":"wavefieldnode.py",
    "FadingHistorySpikeNode":"fading_history_spike_node.py",
    "SignalPlotterNode":"signalplotternode.py",
    "TemporalMultiScopeNode":"temporalmultiscopenode.py",
}
DEF_GRAPH=ROOT/"workflows"/"004_two_fades_one_field.json"


def node_class(name, upstream):
    src=(ROOT/"nodes"/CLASS_FILES[name] if name=="FadingHistorySpikeNode"
         else pathlib.Path(upstream)/"nodes"/CLASS_FILES[name])
    return load(src,name)


def prepare(graph,upstream):
    """The same no-argument construction and config fallback as the GUI."""
    obj={}
    for desc in graph["nodes"]:
        C=node_class(desc["class_name"],upstream)
        n=C()
        config=copy.deepcopy(desc.get("config",{}))
        if hasattr(n,"set_config_options"):
            n.set_config_options(config)
        for k,v in config.items():
            if hasattr(n,k):
                cur=getattr(n,k)
                if cur != v:
                    setattr(n,k,v)
        obj[desc["id"]]=n
    field=obj[1]
    if field.field.shape!=(96,96) or len(field.aperture_xy)!=8:
        raise RuntimeError("Host graph size mismatch: actual wave shape %s" %
                           (field.field.shape,))
    for e in graph["edges"]:
        src=obj[e["from_node_id"]]
        dst=obj[e["to_node_id"]]
        if e["from_port"] not in src.outputs or e["to_port"] not in dst.inputs:
            raise RuntimeError("Invalid edge: "+str(e))
        if src.outputs[e["from_port"]] != dst.inputs[e["to_port"]]:
            raise RuntimeError("Type mismatch: "+str(e))
    return obj


def calibrate(upstream,graph,steps=240):
    """Independent OPEN-LOOP bootstrap, no history spikes written to the field.

    For both units, derive thresholds from the trace peak after ONE source
    pulse, before any closed-loop measurement. This calibrates independently
    for each decay/site change. Also report *frozen baseline thresholds*
    comparisons to avoid confusing recalibration with physical effects.
    """
    no_return=copy.deepcopy(graph)
    no_return["edges"]=[e for e in graph["edges"] if not (
        e["from_node_id"] in (2,3) and e["to_node_id"]==1 and
        e["from_port"]=="pulse")]
    obj=prepare(no_return,upstream)
    seq,_=advance(obj,no_return["edges"],steps,record_energy=False)
    peaks={str(i):max(seq["trace"][str(i)]) for i in (2,3)}
    if min(peaks.values())<=1e-7:
        raise RuntimeError("Open-loop calibrator had no response: "+str(peaks))
    return {
        "trace_peaks":peaks,
        "thresholds":{
            str(i):{"arm_threshold":peaks[str(i)]*.45,
                    "release_threshold":peaks[str(i)]*.20}
            for i in (2,3)
        },
        "open_loop_first_spikes":{
            str(i):seq["spikes"][str(i)][:3] for i in (2,3)
        },
    }


def apply_thresholds(graph,calibration):
    g=copy.deepcopy(graph)
    for i in (2,3):
        node=next(n for n in g["nodes"] if n["id"]==i)
        node["config"].update(calibration["thresholds"][str(i)])
    return g


def advance(obj,edges,steps,cut_b_at=None,cut_a_at=None,record_energy=True):
    """Prestep ALL -> transfer ALL OLD outputs -> step ALL -> measure."""
    record={"spikes":{"2":[],"3":[]},"trace":{"2":[],"3":[]},"armed":{"2":[],"3":[]}}
    maximum_field=0.
    saturated_frames=0
    energy_samples=[]
    # Renderers (IDs >=4) only *observe* the causal subsystem. Skipping
    # their expensive scope/plot redraws in headless sweeps does not alter
    # inputs or state of source, wave or either fade unit. The saved GUI
    # graph still runs all nodes; tests check their real port wiring.
    causal={i:obj[i] for i in (0,1,2,3)}
    for tick in range(steps):
        for n in causal.values():
            n.pre_step()
        for e in edges:
            if e["to_node_id"] not in causal:
                continue
            if (cut_a_at is not None and tick>=cut_a_at and
                e["from_node_id"]==2 and e["to_node_id"]==1 and
                e["from_port"]=="pulse"):
                continue
            if (cut_b_at is not None and tick>=cut_b_at and
                e["from_node_id"]==3 and e["to_node_id"]==1 and
                e["from_port"]=="pulse"):
                continue
            src=obj[e["from_node_id"]];dst=obj[e["to_node_id"]]
            val=src.get_output(e["from_port"])
            if val is not None:
                dst.set_input(e["to_port"],val,
                              src.outputs[e["from_port"]],
                              e.get("learned_weight",1.0))
        for n in causal.values():
            n.step()
        for i in (2,3):
            unit=obj[i]
            record["trace"][str(i)].append(float(unit.trace))
            record["armed"][str(i)].append(int(unit.armed))
            if unit.get_output("pulse")>0:
                record["spikes"][str(i)].append(tick)
        if record_energy:
            field=obj[1]
            peak=float(np.max(np.abs(field.field)))
            maximum_field=max(peak,maximum_field)
            saturated_frames+=int(peak>=3.9998)
            energy_samples.append(float(field.energy_value))
    info={"max_abs_field":round(maximum_field,7),
          "saturated_frames":saturated_frames,
          "mean_last_100_energy":(round(statistics.mean(
              energy_samples[-100:]),9) if energy_samples else None)}
    return record,info


def phase_metrics(a,b,steps):
    """Descriptive relations only. R alone cannot establish interaction."""
    late=int(steps*.5)
    a=[x for x in a if x>=late]
    b=[x for x in b if x>=late]
    def rhythm(times):
        gap=[y-x for x,y in zip(times,times[1:])]
        return {
            "count":len(times),
            "median_isi":statistics.median(gap) if gap else None,
            "mean_isi":round(statistics.mean(gap),4) if gap else None,
            "cv_isi":round(statistics.pstdev(gap)/statistics.mean(gap),4)
                     if len(gap)>1 and statistics.mean(gap)>0 else None
        }
    ra,rb=rhythm(a),rhythm(b)
    out={"a":ra,"b":rb}
    if len(a)>=3 and len(b)>=3 and ra["mean_isi"]:
        period=ra["mean_isi"]
        phases=[2*math.pi*((t-a[0])%period)/period for t in b]
        z=sum(complex(math.cos(x),math.sin(x)) for x in phases)/len(phases)
        out["phase_concentration_r"]=round(abs(z),5)
        out["b_nearest_a_mean_signed_offset"]=round(statistics.mean(
            min((t-x for x in a),key=abs) for t in b),3)
        out["near_coincident_b_spikes_within_2"]=sum(
            1 for t in b if min(abs(t-x) for x in a)<=2)
        out["spike_count_ratio_b_over_a"]=round(len(b)/len(a),5)
    else:
        out.update({"phase_concentration_r":None,
                    "b_nearest_a_mean_signed_offset":None,
                    "near_coincident_b_spikes_within_2":None,
                    "spike_count_ratio_b_over_a":None})
    sequence=sorted([(t,"A") for t in a]+[(t,"B") for t in b])
    if len(sequence)>1:
        out["interleaving_fraction"]=round(
            sum(sequence[i][1]!=sequence[i-1][1]
                for i in range(1,len(sequence)))/(len(sequence)-1),5)
    else:
        out["interleaving_fraction"]=None
    return out


def run_case(upstream,graph,thresholds,steps=650,cut_b_at=None,cut_a_at=None):
    graph=apply_thresholds(graph,thresholds)
    obj=prepare(graph,upstream)
    rec,eng=advance(obj,graph["edges"],steps,cut_b_at=cut_b_at,cut_a_at=cut_a_at)
    spikes=rec["spikes"]
    return {
        "spike_times":{"A":spikes["2"],"B":spikes["3"]},
        "total_spikes":{"A":len(spikes["2"]),"B":len(spikes["3"])},
        "late_spikes":{"A":sum(x>=steps//2 for x in spikes["2"]),
                       "B":sum(x>=steps//2 for x in spikes["3"])},
        "phase":phase_metrics(spikes["2"],spikes["3"],steps),
        "max_trace":{"A":round(max(rec["trace"]["2"]),7),
                     "B":round(max(rec["trace"]["3"]),7)},
        "late_trace_state":{
            label:{
                "min":round(min(rec["trace"][str(i)][steps//2:]),7),
                "mean":round(statistics.mean(rec["trace"][str(i)][steps//2:]),7),
                "max":round(max(rec["trace"][str(i)][steps//2:]),7),
                "fraction_armed":round(statistics.mean(
                    rec["armed"][str(i)][steps//2:]),6),
                "release_threshold":round(float(obj[i].release_threshold),7),
                "fraction_above_release":round(sum(
                    t>obj[i].release_threshold for t in
                    rec["trace"][str(i)][steps//2:])/
                    len(rec["trace"][str(i)][steps//2:]),6)
            } for label,i in (("A",2),("B",3))
        },
        "energy":eng,
        "cut_b_at":cut_b_at,
        "cut_a_at":cut_a_at
    }


def main(upstream,size=96,steps=650):
    if size!=96:
        raise ValueError("004 saved workflows/calibration are 96x96; size change needs new graph")
    paths={
       "coupled":"004_two_fades_one_field.json",
       "a_only":"004_a_only.json",
       "b_only":"004_b_only.json",
       "no_return":"004_no_return.json",
       "no_seed":"004_no_seed.json",
       "swap_decay":"004_swap_decay.json",
       "swap_sites":"004_swap_sites.json",
    }
    graphs={k:json.loads((ROOT/"workflows"/name).read_text())
            for k,name in paths.items()}
    base_cal=calibrate(upstream,graphs["coupled"])
    calibrated={"coupled":base_cal, "a_only":base_cal,"b_only":base_cal,
                "no_return":base_cal,"no_seed":base_cal}
    calibrated["swap_decay"]=calibrate(upstream,graphs["swap_decay"])
    calibrated["swap_sites"]=calibrate(upstream,graphs["swap_sites"])
    cases={}
    for key,graph in graphs.items():
        cases[key]=run_case(upstream,graph,calibrated[key],steps)
    # additional frozen-threshold versions: manipulations without
    # compensating away the readout/amplitude effect.
    cases["swap_decay_frozen"]=run_case(
        upstream,graphs["swap_decay"],base_cal,steps)
    cases["swap_sites_frozen"]=run_case(
        upstream,graphs["swap_sites"],base_cal,steps)
    cases["cut_b_midrun"]=run_case(
        upstream,graphs["coupled"],base_cal,steps,cut_b_at=steps//2)
    cases["cut_a_midrun"]=run_case(
        upstream,graphs["coupled"],base_cal,steps,cut_a_at=steps//2)
    for strength in (0.25,0.50,0.75):
        modified=copy.deepcopy(graphs["coupled"])
        for e in modified["edges"]:
            if (e["from_node_id"]==2 and e["to_node_id"]==1 and
                e["from_port"]=="pulse"):
                e["learned_weight"]=strength
        cases["a_return_"+str(strength)]=run_case(
            upstream,modified,base_cal,steps)
    return {
        "experiment":"004_two_histories",
        "upstream":"PerceptionLab/main; actual WaveField and PulseSource",
        "analysis":"two FadingHistorySpikeNode instances in one 96x96 WaveField",
        "steps":steps,
        "calibrations":calibrated,
        "cases":cases,
        "method_note":"Rate and site swaps run with separate open-loop calibration AND frozen baseline thresholds. Neither variant alone isolates learning, and phase R does not imply causality.",
        "physical_limits":"Fixed injection pulses add energy; not learned neuron dynamics. Field clipping recorded."
    }


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--upstream",default="PerceptionLab")
    ap.add_argument("--steps",type=int,default=650)
    ap.add_argument("--size",type=int,default=96)
    ap.add_argument("--out",default="results/004_two_histories.json")
    args=ap.parse_args()
    res=main(pathlib.Path(args.upstream),args.size,args.steps)
    path=ROOT/args.out
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(res,indent=2)+"\n")
    print(json.dumps({
        "experiment":res["experiment"],
        "calibration":res["calibrations"],
        "cases":{
            name:{"total":c["total_spikes"],
                  "late":c["late_spikes"],
                  "period_A":c["phase"]["a"]["mean_isi"],
                  "period_B":c["phase"]["b"]["mean_isi"],
                  "R":c["phase"]["phase_concentration_r"],
                  "interleaving":c["phase"]["interleaving_fraction"],
                  "clip_frames":c["energy"]["saturated_frames"],
                  "B_armed_fraction":c["late_trace_state"]["B"]["fraction_armed"],
                  "B_above_release":c["late_trace_state"]["B"]["fraction_above_release"]}
            for name,c in res["cases"].items()}
    },indent=2))
