"""010 - Hardening: if used branches become harder to change, does the first history survive later experience?

Same bodies, histories, probe and reader as 009. The only change is in GrowingReturnNode:
each branch keeps a hardness that grows with use, and its plasticity is 1 / (1 + harden_rate * hardness).

Conditions (all with 009's pruning):
  soft      harden_rate 0            (009 as it was)
  use       hardens by own weight per firing      <- the hypothesis
  age       every branch hardens equally per firing (control: plain ageing, same total hardness)
After its history every body lives 10 and then 20 episodes of the OPPOSITE order with growth on.
The reader is fitted on training bodies BEFORE interference and asked for the FIRST history.
"""
from __future__ import annotations
import argparse, json, pathlib, random, statistics, sys, time
from multiprocessing import Pool
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from importlib.util import spec_from_file_location, module_from_spec
def _imp(name, rel):
    s = spec_from_file_location(name, ROOT / rel); m = module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m
r9 = _imp("run009", "experiments/009_morphology_as_memory/run.py")
core = r9.core

HARDEN_RATE = 0.2            # locked after the development sweep (see README)
CHECKPOINTS = (10, 20)       # opposite-order episodes
SEED, DEV_SEED = 1010, 4321  # fresh bodies, not the 009 ones


def params(mode, rate=None):
    p = dict(r9.GROW)
    if mode == "use":
        p.update(harden_rate=HARDEN_RATE if rate is None else rate, harden_mode=1)
    elif mode == "age":
        p.update(harden_rate=HARDEN_RATE if rate is None else rate, harden_mode=2)
    return p


def life(args):
    bp, order, P = args
    rng = random.Random(bp["seed"])
    st = core.uniform_structure(P["budget"]); clip = 0
    for ep in range(r9.EPISODES):
        r = core.episode(st, r9.TH, r9.UP, order, bp["gap"] + rng.randint(-3, 3), bp["scale"], r9.EP_STEPS,
                         learn=1, params=P, jitter=rng.randint(-5, 5))
        st = r["structure"]; clip += r["clipped_frames"]
    out = {"id": bp["id"], "order": order, "after_history": st, "clipped_frames": clip}
    other = "BA" if order == "AB" else "AB"
    cur = st
    for ep in range(1, max(CHECKPOINTS) + 1):
        r = core.episode(cur, r9.TH, r9.UP, other, bp["gap"] + rng.randint(-3, 3), bp["scale"], r9.EP_STEPS,
                         learn=1, params=P, jitter=rng.randint(-5, 5))
        cur = r["structure"]; out["clipped_frames"] += r["clipped_frames"]
        if ep in CHECKPOINTS:
            out["after_%d" % ep] = cur
    return out


def evaluate(pool, bodies, train_ids, floors, rate):
    t = r9.PRIMARY_SNAPSHOT
    def feats(stage):
        keys = sorted(bodies)
        fs = pool.map(r9.probe_body, [({k: v for k, v in bodies[key][stage].items() if k != "hardness"}, "probe") for key in keys])
        return {k: f[t] for k, f in zip(keys, fs)}
    before = feats("after_history")
    tr = {k: v for k, v in before.items() if k[0] in train_ids}
    te = lambda d: {k: v for k, v in d.items() if k[0] not in train_ids}
    out = {"before": r9.fit_and_score(tr, te(before), t, floors)}
    flat = lambda st: np.array([x for row in st["weights"] for x in row])
    for c in CHECKPOINTS:
        out["after_%d" % c] = r9.fit_and_score(tr, te(feats("after_%d" % c)), t, floors)
        out["after_%d" % c]["mean_weight_change"] = round(statistics.mean(
            float(np.abs(flat(b["after_history"]) - flat(b["after_%d" % c])).sum()) for b in bodies.values()), 4)
    hard = [h for b in bodies.values() for row, alive in zip(b["after_history"]["hardness"], b["after_history"]["alive"])
            for h, al in zip(row, alive) if al]
    out["mean_plasticity_of_living_branches_after_history"] = round(statistics.mean(1.0 / (1.0 + rate * h) for h in hard), 4)
    out["living_branches_mean"] = round(statistics.mean(sum(sum(a) for a in b["after_history"]["alive"]) for b in bodies.values()), 2)
    out["clipped_frames"] = sum(b["clipped_frames"] for b in bodies.values())
    return out


def paired(a, b):
    w = sum(a[k] and not b[k] for k in a); l = sum(b[k] and not a[k] for k in a)
    return {"first_only_correct": w, "second_only_correct": l, "sign_p": r9.sign_p(w, l)}


def main(upstream, dev=False, workers=2):
    t0 = time.time()
    r9.UP = pathlib.Path(upstream)
    cal = core.calibrate(r9.UP); r9.TH = cal["thresholds"]
    floors = [0.01 * p for p in cal["peaks"]] + [0.001] * len(cal["peaks"])
    n_tr, n_te = (4, 8) if dev else (r9.N_TRAIN, r9.N_TEST)
    P = r9.body_params(DEV_SEED if dev else SEED, n_tr + n_te)
    train_ids = {p["id"] for p in P[:n_tr]}
    pool = Pool(workers)
    res = {"experiment": "010_hardening", "dev_run": dev, "harden_rate": HARDEN_RATE, "checkpoints": CHECKPOINTS,
           "grow": r9.GROW, "heldout_bodies": 2 * n_te, "train_bodies": 2 * n_tr, "conditions": {}}
    conds = ([("soft", None), ("use", 0.05), ("use", 0.2), ("use", 1.0), ("age", 0.2)] if dev
             else [("soft", None), ("use", None), ("age", None)])
    for mode, rate in conds:
        Pm = params(mode, rate)
        bodies = {(b["id"], b["order"]): b for b in pool.map(life, [(bp, o, Pm) for bp in P for o in ("AB", "BA")])}
        name = mode if not dev or mode == "soft" else "%s_%.2f" % (mode, rate)
        res["conditions"][name] = e = evaluate(pool, bodies, train_ids, floors, Pm.get("harden_rate", 0.0))
        print("%-9s before %d/%d | after10 %d/%d (dw %.2f) | after20 %d/%d (dw %.2f) | plasticity %.3f  branches %.1f  clip %d  %.0fs" % (
            name, e["before"]["correct"], e["before"]["of"], e["after_10"]["correct"], e["after_10"]["of"], e["after_10"]["mean_weight_change"],
            e["after_20"]["correct"], e["after_20"]["of"], e["after_20"]["mean_weight_change"],
            e["mean_plasticity_of_living_branches_after_history"], e["living_branches_mean"], e["clipped_frames"], time.time() - t0), flush=True)
    pool.close()
    if not dev:
        C = res["conditions"]
        res["paired"] = {"%s_vs_%s_after_%d" % (a, b, c): paired(C[a]["after_%d" % c]["per_body"], C[b]["after_%d" % c]["per_body"])
                         for a, b in (("use", "soft"), ("use", "age"), ("age", "soft")) for c in CHECKPOINTS}
        print(json.dumps(res["paired"], indent=1), flush=True)
    res["seconds"] = round(time.time() - t0)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", default="PerceptionLab")
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", default="results/010_hardening.json")
    a = ap.parse_args()
    r = main(a.upstream, a.dev, a.workers)
    (ROOT / a.out).write_text(json.dumps(r, indent=1) + "\n")
    print("done in", r["seconds"], "s")
