# PerceptionLabAI — the experimental workshop

PerceptionLabAI is a collaborative **staging area** for small, falsifiable PerceptionLab experiments. The upstream library is [PerceptionLab](https://github.com/anttiluode/PerceptionLab); the historical inventory and audit live in [PerceptionLabNodes](https://github.com/anttiluode/PerceptionLabNodes).

## The working agreement

1. **Reuse before inventing.** Start with existing PerceptionLab node classes and saved workflows. Add a node only when an existing one cannot express the proposed intervention or readout.
2. **One question, one experiment.** Every numbered experiment has a hypothesis, working graph, baseline/control, test runner, numeric result, limitations, and provenance.
3. **No ghost wires.** Audit actual input/output ports, node initialization and data types. Verify that changing a control changes the measured output; never rely on a label or animation.
4. **Separate model, intervention and instrument.** An observer must not secretly change the medium it observes. Preselect metrics and report failed or null results.
5. **Respect timing.** PerceptionLab transfers previous-step outputs before advancing all nodes: ordinary wired edges introduce a tick. Document graph timing and sample alignment.
6. **Reproduce or do not promote.** Report the environment, dependency and exact upstream revision used. A passing unit test alone does not prove a scientific claim.
7. **Keep failure evidence.** Do not erase negative runs. If a result changes, add a correction rather than rewriting history.
8. **Contributors are welcome.** Humans and AI collaborators use separate branches/PRs, explain their model and tests, and never overwrite another contributor's work without review.
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
- **Upstream proposal:** [PerceptionLab PR #1](https://github.com/anttiluode/PerceptionLab/pull/1) — reusable node and workflow staged for review; **not merged** as of this note.

The next experiments should challenge the result with speed/distance changes, independent input patterns, and explicit failures, rather than assuming success generalizes.

## Experiment 002 — physical transit into resonator logic

[Wave-field / ResonatorSoma XOR timing experiment](experiments/002_wave_xor/README.md) · [saved 96×96 workflow](workflows/002_wavefield_resonator_xor.json) · [arrival gate node](nodes/wave_arrival_gate_node.py) · [first CI run](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43686062648).

The first real-wave sweep found peak overlap at a **−5-frame** offset, matching 4.94 frames of independently predicted extra travel, with no incorrect XOR outputs. This demonstrates timing sensitivity of a **pre-existing XOR gate**, not spontaneously learned logic. A farther-aperture control is underway and results will be retained.
