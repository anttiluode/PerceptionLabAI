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
| 004 | [Two fades, one field](../workflows/004_two_fades_one_field.json) | Reuses `FadingHistorySpikeNode` twice | Can two different histories influence each other's timing? | **First result: A suppresses B; 004 follow-up tests ongoing**: [004](../experiments/004_two_histories/README.md) |

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
