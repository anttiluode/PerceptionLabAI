# 004 — Two fading histories in one propagating field

**Question (preregistered November 15, 2026):** Can two state-dependent,
fade-triggered units influence each other's spike timing through **one shared
WaveField**, and do rate and geometry swaps alter their temporal relation?
This tests one narrow step toward a heterogeneous distributed temporal code;
it does not test learning, musical perception, consciousness or real neurons.

## Real engine and ingredients

Reuse **one** upstream \`WaveFieldNode\` (96×96, speed 0.5, four substeps,
damping 0.006), **one** original \`PulseSourceNode\` (single shot at frame 18,
amplitude 0.12, width 2), and **two instances** of the *existing* workshop
\`FadingHistorySpikeNode\`, without inventing another neuron class.

- Unit A: fast trace decay 0.86, input \`read_1\`, pulse 0.24 into \`write_0\`.
- Unit B: slow trace decay 0.95, input \`read_3\`, pulse 0.24 into \`write_2\`.
- Both integrate \`abs(wave read)\`, arm above high threshold and fire after
  the trace drops below a lower threshold. Neither emits from silence.
- Two SignalPlotter scopes show traces and spikes; the upstream
  TemporalMultiScope shows field propagation across four apertures.
- The host transfers all *previous-tick* outputs, then steps all nodes.
  \`run.py\` reproduces that order and uses the **saved workflow files**
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

\`run.py\` evaluates the real saved graph and these variants:

| Variant | Purpose |
|---|---|
| \`004_two_fades_one_field.json\` | Both active, single common field |
| \`004_a_only.json\` / \`004_b_only.json\` | Each individual return path |
| \`004_no_return.json\` / \`004_no_seed.json\` | Passive ringdown and empty initial state |
| \`004_swap_decay.json\` | Swap only A/B decay rates |
| \`004_swap_sites.json\` | Swap A/B read and write apertures |
| \`cut_b_midrun\` (runner only) | B feedback disconnected after half the run |
| \`swap_*_frozen\` (runner only) | Same swaps with baseline thresholds held fixed |

Each **independent open-loop calibration** drives only the single starter
pulse, with both return wires disconnected. For each trace, select:
\`arm=0.45*peak\`, \`release=0.20*peak\`; freeze during evaluation.
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

\`\`\`bat
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
python -m pip install numpy opencv-python-headless
python -m unittest discover -s tests -v
python experiments\004_two_histories\run.py --upstream PerceptionLab
\`\`\`

With a separate sibling PerceptionLab checkout, instead use
\`--upstream ..\PerceptionLab\`.

**GUI:** copy \`nodes\fading_history_spike_node.py\` into the local
PerceptionLab \`nodes\` folder, restart PerceptionLab, and open
\`workflows\004_two_fades_one_field.json\`. The starting workflow
thresholds are **provisional until replaced with measured calibration
numbers**. The Wave Field must show ~4.9 frames per gap on 96×96.
All variants are graphs loadable in the current host.

## Status

**Not yet measured when this dossier was created.** The actual CI
receipt belongs at \`results/004_two_histories.json\`. Do not infer
coupling, phase locking or alternation until inspecting isolated controls.
