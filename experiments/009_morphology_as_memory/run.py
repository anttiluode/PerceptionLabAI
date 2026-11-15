"""009 - Morphology as memory: does a grown-and-pruned branch structure keep the order of past events?

Three fade-triggered units on one upstream 96x96 WaveField. Each unit's pulse returns to the field
through a GrowingReturnNode: eight candidate branches sharing a fixed budget, growing toward recently
busy sites and pruned for good when they fall below a threshold. The rule is local; no label or reader
touches the body.

A BODY is grown by a HISTORY: repeated episodes of two equal pulses, A then B or B then A.
Between episodes ALL fast state is wiped (field, traces, eligibility). Only the branch weights carry over.

Questions (decision rules are in README.md and were committed before the full run):
  Q1  Do AB and BA histories leave different structures?
  Q2  After a full wipe, can one identical neutral probe pulse reveal which history a held-out body had?
  Q3  Behaviour without a reader: does cue A alone evoke more activity at B's site in AB bodies (and vice versa)?
  Q4  Pruning: after later episodes of the OPPOSITE order, is the first history still readable,
      and does permanent pruning make the difference?
"""
from __future__ import annotations
import argparse, json, pathlib, random, statistics, sys, time
from math import comb
from multiprocessing import Pool
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from importlib.util import spec_from_file_location, module_from_spec
def _imp(name, rel):
    s = spec_from_file_location(name, ROOT / rel); m = module_from_spec(s); s.loader.exec_module(m); return m
core = _imp("core009", "experiments/009_morphology_as_memory/core.py")
lab005 = _imp("lab005", "experiments/005_order_of_falls/run.py")

# ---- settings locked after development runs on DEV seeds only ----
GROW = {"budget": 1.0, "learning_rate": 0.2, "trace_decay": 0.97, "prune_threshold": 0.02}
NO_PRUNE = dict(GROW, prune_threshold=0.0)
EPISODES, EP_STEPS = 20, 400
INTERFERENCE_EPISODES = 10
PROBE_SITE, PROBE_STEPS, SNAPSHOTS, PRIMARY_SNAPSHOT = 3, 320, (150, 300), 300
CUE_WINDOW = (20, 300)
N_TRAIN, N_TEST = 16, 48
SEED, DEV_SEED = 9009, 1234
UP = None; TH = None


def body_params(seed, n):
    rng = random.Random(seed)
    return [{"id": j, "gap": rng.randint(25, 45), "scale": round(rng.uniform(0.90, 1.12), 3),
             "seed": rng.randint(0, 10 ** 9)} for j in range(n)]


def grow_body(args):
    """Grow one body. Returns structure after the history, and after interference if asked."""
    bp, order, params, learn, interfere = args
    rng = random.Random(bp["seed"])
    st = core.uniform_structure(params["budget"])
    spikes = clip = 0
    for ep in range(EPISODES):
        r = core.episode(st, TH, UP, order, bp["gap"] + rng.randint(-3, 3), bp["scale"], EP_STEPS,
                         learn=learn, params=params, jitter=rng.randint(-5, 5))
        st = r["structure"]; clip += r["clipped_frames"]; spikes += sum(len(v) for v in r["spikes"].values())
    out = {"id": bp["id"], "order": order, "structure": st, "history_spikes": spikes, "clipped_frames": clip}
    if interfere:
        other = "BA" if order == "AB" else "AB"
        st2 = st
        for ep in range(INTERFERENCE_EPISODES):
            st2 = core.episode(st2, TH, UP, other, bp["gap"] + rng.randint(-3, 3), bp["scale"], EP_STEPS,
                               learn=1, params=params, jitter=rng.randint(-5, 5))["structure"]
        out["structure_after_interference"] = st2
    return out


def probe_body(args):
    """Full wipe is implicit: a fresh graph is built from the structure alone. Growth is off."""
    st, mode = args
    if mode == "probe":
        g = core.build_graph(st, TH, None, probe_site=PROBE_SITE, learn=0)
        return core.simulate(g, UP, PROBE_STEPS, SNAPSHOTS)["features"]
    g = core.build_graph(st, TH, [(mode, 20, 1.0)], learn=0)          # mode is "A" or "B": cue alone
    return core.simulate(g, UP, CUE_WINDOW[1], windows={"w": CUE_WINDOW})["site_energy"]["w"]


def shuffled(st, seed):
    """Same budget, same number of living branches per unit, arrangement scrambled."""
    rng = random.Random(seed); W, A = [], []
    for w, a in zip(st["weights"], st["alive"]):
        perm = list(range(core.N_SITES)); rng.shuffle(perm)
        W.append([w[p] for p in perm]); A.append([a[p] for p in perm])
    return {"weights": W, "alive": A}


def fit_and_score(train, test, t, floors=None):
    """train/test: dict (id, order) -> feature list. Ridge reader as in 005, fitted on training bodies only."""
    def pack(d):
        out = {}
        for k, f in d.items():
            v = list(f)
            if floors:
                v = [0.0 if abs(x) < fl else x for x, fl in zip(v, floors)]
            out[k] = {"features": {t: v}}
        return out
    tr, te = pack(train), pack(test)
    n = len(next(iter(train.values())))
    lab005.FEATURE_SETS["custom"] = tuple(range(n))
    m = lab005.fit_linear(tr, t, "custom")
    w, b = np.array(m["weights"]), m["bias"]
    per = {}
    for (j, order), rec in sorted(te.items()):
        s = float(np.asarray(rec["features"][t]) @ w + b)
        per["%d%s" % (j, order)] = bool(s >= 0 if order == "AB" else s < 0)
    return {"correct": sum(per.values()), "of": len(per), "accuracy": round(sum(per.values()) / len(per), 4), "per_body": per}


def binom_p(k, n):
    """Two-sided exact binomial test against 0.5."""
    lo = min(k, n - k)
    return round(min(1.0, 2 * sum(comb(n, i) for i in range(lo + 1)) / 2 ** n), 6)


def sign_p(wins, losses):
    return binom_p(wins, wins + losses) if wins + losses else 1.0


def main(upstream, dev=False, workers=4):
    global UP, TH
    t0 = time.time()
    UP = pathlib.Path(upstream)
    cal = core.calibrate(UP); TH = cal["thresholds"]
    floors = [0.01 * p for p in cal["peaks"]] + [0.001] * len(cal["peaks"])
    n_tr, n_te = (4, 8) if dev else (N_TRAIN, N_TEST)
    P = body_params(DEV_SEED if dev else SEED, n_tr + n_te)
    train_ids = {p["id"] for p in P[:n_tr]}
    res = {"experiment": "009_morphology_as_memory", "dev_run": dev,
           "settings": {"grow": GROW, "episodes": EPISODES, "episode_steps": EP_STEPS,
                        "interference_episodes": INTERFERENCE_EPISODES, "probe_site": PROBE_SITE,
                        "primary_snapshot": PRIMARY_SNAPSHOT, "train_bodies_per_order": n_tr,
                        "heldout_bodies_per_order": n_te, "unit_reads": core.UNIT_READS,
                        "unit_decays": core.UNIT_DECAYS, "stim_sites": core.STIM_SITE},
           "calibration": cal, "floors": floors, "body_parameters": P}
    pool = Pool(workers)
    jobs = lambda params, learn, interfere: [(bp, o, params, learn, interfere) for bp in P for o in ("AB", "BA")]
    split = lambda d: ({k: v for k, v in d.items() if k[0] in train_ids}, {k: v for k, v in d.items() if k[0] not in train_ids})

    # ---------- grow ----------
    grown = {(b["id"], b["order"]): b for b in pool.map(grow_body, jobs(GROW, 1, True))}
    print("grown with pruning  %.0fs" % (time.time() - t0), flush=True)
    grown_np = {(b["id"], b["order"]): b for b in pool.map(grow_body, jobs(NO_PRUNE, 1, True))}
    print("grown without pruning  %.0fs" % (time.time() - t0), flush=True)
    frozen = {(b["id"], b["order"]): b for b in pool.map(grow_body, jobs(GROW, 0, False))}

    # ---------- Q1: structure ----------
    flat = lambda st: [x for row in st["weights"] for x in row]
    living = lambda st: sum(sum(a) for a in st["alive"])
    mean_w = {o: np.mean([np.array(grown[k]["structure"]["weights"]) for k in grown if k[1] == o], axis=0).round(3).tolist()
              for o in ("AB", "BA")}
    res["Q1_structure"] = {
        "mean_weights_by_history": mean_w,
        "living_branches_mean": {o: round(statistics.mean(living(grown[k]["structure"]) for k in grown if k[1] == o), 2) for o in ("AB", "BA")},
        "living_branches_no_prune_mean": round(statistics.mean(living(b["structure"]) for b in grown_np.values()), 2),
        "history_spikes_mean": round(statistics.mean(b["history_spikes"] for b in grown.values()), 1),
        "clipped_frames_total": sum(b["clipped_frames"] for b in grown.values()) + sum(b["clipped_frames"] for b in grown_np.values())}

    # ---------- Q2: probe after full wipe ----------
    def probe_all(structs):
        keys = sorted(structs)
        feats = pool.map(probe_body, [(structs[k], "probe") for k in keys])
        return {k: f for k, f in zip(keys, feats)}
    S = {k: b["structure"] for k, b in grown.items()}
    variants = {
        "grown": S,
        "growth_off": {k: b["structure"] for k, b in frozen.items()},
        "shuffled_arrangement": {k: shuffled(s, 7919 * k[0] + (k[1] == "AB")) for k, s in S.items()},
        "grown_no_prune": {k: b["structure"] for k, b in grown_np.items()},
    }
    probes = {name: probe_all(st) for name, st in variants.items()}
    res["Q2_probe_decoding"] = {}
    for name, feats in probes.items():
        res["Q2_probe_decoding"][name] = {}
        for t in SNAPSHOTS:
            tr, te = split({k: f[t] for k, f in feats.items()})
            r = fit_and_score(tr, te, t, floors)
            r["p_vs_chance"] = binom_p(r["correct"], r["of"])
            res["Q2_probe_decoding"][name][str(t)] = r
        print("Q2 %-22s %s" % (name, {t: "%d/%d" % (v["correct"], v["of"]) for t, v in res["Q2_probe_decoding"][name].items()}), flush=True)
    tr, te = split({k: flat(s) for k, s in S.items()})
    res["Q2_probe_decoding"]["direct_weight_readout_upper_bound"] = fit_and_score(tr, te, 0)
    print("Q2 direct weights", res["Q2_probe_decoding"]["direct_weight_readout_upper_bound"]["correct"], flush=True)

    # ---------- Q3: cue completion, no reader ----------
    test_keys = sorted(k for k in S if k[0] not in train_ids)
    cueA = dict(zip(test_keys, pool.map(probe_body, [(S[k], "A") for k in test_keys])))
    cueB = dict(zip(test_keys, pool.map(probe_body, [(S[k], "B") for k in test_keys])))
    naiveA, naiveB = probe_body((core.uniform_structure(), "A")), probe_body((core.uniform_structure(), "B"))
    farA = lambda e: (e[6] + e[7]) / 2      # activity near B's site after cue A
    farB = lambda e: (e[0] + e[1]) / 2      # activity near A's site after cue B
    ids = sorted({k[0] for k in test_keys})
    a_w = sum(farA(cueA[(j, "AB")]) > farA(cueA[(j, "BA")]) for j in ids); a_l = sum(farA(cueA[(j, "AB")]) < farA(cueA[(j, "BA")]) for j in ids)
    b_w = sum(farB(cueB[(j, "BA")]) > farB(cueB[(j, "AB")]) for j in ids); b_l = sum(farB(cueB[(j, "BA")]) < farB(cueB[(j, "AB")]) for j in ids)
    res["Q3_cue_completion"] = {
        "cue_A_far_site_energy": {"AB_bodies": round(statistics.mean(farA(cueA[(j, "AB")]) for j in ids), 3),
                                  "BA_bodies": round(statistics.mean(farA(cueA[(j, "BA")]) for j in ids), 3),
                                  "naive_body": round(farA(naiveA), 3),
                                  "pairs_AB_higher": a_w, "pairs_BA_higher": a_l, "sign_p": sign_p(a_w, a_l)},
        "cue_B_far_site_energy": {"BA_bodies": round(statistics.mean(farB(cueB[(j, "BA")]) for j in ids), 3),
                                  "AB_bodies": round(statistics.mean(farB(cueB[(j, "AB")]) for j in ids), 3),
                                  "naive_body": round(farB(naiveB), 3),
                                  "pairs_BA_higher": b_w, "pairs_AB_higher": b_l, "sign_p": sign_p(b_w, b_l)},
        "predicted": "AB bodies higher for cue A, BA bodies higher for cue B"}
    print("Q3", json.dumps(res["Q3_cue_completion"]), flush=True)

    # ---------- Q4: interference and pruning ----------
    res["Q4_interference"] = {}
    per = {}
    for name, G in (("pruning", grown), ("no_pruning", grown_np)):
        before = probe_all({k: b["structure"] for k, b in G.items()})
        after = probe_all({k: b["structure_after_interference"] for k, b in G.items()})
        tr, _ = split({k: f[PRIMARY_SNAPSHOT] for k, f in before.items()})
        _, te_before = split({k: f[PRIMARY_SNAPSHOT] for k, f in before.items()})
        _, te_after = split({k: f[PRIMARY_SNAPSHOT] for k, f in after.items()})
        rb, ra = fit_and_score(tr, te_before, PRIMARY_SNAPSHOT, floors), fit_and_score(tr, te_after, PRIMARY_SNAPSHOT, floors)
        change = statistics.mean(float(np.abs(np.array(flat(b["structure"])) - np.array(flat(b["structure_after_interference"]))).sum())
                                 for b in G.values())
        res["Q4_interference"][name] = {"before": {k: rb[k] for k in ("correct", "of", "accuracy")},
                                        "first_history_still_read_after": {k: ra[k] for k in ("correct", "of", "accuracy")},
                                        "mean_total_weight_change_during_interference": round(change, 4)}
        per[name] = ra["per_body"]
        print("Q4 %-11s before %d/%d  after %d/%d  weight change %.3f" % (name, rb["correct"], rb["of"], ra["correct"], ra["of"], change), flush=True)
    w = sum(per["pruning"][k] and not per["no_pruning"][k] for k in per["pruning"]); l = sum(per["no_pruning"][k] and not per["pruning"][k] for k in per["pruning"])
    res["Q4_interference"]["paired"] = {"pruning_only_correct": w, "no_pruning_only_correct": l, "sign_p": sign_p(w, l)}
    print("Q4 paired", res["Q4_interference"]["paired"], flush=True)
    pool.close()
    res["example_structures"] = {"%d%s" % k: grown[k]["structure"] for k in sorted(grown)[:4]}
    res["seconds"] = round(time.time() - t0)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", default="PerceptionLab")
    ap.add_argument("--dev", action="store_true", help="small run on development seeds")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="results/009_morphology_as_memory.json")
    a = ap.parse_args()
    r = main(a.upstream, a.dev, a.workers)
    (ROOT / a.out).write_text(json.dumps(r, indent=1) + "\n")
    print(json.dumps(r["Q1_structure"], indent=1)); print("done in", r["seconds"], "s")
