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
**Graph thresholds are demonstrative, not headless-calibrated values**:
readjust thresholds for the actual run and do not claim that the GUI
configuration was scientifically validated by the headless receipt.

**Caveats:** finite pulse widths and multiple wave lobes can make
coincidence non-monotone. A hard threshold changes the effective duration
of an event. The 2-lane construction isolates travel distance rather than
claiming collision-based computation inside one physical field.
