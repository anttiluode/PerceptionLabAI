# PerceptionLabAI Workflow Manual

This is the **workshop's operating catalogue** of runnable saved graphs.
Whenever a workflow changes, update this page, its experiment dossier and
tests. New graphs belong in this repository's `workflows/`; only verified
reusable graphs should be proposed upstream.

## Workflow index

| # | Saved graph(s) | New node | Question | Evidence |
|---|---|---|---|---|
| 001 | [Wave transit predictor](../workflows/001_wave_transit_predictor.json) | `TemporalTransitPredictorNode` | Does delayed near-field input predict the far aperture better than simultaneous input? | 6 tests passed, +11.89 dB headless rolling advantage; [dossier](../experiments/001_causal_age/README.md) |
| 002 | [Wave → XOR](../workflows/002_wavefield_resonator_xor.json) | `WaveArrivalGateNode` | Does physical travel time shift the coincident XOR window? | −5 and −10 frame compensation on doubled path; [dossier](../experiments/002_wave_xor/README.md) |
| 003 | [Self-regenerating fade loop](../workflows/003_fading_feedback_wave.json) | `FadingHistorySpikeNode` | Does a pulse fired at the end of a fading history regenerate activity through the wave? | GUI verified after size repair, recurrence requires feedback; [dossier](../experiments/003_fade_closed_loop/README.md) |
| 004 | [Two fades, one field](../workflows/004_two_fades_one_field.json) | Reuses `FadingHistorySpikeNode` twice | Can two different histories influence each other's timing? | **Two tested regimes: suppression at A=0.50+, alternating mutual regeneration at A=0.15–0.45**: [004](../experiments/004_two_histories/README.md) |
| 007 | [Homeostatic A return](../workflows/007_homeostatic_a_return.json) | `HomeostaticReturnGateNode` | Can a return edge reach the turn-taking regime using only its own unit's firing rate? | **Yes from five starting weights: 1.00 → 0.41, B rescued, alternation at ~104 frames; an isolated loop dies**: [007](../experiments/007_homeostatic_return/README.md) |
| 008 | [Self-tuning, three units](../workflows/008_AB_self_tuning_live.json) | Reuses `HomeostaticReturnGateNode` three times | Does a self-tuned network hold AB/BA order better than hand-set weights? | **No: 60/96 against 81/96 held-out, p = 0.0003**: [008](../experiments/008_self_tuned_order/README.md) |

004 controls available as GUI-loadable graphs:
[ A alone ](../workflows/004_a_only.json),
[ B alone ](../workflows/004_b_only.json),
[ no return ](../workflows/004_no_return.json),
[ no seed ](../workflows/004_no_seed.json),
[ swapped decay ](../workflows/004_swap_decay.json),
[ swapped sites ](../workflows/004_swap_sites.json).

## Local installation on Windows

The two repositories are different. Pull both; put only the workshop
*custom* node sources into the host's `nodes/` directory:

```bat
cd /d D:\anttiluode\PerceptionLab
git pull origin main
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
copy /Y nodes\fading_history_spike_node.py ..\PerceptionLab\nodes\
```

**Restart PerceptionLab**, then open one JSON graph from
`D:\anttiluode\PerceptionLabAI\workflows`. Do **not** copy the JSON
into `graph workflows/` unless you want to promote it upstream.

To run tests in the workshop:
```bat
cd /d D:\anttiluode\PerceptionLabAI
python -m pip install numpy opencv-python-headless
python experiments\004_two_histories\run.py --upstream ..\PerceptionLab
```

The Wave Field node must visibly report a lag around **4.9 frames/gap**
for these 96×96 graphs (speed=0.5, four substeps). If it says 13.2,
the host still holds the old 256×256 arrays. Restart with a current
upstream checkout.

## Interpreting workflows

- A graph is not evidence until its **real port types and host timing**
  have been checked, and ideally the GUI has been tried.
- If changing rate/geometry, measure the input scale before changing
  the arming threshold. Distinguish frozen-threshold swaps from
  separately calibrated swaps.
- A visible rhythm proves a **closed feedback loop**, not autonomous
  learning, coupled cognition, biological identity, or transfer to audio.
- All `pulse` output represents freshly injected energy. WaveField is
  damped; it cannot maintain output without drive.
- Negative controls and raw spike times belong in the numbered
  experiment dossier/receipts.

[Node Manual](NODE_MANUAL.md) ·
[Contributing](../CONTRIBUTING.md)

## 004 - field-sharing and suppression controls

The new [two-fade shared field workflow](../workflows/004_two_fades_one_field.json) contains **one** `WaveFieldNode`, **two instances of the same** `FadingHistorySpikeNode`, and one single-shot source. A receives read_1 and writes at write_0; B receives read_3 and writes at write_2. Both node configurations now contain individually measured calibration thresholds.

The [first 650-frame receipt](../results/004_two_histories_initial.json) reports A=21 spikes and B=0 when both are connected, while B alone produced four spikes. Rate-swapping reversed which node was active; position-swapping did not in the separately calibrated runs. This is **not** a demonstrated two-unit lock or alternation. We are testing B's state and the effect of cutting A's feedback.

Open the [004 experiment dossier](../experiments/004_two_histories/README.md) before using a variant. The GUI hasn't been verified for 004.

## 004's decisive GUI comparison

[Competition (A return 1.0)](../workflows/004_two_fades_one_field.json) versus [alternation (A return 0.25)](../workflows/004_weak_a_interleaving.json) versus [weak A, B disconnected](../workflows/004_weak_a_without_b_return.json). All three use the same 96×96 wave physics and independently calibrated thresholds, so only edge strength/connectivity differs. A and B are **two instances of the same node class**, not two different handcrafted algorithms.

The 650-step [gain sweep](../results/004_two_histories_gain_sweep.json) showed alternating A/B event sequences at A-return weights 0.15–0.45 and suppression of B from 0.50 upward. The [1,800-step check](../results/004_two_histories_long.json) preserved both regimes, including a successful site-swap alternation and a reversed decay-rate winner. Both returns are necessary for the weak-A cycle: the B-return-off control dies. Headless verification used the original upstream WaveField; 004 GUI playback is still a separate check.

## 005 — Does the *order of past stimuli* survive in future activity?

[005 main AB graph](../workflows/005_AB_three_histories.json) · [005 main BA graph](../workflows/005_BA_three_histories.json) · [005 dossier](../experiments/005_order_of_falls/README.md).

Seven GUI-loadable graphs, all in `workflows/`:

| Variant | AB | BA | What it changes |
|---|---|---|---|
| Three recurrent fading units | [AB](../workflows/005_AB_three_histories.json) | [BA](../workflows/005_BA_three_histories.json) | Exactly one A pulse and one B pulse; order swapped |
| All pulse returns unplugged | [AB](../workflows/005_AB_no_return.json) | [BA](../workflows/005_BA_no_return.json) | Passive WaveField order-retention control |
| Slow C return unplugged | [AB](../workflows/005_AB_slow_disconnected.json) | [BA](../workflows/005_BA_slow_disconnected.json) | Does the third active unit matter? |
| No source pulse | [Silent](../workflows/005_no_stimulus.json) | — | Non-spontaneous-activity control |

**Crucial distinction:** AB/BA are not different graphs internally except the two source warmups, which are swapped. Per paired trial they contain identical source amplitudes, sites, durations, gap and energy. The runner perturbs timing and amplitudes identically within each AB/BA pair, freezes thresholds from a pooled open-loop calibration, trains an external linear readout on 8 matched pairs, and tests on **8 unseen pairs**. Snapshots: 160, 240, 360, 520 and 650 frames. The passive no-return control must be compared to any apparent order retention. No source labels enter the readout.

The fourth `PopulationOrderReadoutNode` initially has **zero weights**; a GUI display is not a trained classification until a validated model is installed. Calibrated thresholds and any justified frozen decoder coefficients should be copied to both AB/BA GUI graphs from the measured run. The PerceptionLab GUI has not yet been verified for 005.

To run: `python experiments/005_order_of_falls/run.py --upstream PerceptionLab` from PerceptionLabAI, using the sibling host checkout if needed. Copy `nodes/population_order_readout_node.py` (and `nodes/fading_history_spike_node.py`) into the host `nodes/` folder and restart. [Node manual](NODE_MANUAL.md).


## 005 current measured workflows and operating procedure

**Original calibrated study (C=.975, silent):**

- [AB fitted readout](../workflows/005_AB_three_histories.json) and [BA fitted readout](../workflows/005_BA_three_histories.json) carry a frozen linear probe trained for **frame 360** (14/16 held-out correct). Only warmup ordering differs between them.
- [Passive AB](../workflows/005_AB_no_return.json), [passive BA](../workflows/005_BA_no_return.json), [C-return-off AB](../workflows/005_AB_slow_disconnected.json), [C-return-off BA](../workflows/005_BA_slow_disconnected.json), and [silent source](../workflows/005_no_stimulus.json) are controls. The passive and silent observer is untrained.

**Exploratory three-active follow-up (C=.93):**

- [Three-active AB](../workflows/005_ABC093_AB.json), [three-active BA](../workflows/005_ABC093_BA.json)
- [C return disconnected AB](../workflows/005_ABC093_AB_no_C.json), [BA](../workflows/005_ABC093_BA_no_C.json)
- [Passive AB](../workflows/005_ABC093_AB_passive.json), [BA](../workflows/005_ABC093_BA_passive.json)

All six C=.93 graphs have valid pooled open-loop thresholds, but **the observer is deliberately untrained**. Use the signal plots and node counters to see C actually participating; do not transplant the original frozen C=.975 classifier. This follow-up scored only **10/16** at frame 650 with all feedback connected, but **15/16** when C's return was disconnected. The [six-rate exploratory scan](../results/005_C_recruitment.json) and [fresh held-out follow-up](../experiments/005_order_of_falls/THREE_ACTIVE.md) preserve the negative result.

For local Windows use, pull `PerceptionLabAI/main`, copy **both** `nodes/fading_history_spike_node.py` and `nodes/population_order_readout_node.py` to the upstream PerceptionLab `nodes/` folder, fully restart the host, then open any `005_*.json` from this workshop. The actual wave field must have real 96×96 state arrays. The GUI's file-loader path and the automatic CI tests are distinct; GUI playback of 005 still needs local verification.

**Meaning of the result:** the readout is a small externally trained classifier over a deterministic system of fixed weights. Order information can survive as recurrent dynamics after the passive wave becomes too small to read at the chosen resolution; three feedback units are not automatically better than two. This is not neural learning or evidence of biological memory capacity.

## 006 / 006b — Reward-guided retention of C's return pathway (negative results)

[AB plastic graph](../workflows/006_AB_plastic_return.json) · [BA plastic graph](../workflows/006_BA_plastic_return.json) · [AB permanently pruned control](../workflows/006_AB_pruned_return.json) · [BA permanently pruned control](../workflows/006_BA_pruned_return.json).

The two pulses are again equal in amplitude and width and occupy the same two time slots; only the AB vs BA order differs. A and B are fixed, C decays at 0.93, and its return to WaveField write_4 passes through a real `PlasticReturnGateNode`. **All** comparisons use this same gate and its extra one-frame transfer delay, so disconnecting C means reducing its stored gain to zero rather than removing the node.

**Original 006:** eight reader-fit training pairs, eight paired reward experiences, eight different held-out AB/BA pairs. The reward is externally supervised classification utility, not a signal originating from the physical network. The learning rule drove weight from 0.5 to 1.0 immediately and finished at 0.847595, giving **6/16** held-out versus **14/16** for fixed 0.5 or pruned 0.0. [Full report](../experiments/006_reward_selected_return/README.md) · [Receipt](../results/006_reward_selected_return.json) · [Passing CI](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43697926136).

**Exploratory 006b:** a smaller learning rate and maximum update 0.05, averaged over two contexts per step. On an entirely new final split, the learned w=0.419569 gave **8/16**, fixed 0.5 gave **10/16**, and completely pruned 0 gave **14/16**. The more conservative rule still failed to generalize usefully. [006b report](../experiments/006b_bounded_selection/README.md) · [Receipt](../results/006b_bounded_selection.json) · [Passing CI](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43698479884).

**Manual use:** copy `plastic_return_gate_node.py`, `population_order_readout_node.py`, and `fading_history_spike_node.py` from workshop `nodes/` into upstream PerceptionLab `nodes/`, restart, and load the JSON from workshop `workflows/`. The GUI graph has no reward-producing teacher wired in, so the saved version is an observable but **not self-training** demonstration. Both reported results come from tested headless replays of the real upstream wave and node classes, not from an interactive GUI session.

## 007 — Homeostatic return: a label-free rule finds the turn-taking regime

*Added by Claude Fable 5.2, 15 November 2026.* [Report](../experiments/007_homeostatic_return/README.md) · [Receipt](../results/007_homeostatic_return.json).

All five graphs are the measured 004 system (same field, source, units and thresholds) with A's return routed through a `HomeostaticReturnGateNode`. Every comparison uses the same gate and its one-frame delay.

- [Primary: homeostatic A return](../workflows/007_homeostatic_a_return.json) — weight starts at 1.00, target 0.010 pulses/frame, learning rate 0.02, rate window 200. Headless: weight reaches 0.41, B fires from about frame 1,500, strict alternation at about 104 frames.
- [Frozen gate at 1.00](../workflows/007_frozen_gate_full.json) — learning off. A alone at 29 frames, B silent.
- [Homeostatic A, B return unplugged](../workflows/007_homeostatic_a_no_b_return.json) — the loop dies near frame 1,500 and does not restart.
- [Both returns homeostatic](../workflows/007_both_homeostatic.json) — same outcome as the primary; B's weight stays at 1.00.
- [Anti-homeostatic control from 0.30](../workflows/007_anti_homeostatic_a.json) — sign flipped. **Uninformative as designed:** the weight drifts to 0.04 and turn-taking continues, because every weight from 0.00 to 0.45 takes turns.

Runner-only variants (fixed-weight sweep, other starting weights, targets, learning rates and rate windows, plus labelled post-hoc checks) are in the receipt.

**Manual use:** copy `homeostatic_return_gate_node.py` and `fading_history_spike_node.py` from workshop `nodes/` into upstream PerceptionLab `nodes/`, restart, load a `007_*.json`. The extra plotter shows A's weight and A's rate over target; that plotter draws its "Red" input in blue. **GUI observation, 15 November 2026 (Antti, screenshots):** the [both-homeostatic graph](../workflows/007_both_homeostatic.json) was run interactively in PerceptionLab. Early: A weight 0.61, A rate 3.65 times target, B silent (0 pulses), field energy 0.0040. Later: A weight 0.36, A rate 0.87 times target, B at 11 pulses, field energy 0.0001, with A and B pulses visibly alternating in the shared-wave scope. This matches the headless run, where the weight bottoms at 0.358 before rising toward 0.41. The other four 007 graphs have not been run in the GUI.

## 008 — Self-tuned returns and order memory (negative result)

*Added by Claude Fable 5.2, 15 November 2026.* [Report](../experiments/008_self_tuned_order/README.md) · [Receipt](../results/008_self_tuned_order.json).

All five graphs are the 005b three-active circuit with each of the three returns routed through a `HomeostaticReturnGateNode` (same one-frame delay everywhere) and an extra plotter showing the three return weights.

- [Self-tuning live, AB](../workflows/008_AB_self_tuning_live.json) — gates learning from the 005b weights (0.30, 1.00, 0.50). This is the label-free development phase.
- [Self-tuned frozen, AB](../workflows/008_AB_self_tuned_frozen.json) · [BA](../workflows/008_BA_self_tuned_frozen.json) — weights 0.22, 0.90, 0.47, learning off.
- [Hand-set through gates, AB](../workflows/008_AB_fixed_gated.json) · [BA](../workflows/008_BA_fixed_gated.json) — weights 0.30, 1.00, 0.50, learning off.

**Measured headless, 96 held-out runs at frame 650:** hand-set 81, C's return cut 85, self-tuned frozen 60, self-tuned live 75, passive 48, uniform control 46, rotated control 65. Self-tuned is worse than hand-set (paired p = 0.0003). Cutting C's return is not distinguishable from keeping it (p = 0.48), which does not support the 16-run result of 005b.

The order readout node in these graphs is untrained; readers are fitted offline. Copy the three workshop nodes into PerceptionLab `nodes/`, restart and load. **No 008 graph has been run in the GUI.**
