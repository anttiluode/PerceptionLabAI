"""007 - Can a return edge find the turn-taking band from its own firing rate?

Same upstream WaveField, PulseSource and FadingHistorySpikeNode units as 004,
loaded from saved host graphs and stepped in the host order
(pre-step all -> transfer previous outputs -> step all).
The only new part is HomeostaticReturnGateNode on a unit's return edge.
No label, no reader, no reward.
"""
from __future__ import annotations
import argparse, copy, json, pathlib, statistics, sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from host_shim import load
from importlib.util import spec_from_file_location, module_from_spec

_s = spec_from_file_location("lab004", ROOT / "experiments" / "004_two_histories" / "run.py")
lab004 = module_from_spec(_s); _s.loader.exec_module(lab004)

WORKSHOP = {"FadingHistorySpikeNode": "fading_history_spike_node.py",
            "HomeostaticReturnGateNode": "homeostatic_return_gate_node.py"}
UPSTREAM = {"PulseSourceNode": "pulsesourcenode.py", "WaveFieldNode": "wavefieldnode.py",
            "SignalPlotterNode": "signalplotternode.py",
            "TemporalMultiScopeNode": "temporalmultiscopenode.py"}
RENDER_ONLY = ("SignalPlotterNode", "TemporalMultiScopeNode")
BAND = (0.15, 0.45)   # A return weights where 004 measured alternation


def node_class(name, upstream):
    if name in WORKSHOP:
        return load(ROOT / "nodes" / WORKSHOP[name], name)
    return load(pathlib.Path(upstream) / "nodes" / UPSTREAM[name], name)


def prepare(graph, upstream):
    obj, cls = {}, {}
    for desc in graph["nodes"]:
        n = node_class(desc["class_name"], upstream)()
        config = copy.deepcopy(desc.get("config", {}))
        if hasattr(n, "set_config_options"):
            n.set_config_options(config)
        for k, v in config.items():
            if hasattr(n, k) and getattr(n, k) != v:
                setattr(n, k, v)
        obj[desc["id"]] = n; cls[desc["id"]] = desc["class_name"]
    if obj[1].field.shape != (96, 96):
        raise RuntimeError("wave field is not 96x96: %s" % (obj[1].field.shape,))
    for e in graph["edges"]:
        s, d = obj[e["from_node_id"]], obj[e["to_node_id"]]
        if e["from_port"] not in s.outputs or e["to_port"] not in d.inputs:
            raise RuntimeError("invalid edge %s" % e)
        if s.outputs[e["from_port"]] != d.inputs[e["to_port"]]:
            raise RuntimeError("type mismatch %s" % e)
    return obj, cls


def run_graph(graph, upstream, steps=6000, overrides=None):
    g = copy.deepcopy(graph)
    for node in g["nodes"]:
        for key, val in (overrides or {}).get(node["id"], {}).items():
            node["config"][key] = val
    obj, cls = prepare(g, upstream)
    causal = {i: n for i, n in obj.items() if cls[i] not in RENDER_ONLY}
    gates = [i for i in causal if cls[i] == "HomeostaticReturnGateNode"]
    spikes = {2: [], 3: []}
    weights = {i: [] for i in gates}
    clip_frames = 0
    for tick in range(steps):
        for n in causal.values():
            n.pre_step()
        for e in g["edges"]:
            if e["to_node_id"] not in causal:
                continue
            s = obj[e["from_node_id"]]
            val = s.get_output(e["from_port"])
            if val is not None:
                obj[e["to_node_id"]].set_input(e["to_port"], val,
                    s.outputs[e["from_port"]], e.get("learned_weight", 1.0))
        for n in causal.values():
            n.step()
        for i in (2, 3):
            if obj[i].get_output("pulse") > 0:
                spikes[i].append(tick)
        for i in gates:
            weights[i].append(float(obj[i].weight))
        clip_frames += int(float(np.max(np.abs(obj[1].field))) >= 3.9998)
    q = steps // 4
    quarters = lambda seq: [sum(lo <= t < lo + q for t in seq) for lo in (0, q, 2 * q, 3 * q)]
    last = lambda seq: [t for t in seq if t >= 3 * q]
    def isi(seq):
        gaps = [b - a for a, b in zip(seq, seq[1:])]
        return round(statistics.mean(gaps), 2) if gaps else None
    order = sorted([(t, "A") for t in last(spikes[2])] + [(t, "B") for t in last(spikes[3])])
    inter = (round(sum(order[k][1] != order[k - 1][1] for k in range(1, len(order)))
                   / (len(order) - 1), 4) if len(order) > 1 else None)
    names = {7: "A", 8: "B"}
    out = {
        "quarter_spikes": {"A": quarters(spikes[2]), "B": quarters(spikes[3])},
        "last_quarter_mean_interval": {"A": isi(last(spikes[2])), "B": isi(last(spikes[3]))},
        "last_quarter_interleaving": inter,
        "clip_frames": clip_frames,
        "weights": {},
    }
    for i in gates:
        w = weights[i]
        tail = w[3 * q:]
        out["weights"][names.get(i, str(i))] = {
            "at_quarters": [round(w[k * q - 1], 4) for k in (1, 2, 3, 4)],
            "final": round(w[-1], 4),
            "last_quarter_min": round(min(tail), 4),
            "last_quarter_max": round(max(tail), 4),
            "final_in_004_band": bool(BAND[0] <= w[-1] <= BAND[1]),
            "trajectory_every_100": [round(x, 4) for x in w[::100]],
        }
    both_alive = out["quarter_spikes"]["A"][3] > 0 and out["quarter_spikes"]["B"][3] > 0
    out["regime_last_quarter"] = (
        "both fire, alternating" if both_alive and inter is not None and inter >= 0.9 else
        "both fire, not strictly alternating" if both_alive else
        "A only" if out["quarter_spikes"]["A"][3] > 0 else
        "B only" if out["quarter_spikes"]["B"][3] > 0 else "silent")
    return out


def main(upstream, steps=6000):
    G = {p.name: json.loads(p.read_text()) for p in sorted((ROOT / "workflows").glob("007_*.json"))}
    primary = G["007_homeostatic_a_return.json"]
    frozen = G["007_frozen_gate_full.json"]
    res = {"experiment": "007_homeostatic_return", "steps": steps,
           "primary_settings": {"target_rate": 0.010, "learning_rate": 0.02,
                                "rate_tau": 200, "initial_weight": 1.0},
           "band_from_004": list(BAND), "cases": {}}
    C = res["cases"]
    C["primary_homeostatic_A"] = run_graph(primary, upstream, steps)
    C["control_frozen_gate_1.00"] = run_graph(frozen, upstream, steps)
    C["control_anti_homeostatic_from_0.30"] = run_graph(G["007_anti_homeostatic_a.json"], upstream, steps)
    C["control_homeostatic_A_no_B_return"] = run_graph(G["007_homeostatic_a_no_b_return.json"], upstream, steps)
    C["both_homeostatic"] = run_graph(G["007_both_homeostatic.json"], upstream, steps)
    # Fixed-gain sweep THROUGH the gate (same one-frame delay), learning off.
    for w in (0.15, 0.25, 0.30, 0.45, 0.50, 0.75):
        C["frozen_gate_%.2f" % w] = run_graph(frozen, upstream, steps, {7: {"weight": w}})
    # Does the end state depend on where the weight starts?
    for w0 in (0.75, 0.50, 0.30, 0.05):
        C["homeostatic_A_start_%.2f" % w0] = run_graph(primary, upstream, steps, {7: {"weight": w0}})
    # Does it depend on the chosen target and speed?
    for tr in (0.004, 0.006, 0.008, 0.0125, 0.016, 0.020, 0.030):
        C["homeostatic_A_target_%.4f" % tr] = run_graph(primary, upstream, steps, {7: {"target_rate": tr}})
    for lr in (0.005, 0.08, 0.32):
        C["homeostatic_A_lr_%.3f" % lr] = run_graph(primary, upstream, steps, {7: {"learning_rate": lr}})
    for tau in (50.0, 800.0):
        C["homeostatic_A_tau_%d" % tau] = run_graph(primary, upstream, steps, {7: {"rate_tau": tau}})
    # ---- Added AFTER seeing the first results (post hoc, labelled as such) ----
    # Is 0.15 really a lower edge of the band? Is A's return needed at all?
    for w in (0.00, 0.05):
        C["posthoc_frozen_gate_%.2f" % w] = run_graph(frozen, upstream, steps, {7: {"weight": w}})
    # The planned anti control started at 0.30 and could not discriminate. Start it where it can.
    anti = G["007_anti_homeostatic_a.json"]
    for w0 in (0.45, 1.00):
        C["posthoc_anti_homeostatic_from_%.2f" % w0] = run_graph(anti, upstream, steps, {7: {"weight": w0}})
    # Two cases were still drifting at 6,000 frames; run them twice as long.
    C["posthoc_start_0.05_12000_frames"] = run_graph(primary, upstream, 2 * steps, {7: {"weight": 0.05}})
    C["posthoc_tau_800_12000_frames"] = run_graph(primary, upstream, 2 * steps, {7: {"rate_tau": 800.0}})
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", default="PerceptionLab")
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--out", default="results/007_homeostatic_return.json")
    a = ap.parse_args()
    res = main(pathlib.Path(a.upstream), a.steps)
    (ROOT / a.out).write_text(json.dumps(res, indent=1) + "\n")
    for name, c in res["cases"].items():
        w = {k: (v["final"], v["last_quarter_min"], v["last_quarter_max"]) for k, v in c["weights"].items()}
        print("%-38s A%s B%s isi=%s inter=%s w(final,min,max)=%s clip=%d | %s" % (
            name, c["quarter_spikes"]["A"], c["quarter_spikes"]["B"],
            c["last_quarter_mean_interval"], c["last_quarter_interleaving"], w,
            c["clip_frames"], c["regime_last_quarter"]))
