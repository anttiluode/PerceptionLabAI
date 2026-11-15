"""Experiment 003: WaveField -> fade-unit -> WaveField with a single bootstrap pulse.

Uses genuine upstream PulseSourceNode and WaveFieldNode. Each experimental
control has freshly initialized state. Thresholds are fitted ONCE on a
separate open-loop bootstrap calibration and are frozen during subsequent
closed- and open-loop tests at that geometry.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from host_shim import load


def classes(upstream):
    upstream = pathlib.Path(upstream)
    return (
        load(upstream / "nodes" / "pulsesourcenode.py", "PulseSourceNode"),
        load(upstream / "nodes" / "wavefieldnode.py", "WaveFieldNode"),
        load(ROOT / "nodes" / "fading_history_spike_node.py",
             "FadingHistorySpikeNode"),
    )


def instruments(mods, size=96, read=1, speed=0.5, damping=0.006,
                decay=0.90, steps=230):
    """Measure an exogenous *single pulse* with feedback completely absent."""
    Pulse, Wave, _ = mods
    p = Pulse(period=0, width=2, amplitude=1.0)
    p.warmup = 18
    w = Wave(size=size)
    w.speed = speed
    w.damping = damping
    trace = 0.0
    trace_peak = 0.0
    wave_peak = 0.0
    tap_values = []
    for t in range(steps):
        tap = float(w.get_output("read_%d" % read))
        tap_values.append(tap)
        trace = decay * trace + (1.0 - decay) * abs(tap)
        trace_peak = max(trace_peak, trace)
        wave_peak = max(wave_peak, abs(tap))

        pulse = p.get_output("signal")
        w.pre_step()
        w.set_input("write_0", pulse)
        w.step()
        p.pre_step()
        p.step()

    if trace_peak <= 1e-6:
        raise RuntimeError("Single-pulse calibration has no wave at read_%d" % read)
    return {
        "trace_peak": trace_peak,
        "wave_peak": wave_peak,
        "arm_threshold": 0.45 * trace_peak,
        "release_threshold": 0.20 * trace_peak,
        "tap_samples": tap_values,
    }


def one_run(mods, thresholds, *,
            size=96, read=1, speed=0.5, damping=0.006, decay=0.90,
            steps=550, feedback=True, bootstrap=True, enabled=True,
            pulse_amplitude=2.0, refractory=3):
    Pulse, Wave, Fade = mods
    source = Pulse(period=0, width=2, amplitude=1.0 if bootstrap else 0.0)
    source.warmup = 18
    field = Wave(size=size)
    field.speed = float(speed)
    field.damping = float(damping)
    unit = Fade(
        decay=decay,
        arm_threshold=thresholds["arm_threshold"],
        release_threshold=thresholds["release_threshold"],
        pulse_amplitude=pulse_amplitude,
        refractory=refractory,
        enabled=enabled,
    )
    times = []
    powers = []
    tap_abs = []
    trace_peak = 0.0
    raw_pulse_frames = 0

    for t in range(steps):
        # All edges deliver PREVIOUS-TICK values; never hand the field an
        # already-updated output from the current step.
        prev_source = source.get_output("signal")
        prev_feedback = unit.get_output("pulse")
        prev_wave_read = field.get_output("read_%d" % read)

        unit.pre_step()
        unit.set_input("signal_in", prev_wave_read)
        unit.step()

        field.pre_step()
        field.set_input("write_0", prev_source)
        if feedback:
            field.set_input("write_0", prev_feedback)
        field.step()

        source.pre_step()
        source.step()

        powers.append(float(field.get_output("energy")))
        tap_abs.append(abs(float(prev_wave_read)))
        trace_peak = max(trace_peak, unit.trace)
        if unit.pulse:
            times.append(t)
            raw_pulse_frames += 1

    late_start = int(0.5 * steps)
    late_times = [x for x in times if x >= late_start]
    diffs = [b-a for a,b in zip(times, times[1:])]
    late_diffs = [b-a for a,b in zip(late_times, late_times[1:])]
    mean_period = statistics.mean(late_diffs) if late_diffs else None
    cv = (statistics.pstdev(late_diffs)/mean_period
          if mean_period and len(late_diffs)>1 else None)
    def round_(value):
        return round(float(value), 8) if value is not None else None
    return {
        "feedback": bool(feedback),
        "bootstrap": bool(bootstrap),
        "enabled": bool(enabled),
        "read_aperture": read,
        "size": size,
        "speed": speed,
        "damping": damping,
        "decay": decay,
        "steps": steps,
        "total_spikes": len(times),
        "late_spikes": len(late_times),
        "spike_times": times,
        "first_spike": times[0] if times else None,
        "last_spike": times[-1] if times else None,
        "late_mean_isi_frames": round_(mean_period),
        "late_isi_cv": round_(cv),
        "last_100_mean_energy": round_(statistics.mean(powers[-100:])),
        "last_100_max_abs_tap": round_(max(tap_abs[-100:])),
        "trace_peak": round_(trace_peak),
        "intervals_first_20": diffs[:20],
        "recurrence_criterion": len(late_times) >= 3 and
                                bool(times and times[-1] >= steps - 50),
    }


def sweep(upstream, size=96, steps=550):
    mods = classes(upstream)
    setups = [
        ("reference", dict(read=1, speed=.5, damping=.006, decay=.90)),
        ("farther_read", dict(read=2, speed=.5, damping=.006, decay=.90)),
        ("slower_wave", dict(read=1, speed=.35, damping=.006, decay=.90)),
        ("higher_damping", dict(read=1, speed=.5, damping=.035, decay=.90)),
        ("longer_trace", dict(read=1, speed=.5, damping=.006, decay=.96)),
    ]
    trials = {}
    cal = {}
    for name,params in setups:
        settings = instruments(mods, size=size, **params)
        frozen = {key:settings[key] for key in
                  ("trace_peak","wave_peak","arm_threshold","release_threshold")}
        cal[name] = {k:round(float(v),9) for k,v in frozen.items()}
        trials[name] = one_run(mods,settings,size=size,steps=steps,feedback=True,**params)
    # Controls share the REFERENCE calibration and source/field parameters.
    standard = dict(setups[0][1])
    refcal = instruments(mods,size=size,**standard)
    controls = {
        "no_feedback": one_run(mods,refcal,size=size,steps=steps,feedback=False,**standard),
        "no_bootstrap": one_run(mods,refcal,size=size,steps=steps,feedback=True,bootstrap=False,**standard),
        "unit_disabled": one_run(mods,refcal,size=size,steps=steps,feedback=True,enabled=False,**standard),
    }
    return {
        "experiment":"003_fade_closed_loop",
        "upstream":"PerceptionLab/main: unmodified PulseSourceNode and WaveFieldNode",
        "calibration":"Each geometry gets independent one-shot calibration; settings frozen before feedback tests",
        "pulse_source":"period=0, width=2, warmup=18; exactly one external pulse event",
        "write_port":"WaveField.write_0",
        "node_model":"EMA(|read|) -> high-threshold armed -> low-threshold one-tick pulse",
        "calibrations":cal,
        "trials":trials,
        "controls":controls,
        "limits":"toy fade spike, not GN27 or biological AP; recurrence requires feedback and energy supplied by the spike output; pass/fail reported as measured",
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", default="PerceptionLab")
    ap.add_argument("--size", type=int, default=96)
    ap.add_argument("--steps", type=int, default=550)
    ap.add_argument("--out", default="results/003_fade_closed_loop.json")
    args = ap.parse_args()
    result = sweep(pathlib.Path(args.upstream), args.size, args.steps)
    path = ROOT / args.out
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "experiment":result["experiment"],
        "calibrations":result["calibrations"],
        "summary":{
            key:{k:v for k,v in x.items() if k in (
                "total_spikes","late_spikes","last_spike","late_mean_isi_frames",
                "late_isi_cv","last_100_mean_energy","recurrence_criterion")}
            for key,x in {**result["trials"], **result["controls"]}.items()
        }
    },indent=2))
