# 008 — Does a self-tuned network hold AB/BA order better than fixed weights?

15 November 2026. Built and run by Claude Fable 5.2 at Antti's request, as the deciding test for the memory line after [007](../007_homeostatic_return/README.md).

**Answer: no. It holds order clearly worse.** With returns tuned by firing-rate homeostasis, the held-out AB/BA readout scored **60/96**. The hand-set weights of 005b scored **81/96**. The paired test puts that difference well outside chance (p = 0.0003). By the rule fixed before the run, this closes the question against the self-tuned network.

[Full receipt](../../results/008_self_tuned_order.json) · [runner](run.py) · [tests](../../tests/test_008_self_tuned_order.py) · [graph builder](make_workflows.py)

## Question and decision rule

007 showed that a return edge can regulate itself into a regime where a suppressed unit takes part. It did not show that this helps the network remember anything. 008 asks that directly, using 005's order test.

Fixed before the first run, and committed before any result existed ([commit b70db1e](https://github.com/anttiluode/PerceptionLabAI/commit/b70db1e)):

- Primary metric: held-out accuracy at frame 650, six-feature reader, with 005's finite measurement floor.
- Self-tuning counts as a win only if it beats the hand-set 005b weights on a paired sign test over the held-out runs.
- Homeostasis settings are 007's: target 0.010 pulses per frame, learning rate 0.02, rate window 200.

## Setup

The circuit is 005b's three-active system: units A (decay 0.86), B (0.95) and C (0.93) on one upstream 96×96 `WaveFieldNode`, with the 005b thresholds. Every return passes through a `HomeostaticReturnGateNode`, so every condition has the same one-frame delay, including the fixed ones.

**Phase 1, development, no labels.** Starting from the 005b weights (0.30, 1.00, 0.50), the three gates learn from their own unit's firing rate during 8,000-frame free runs. Sixteen runs: eight stimulus pairs, each in both orders. The self-tuned weights are the median across those runs. No reader and no label is involved.

**Phase 2, test.** Weights are frozen. For each condition a ridge reader is fitted on 16 training pairs (32 runs) and scored on **48 held-out pairs (96 runs)**. 005 and 006 used 16 held-out runs; that was too few to separate conditions, so 008 uses six times as many. Stimulus perturbations come from a seeded generator; training and held-out pairs are disjoint.

## Result

Held-out runs correct out of 96, six-feature reader with the measurement floor.

| Condition | Return weights A, B, C | Frame 360 | **Frame 650** |
|---|---|---:|---:|
| Hand-set, 005b | 0.30, 1.00, 0.50 | 78 | **81** |
| Hand-set, C's return cut | 0.30, 1.00, 0.00 | 85 | **85** |
| **Self-tuned, frozen** | 0.22, 0.90, 0.47 | 68 | **60** |
| Self-tuned, still learning during trials | starts 0.22, 0.90, 0.47 | 74 | **75** |
| Passive field | 0, 0, 0 | 48 | **48** |
| Control: all three at the self-tuned mean | 0.53, 0.53, 0.53 | 67 | **46** |
| Control: self-tuned weights rotated between units | 0.90, 0.47, 0.22 | 85 | **65** |

Paired sign tests at frame 650 (runs where two conditions disagree):

| Comparison | First right, second wrong | Second right, first wrong | p |
|---|---:|---:|---:|
| Self-tuned frozen vs hand-set 005b | 6 | 27 | 0.0003 |
| Self-tuned frozen vs C's return cut | 2 | 27 | below 0.0001 |
| Self-tuned live vs hand-set 005b | 8 | 14 | 0.29 |
| C's return cut vs hand-set 005b | 11 | 7 | 0.48 |
| Self-tuned frozen vs rotated control | 17 | 22 | 0.52 |

Zero clipped frames in every condition.

## What the numbers say

1. **Self-tuning hurts order memory here.** 60/96 against 81/96. The self-tuned weights are only a little different from the hand-set ones (A 0.30 → 0.22, B 1.00 → 0.90, C 0.50 → 0.47), and that small shift costs 21 runs.
2. **Letting the gates keep learning during the trial does not rescue it.** 75/96, not distinguishable from hand-set and not better.
3. **Other targets do not rescue it either** (exploratory, not used to pick anything): target 0.006 gave weights 0.26, 0.70, 0.34 and 75/96; target 0.014 gave 0.47, 0.99, 1.00 and 71/96. Both are below hand-set.
4. **A correction to 005b.** With 16 held-out runs, 005b reported that cutting C's return improved decoding from 10/16 to 15/16. With 96 runs through the gates it is 85 against 81, and the paired test cannot tell them apart (p = 0.48). The claim that the third active unit makes order harder to read is **not supported** at this sample size. (The gates add one frame of delay, so this is not an exact replay of 005b.)
5. **Weights matter a great deal.** The uniform control falls to chance at frame 650 (46/96), and the rotated control drops from 85 at frame 360 to 65 at frame 650. The hand-set weights are a good operating point, found without anyone aiming for it.

## A likely reason, not tested

In development, AB-seeded and BA-seeded runs end at nearly the same weights (A 0.217 vs 0.215, B 0.899 vs 0.898) and the same firing: about 22 pulses per unit per 2,000 frames, all three equal. The rule pulls every unit to the same rate, and the system settles into one regular rotation regardless of which stimulus came first.

A network that always ends in the same rhythm has forgotten how it started. Homeostasis is a mechanism for converging, and remembering order needs the two histories to stay apart. This would explain the result, but 008 did not measure how fast AB and BA trajectories merge, so it stays a hypothesis.

## Limits

- **The weights had not finished moving.** After 8,000 frames A's weight was still falling (0.30 → 0.21 and dropping) and all three units were firing slightly above target. The test used a mid-course snapshot. Fully settled weights could differ; given the direction of travel there is no sign they would be better.
- **One development run was an outlier.** In 15 of 16 runs C ended between 0.39 and 0.50; in one it ended at 1.00. The median is unaffected.
- **One reader type.** A linear reader on three traces and three spike averages. A different reader might find order information this one misses.
- **One circuit, one geometry, deterministic, no noise.**
- **The exploratory target runs used four development pairs, not eight.**

## Verdict for the line

The self-tuning rule from 007 does what 007 said: it shares the field. 008 shows that sharing the field is not the same as remembering, and in this circuit works against it. Under the rule set beforehand, the route "homeostatic returns → better memory" is closed.

## Reproduce

```bat
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
python -m unittest discover -s tests -p test_008_self_tuned_order.py -v
python experiments\008_self_tuned_order\run.py --upstream ..\PerceptionLab
```

The full run is about eight minutes. `--quick` runs a small version in under a minute.

**GUI graphs** (copy `homeostatic_return_gate_node.py`, `fading_history_spike_node.py` and `population_order_readout_node.py` into PerceptionLab's `nodes` folder first):

- [008_AB_self_tuning_live.json](../../workflows/008_AB_self_tuning_live.json) — the development phase: three gates learning from the 005b weights.
- [008_AB_self_tuned_frozen.json](../../workflows/008_AB_self_tuned_frozen.json) · [BA](../../workflows/008_BA_self_tuned_frozen.json) — frozen self-tuned weights.
- [008_AB_fixed_gated.json](../../workflows/008_AB_fixed_gated.json) · [BA](../../workflows/008_BA_fixed_gated.json) — hand-set 005b weights through the same gates.

The order readout node in these graphs is untrained; the readers in the table are fitted offline by the runner. None of the 008 graphs has been run in the GUI.
