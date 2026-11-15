# Experiment 003 — Does a fading-history unit close a physical wave loop?

**Proposal inspired by the Geometric Neuron V26–V29 discussions (15 Nov 2026).**

> WaveField.read_1 → new FadingHistorySpikeNode → WaveField.write_0

An existing **single-shot** PulseSource also injects into write_0 once,
but `period=0` means there is **no external repeating clock**.

## What is genuinely new

The original WaveField implements a propagating, damped second-order
wave equation. Its `write_0..7` ports are real injection interfaces;
they are not newly implemented here.

The small *FadingHistorySpikeNode* accumulates recent absolute field
activity as a leaky trace:

`m[t+1] = decay*m[t] + (1-decay)*abs(read[t])`.

When m exceeds an **arming threshold**, it enters an armed state.
When m subsequently **fades below a lower threshold**, it emits one
one-tick output pulse, then disarms. No incoming activity, no arming,
no spontaneous spike. The pulse is then written into WaveField at a
different aperture (read_1 → write_0), and has to propagate to return.

This node is **not** a port of the original GeometricNeuron dynamics.
It is a deliberately simple hypothesis-testing component. It has a
minimum gap guard and fixed threshold hysteresis; it does not learn
or simulate ion channels.

## Hypotheses registered before measuring

**H1 (feedback dependence).** If feedback regenerates impulses, the
closed loop may show many more *late* spikes after one startup pulse
than the same field and sensor with the pulse return wire disconnected.
A result with no late events is a valid negative result.

**H2 (distance).** Moving the readout farther from the write aperture
should change arrival latency and may change the resulting spike timing.
But the fading threshold and decay also contribute to the period,
so pure wave distance is NOT predicted to set the rhythm alone.

**H3 (time constant).** Changing the fading rate at fixed geometry
should affect timing if the unit's history is dynamically relevant.

**H4 (damping).** Increasing WaveField damping can suppress recurrent
activity even with the wire connected.

**Controls:** disabled unit, no startup pulse, wire disconnected.
The no-bootstrap case must remain entirely silent. All thresholds are
calibrated on an independent single-pulse **open-loop** response for
each changed geometry, then frozen for its closed-loop run.

## Reproduce

```bash
git clone https://github.com/anttiluode/PerceptionLab PerceptionLab
python -m pip install numpy opencv-python-headless
python -m unittest discover -s tests -v
python experiments/003_fade_closed_loop/run.py --upstream PerceptionLab
```

The runner dynamically imports the **actual upstream WaveField and
PulseSource implementations**; the headless shim only replaces the GUI
node base interface, not the physical update rules. Each run gets a
fresh medium and oscillator state.

The workbench GUI graph is at
`workflows/003_fading_feedback_wave.json`. Copy the new node
`nodes/fading_history_spike_node.py` to PerceptionLab's `nodes/`
folder, then load the JSON graph. Its thresholds are fixed from the 96×96 open-loop calibration:
arm=0.72201012 and release=0.320893387 for read_1.
The GUI path has not yet been manually inspected.

## Important causal boundaries

A persistent cycle would not prove that the original Geometric Neuron
or biological neurons work by the same mechanism. A pulse contains
new energy because the node explicitly generates it; the field is not
a passive source of free energy. The startup source fires once.
Test a **disconnected return wire**, not only an external-source-off
control. Even a beautiful periodic waveform can be a threshold artifact
or a residual reflection, so report pulse times and late event counts.

**No result is claimed here until CI has run.**

## First actual CI measurement (15 November 2026)

[GitHub Actions first run](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43688727541): **17 automated tests passed**. A separate open-loop pulse calibration fixed the reference thresholds (trace peak 1.604466933; arm 0.72201012; release 0.320893387). The real upstream 96×96 wave was run for 550 frames.

| Configuration | Spikes total / last half | Late average interspike interval |
|---|---:|---:|
| Read_1, decay .90, speed .50 | 14 / 8 | 36 frames, CV 0 |
| Farther read_2 | 6 / 3 | 82.5 frames |
| Wave speed .35 | 12 / 7 | 43 frames |
| Damping .035 | 12 / 7 | 44 frames |
| Slower memory fade, decay .96 | 5 / 3 | 104 frames |
| **Return wire disconnected** | 1 / 0 | None |
| **No startup pulse** | 0 / 0 | None |
| **Unit disabled** | 0 / 0 | None |

This is a **constructed regenerative-feedback oscillator**, using a one-tick pulse generated after the trace crosses the release threshold. The pulse actively supplies energy to the field; damping and travel delay are not the only determinants of the cycle. The result does **not** demonstrate real action potential physiology, a learned network, or multimodal processing.

Follow-up pre-registered controls: place the read at write_0 (zero path), cut the feedback return halfway, reduce return amplitude, and raise damping. The full initial CI artifact records raw spike times and all outputs. 

## Stronger instrument control: WaveField amplitude clipping

The WaveField itself clips its field and velocity state to ±4. The first
reference run reached the ±4 field clamp for **100/550 frames**;
a single open-loop bootstrap also hit the clamp briefly. The
reported 36-frame rhythm is therefore **not demonstrated to be a
purely linear-wave phenomenon**.

The next preregistered comparison retains the same `pulse/boot=2`
ratio and geometry but scales both pulse magnitudes down by ≈8.3×:
bootstrap amplitude **0.12**, feedback pulse **0.24**, with thresholds
calibrated separately on the smaller, open-loop stimulus. Record
the number of frames in which `abs(field)` reaches 3.9998.
If the low-amplitude loop still oscillates while showing zero
saturated frames, the mechanism is not dependent on the WaveField
amplitude clamp. If it fails, keep the negative result.
