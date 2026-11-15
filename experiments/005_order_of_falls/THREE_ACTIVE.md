# 005b — Three active histories: improved complexity, worse order decoding

**Exploratory follow-up to [005](README.md); 15 November 2026.** C was silent at decay 0.975 in the preregistered run. We ran [a six-value C-decay scan](../../results/005_C_recruitment.json) at 0.70, 0.80, 0.86, 0.90, 0.93, and 0.975. At 0.70–0.86 C suppressed A and B, at 0.975 C was silent, and at **0.93 all three** emitted recurrent events. The scan, including failed configurations, is retained rather than replacing the first study.

## Construction

Three instances of the existing `FadingHistorySpikeNode` in **one original WaveField** (96×96):

- A decay **0.86**, source `read_1`, pulse return `write_0` weight 0.30.
- B decay **0.95**, source `read_3`, pulse return `write_2` weight 1.00.
- C decay **0.93**, source `read_5`, pulse return `write_4` weight 0.50.

C's arm and release thresholds, **0.06781459787754025** and **0.030139821278906784**, came from a pooled, no-feedback AB/BA calibration. The original A/B thresholds and all wave physics are unchanged. Each AB/BA trial uses the same two equal-amplitude and equal-duration pulses in opposite order.

## Fresh held-out study

[Source and runner](three_active.py) · [Complete receipt](../../results/005b_three_active_heldout.json) · [Passing CI](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43695493471).

The C=0.93 value was *selected after seeing a development trial*. We then locked it and evaluated on **eight new matched held-out AB/BA pairs**, with timing and amplitude settings that had not been used in the C scan. This remains an exploratory follow-up, not an independent preregistration.

| Frame 650, finite-resolution readout | Correct of 16 |
|---|---:|
| **All three pulse returns active** | **10/16 (62.5%)** |
| Same three nodes, **C feedback disconnected** | **15/16 (93.75%)** |
| **All returns disconnected (passive)** | **8/16 (50%)** |

Mean post-frame-160 recurrent spikes across held-out runs (all three connected): A **6.062**, B **5.625**, C **4.188**. No waveform clipping was recorded.

At frame 360, the three-active six-feature probe scored 11/16, trace-only 13/16 and spike-history-only 7/16. At frame 650, those scored 10/16, 10/16 and 9/16 respectively.

Removing C's return does **not** remove C's ability to emit a pulse in response to A and B. It removes its *influence on the shared field*. With its return disconnected, the other units retain a more easily decoded order state.

This is not proof that C "destroys memory" in general. The linear six-feature readout may be inappropriate for a more complex nonlinear code; the range of delays, initial conditions and noise is limited; the parameter was chosen post hoc. It **does** show that additional active feedback is not automatically an improvement in readable order information.

## Loadable GUI graphs

- [Three-active AB](../../workflows/005_ABC093_AB.json) and [BA](../../workflows/005_ABC093_BA.json)
- [C disconnected AB](../../workflows/005_ABC093_AB_no_C.json) and [BA](../../workflows/005_ABC093_BA_no_C.json)
- [Passive AB](../../workflows/005_ABC093_AB_passive.json) and [BA](../../workflows/005_ABC093_BA_passive.json)

All graphs use the **measured thresholds**, but their order readout weights remain **zero/untrained**. They are valid dynamic visualization and control graphs; a trained diagnostic readout from the different C=0.975 system has deliberately **not** been transplanted into them. Headless results are reproducible; interactive GUI results for 005b still require local confirmation.

## Scientific boundary

005b is **not** evidence of biological neurons learning, general neural binding, consciousness, or information-theoretic memory capacity. It is a test of how a fixed wave-feedback circuit transforms identical-energy temporal sequences.
