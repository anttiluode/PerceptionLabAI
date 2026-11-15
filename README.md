# PerceptionLabAI — the experimental workshop

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
