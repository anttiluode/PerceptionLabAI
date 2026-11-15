# Experiment 002 — Wave-field travel time meets a resonator XOR

**Question:** Does changing the travel distance of one of two independently
propagating field signals shift the stimulus offset at which their binary
arrival *gate traces* coincide, changing the XOR output?

**This is not a newly emergent XOR.** `ResonatorSomaNode` implements XOR
by a predefined phase/amplitude band. The physical field supplies delayed,
attenuated and distorted analog inputs; `WaveArrivalGateNode` makes the
analog-to-bit conversion explicit. The scientific variable is the
*arrival-time compensation* and XOR activity during the event.

## Reused existing components

Two original `PulseSourceNode` instances feed independent unmodified
`WaveFieldNode` lanes. Lane A reads `read_0`, while lane B reads the
farther `read_1`. Each feeds one threshold adapter and an existing
`ResonatorSomaNode` in XOR mode. An existing `SignalPlotterNode`
shows XOR (red), arrival A (green), and arrival B (blue).
There are **no direct pulse-to-soma wires**.

## Preregistered predicted direction

For 96×96 headless fields, x difference between aperture 0 and 1 is
(0.92−0.20)×96/7≈9.87 pixels. The existing wave speed is
0.5 pixels/substep × 4 substeps/frame = 2 pixels/frame.
So B's pulse should be injected approximately **5 frames earlier** to
compensate for its longer travel.

Predictions (not measured at the time of setup):
1. Single pulse calibration gives nonzero signal at both taps and fixed
   thresholds based on 30% of each lane's calibration peak.
2. Temporal compensation should yield *greater binary overlap* than zero
   input offset and large positive/negative offsets, **if** the wave
   envelopes remain comparable.
3. XOR is exactly 1 when the two registered bits disagree and zero when
   they agree, regardless of transit delay.
4. A lane with no pulse should not hallucinate events.

The receipt records both raw gate overlap and XOR active frames, to avoid
mistaking the wired XOR truth table for a new computational discovery.
A negative or ambiguous outcome is retained.

## Run

```bash
# In the PerceptionLabAI repository root, with upstream cloned below:
git clone https://github.com/anttiluode/PerceptionLab PerceptionLab
python -m pip install numpy opencv-python-headless
python -m unittest discover -s tests -v
python experiments/002_wave_xor/run.py --upstream PerceptionLab
```

The saved `workflows/002_wavefield_resonator_xor.json` can be loaded in
the graphical PerceptionLab host after copying the small adapter from
`nodes/wave_arrival_gate_node.py` into upstream's node folder.
**Graph thresholds now match the 96×96 headless calibration**:
these are explicit constants, not automatically calibrated by the GUI.
The saved graph's GUI execution has not been separately verified.

**Caveats:** finite pulse widths and multiple wave lobes can make
coincidence non-monotone. A hard threshold changes the effective duration
of an event. The 2-lane construction isolates travel distance rather than
claiming collision-based computation inside one physical field.

## First measured result (15 November 2026)

[Experiment 002 CI run](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43686062648) passed 10/10 checks, including the real upstream wave classes and the existing XOR truth table.

On a **96×96** field at speed **0.5/substep × 4**, the geometrically predicted B-minus-A transit difference was **4.9371 frames**. The frozen calibration thresholds were **0.91958857** on near aperture 0 and **0.65914607** on farther aperture 1 (30% of each single-pulse peak).

- **Offset −5:** 15/15 active frames coincident, **zero XOR-active frames**.
- **Offset 0:** 10/20 frames coincident (50%), **10 XOR-active frames**.
- **Either source disabled:** 15 XOR-active frames from the other source.
- **Both disabled:** no events. XOR truth table mismatches: **0**.

The ±16-frame offset sweep was recorded in CI. This first run agrees with a geometric transit prediction, but one geometry does not establish generality.

The saved GUI graph has now been aligned to the **96×96 calibrated case** (thresholds and −5-frame warmup offset), rather than the initially exploratory 128×128/default-threshold configuration.

## Independent follow-up hypothesis

Move lane B from `read_1` to `read_2`, which doubles the extra distance. With wave speed unchanged, nominal compensation becomes **approximately −10 frames** instead of −5. This is a different geometry with new one-pulse calibration; it tests whether the coincidence minimum follows *distance* rather than merely the original scheduling choice.

The same runner supports `--tap-b 2` and `--out results/002_wave_xor_farther.json`.
