# 004 — Two fading histories in one propagating field

## Latest result — two regimes in the same shared medium

**Recorded on 15 November 2026:** [full 650-frame gain sweep](../../results/004_two_histories_gain_sweep.json) · [1,800-frame long-run receipt](../../results/004_two_histories_long.json) · [long-run CI](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43692611309).

The decisive intervention was to weaken **only A's feedback into the shared wave**. The slow unit B had remained armed and *above its release threshold 100% of the late period* under full-strength A feedback, explaining its lack of firing in the strong-A condition.

| A return weight | Behaviour over 650 frames | B late activity |
|---|---|---|
| 1.00 | A=21 spikes, B=0 | Fully suppressed |
| 0.50 | A=25, B=0 | Fully suppressed |
| 0.45 | A=8, B=6 | Alternating events |
| 0.30 | A=6, B=5 | Alternating events |
| 0.25 | A=5, B=5 | Alternating events |
| 0.15 | A=5, B=5 | Alternating events |

**Causal controls:** Cutting A's return halfway allows B to resume firing (B=2). At weak A return (0.25 or 0.30), removing B's return makes **both** lose recurrence after the initial stimulus. Thus in the measured regime B's contributions are essential for A's continuing activity, whereas with strong A feedback B is suppressed.

**Longer 1,800-frame confirmation** (single deterministic configuration, one shared 96×96 field):

| Case | A quarter counts | B quarter counts | Late period |
|---|---|---|---|
| A return 0.30 | 4, 4, 4, 3 | 3, 4, 4, 4 | both 118 frames |
| A return 0.45 | 6, 5, 4, 5 | 4, 4, 5, 5 | both ~96.7 frames |
| A return 0.50 | 17, 19, 19, 18 | 0, 0, 0, 0 | A 24 frames |
| A return 0.30; B return disconnected | 1, 0, 0, 0 | 1, 0, 0, 0 | recurrence dies |
| A return 0.30, spatial sites swapped | 6, 6, 7, 6 | 6, 6, 6, 7 | both 70 frames |
| A return 0.30, decay rates swapped | 0, 0, 0, 0 | 6, 5, 6, 5 | B 81 frames |

All long-run cases had **zero wave-amplitude clipping frames**. The weak 0.30 and 0.45 conditions showed late interleaving fraction **1.0** and phase-concentration R nearly 1.0. These are deterministic locked event sequences, not learning or stable coordination under noise or varying stimuli.

**Load and compare in the real GUI:**
[004 full-strength competition](../../workflows/004_two_fades_one_field.json) ·
[004 weak-A alternating condition](../../workflows/004_weak_a_interleaving.json) ·
[004 weak-A without B return](../../workflows/004_weak_a_without_b_return.json).
The baseline A and B weights are 1.0; the weak A workflow changes A->WaveField return weight to **0.25** while leaving B's weight at 1.0. It uses the **same measured node thresholds**, wave size, source and rates. This makes the comparison directly controllable by loading different graphs. **Interactive GUI playback of 004 has not been independently observed yet.**

The mechanism is conventional wave propagation plus a thresholded leaky trace in a regenerative loop. The novelty here is an explicitly controlled demonstration in our compositional node laboratory that **asymmetric feedback strength shifts the same network from suppression to mutual regeneration**. Remaining checks: perturbation recovery, different stimulus strengths, boundary conditions, and whether a genuinely different input sequence can leave accessible information beyond periodic phase.

---

**Question (preregistered November 15, 2026):** Can two state-dependent,
fade-triggered units influence each other's spike timing through **one shared
WaveField**, and do rate and geometry swaps alter their temporal relation?
This tests one narrow step toward a heterogeneous distributed temporal code;
it does not test learning, musical perception, consciousness or real neurons.

## Real engine and ingredients

Reuse **one** upstream `WaveFieldNode` (96×96, speed 0.5, four substeps,
damping 0.006), **one** original `PulseSourceNode` (single shot at frame 18,
amplitude 0.12, width 2), and **two instances** of the *existing* workshop
`FadingHistorySpikeNode`, without inventing another neuron class.

- Unit A: fast trace decay 0.86, input `read_1`, pulse 0.24 into `write_0`.
- Unit B: slow trace decay 0.95, input `read_3`, pulse 0.24 into `write_2`.
- Both integrate `abs(wave read)`, arm above high threshold and fire after
  the trace drops below a lower threshold. Neither emits from silence.
- Two SignalPlotter scopes show traces and spikes; the upstream
  TemporalMultiScope shows field propagation across four apertures.
- The host transfers all *previous-tick* outputs, then steps all nodes.
  `run.py` reproduces that order and uses the **saved workflow files**
  as the source of graph wiring.

## Predicted outcomes

H1. Both nodes may exhibit recurrent pulses after the initial source becomes
silent, but the result may also be extinction. They are individually capable
of fade-triggered pulses; joint recurrence is NOT guaranteed.

H2. Changing only decay rates can change spike times. Whether the phase
relationship locks, alternates or suppresses one unit must be **measured**,
not guessed from a pretty waveform.

H3. Changing only spatial reading/writing locations alters which wave
history each node sees. It may change activity, but input amplitude changes
too, so compare *frozen thresholds* with an *independently open-loop
calibrated* swap.

H4. Disabling A or B and cutting B's feedback halfway measures causal
dependence rather than a spurious correlation of two responders to the same
startup pulse.

## Controls and methods

`run.py` evaluates the real saved graph and these variants:

| Variant | Purpose |
|---|---|
| `004_two_fades_one_field.json` | Both active, single common field |
| `004_a_only.json` / `004_b_only.json` | Each individual return path |
| `004_no_return.json` / `004_no_seed.json` | Passive ringdown and empty initial state |
| `004_swap_decay.json` | Swap only A/B decay rates |
| `004_swap_sites.json` | Swap A/B read and write apertures |
| `cut_b_midrun` (runner only) | B feedback disconnected after half the run |
| `swap_*_frozen` (runner only) | Same swaps with baseline thresholds held fixed |

Each **independent open-loop calibration** drives only the single starter
pulse, with both return wires disconnected. For each trace, select:
`arm=0.45*peak`, `release=0.20*peak`; freeze during evaluation.
Swaps have both recalibrated and frozen-threshold comparisons. A positive
or null result of a swap is not necessarily an isolation of the fading
time constant because the calibration also changes excitation thresholds.

Descriptive outputs: full spike rasters for A and B, late count, mean ISI,
ISI CV, B-over-A phase concentration R, signed nearest offset, near-time
coincidence and interleaving. R can be high even for unrelated oscillators
with near-commensurate periods. Report changes against the one-unit controls.
Wave clipping count is recorded. **One deterministic seeded run is not a
statistical population.**

## Running

```bat
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
python -m pip install numpy opencv-python-headless
python -m unittest discover -s tests -v
python experiments\004_two_histories\run.py --upstream PerceptionLab
```

With a separate sibling PerceptionLab checkout, instead use
`--upstream ..\PerceptionLab`.

**GUI:** copy `nodes\fading_history_spike_node.py` into the local
PerceptionLab `nodes` folder, restart PerceptionLab, and open
`workflows\004_two_fades_one_field.json`. All seven workflow configurations now contain **measured open-loop calibration thresholds** from the CI reference run. The Wave Field must show ~4.9 frames per gap on 96×96.
All variants are graphs loadable in the current host.

## Status

**Measured**: see below. The experiment's initial hypothesis of interleaving was not supported.

## First measured result — suppression rather than alternation

[Passing first 004 CI run](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43691739662), six workflow tests and a deterministic 650-step simulation of the actual WaveField. [Permanent numerical receipt](../../results/004_two_histories_initial.json).

| Case | A spikes (late) | B spikes (late) | Measured mean late interval |
|---|---:|---:|---|
| Both connected, A fast/B slow | **21 (11)** | **0 (0)** | A: 29 frames |
| A-only | **21 (11)** | 0 | A: 29 frames |
| B-only | 0 | **4 (2)** | B: 154 frames |
| Both returns unplugged | 1 | 1 | No recurrence |
| No starter pulse | 0 | 0 | None |
| Rates swapped, separately calibrated | 0 | **8 (4)** | B: 81 frames |
| Sites swapped, separately calibrated | **8 (4)** | 0 | A: 81 frames |
| Rates swapped, original thresholds frozen | 10 (5) | 2 (1) | A: 62.25 frames |

All cases recorded **zero field-clipping frames**. The faster-decay identity was dominant in the separately calibrated rate and position swaps of this particular configuration.

**Interpretation limit:** We have evidence that activity from the fast unit is associated with silence in the slower one; B can fire alone but not while A is continuously regenerating the wave. It is *consistent* with A keeping B's leaky trace above the lower release threshold. The first sweep did **not** directly test B's trace against that threshold or rescue B by disabling A; no phase-locking measurement is meaningful when B emits no spikes.

**Follow-up implemented:** the runner now cuts **A's** return halfway through, varies its return weight (0.25/0.5/0.75), and records B's late trace min/mean/max, armed fraction, and fraction above the release threshold. Compare rescued B spikes to B-only. These new measurements must be inspected before promoting a mechanism claim. Additional GUI validation is still pending.

Measured GUI thresholds for the base graph: A arm **0.10849628**, release **0.04822057**; B arm **0.03350883**, release **0.01489281**. Swapped-rate and swapped-site graphs use their respective independent open-loop calibration values, not these base numbers.
