# 005 — Can the order of falls remember AB versus BA?

**Study question, preregistered November 15, 2026:** does a recurrent field of
**three differently fading history-triggered units** retain information about
whether stimulus A came before stimulus B, after both source pulses are silent?
Can an independent read-only linear probe recover that order from population
state on held-out trials, rather than inspecting stimulus labels?

This follows [004](../004_two_histories/README.md): the exact same fading
node class can compete, alternate, or suppress through shared propagation.
005 asks a **different** question: does altered firing order carry *input
history* rather than merely run as a clock?

## Actual components, not a separate simulator

Reuse genuine upstream **WaveFieldNode** (96×96, speed .5, damping .006),
two upstream **PulseSourceNode** (exactly one 2-frame pulse each),
and three instances of workshop **FadingHistorySpikeNode**:

- Fast: decay .86, read_1, return write_0 with gain .30
- Medium: decay .95, read_3, return write_2 with gain 1.0
- Slow: decay .975, read_5, return write_4 with gain .50
- A pulse enters **write_0**; B pulse enters **write_3**.
- Fourth, separate **PopulationOrderReadoutNode** listens only to three
  traces and their three pulse outputs. No teacher input; no return wire.

The readout includes its own 0.92-rate EWMA of recent spikes. That is
**additional memory in the observer**; any decoding is from three traces
plus this explicitly declared readout memory, not proof of pure instantaneous
trace-only memory. Its weights are initially all zero. After a reproducible
held-out study, freeze and publish weights only if justified.

## Matched AB / BA trials

For each perturbation trial we emit two same-amplitude, same-duration
pulses (one at each write port) with a shared early slot and late slot.
Swap only which source occupies the early slot.

- A and B pulse energy is exactly matched **within each AB/BA pair**.
- Jitter, time gap and amplitude scale vary across 8 training pairs
  and 8 disjoint held-out pairs.
- Each pair yields two runs with freshly initialized field and nodes.
- Labels are used **only by the offline training/evaluation script**.
  They are never wired into the physical graph or readout node.
- Predefined snapshots: frames 160, 240, 360, 520, 650. Both pulses
  finish long before these snapshots.

At each snapshot, fit a ridge-regularized linear readout using only the
16 labelled training runs. Evaluate on 16 unseen held-out runs (8 AB,
8 BA). Report balanced accuracy and how many held-out *pairs* had
**both** orders correctly decoded. Baseline balanced chance is 50%;
a single model on one small set does not establish generalization.

**Crucial null controls:** run identically with every unit's return
unplugged (passive wave), with slow C's return unplugged, and with
both source amplitudes zero. If a passive wave predicts equally well,
do not attribute information to recurrent pulse trains. Record spikes
from each unit to test whether a readout is just recognizing waveform
amplitude or whether its histories actually change the firing events.

The wave's finite residual activity can preserve source history
without any learning. The 005 system has **fixed** parameters; the
offline linear readout is the only trained component.

## Reproduce

```bat
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
cd /d D:\anttiluode\PerceptionLab
git pull origin main
cd /d D:\anttiluode\PerceptionLabAI
copy /Y nodes\fading_history_spike_node.py ..\PerceptionLab\nodes\
copy /Y nodes\population_order_readout_node.py ..\PerceptionLab\nodes\
python -m pip install numpy opencv-python-headless
python -m unittest discover -s tests -p test_005_order_of_falls.py -v
python experiments\005_order_of_falls\run.py --upstream ..\PerceptionLab
```

**GUI graphs** in `workflows/`:
- `005_AB_three_histories.json` / `005_BA_three_histories.json`
- `005_AB_no_return.json` / `005_BA_no_return.json`
- `005_AB_slow_disconnected.json` / `005_BA_slow_disconnected.json`
- `005_no_stimulus.json`

**After the headless run:** all seven original 005 GUI graphs now have their pooled open-loop calibration thresholds. The main AB/BA and C-return-off graphs contain the same **frame-360 trained readout**, whose held-out accuracy was 14/16. Passive/no-stimulus observer weights remain zero. The trained readout is diagnostic at its fitted observation time; the GUI graph itself has not been manually verified. See the measured report below.

See also [Node Manual](../../docs/NODE_MANUAL.md) and
[Workflow Manual](../../docs/WORKFLOW_MANUAL.md).

**An oscillator is not memory of AB/BA by itself.**

## Measured result, 15 November 2026

[Complete original data and fitted models](../../results/005_order_of_falls.json) · [successful CI run](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43695094816) · [frozen frame-360 model](../../results/005_frozen_readout_360.json).

All seven 005 automated checks passed. Three fading units shared one original WaveField, but **C=.975 never fired in this initial configuration**. The A/B subsystem produced recurrent events after both external source pulses stopped.

**Primary (original, unlimited numerical precision) combined six-feature readout:**

| Observation | Recurrent | No feedback (passive) |
|---|---:|---:|
| Frame 160 | 15/16 | 16/16 |
| Frame 360 | **14/16** | 16/16 |
| Frame 650 | 15/16 | 16/16 |

Thus there is **no advantage** for feedback over the passive field with unlimited numerical sensitivity. Source order itself already leaves extremely small but perfectly reproducible traces in the passive deterministic medium. This is a meaningful negative control.

**Exploratory finite-resolution check:** A post-hoc observer floor zeroes traces below 1% of their own *open-loop trace peak* and spike memory below 0.001. At frame 650 the passive medium's largest traces were on the order of `10^-6`, below this floor. Under this observer specification, the recurrent combined readout and recurrent spike-history-only readout each scored **15/16 (93.75%)**, while passive scored **8/16 (50%)**. These are **different linear models fitted at each snapshot** using the same training examples, not one fixed readout tracking accuracy across all times.

The frozen GUI readout is a single **frame-360** model fitted on all six features and scored 14/16 held-out. Accuracy at frame 650 from a separately fitted model must not be attributed to those exact frozen GUI coefficients.

The source amplitudes, pulse widths, and timing gaps were matched within each AB/BA pair. Eight training pairs and eight different held-out pairs were used; the results come from one deterministic model, so neither standard-error claims nor biological generalization are warranted.

**Exploratory 005b:** A separate [six-rate scan](../../results/005_C_recruitment.json) found a C=.93 setting where **all three units fired**. That three-active system was evaluated with [fresh held-out pairs](THREE_ACTIVE.md): recurrent feedback decoded only **10/16 at frame 650**, while removing C's return yielded **15/16**, and a passive field at the same finite resolution gave **8/16**. The extra active feedback made the linear order representation *less* accessible in this setting. Its own six GUI graphs are calibrated but have untrained observer weights.

**Outcome:** 005 demonstrates how to turn the phrase "past caught in signal trains" into a falsifiable observable. It does not show that a three-neuron network learned order, that the order is stored exclusively in spikes, or that adding more nodes increases memory capacity.
