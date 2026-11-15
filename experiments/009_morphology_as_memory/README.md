# 009 — Morphology as memory

15 November 2026. Built and run by Claude Fable 5.2 at Antti's request, from Sol's "Morphology as Memory" proposal.

**Result: one of three questions passed.** Branch structure grown by a local rule keeps the order of past events after every signal is gone, and one identical probe pulse reads it out at **89 of 96 held-out bodies**. The predicted behaviour (cue A recalling B) did **not** appear; it came out reversed for one cue. Pruning did **not** protect the memory against later experience.

[Full receipt](../../results/009_morphology_as_memory.json) · [runner](run.py) · [core](core.py) · [node](../../nodes/growing_return_node.py) · [tests](../../tests/test_009_morphology_as_memory.py) · [design commit, before results](https://github.com/anttiluode/PerceptionLabAI/commit/dce4242)

## Why this experiment

006 and 008 tried to make a connection learn what to keep by adjusting one number per edge, first by outside reward, then by self-tuning. Both failed. 009 changes what is allowed to change: where a unit's output goes.

## The body

Three fade-triggered units (the same `FadingHistorySpikeNode` as 003–008) sit on one upstream 96×96 `WaveFieldNode`, reading apertures 1, 4 and 6. Each unit returns its pulse to the field through a new `GrowingReturnNode` with **eight candidate branches**, one per write site.

```math
e_s \leftarrow \lambda\, e_s + (1-\lambda)\,\lvert F_s \rvert
```

```math
\text{when the unit fires:}\quad w_s \leftarrow w_s + \eta\,\bigl(p_s - \bar p\bigr), \qquad p_s = \frac{e_s}{\sum_k e_k}
```

Here $`F_s`$ is the field at the tip of branch $`s`$, $`e_s`$ is how busy that site has been lately, and $`w_s`$ is the branch weight. After each update the weights are rescaled so they always sum to a fixed budget, and any branch below the prune threshold is removed for good. So a branch grows only at the expense of the unit's other branches.

The rule sees the unit's own pulse and the field at its branch tips. Nothing else. The ingredients are old: Hebbian growth toward recently active targets, budget competition and pruning. The question is what they do in this system.

## Protocol

- **History.** A body starts with all branches equal and lives through 20 episodes of 400 frames. Each episode delivers two equal pulses at opposite ends of the aperture line: A then B, or B then A. Gap, strength and timing jitter vary by body and by episode.
- **Wipe.** Between episodes all fast state is discarded: the field, the unit traces, the branch-tip traces. Only branch weights and the list of pruned branches carry over.
- **Bodies.** 64 parameter sets, each grown under both orders. 16 are used to fit readers, 48 are held out (96 held-out bodies).
- **Settings** were chosen on a small development batch from a separate seed, then locked and committed together with the decision rules before the full run.

Zero clipped frames across every grown body.

## Q1 — Do the two histories leave different structures?

Yes. Mean branch weights over all 64 bodies per history (rows are units, columns are write sites 0–7):

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **AB** unit near A | 0 | 0 | 0.57 | 0.39 | 0.04 | 0 | 0 | 0 |
| **AB** middle unit | 0.11 | 0.13 | 0.15 | 0.15 | 0.14 | 0.12 | 0.11 | 0.09 |
| **AB** unit near B | 0.04 | 0.15 | 0.23 | 0.27 | 0.17 | 0.07 | 0.05 | 0.04 |
| **BA** unit near A | 0 | 0 | 0 | 0.69 | 0.32 | 0 | 0 | 0 |
| **BA** middle unit | 0.11 | 0.14 | 0.15 | 0.16 | 0.15 | 0.12 | 0.10 | 0.07 |
| **BA** unit near B | 0 | 0 | 0 | 0.64 | 0.36 | 0 | 0 | 0 |

Of 24 branches, a body keeps 16.3 on average after an AB history and 11.9 after BA. Branches collect toward the middle of the line, where the two waves overlap, and which middle sites win depends on the order. The middle unit barely fired and barely changed.

## Q2 — After a full wipe, can one probe pulse reveal the history?

Each held-out body gets the same single pulse at site 3, with growth off. A linear reader, fitted on the 32 training bodies, reads three unit traces and three spike averages 300 frames later.

| Body | Held-out correct, frame 150 | **Frame 300** |
|---|---:|---:|
| **Grown** | 90/96 | **89/96** |
| Growth switched off during the history | 48/96 | **48/96** |
| Same branches, positions scrambled | 64/96 | **55/96** |
| Grown without pruning | 88/96 | **88/96** |
| Reading the weights directly (upper bound) | | 91/96 |

**Rule (set beforehand):** grown at 75% or better, growth-off at chance, scrambled at 65% or below, at frame 300. **All three hold.** The history is in the arrangement of the branches, not in how many survive, and the probe recovers nearly everything a direct look at the weights would give (89 against 91).

One caution on the scrambled control: at frame 150 it scores 64/96, which is above chance (p = 0.001) and a hair over the 65% line. The rule named frame 300, where it is 55/96. Some information that does not depend on position does leak through early.

## Q3 — Behaviour without a reader: does cue A recall B?

**No.** The prediction was that in a body grown on A-then-B, pulse A alone would evoke more activity near B's site than in the matching BA body, and the mirror image for cue B.

| Cue | Mean activity near the *other* site | Paired comparison over 48 bodies |
|---|---|---|
| A alone | AB bodies 9.9 · BA bodies 16.9 · ungrown body 21.0 | BA higher in 42, AB higher in 6: **opposite to prediction** |
| B alone | BA bodies 23.0 · AB bodies 21.5 · ungrown body 13.4 | BA higher in 33, AB higher in 15 (p = 0.013): as predicted |

The rule required both. One cue went the predicted way and the other went strongly the wrong way, so this is a fail. The cause is visible in Q1: branches grow toward the busy middle, not toward the partner's site. An AB body answers cue A with less far-side activity than a body that never grew at all.

So the structure distinguishes the histories, and the bodies do behave differently, but not as recall of the missing event.

## Q4 — Does the memory survive later experience, and does pruning help?

After its history each body lived ten more episodes of the **opposite** order, with growth on. The reader fitted before this interference was then asked for the first history.

| Body | Before | First history still read after | Mean weight change |
|---|---:|---:|---:|
| With pruning | 89/96 | 64/96 | 1.10 |
| Without pruning | 88/96 | 57/96 | 0.81 |

Paired: pruning-only correct 19, no-pruning-only correct 12, p = 0.28. **By the rule, pruning does not help.** Both kinds of body lose most of the first history; 64/96 is still above chance, 57/96 is not clearly so.

Pruned bodies changed *more* during interference, not less. A dead branch cannot return, but the living ones keep trading weight, so pruning does not freeze a body.

## What this adds, and what it does not

**Adds.** This is the first positive result in the series for a change made by the system to itself. A purely local rule, with no label, reward or reader, leaves a record of event order in structure. The record survives total silence, which the pulse-train memory of 005 cannot, and it can be read back through the body's ordinary response to one pulse.

**Does not add.**

- **It is close to expected.** Any growth rule that is sensitive to timing will leave order in the weights. What needed showing was that it happens robustly across varied histories (93% on unseen bodies), that it is readable through dynamics, and that position carries it. Those hold.
- **No usefulness.** Sol's third criterion, that the grown structure improves a task, was not tested beyond Q3, and Q3 failed.
- **Not durable.** Ten episodes of the other order mostly overwrite it.
- **Not a comparison with a standard method.** A plain Hebbian weight matrix would also store order. 009 does not show that branches and budgets do it better.
- **One geometry, three units, deterministic, no noise.** The middle unit hardly took part.
- **Episodes are separated by an imposed wipe.** A body left running would keep rewriting itself with its own activity; that case was not tested.

## Reproduce

```bat
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
python -m unittest discover -s tests -p test_009_morphology_as_memory.py -v
python experiments\009_morphology_as_memory\run.py --upstream ..\PerceptionLab --dev
python experiments\009_morphology_as_memory\run.py --upstream ..\PerceptionLab
```

`--dev` is the small development-seed run (about four minutes on two cores). The full run took 18 minutes on two cores; `--workers` sets the number of processes.

**GUI graphs** (copy `growing_return_node.py` and `fading_history_spike_node.py` into PerceptionLab's `nodes` folder first):

- [009_AB_growing_one_episode.json](../../workflows/009_AB_growing_one_episode.json) · [BA](../../workflows/009_BA_growing_one_episode.json) — one episode from equal branches, growth on. The bars on each Growing Return node are its eight branch weights; grey outlines are pruned branches.
- [009_probe_AB_grown_body.json](../../workflows/009_probe_AB_grown_body.json) · [BA](../../workflows/009_probe_BA_grown_body.json) · [naive](../../workflows/009_probe_naive_body.json) — one grown example body of each kind, and an ungrown one, answering the same probe pulse.

The GUI runs one continuous episode; the wipe between episodes exists only in the runner. None of the 009 graphs has been run in the GUI.
