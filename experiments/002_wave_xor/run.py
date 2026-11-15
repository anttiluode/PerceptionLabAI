"""Experiment 002: genuine upstream wave propagation -> gate -> resonator XOR.

Calibrate each field tap once using a single pulse, freeze thresholds, then
sweep relative source timing. The test input does not adjust thresholds.
"""
import argparse
import json
import pathlib
import sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load

def modules(upstream):
    return (
        load(upstream/"nodes"/"pulsesourcenode.py","PulseSourceNode"),
        load(upstream/"nodes"/"wavefieldnode.py","WaveFieldNode"),
        load(upstream/"nodes"/"resonatorsomanode.py","ResonatorSomaNode"),
        load(ROOT/"nodes"/"wave_arrival_gate_node.py","WaveArrivalGateNode")
    )

def single_peak(Pulse,Wave,size,tap,steps=150,speed=.5):
    p=Pulse(period=0,width=3,amplitude=1.0)
    p.warmup=25
    w=Wave(size=size)
    w.damping=.006
    w.speed=speed
    peak=0.0
    for t in range(steps):
        peak=max(peak,abs(float(w.get_output("read_"+str(tap)))))
        previous=p.get_output("signal")
        w.pre_step();w.set_input("impulse",previous);w.step()
        p.pre_step();p.step()
    return peak

def one_case(mods,size,thresholds,offset,steps=170,enable_a=True,enable_b=True,tap_b=1,speed=.5):
    Pulse,Wave,Soma,Gate=mods
    a=Pulse(period=0,width=3,amplitude=1.0 if enable_a else 0.0)
    b=Pulse(period=0,width=3,amplitude=1.0 if enable_b else 0.0)
    a.warmup=35
    b.warmup=35+offset
    wa,wb=Wave(size=size),Wave(size=size)
    wa.damping=wb.damping=.006
    wa.speed=wb.speed=speed
    ga,gb=Gate(thresholds[0]),Gate(thresholds[1])
    soma=Soma(gate="XOR")
    n_a=n_b=both=union=xor=disagree=0
    trace=[]
    for t in range(steps):
        # Read all *previous* node outputs BEFORE stepping any node.
        pulse_a,pulse_b=a.get_output("signal"),b.get_output("signal")
        read_a,read_b=wa.get_output("read_0"),wb.get_output("read_"+str(tap_b))
        gate_a,gate_b=ga.get_output("gate"),gb.get_output("gate")
        soma.pre_step()
        soma.set_input("in_a",gate_a)
        soma.set_input("in_b",gate_b)
        soma.step()
        fire=int(soma.get_output("fire")>.5)
        expected=int(bool(gate_a) != bool(gate_b))
        if fire!=expected:disagree+=1
        n_a+=int(bool(gate_a));n_b+=int(bool(gate_b))
        both+=int(bool(gate_a) and bool(gate_b))
        union+=int(bool(gate_a) or bool(gate_b))
        xor+=fire
        trace.append([int(bool(gate_a)),int(bool(gate_b)),fire])
        ga.pre_step();ga.set_input("signal_in",read_a);ga.step()
        gb.pre_step();gb.set_input("signal_in",read_b);gb.step()
        wa.pre_step();wa.set_input("impulse",pulse_a);wa.step()
        wb.pre_step();wb.set_input("impulse",pulse_b);wb.step()
        a.pre_step();a.step()
        b.pre_step();b.step()
    return {"offset":offset,"a_active":n_a,"b_active":n_b,"both_active":both,
            "either_active":union,"xor_active":xor,
            "overlap_fraction":both/union if union else 0.0,
            "xor_fraction":xor/union if union else 0.0,
            "truth_table_mismatches":disagree}

def run(upstream,size=96,steps=170,tap_b=1,speed=.5):
    mods=modules(upstream)
    Pulse,Wave,Soma,Gate=mods
    peaks=[single_peak(Pulse,Wave,size,tap,speed=speed) for tap in (0,tap_b)]
    thresholds=[0.30*peak for peak in peaks]
    if min(thresholds)<=0:raise RuntimeError("Wave calibration failed: zero peak")
    travel=(.92-.20)*size/7*tap_b/(speed*4)
    nominal=-round(travel)
    offsets=list(range(-22,21,2))
    for k in (nominal,0):
        if k not in offsets: offsets.append(k)
    offsets.sort()
    cases=[one_case(mods,size,thresholds,k,steps,tap_b=tap_b,speed=speed) for k in offsets]
    no_a=one_case(mods,size,thresholds,0,steps,False,True,tap_b=tap_b,speed=speed)
    no_b=one_case(mods,size,thresholds,0,steps,True,False,tap_b=tap_b,speed=speed)
    none=one_case(mods,size,thresholds,0,steps,False,False,tap_b=tap_b,speed=speed)
    best=max(cases,key=lambda c:c["overlap_fraction"])
    by={c["offset"]:c for c in cases}
    return {
        "experiment":"002_wave_xor","upstream":"PerceptionLab/main",
        "size":size,"steps":steps,"far_aperture":tap_b,"wave_speed_per_substep":speed,"calibration_peaks":peaks,
        "frozen_thresholds":thresholds,"predicted_b_starts_earlier_by_frames":travel,
        "nominal_compensation_offset":nominal,
        "best_measured_offset_by_overlap":best["offset"],
        "best_overlap_fraction":best["overlap_fraction"],
        "nominal_case":by[nominal],"zero_offset_case":by[0],
        "sweep":cases,"controls":{"a_off":no_a,"b_off":no_b,"both_off":none},
        "interpretation":"Preset resonator XOR on thresholded physical time-of-flight wave readouts; no emergent XOR or adaptive material."
    }

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--upstream",default="PerceptionLab")
    ap.add_argument("--size",type=int,default=96)
    ap.add_argument("--steps",type=int,default=170)
    ap.add_argument("--out",default="results/002_wave_xor.json")
    ap.add_argument("--tap-b",type=int,choices=[1,2,3],default=1)
    ap.add_argument("--speed",type=float,default=.5)
    a=ap.parse_args()
    result=run(pathlib.Path(a.upstream),a.size,a.steps,tap_b=a.tap_b,speed=a.speed)
    path=ROOT/a.out
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="sweep"},indent=2))
    print("Sweep offsets/overlap:",[(c["offset"],round(c["overlap_fraction"],3)) for c in result["sweep"]])
