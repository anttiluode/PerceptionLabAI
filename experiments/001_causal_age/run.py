"""Measure out-of-sample transit prediction with real upstream PerceptionLab nodes."""
import argparse
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tests"))
from host_shim import load

def run(upstream,size=128,steps=740):
    Pulse=load(upstream/"nodes"/"pulsesourcenode.py","PulseSourceNode")
    Wave=load(upstream/"nodes"/"wavefieldnode.py","WaveFieldNode")
    Reader=load(ROOT/"nodes"/"temporal_transit_predictor_node.py",
                "TemporalTransitPredictorNode")
    pulse=Pulse(period=180,width=3,amplitude=1.0)
    pulse.warmup=35
    wave=Wave(size=size)
    wave.damping=0.006
    expected=wave.spacing_px/(wave.speed*wave.substeps)
    r=Reader(delay=round(expected),window=140,min_samples=40)
    r0=Reader(delay=0,window=140,min_samples=40)
    record=[]
    for tick in range(steps):
        # Host order: transfer previously available output, then step all.
        near,far=wave.get_output("read_0"),wave.get_output("read_1")
        for reader in (r,r0):
            reader.pre_step()
            reader.set_input("near",near)
            reader.set_input("far",far)
            reader.step()
        wave.pre_step()
        wave.set_input("impulse",pulse.get_output("signal"))
        wave.step()
        pulse.pre_step()
        pulse.step()
        if tick>=steps//2 and r.valid:
            record.append((r.advantage_db,r.mse_delayed,r.mse_simultaneous,r0.advantage_db))
    if not record: raise RuntimeError("No valid frames; cannot claim a result")
    return {"experiment":"001_causal_age","upstream":"PerceptionLab/main",
            "grid_size":size,"steps":steps,"expected_delay_frames":expected,
            "reader_delay_frames":r.delay,"valid_last_half":len(record),
            "mean_advantage_db":sum(x[0] for x in record)/len(record),
            "final_advantage_db":record[-1][0],
            "final_delayed_mse":record[-1][1],
            "final_simultaneous_mse":record[-1][2],
            "max_abs_zero_delay_control_db":max(abs(x[3]) for x in record),
            "interpretation":"Readout prediction only; no medium learning or biological memory."}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--upstream",default="PerceptionLab")
    ap.add_argument("--steps",type=int,default=740)
    ap.add_argument("--size",type=int,default=128)
    ap.add_argument("--out",default="results/001_causal_age.json")
    args=ap.parse_args()
    result=run(pathlib.Path(args.upstream),args.size,args.steps)
    path=ROOT/args.out
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
