# 007 — Can a return edge find the turn-taking regime from its own firing rate?

15 November 2026. Built and run by Claude Fable 5.2 at Antti's request, as the label-free follow-up to [006 / 006b](../006_reward_selected_return/README.md).

**Answer: yes, in this two-unit system, with one clear limit.** A return edge that only watches how often its own unit fires lowers itself from 1.00 to about 0.41, the suppressed slow unit starts firing, and the two take turns. No label, no reader and no reward are involved. The same rule kills a loop that has no partner.

[Full receipt](../../results/007_homeostatic_return.json) · [runner](run.py) · [node](../../nodes/homeostatic_return_gate_node.py) · [tests](../../tests/test_007_homeostatic_return.py) · [graph builder](make_workflows.py)

## Why this experiment

006 gave a return edge a reward computed by an outside reader that knew the AB/BA labels. It failed twice. The reward landscape is a staircase (a unit fires or it does not), and the reader had been fitted with that return switched off.

[004](../004_two_histories/README.md) had already measured something a local rule could aim for. With fast unit A and slow unit B on one field, A's return weight decides the regime: at 0.50 and above A fires alone and B is silenced; at 0.45 and below they take turns.

So the question is narrow: **can A's return edge get from 1.00 into the turn-taking range using only A's own firing rate?**

## The rule

`HomeostaticReturnGateNode` sits between a unit's pulse and the field's write port.

```math
r_{t+1} = r_t + \frac{s_t - r_t}{\tau}
```

```math
w_{t+1} = \operatorname{clip}_{[0,1]}\bigl(w_t + \eta\,(r^\ast - r_{t+1})\bigr)
```

Here $`s_t`$ is 1 on a frame where the unit fired and 0 otherwise, $`r`$ is the running firing rate, $`r^\ast`$ the target rate and $`w`$ the return weight. Firing more than the target lowers the weight; firing less raises it. The node has one input, the unit's own pulse.

Homeostatic regulation of firing rate is an old idea in neuroscience (synaptic scaling, intrinsic plasticity). Nothing about the rule is new. The question is only whether it works on this system.

## Setup

Everything except the gate is the measured 004 system: the upstream 96×96 `WaveFieldNode`, one single-shot `PulseSourceNode`, unit A (decay 0.86, `read_1` → `write_0`) and unit B (decay 0.95, `read_3` → `write_2`), with the 004 open-loop thresholds. A test checks that those four nodes are configured identically to the 004 graph.

A's return now passes through the gate. This adds one frame of delay, so every comparison, including fixed weights, goes through the same gate with learning off.

**Primary settings, fixed before the first run:** target rate 0.010 pulses per frame (one per 100 frames), learning rate 0.02, rate window 200 frames, starting weight 1.00, 6,000 frames.

**Planned before the first run:** frozen gate at 1.00; anti-homeostatic rule (sign flipped) from 0.30; A homeostatic with B's return disconnected; both returns homeostatic; fixed-weight sweep through the gate; four other starting weights; seven other targets; three other learning rates; two other rate windows.

**Added after seeing the first results (post hoc):** fixed weights 0.00 and 0.05; the anti rule from 0.45 and 1.00; two slow cases re-run for 12,000 frames.

## Results

Spike counts are per quarter of the run (1,500 frames each). Every case recorded zero clipped frames.

### Primary result and controls

| Case | A per quarter | B per quarter | Final weight | Last quarter |
|---|---|---|---:|---|
| **Homeostatic A, from 1.00** | 49, 13, 15, 14 | 1, 14, 14, 14 | **0.408** | both fire, strict alternation, 104 frames |
| Frozen gate at 1.00 | 50, 51, 51, 51 | 0, 0, 0, 0 | 1.000 | A alone, 29 frames |
| Anti rule from 1.00 (post hoc) | 50, 51, 51, 51 | 0, 0, 0, 0 | 1.000 | A alone |
| Both returns homeostatic | 49, 14, 14, 14 | 1, 14, 14, 14 | A 0.409, B 0.999 | strict alternation, 105 frames |
| **Homeostatic A, B's return disconnected** | 48, 0, 0, 0 | 1, 0, 0, 0 | 1.000 | **silent** |

The weight falls steadily, reaches 0.49 near frame 1,300, and B's sustained firing begins in the second quarter of the run. It bottoms at 0.358 around frame 2,100 and creeps up to 0.408 by frame 6,000, still rising very slowly.

### Fixed weights through the same gate

| A weight | A per quarter | B per quarter | Last quarter |
|---:|---|---|---|
| 0.00 (post hoc) | 10, 10, 10, 9 | 9, 10, 10, 10 | alternation, 154 frames |
| 0.05 (post hoc) | 11, 10, 10, 10 | 10, 10, 10, 10 | alternation, 147 frames |
| 0.15 | 12, 12, 12, 12 | 11, 12, 12, 12 | alternation, 125 frames |
| 0.25 | 13, 12, 13, 12 | 12, 12, 13, 12 | alternation, 120 frames |
| 0.30 | 13, 13, 12, 13 | 12, 13, 13, 12 | alternation, 118 frames |
| 0.45 | 15, 16, 15, 16 | 15, 15, 16, 15 | alternation, 97 frames |
| 0.50 | 59, 60, 60, 60 | 0, 0, 0, 0 | A alone, 25 frames |
| 0.75 | 52, 54, 54, 53 | 0, 0, 0, 0 | A alone, 28 frames |

This reproduces 004 through the gate: the switch lies between 0.45 and 0.50. It also corrects a reading of 004. **Turn-taking continues at weight 0.00.** B's loop sustains itself (period 154) and A fires in answer without writing anything back. A's return is not needed for the pattern; it only speeds it up, from 154 frames to 97. What 004 showed is that A cannot sustain itself at weak return without B. The dependence is one-way.

### Does the end state depend on the starting weight?

| Start | Final weight | Last quarter |
|---:|---:|---|
| 1.00 | 0.408 | alternation, 104 frames |
| 0.75 | 0.410 | alternation, 105 frames |
| 0.50 | 0.416 | alternation, 100 frames |
| 0.30 | 0.417 | alternation, 103 frames |
| 0.05 | 0.303 at 6,000 frames, still rising | alternation, 119 frames |
| 0.05, 12,000 frames (post hoc) | 0.410 | alternation, 106 frames |

All five starting points arrive at about 0.41.

### Does it depend on the target?

| Target (pulses/frame) | Final weight (last-quarter range) | A, B in last quarter | Pattern |
|---:|---|---|---|
| 0.004 | 0.00 (0.00–0.06) | 11, 10 | alternation, 149 frames |
| 0.006 | 0.12 (0.12–0.18), still falling | 12, 12 | alternation, 124 frames |
| 0.008 | 0.28 (0.28–0.30) | 13, 12 | alternation, 118 frames |
| **0.010** | **0.41 (0.39–0.41)** | 14, 14 | alternation, 104 frames |
| 0.0125 | 0.49 (0.49–0.50) | 19, 13 | mixed |
| 0.016 | 0.48 (0.42–0.51) | 25, 12 | mixed |
| 0.020 | 0.50 (0.44–0.54) | 33, 9 | mixed |
| 0.030 | 0.53 (0.46–0.58) | 47, 4 | mixed, B rare |

Two regimes of the rule itself:

- **Target at or below what turn-taking can deliver** (about one pulse per 97 frames): the weight settles inside the turn-taking range and the target sets the tempo.
- **Target above that:** strict turn-taking cannot supply the rate. The weight does not settle. It swings back and forth across the switch point near 0.45–0.50, A meets its target on average, and B fires in the gaps. A's last-quarter rate matches the target in each row (for example 25 pulses in 1,500 frames against a target of 0.016).

The second regime gives firing ratios that no fixed weight in the tested sweep produced. Fixed weights gave either even turn-taking or A alone. The sweep is coarse between 0.45 and 0.50, so a fixed weight in that gap might also give a mixed pattern; this was not tested.

### Learning rate and rate window

| Setting | Final weight | Last quarter |
|---|---:|---|
| Learning rate 0.005 | 0.433, still falling | alternation from the last quarter only |
| Learning rate 0.08 | 0.417 | alternation, 100 frames |
| Learning rate 0.32 | 0.410 | alternation, 101 frames |
| Rate window 50 | 0.419 | alternation, 99 frames |
| Rate window 800 | 0.189 at 6,000 frames, still moving | alternation, 124 frames |
| Rate window 800, 12,000 frames (post hoc) | 0.376, still rising | alternation, 114 frames |

A 64-fold range of learning rate reaches the same place. A long rate window overshoots downward and recovers slowly.

## What failed or was uninformative

- **The planned anti-homeostatic control did not discriminate.** Started at 0.30 it drifted down to 0.04 and the units kept taking turns, because the whole range from 0.00 to 0.45 takes turns. Started at 0.45 (post hoc) it also drifted down, to 0.33. Only the start at 1.00 is informative: there the anti rule stays at 1.00 and B stays silent, like the frozen gate.
- **An isolated loop dies under this rule.** With B's return disconnected, A's weight falls as intended, the loop stops near weight 0.40 around frame 1,500, and nothing restarts it. The weight then climbs back to 1.00 with nothing to pass. The rule can only lower a unit safely when something else keeps the field alive. A unit that cannot fire from silence cannot recover.
- **"Both homeostatic" tested nothing about B.** B's rate sits just under the target, so its weight stays pinned at 1.00.

## What this does and does not show

It shows that the regime 004 found by hand can be reached by a rule that uses only a unit's own firing rate, from any tested starting weight, across a wide range of learning rates, with zero clipping.

It does not show:

- **Memory or usefulness.** Nothing here measures whether the resulting rhythm carries information. 005's order test was not run on the self-tuned system.
- **Generality.** Two units, one geometry, one deterministic run per condition, no noise.
- **A free lunch on the target.** The target rate was chosen by hand. A target of 0.010 happens to lie just inside what turn-taking can deliver; the table shows what other choices do.
- **Three units.** 005b found that a third active unit made order harder to read. Whether three homeostatic returns settle into something better is the obvious next test and was not done.
- **Growth.** One number per edge changes. No edge appears or disappears.

## Reproduce

```bat
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
python -m pip install numpy opencv-python-headless
python -m unittest discover -s tests -p test_007_homeostatic_return.py -v
python experiments\007_homeostatic_return\run.py --upstream ..\PerceptionLab
```

The full run is 34 simulations and takes about six minutes.

**GUI:** copy `nodes\homeostatic_return_gate_node.py` and `nodes\fading_history_spike_node.py` into PerceptionLab's `nodes` folder, restart, and load:

- [007_homeostatic_a_return.json](../../workflows/007_homeostatic_a_return.json) — the primary graph. A's weight should fall from 1.00 and B should start firing after roughly frame 1,500.
- [007_frozen_gate_full.json](../../workflows/007_frozen_gate_full.json) — same graph, learning off. B stays silent.
- [007_homeostatic_a_no_b_return.json](../../workflows/007_homeostatic_a_no_b_return.json) — B's return unplugged. Activity dies near frame 1,500.
- [007_both_homeostatic.json](../../workflows/007_both_homeostatic.json) and [007_anti_homeostatic_a.json](../../workflows/007_anti_homeostatic_a.json).

The plotter on each graph shows A's weight (drawn blue, because that plotter swaps red and blue) and A's rate divided by its target (green). **None of the 007 graphs has been run in the GUI.** All numbers are headless replays of the real upstream wave and unit classes in host step order.
