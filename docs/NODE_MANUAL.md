# PerceptionLabAI Node Manual

This is the **workshop's living inventory** of new and reused nodes. Keep it
current whenever an experiment adds or changes a node. A node is promoted to
PerceptionLab via review only when it passes controls; promotion is **not**
automatic. All nodes inherit upstream `BaseNode` and are loaded by class
name from Python files under `nodes/`. The host constructs each with **no
arguments**, then calls `set_config_options(config)`. Signals are scalar
floats; edges transfer *previous-frame* output with an optional weight.

## Reusable workshop nodes

| Class / file | Category | Inputs | Outputs | Current use | Upstream |
|---|---|---|---|---|---|
| [TemporalTransitPredictorNode](../nodes/temporal_transit_predictor_node.py) | Analysis | `near`, `far` (signal) | `prediction`, `innovation`, `mse_delayed`, `mse_simultaneous`, `advantage_db`, `valid` | [001](../experiments/001_causal_age/README.md) | [PR #1 merged](https://github.com/anttiluode/PerceptionLab/pull/1) |
| [WaveArrivalGateNode](../nodes/wave_arrival_gate_node.py) | Analysis | `signal_in` (signal) | `gate`, `amplitude` | [002](../experiments/002_wave_xor/README.md) | [PR #3 merged](https://github.com/anttiluode/PerceptionLab/pull/3) |
| [FadingHistorySpikeNode](../nodes/fading_history_spike_node.py) | Cognition | `signal_in` (signal) | `pulse`, `trace`, `amplitude`, `armed`, `fire_count` | [003](../experiments/003_fade_closed_loop/README.md), [004](../experiments/004_two_histories/README.md) | Workshop only; GUI verified for 003 after wave-size repair |

### FadingHistorySpikeNode

A first-order exponential trace of **absolute** input:
`trace(t+1)=decay*trace(t)+(1-decay)*abs(input(t))`.
Arms when trace reaches `arm_threshold`; emits a **one-tick positive**
`pulse_amplitude` only after trace has *fallen* below
`release_threshold`. Disarms and observes a `refractory` guard.
`enabled=0` prevents output. It **does not spike spontaneously**, detect
a phase, learn weights, or implement GeometricNeuron's 50-tick variance rule.

Key controls: `decay` (0–1), `arm_threshold`,
`release_threshold` (less than arm), `pulse_amplitude`,
`refractory`, `enabled`. Changing primary config resets transient state.
Thresholds depend on WaveField size, source, drive gain and read position;
use **open-loop calibration** before interpreting activity.

### TemporalTransitPredictorNode

Fits two linear predictors on **earlier paired samples** and reports
held-out current errors. `delay=0` yields the identity control; positive
`advantage_db` favors the delayed readout. This is not learning inside
WaveField and does not show that a physical neuron predicts anything.

### WaveArrivalGateNode

`gate=1` when `abs(signal_in)>=threshold`, else zero. Converts analog
field activity into a bit and leaves the physical field unchanged. Do not
confuse the original hardcoded `ResonatorSomaNode` XOR with computation
emerging spontaneously from the wave.

## Important *reused upstream* nodes

| Class | Source | Relevant ports / properties |
|---|---|---|
| `PulseSourceNode` | [pulsesourcenode.py](https://github.com/anttiluode/PerceptionLab/blob/main/nodes/pulsesourcenode.py) | output `signal`; `period=0` is single-shot; `warmup`, `width`, `amplitude` |
| `WaveFieldNode` | [wavefieldnode.py](https://github.com/anttiluode/PerceptionLab/blob/main/nodes/wavefieldnode.py) | `write_0..7` and `impulse`; outputs `read_0..7`, `energy`, `image`; 2nd-order damped wave, **size must be actually 96** in 003/004 |
| `TemporalMultiScopeNode` | [temporalmultiscopenode.py](https://github.com/anttiluode/PerceptionLab/blob/main/nodes/temporalmultiscopenode.py) | `sig_0..3` in, multiple transit/coherence metrics |
| `SignalPlotterNode` | [signalplotternode.py](https://github.com/anttiluode/PerceptionLab/blob/main/nodes/signalplotternode.py) | `signal_A (Red)`, `signal_B (Green)`, `signal_C (Blue)`; host image display colors can differ |
| `ResonatorSomaNode` | [resonatorsomanode.py](https://github.com/anttiluode/PerceptionLab/blob/main/nodes/resonatorsomanode.py) | `in_a`, `in_b` → `fire`; XOR is preset |
 
**Mandatory regression:** Before relying on any saved wave graph,
check actual arrays match `size` after the no-arg constructor plus
`set_config_options`. The 2026-11-15 size-loader bug produced a
convincing but physically miscalibrated GUI. The fix is on PerceptionLab
main. Ports existing is not sufficient; values must travel through them.

See [Workflow Manual](WORKFLOW_MANUAL.md) and
[historical node atlas](https://anttiluode.github.io/PerceptionLabNodes/).

## 004: same node class, different histories

No new node was required for 004. It uses two instances of **FadingHistorySpikeNode** with decay rates 0.86 and 0.95, independent thresholds and separate physical read/write sites in one WaveField. The initial tests showed fast A=21 spikes and slow B=0 when coupled, although slow B produced four when isolated. Rate-swapping reversed the active identity. This could be **activity-dependent suppression**: A's recurring input may hold B's trace above its release threshold. The new intervention measures B's trace and removes A's return. [004 dossier](../experiments/004_two_histories/README.md) and [first results](../results/004_two_histories_initial.json). Avoid claiming phase locking when one node is silent.
