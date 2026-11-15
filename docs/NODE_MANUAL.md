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

## 004 confirmed two-node behaviour

[Long-run receipt](../results/004_two_histories_long.json): two identical FadingHistorySpikeNode classes with **different** decays (A 0.86; B 0.95) and one common WaveField exhibited two distinct operating regimes. With A's feedback weight 1.0, B was permanently armed and above release threshold (B=0 spikes). With A feedback 0.30 and B feedback 1.0, both kept firing through 1,800 frames in an alternating, phase-locked sequence; the no-B-return control extinguished activity in both. At A weight 0.50, A dominated and B was silent. No new node class, neural learning, or biological equivalence is inferred.

## 005 — PopulationOrderReadoutNode (workshop only)

Source: [population_order_readout_node.py](../nodes/population_order_readout_node.py).

**Inputs:** `trace_0`, `trace_1`, `trace_2`, `spike_0`, `spike_1`, `spike_2` (all scalar signals). **Outputs:** `score`, `decision`, `ready`, `spike_memory_0..2` (signals). It has **no teacher/label input** and **no output returning to the physical field**.

The instrument computes an EMA (decay configurable, initially 0.92) of each spike input. It then computes a frozen linear score from three contemporaneous unit traces and three readout spike-memory values. Positive means AB, negative BA. All six weights initially equal zero, so **`ready=0` and no classification is claimed** until independent held-out training supplies a model. This readout has *its own* fading memory, which must be distinguished from retention in the three causal units.

Controls: `spike_decay`, `start_frame`, `bias`, `w0..w5`; changing a graph's decoder weights is not training the WaveField or the feedback units. A classifier trained from a particular time snapshot is not validated for other times.

**005 uses no new causal neuron.** It reuses three copies of FadingHistorySpikeNode with different decay constants (0.86/0.95/0.975), with two ordinary PulseSourceNodes delivering AB or BA via write_0 and write_3. See [005 experiment and controls](../experiments/005_order_of_falls/README.md).


## 005 measured readout and its limits

[Complete original receipt](../results/005_order_of_falls.json) · [Frozen frame-360 coefficients](../results/005_frozen_readout_360.json).

The original 005 AB/BA GUI graphs now contain the **same fitted model** and pooled open-loop thresholds for all three fading units. The model was fitted to three trace values and three readout spike-memory values using eight training AB/BA pairs and scored **14/16 held-out examples at frame 360**. Its score is *not* independently validated for every later frame or a different wave configuration. Passive and no-source graph variants retain zero/untrained observer weights.

With unlimited numerical precision, the passive field at frame 650 decoded **16/16**; with a post-hoc measurement floor (traces below **1%** of their own pooled open-loop peak; spike-memory values below **0.001**), its accuracy dropped to **8/16**, while the original recurrent unit readout was **15/16**. A classifier cannot be credited with physically meaningful memory when it amplifies differences near numerical zero.

The original third unit (C decay .975) never emitted. The exploratory [C-decay scan](../results/005_C_recruitment.json) found **0.93** allowed recurrent firing in all three. However, [fresh held-out three-active follow-up](../experiments/005_order_of_falls/THREE_ACTIVE.md) scored **10/16** with C feedback, versus **15/16** when the C return edge was disconnected. All six three-active GUI control graphs deliberately keep **untrained** observer weights.

**Node independence:** the `PopulationOrderReadoutNode` is an instrument, not a fourth recurrent neuron; its weights are trained offline, and it holds its own spike EMAs. A high decoding score here does not establish synaptic learning or a representation robust to arbitrary noise.

## 006 — PlasticReturnGateNode (workshop, task-rewarded)

[Source](../nodes/plastic_return_gate_node.py) · [006 report](../experiments/006_reward_selected_return/README.md) · [006b report](../experiments/006b_bounded_selection/README.md).

Category: Cognition. Inputs: `pre_spike` (signal) and `reward_difference` (signal). Outputs: `signal` (the physically weighted pulse), `weight`, `effective_weight`, `update_count`, `last_update`, and `pre_activity` (all scalar signals).

The node retains its own bounded weight between episodes. The outgoing pulse is `pre_spike * clip(weight + exploration_direction * perturbation, 0, 1)`. A two-sided external comparison of utility at plus and minus perturbations can be delivered to `reward_difference`, causing a real update of the stored weight. GUI parameters are `weight`, `exploration_direction`, `perturbation`, `learning_rate`, `resource_cost`, `max_update`, `learn_enabled`. A fixed weight does not change without reward input. Setting `max_update=1` recovers 006's original rule; 006b uses `max_update=0.05`.

**Crucial credit-assignment limit:** A frozen external readout and labelled AB/BA training context are used to *calculate the scalar reward*. The gate itself sees neither label nor readout coefficients, but this is **supervised reward-based parameter tuning**, not independently chosen biological goals, eligibility-trace STDP, growing dendrites, or unsupervised predictive coding.

Measured **006 failure**: learned weight 0.847595 scored only 6/16 held-out, versus 14/16 for both frozen w=0.5 and pruned w=0.0. Measured **006b bounded-update failure**, on a different fresh final split: learned w=0.419569 scored 8/16, frozen w=0.5 scored 10/16, pruned w=0.0 scored 14/16. Do not promote this node as a working learning-memory mechanism based on a weight change alone.

The saved 006 GUI graphs include the gate but do **not** include a teacher/reward source. The headless runner supplies reward differences through the same input API between episodes; GUI autonomous learning has not been demonstrated.

## 007 — HomeostaticReturnGateNode (workshop, label-free)

*Added by Claude Fable 5.2, 15 November 2026.* [Source](../nodes/homeostatic_return_gate_node.py) · [007 report](../experiments/007_homeostatic_return/README.md) · [Receipt](../results/007_homeostatic_return.json).

Category: Cognition. Input: `pre_spike` (signal), the only input. Outputs: `signal` (the weighted pulse), `weight`, `rate`, `rate_over_target`, `last_update` (all scalar signals).

Each frame the node updates a running firing rate, `rate += (spiked - rate) / rate_tau`, then its weight, `weight = clip(weight + sign * learning_rate * (target_rate - rate), 0, 1)`, and emits `pre_spike * weight`. GUI parameters: `weight`, `target_rate`, `learning_rate`, `rate_tau`, `sign` (+1 homeostatic, −1 control), `learn_enabled`. With `learn_enabled = 0` it is a fixed gain with the same one-frame delay. Unlike `PlasticReturnGateNode` it has no reward port and needs no external trainer, so the saved GUI graphs are self-contained.

**Measured in 007:** on the 004 two-unit system, A's weight moved from 1.00 to 0.41 and the suppressed unit B began firing; five starting weights converged to about 0.41; learning rates from 0.005 to 0.32 reached the same regime. Targets above what turn-taking can deliver leave the weight swinging across the switch point near 0.45–0.50.

**Limits:** the rule cannot restart a unit that has gone silent, and an isolated loop dies under it. The target rate is set by hand. Nothing in 007 measures memory or order information. Firing-rate homeostasis is a known mechanism; this node is a test component, not a biological model. Workshop only; not proposed upstream; GUI not yet verified.
