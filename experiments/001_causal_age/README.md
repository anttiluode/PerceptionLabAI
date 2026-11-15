# Experiment 001 — wave transit as a causal-age readout

**Hypothesis (preregistered):** a near wave-field aperture at t-D should
predict a farther aperture at t better than near[t] does, with D independently
estimated by distance / propagation speed. No changes to the upstream physics.

The new `TemporalTransitPredictorNode` learns two scalar regressions on
**previous frames only**. Each current far sample is held out. Outputs:
`prediction`, `innovation`, `mse_delayed`, `mse_simultaneous`,
`advantage_db` and `valid`. Advantage in decibels is
`10 log10(MSE_simultaneous / MSE_delayed)`: positive favors delayed information.

**Controls:** D=0 must give identically zero advantage; a deterministic
artificial delay must favor delayed prediction; a flat source must never
claim success; the upstream wave must actually transmit to both probes.
Same-time near[t] is a contemporaneous baseline, not a past-only forecaster.

**Saved graph:** `workflows/001_wave_transit_predictor.json`, to open with
PerceptionLab's Load Graph after copying our new file into `nodes/`.
Source → WaveField → MultiScope, with WaveField read_0/read_1 → our
reader → SignalDisplay. All wiring is separate from the field's physics.

At the graph's 256-cell, 0.50 × 4 substep settings,
aperture spacing is 26.33 px; predicted lag is 13.17 frames.
The reader uses 13 frames. This is a *prediction*, not a measured result.

**Reproduce (inside PerceptionLabAI directory):**
```bash
git clone https://github.com/anttiluode/PerceptionLab.git PerceptionLab
python -m pip install numpy opencv-python-headless
python -m unittest discover -s tests -v
python experiments/001_causal_age/run.py --upstream PerceptionLab
```
The runner invokes **real upstream wave and pulse classes** with lightweight
headless UI stubs and writes `results/001_causal_age.json`.
CI runs and uploads the same receipt. Inspect whether the result actually
favors D; negative or ambiguous results must be retained.

**Limits:** linear fit, amplitude attenuation, noisy oscillatory fronts,
integer-delay approximation, and old-host one-step output transport.
Even success is evidence of *time-of-flight information*, not learning,
cognition or biological memory.

## First measured receipt — 15 November 2026

GitHub Actions [run 43684177103](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43684177103) passed all five initial tests using upstream PerceptionLab main.

* 128 × 128 wave field; 740 steps; predicted spacing delay 6.5829 frames, configured D=7.
* 370 valid evaluated frames in the latter half (overlapping windows, **not** 370 independent experiments).
* Mean reported delayed advantage **+11.8858 dB** over those frames; final advantage **+4.7431 dB**.
* Final online MSE: delayed **0.00664636**, simultaneous **0.01981033**.
* No-delay control advantage **0.0 dB** exactly.

These are simulator-specific readout results, not evidence of learned material or an organism. This receipt predates the workflow-display name correction; the underlying wave and reader were unaffected. The next CI run checks all graph classes and ports.
