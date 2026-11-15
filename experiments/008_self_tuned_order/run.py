"""008 - Does a self-tuned network hold AB/BA order better than fixed weights?

System: the 005b three-active circuit (A 0.86, B 0.95, C 0.93 on one upstream
96x96 WaveField, 005b thresholds), with EVERY return routed through a
HomeostaticReturnGateNode so all conditions share the same one-frame delay.

Phase 1 (label-free development): gates learn from their own unit's firing
rate during long free runs seeded by development stimuli. No reader, no label.
Phase 2 (test): weights are frozen and the 005 protocol is run: a ridge
reader is fitted per condition on training pairs and scored on held-out pairs.

Everything marked PRIMARY below was fixed before the first run.
"""
from __future__ import annotations
import argparse, copy, json, pathlib, random, statistics, sys, time
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from host_shim import load
from importlib.util import spec_from_file_location, module_from_spec

def _imp(name, rel):
    s = spec_from_file_location(name, ROOT / rel); m = module_from_spec(s); s.loader.exec_module(m); return m
lab005 = _imp("lab005", "experiments/005_order_of_falls/run.py")
lab005b = _imp("lab005b", "experiments/005_order_of_falls/three_active.py")

UNITS = (3, 4, 5)                      # A, B, C
GATES = {3: 9, 4: 10, 5: 11}
WRITE = {3: "write_0", 4: "write_2", 5: "write_4"}
W_005B = (0.30, 1.00, 0.50)            # hand-set weights of 005b
CAL = lab005b.CAL
FLOORS = [.01 * CAL[str(i)]["trace_peak"] for i in UNITS] + [.001] * 3   # 005's finite-resolution floor
# ---- PRIMARY settings ----
TARGET, LR, TAU = 0.010, 0.02, 200.0   # same as 007
DEV_STEPS = 8000
TRIAL_STEPS, SNAPSHOTS = 660, (360, 650)
PRIMARY_SNAPSHOT, PRIMARY_FEATURES = 650, "all_six"
N_TRAIN, N_TEST, SEED = 16, 48, 8008

FILES = {"PulseSourceNode": ("up", "pulsesourcenode.py"), "WaveFieldNode": ("up", "wavefieldnode.py"),
         "SignalPlotterNode": ("up", "signalplotternode.py"),
         "FadingHistorySpikeNode": ("ws", "fading_history_spike_node.py"),
         "PopulationOrderReadoutNode": ("ws", "population_order_readout_node.py"),
         "HomeostaticReturnGateNode": ("ws", "homeostatic_return_gate_node.py")}


def make_pairs():
    """Seeded, label-free stimulus perturbations: (jitter, gap, amplitude scale)."""
    rng = random.Random(SEED)
    seen, out = set(), []
    while len(out) < N_TRAIN + N_TEST:
        j, g = rng.randint(-5, 5), rng.randint(25, 45)
        if (j, g) in seen:
            continue
        seen.add((j, g)); out.append((j, g, round(rng.uniform(0.90, 1.12), 3)))
    return out[:N_TRAIN], out[N_TRAIN:]


def build_graph(weights, learn=0, target=TARGET, lr=LR, tau=TAU):
    """005b three-active graph with all three returns passing through gates."""
    g = json.loads((ROOT / "workflows" / "005_ABC093_AB.json").read_text())
    g["edges"] = [e for e in g["edges"] if not (e["from_node_id"] in UNITS and e["to_node_id"] == 2)]
    for k, u in enumerate(UNITS):
        gid = GATES[u]
        g["nodes"].append({"id": gid, "class_name": "HomeostaticReturnGateNode",
                           "pos_x": 20.0 + 345.0 * k, "pos_y": 520.0, "width": 325.0, "height": 170.0,
                           "config": {"node_title": "%s return gate" % "ABC"[k], "weight": float(weights[k]),
                                      "target_rate": target, "learning_rate": lr, "rate_tau": tau,
                                      "sign": 1.0, "learn_enabled": int(learn)},
                           "custom_state_file": None})
        g["edges"] += [{"from_node_id": u, "from_port": "pulse", "to_node_id": gid, "to_port": "pre_spike", "learned_weight": 1},
                       {"from_node_id": gid, "from_port": "signal", "to_node_id": 2, "to_port": WRITE[u], "learned_weight": 1}]
    return g


def instantiate(graph, upstream):
    obj = {}
    for d in graph["nodes"]:
        where, fname = FILES[d["class_name"]]
        src = (pathlib.Path(upstream) / "nodes" if where == "up" else ROOT / "nodes") / fname
        n = load(src, d["class_name"])()
        cfg = copy.deepcopy(d.get("config", {}))
        if hasattr(n, "set_config_options"):
            n.set_config_options(cfg)
        for k, v in cfg.items():
            if hasattr(n, k) and getattr(n, k) != v:
                setattr(n, k, v)
        n._render = lambda *a: None          # drawing only; state update untouched
        obj[d["id"]] = n
    if obj[2].field.shape != (96, 96):
        raise RuntimeError("wave is not 96x96")
    for e in graph["edges"]:
        a, b = obj[e["from_node_id"]], obj[e["to_node_id"]]
        if e["from_port"] not in a.outputs or e["to_port"] not in b.inputs:
            raise RuntimeError("bad edge %s" % e)
    return obj


def simulate(graph, upstream, steps, snapshots=()):
    obj = instantiate(graph, upstream)
    ids = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11]
    active = {i: obj[i] for i in ids}
    edges = [e for e in graph["edges"] if e["to_node_id"] in active]
    feats, spikes, clip = {}, {u: [] for u in UNITS}, 0
    wtraj = {u: [] for u in UNITS}
    for tick in range(steps):
        for n in active.values():
            n.pre_step()
        for e in edges:
            a = active[e["from_node_id"]]
            v = a.get_output(e["from_port"])
            if v is not None:
                active[e["to_node_id"]].set_input(e["to_port"], v, a.outputs[e["from_port"]], e.get("learned_weight", 1.0))
        for n in active.values():
            n.step()
        for u in UNITS:
            if obj[u].pulse:
                spikes[u].append(tick)
        if tick % 200 == 0:
            for u in UNITS:
                wtraj[u].append(round(float(obj[GATES[u]].weight), 4))
        clip += int(float(np.max(np.abs(obj[2].field))) >= 3.9998)
        if tick in snapshots:
            feats[tick] = [float(v) for v in obj[6].features]
    return {"features": feats, "spikes": spikes, "clipped_frames": clip,
            "final_weights": [float(obj[GATES[u]].weight) for u in UNITS], "weight_every_200": wtraj}


def develop(upstream, pairs, steps=DEV_STEPS, target=TARGET, start=W_005B):
    """Label-free: gates learn during free runs seeded by dev stimuli in both orders."""
    runs = []
    for trial in pairs:
        for order in ("AB", "BA"):
            g = lab005.prepare_trial(build_graph(start, learn=1, target=target), order, trial)
            r = simulate(g, upstream, steps)
            q = steps // 4
            runs.append({"trial": list(trial), "order": order, "final_weights": [round(w, 4) for w in r["final_weights"]],
                         "last_quarter_spikes": [sum(t >= 3 * q for t in r["spikes"][u]) for u in UNITS],
                         "weight_every_200": r["weight_every_200"], "clipped_frames": r["clipped_frames"]})
    W = [round(statistics.median(x["final_weights"][k] for x in runs), 4) for k in range(3)]
    spread = [round(max(x["final_weights"][k] for x in runs) - min(x["final_weights"][k] for x in runs), 4) for k in range(3)]
    by_order = {o: [round(statistics.mean(x["final_weights"][k] for x in runs if x["order"] == o), 4) for k in range(3)]
                for o in ("AB", "BA")}
    return {"median_weights": W, "range_across_runs": spread, "mean_by_order": by_order, "runs": runs}


def collect(upstream, weights, pairs, learn=0, target=TARGET):
    data = {}
    for j, trial in enumerate(pairs):
        for order in ("AB", "BA"):
            g = lab005.prepare_trial(build_graph(weights, learn=learn, target=target), order, trial)
            data[(j, order)] = simulate(g, upstream, TRIAL_STEPS, SNAPSHOTS)
    return data


def score(train, test):
    """005's reader: ridge fit on training runs only, finite-resolution floor applied to both."""
    tr, te = lab005.observed_resolution(train, FLOORS), lab005.observed_resolution(test, FLOORS)
    out = {}
    for t in SNAPSHOTS:
        out[str(t)] = {}
        for fs in ("all_six", "traces_only", "spike_history_only"):
            m = lab005.fit_linear(tr, t, fs)
            w, b = np.array(m["weights"]), m["bias"]
            idx = lab005.FEATURE_SETS[fs]
            correct = {}
            for (j, order), rec in sorted(te.items()):
                s = float(np.asarray([rec["features"][t][i] for i in idx]) @ w + b)
                correct["%d%s" % (j, order)] = bool(s >= 0 if order == "AB" else s < 0)
            out[str(t)][fs] = {"correct": sum(correct.values()), "of": len(correct),
                               "accuracy": round(sum(correct.values()) / len(correct), 4), "per_run": correct}
    return out


def sign_test(a, b):
    """Exact two-sided sign test on runs where the two conditions disagree."""
    from math import comb
    wins = sum(a[k] and not b[k] for k in a); losses = sum(b[k] and not a[k] for k in a)
    n = wins + losses
    p = 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(0, min(wins, losses) + 1)) / 2 ** n)
    return {"first_only_correct": wins, "second_only_correct": losses, "p_two_sided": round(p, 5)}


def condition(upstream, weights, train_pairs, test_pairs, learn=0, target=TARGET):
    train, test = collect(upstream, weights, train_pairs, learn, target), collect(upstream, weights, test_pairs, learn, target)
    mean_sp = [round(statistics.mean(sum(t >= 160 for t in r["spikes"][u]) for r in test.values()), 2) for u in UNITS]
    return {"weights": [round(float(w), 4) for w in weights], "learning_during_trials": bool(learn),
            "scores": score(train, test), "mean_post160_spikes_ABC": mean_sp,
            "clipped_frames": sum(r["clipped_frames"] for r in list(train.values()) + list(test.values())),
            "end_weights_live_mean": [round(statistics.mean(r["final_weights"][k] for r in test.values()), 4) for k in range(3)]}


def main(upstream, quick=False):
    t0 = time.time()
    train_pairs, test_pairs = make_pairs()
    if quick:
        train_pairs, test_pairs = train_pairs[:4], test_pairs[:6]
    res = {"experiment": "008_self_tuned_order",
           "primary": {"target_rate": TARGET, "learning_rate": LR, "rate_tau": TAU, "dev_steps": DEV_STEPS,
                       "snapshot": PRIMARY_SNAPSHOT, "features": PRIMARY_FEATURES, "start_weights": list(W_005B),
                       "train_pairs": len(train_pairs), "heldout_pairs": len(test_pairs), "seed": SEED},
           "train_pairs": train_pairs, "heldout_pairs": test_pairs, "floors": FLOORS}
    dev = develop(upstream, train_pairs[:8] if not quick else train_pairs[:2], DEV_STEPS if not quick else 2000)
    res["development"] = dev
    W = dev["median_weights"]
    print("dev weights", W, "range", dev["range_across_runs"], "by order", dev["mean_by_order"], "%.0fs" % (time.time() - t0), flush=True)
    mean = round(sum(W) / 3, 4)
    conds = {"fixed_005b": (W_005B, 0), "pruned_C": ((0.30, 1.00, 0.00), 0), "self_tuned_frozen": (W, 0),
             "self_tuned_live": (W, 1), "passive": ((0.0, 0.0, 0.0), 0),
             "control_uniform_mean": ((mean, mean, mean), 0), "control_rotated": ((W[1], W[2], W[0]), 0)}
    res["conditions"] = {}
    for name, (w, learn) in conds.items():
        res["conditions"][name] = c = condition(upstream, w, train_pairs, test_pairs, learn)
        print("%-22s w=%s  %s  spikes=%s clip=%d  %.0fs" % (name, c["weights"],
              {t: "%d/%d" % (c["scores"][t]["all_six"]["correct"], c["scores"][t]["all_six"]["of"]) for t in c["scores"]},
              c["mean_post160_spikes_ABC"], c["clipped_frames"], time.time() - t0), flush=True)
    P = lambda n: res["conditions"][n]["scores"][str(PRIMARY_SNAPSHOT)][PRIMARY_FEATURES]["per_run"]
    res["paired_tests_primary"] = {
        "self_tuned_frozen_vs_fixed_005b": sign_test(P("self_tuned_frozen"), P("fixed_005b")),
        "self_tuned_frozen_vs_pruned_C": sign_test(P("self_tuned_frozen"), P("pruned_C")),
        "self_tuned_live_vs_fixed_005b": sign_test(P("self_tuned_live"), P("fixed_005b")),
        "pruned_C_vs_fixed_005b": sign_test(P("pruned_C"), P("fixed_005b")),
        "self_tuned_frozen_vs_control_rotated": sign_test(P("self_tuned_frozen"), P("control_rotated"))}
    print(json.dumps(res["paired_tests_primary"], indent=1), flush=True)
    if not quick:
        # Exploratory: other targets. NOT to be used for picking a winner.
        res["exploratory_targets"] = {}
        for tr in (0.006, 0.014):
            d = develop(upstream, train_pairs[:4], DEV_STEPS, target=tr)
            c = condition(upstream, d["median_weights"], train_pairs, test_pairs, 0, tr)
            res["exploratory_targets"]["%.3f" % tr] = {"development": {k: d[k] for k in ("median_weights", "range_across_runs", "mean_by_order")}, "condition": c}
            print("target %.3f w=%s %s" % (tr, d["median_weights"],
                  {t: "%d/%d" % (c["scores"][t]["all_six"]["correct"], c["scores"][t]["all_six"]["of"]) for t in c["scores"]}), flush=True)
    res["seconds"] = round(time.time() - t0)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", default="PerceptionLab")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", default="results/008_self_tuned_order.json")
    a = ap.parse_args()
    r = main(pathlib.Path(a.upstream), a.quick)
    (ROOT / a.out).write_text(json.dumps(r, indent=1) + "\n")
    print("done in", r["seconds"], "s")
