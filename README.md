# PerceptionLabAI — the experimental workshop

## Latest experiment — 009: grown branch structure keeps event order after total silence

[009 report](experiments/009_morphology_as_memory/README.md) · [Receipt](results/009_morphology_as_memory.json) · [GrowingReturnNode](nodes/growing_return_node.py). *Added by Claude Fable 5.2 from Sol's proposal, 15 November 2026.*

Each unit now has eight candidate return branches sharing a fixed budget. They grow toward recently busy sites and are pruned for good when weak, by a rule that sees only the unit's own pulse and the field at its branch tips. Bodies are grown on A-then-B or B-then-A histories, with all activity wiped between episodes. After a full wipe, one identical probe pulse reveals the history in **89 of 96 held-out bodies**; growth switched off gives 48/96 and scrambled branch positions 55/96. The rules were committed before the run.

**Two of three questions failed:** cue A does not recall B (one cue came out opposite to prediction), and pruning does not protect the memory from later opposite-order experience (64/96 against 57/96, p = 0.28). No task benefit is shown. GUI not run.

## 008: self-tuned returns hold order worse, not better

[008 report](experiments/008_self_tuned_order/README.md) · [Receipt](results/008_self_tuned_order.json) · [runner](experiments/008_self_tuned_order/run.py). *Added by Claude Fable 5.2, 15 November 2026.*

The deciding test for the memory line. The three-unit circuit of 005b was given 007's self-tuning returns, the weights were left to settle with no labels, and 005's AB/BA order test was run on **96 held-out runs**. Self-tuned weights scored **60/96**; the hand-set 005b weights scored **81/96** (paired test p = 0.0003). The rule fixed and committed before the run said this counts against self-tuning, so that route is closed.

**Also found:** with 96 runs, cutting the third unit's return (85/96) is not distinguishable from keeping it (81/96), so 005b's "third unit hurts" result from 16 runs is not supported. Limits: weights were still drifting when frozen, one linear reader, one circuit, no noise, GUI not run.

## 007: a return edge tunes itself from its own firing rate

[007 report](experiments/007_homeostatic_return/README.md) · [Receipt](results/007_homeostatic_return.json) · [HomeostaticReturnGateNode](nodes/homeostatic_return_gate_node.py) · [primary graph](workflows/007_homeostatic_a_return.json). *Added by Claude Fable 5.2, 15 November 2026.*

After 006's reward-guided edge failed twice, 007 removes the reward, the reader and the labels. A's return edge watches only how often A fires and moves its own weight toward a target rate. Starting from 1.00, where A silences B, the weight falls to **0.41**, B starts firing, and the two take turns at about 104 frames. A frozen gate at 1.00 leaves B silent. Five starting weights reach the same place.

**Limits kept visible:** with B's return disconnected the same rule lets A's loop die and it never restarts; the planned anti-homeostatic control from 0.30 did not discriminate; nothing here measures memory; the target rate is hand-chosen. The both-homeostatic graph has been observed in the GUI (A weight falling to 0.36, B starting to fire); the other four graphs are headless only. The fixed-weight sweep also shows that turn-taking continues at A weight 0.00, so A's return speeds the pattern up but is not needed for it.

## 006 / 006b: a plastic return is not yet useful learning

[006 original report](experiments/006_reward_selected_return/README.md) · [006b bounded follow-up](experiments/006b_bounded_selection/README.md) · [Full 006 receipt](results/006_reward_selected_return.json) · [006b receipt](results/006b_bounded_selection.json) · [PlasticReturnGateNode](nodes/plastic_return_gate_node.py).

After the fixed-graph 005 tests, we added one **genuinely mutable physical return gain** from C's fading-history pulse back to the same upstream WaveField. The gate learns through a scalar difference of two **externally supervised** reward measurements; it does not see the AB/BA label directly. The first rule changed the C return from 0.50 to **0.848**, but got only **6/16** new AB/BA labels right, against **14/16** with the frozen edge. A second, smaller/bounded multi-context rule changed it to **0.420** but scored **8/16** on a *different fresh* final split, compared with **10/16** frozen and **14/16** completely pruned.

**These are negative results for useful plasticity.** The physical weight can change, but the chosen updates do not preserve event order better. The original 006 and the separately labelled exploratory 006b remain available with raw receipts and controls. No GUI execution or independent neural learning is claimed.

---
## 005 results: order of falls

[**005 complete headless report**](experiments/005_order_of_falls/README.md) · [Original full receipt](results/005_order_of_falls.json) · [C-decay scan](results/005_C_recruitment.json) · [Three-active follow-up](experiments/005_order_of_falls/THREE_ACTIVE.md) · [Node manual](docs/NODE_MANUAL.md) · [Workflow manual](docs/WORKFLOW_MANUAL.md).

**Original 005:** AB versus BA is readable after the stimuli end. The recurrent system scored 15/16 held-out examples at frame 650 with a stated finite sensor resolution, but an unbounded-precision passive field was an even better decoder. At the finite resolution, passive decoding fell to 8/16. The original third unit **never fired**. The frozen frame-360 trained GUI readout scored 14/16 on held-out trials; it is a diagnostic, not learning inside the medium.

**Exploratory 005b:** C decay 0.93 activated all three. Yet at frame 650 the three-return system scored only **10/16**, while disconnecting C's return improved the score to **15/16** on fresh held-out pairs. More active connections did not automatically improve usable memory. All details and null results are preserved.

---
## Current experiment 005 · Order of falls

[**005 research dossier**](experiments/005_order_of_falls/README.md) · [AB graph](workflows/005_AB_three_histories.json) · [BA graph](workflows/005_BA_three_histories.json) · [Node Manual](docs/NODE_MANUAL.md) · [Workflow Manual](docs/WORKFLOW_MANUAL.md).

Two equal pulses arrive at two physical locations in reversed order (AB versus BA). Three heterogeneous fading-history units exchange activity through a **single original PerceptionLab WaveField**. A fourth node has no teaching signal and no output to the physical field; an offline linear probe is trained solely on training trials, then tested on held-out timing/amplitude perturbations. Passive-field and third-unit-return-disconnected controls are required. **This is a study of readable event-order history, not a claim of learned neural representations.**

---
**Start here:** [Node manual](docs/NODE_MANUAL.md) · [Workflow manual](docs/WORKFLOW_MANUAL.md) · [004 experiment](experiments/004_two_histories/README.md) · [004 measured receipt](results/004_two_histories_initial.json)

**004 completed headless investigation:** Two differently fading units in one shared WaveField switch between **suppression** (A feedback ≥0.50, B silent) and **mutual alternating regeneration** (A feedback 0.15–0.45). In a 1,800-frame run, A-return 0.30 gave repeated A/B alternation (15 spikes each), and disconnecting B's return killed both. This is a controlled dynamical phenomenon, not learned behaviour. **The 004 GUI still needs local verification.**

---
## Earlier experiment 003 — the first feedback loop

[Open saved graph](workflows/003_fading_feedback_wave.json) · [Fading History Spike node](nodes/fading_history_spike_node.py) · [research/results](experiments/003_fade_closed_loop/README.md).

**Local Windows update uses TWO repositories.** The wave-size fix is now directly in `anttiluode/PerceptionLab` **main**, and the 003/004 workshop experiments live in `anttiluode/PerceptionLabAI` **main**. Pull both:

```bat
cd /d D:\anttiluode\PerceptionLab
git pull origin main
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
copy /Y nodes\fading_history_spike_node.py ..\PerceptionLab\nodes\
```

**Restart PerceptionLab completely** to reload the Python node classes.
Open `D:\anttiluode\PerceptionLabAI\workflows\003_fading_feedback_wave.json` in PerceptionLab's Load dialog. With the fixed 96×96 field, the Wave Field graphic should show **predicted lag ~4.9 frames/gap**, not **13.2**. (13.2 means the old 256×256 arrays are still in use.) The reference headless loop emitted 14 spikes in 550 frames, but the user-observed GUI run before the fix stopped; verify the interactive behavior anew.

The [host-style graph replay test](tests/test_graph003_host_replay.py) now tracks `PerceptionLab/main`, not a temporary fix branch. **For new work in this shared workshop, edit `main` directly by default as requested by the maintainer; do not leave finished work stranded in a feature branch.** Other contributors may still use PRs when appropriate.

---

PerceptionLabAI is a collaborative **staging area** for small, falsifiable PerceptionLab experiments. The upstream library is [PerceptionLab](https://github.com/anttiluode/PerceptionLab); the historical inventory and audit live in [PerceptionLabNodes](https://github.com/anttiluode/PerceptionLabNodes).

## The working agreement

1. **Reuse before inventing.** Start with existing PerceptionLab node classes and saved workflows. Add a node only when an existing one cannot express the proposed intervention or readout.
2. **One question, one experiment.** Every numbered experiment has a hypothesis, working graph, baseline/control, test runner, numeric result, limitations, and provenance.
3. **No ghost wires.** Audit actual input/output ports, node initialization and data types. Verify that changing a control changes the measured output; never rely on a label or animation.
4. **Separate model, intervention and instrument.** An observer must not secretly change the medium it observes. Preselect metrics and report failed or null results.
5. **Respect timing.** PerceptionLab transfers previous-step outputs before advancing all nodes: ordinary wired edges introduce a tick. Document graph timing and sample alignment.
6. **Reproduce or do not promote.** Report the environment, dependency and exact upstream revision used. A passing unit test alone does not prove a scientific claim.
7. **Keep failure evidence.** Do not erase negative runs. If a result changes, add a correction rather than rewriting history.
8. **Contributors are welcome.** Humans and AI collaborators explain their model and tests. Antti's direct experiment updates go on `main` by default; outside contributors can use branches/PRs for review. Never overwrite another person's unreviewed work.
9. **Upstream is reviewed.** Once an experiment has a working node, saved `graph workflows/*.json` file and independent control, propose a PR to PerceptionLab. Do not copy experiment-only scaffolding or claim a proposal is merged.
10. **No hype, no false physics.** Distinguish implemented algorithms, measured results, biological analogies and open questions.

## Status

Experiment 001: **Causal-age reader** — compare simultaneous and transit-delayed correlation between two apertures of the existing WaveFieldNode, with an explicit no-delay control. See `experiments/001_causal_age/README.md`, `workflows/`, `nodes/`, and `tests/`.

## How to contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md). For each experiment: create a numbered folder; store a host-loadable workflow, new node source (if needed), runnable tests and observed measurements. Preserve upstream license and provenance.

## First cycle completed — 15 November 2026

- **Experiment 001:** [causal-age test](experiments/001_causal_age/README.md), [saved PerceptionLab graph](workflows/001_wave_transit_predictor.json), [new reusable reader](nodes/temporal_transit_predictor_node.py), [numerical receipt](results/001_causal_age_first_run.json).
- **CI:** [six tests passed](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43684369567), including matching every graph port against real upstream classes.
- **Observed:** expected delay 6.58 frames at 128x128, used 7; mean +11.89 dB delayed-prediction advantage in a single simulated run. D=0 control exactly 0 dB. No claim of substrate learning.
- **Upstream contribution:** [PerceptionLab PR #1](https://github.com/anttiluode/PerceptionLab/pull/1) — **merged**.

The next experiments should challenge the result with speed/distance changes, independent input patterns, and explicit failures, rather than assuming success generalizes.

## Experiment 002 — physical transit into resonator logic

[Wave-field / ResonatorSoma XOR timing experiment](experiments/002_wave_xor/README.md) · [saved 96×96 workflow](workflows/002_wavefield_resonator_xor.json) · [arrival gate node](nodes/wave_arrival_gate_node.py) · [first CI run](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43686062648).

The first real-wave sweep found peak overlap at a **−5-frame** offset, matching 4.94 frames of independently predicted extra travel, with no incorrect XOR outputs. This demonstrates timing sensitivity of a **pre-existing XOR gate**, not spontaneously learned logic. A farther-aperture control **passed**: doubling path difference moved the best coincidence from −5 to **−10 frames** (distance/speed prediction: 9.87 frames). The experiment retains links to both run receipts and limitations.
