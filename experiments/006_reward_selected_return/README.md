# Experiment 006 — Can a return connection learn what is worth preserving?

15 November 2026. Exploratory continuation of [GeometricNeuronV30](https://github.com/anttiluode/GeometricNeuronV30) and [005](../005_order_of_falls/README.md).

**Answer from this first test: not successfully.** The connection really changed its retained weight under experience-dependent reward, but the resulting circuit remembered AB/BA **worse** on unseen examples than either an untrained or completely disconnected connection.

[Full measured receipt](../../results/006_reward_selected_return.json) · [passing CI after repaired wiring](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43697926136) · [runner](run.py) · [new node](../../nodes/plastic_return_gate_node.py).

## The honest boundary

001–005 used a fixed physical graph; an external linear observer learned how to read the signal trains. In 006, **one return connection in the physical graph is plastic**: the pathway from C's output pulse into the WaveField's write_4 port.

The new **PlasticReturnGateNode** stores a bounded scalar gain *w* across trial episodes. The field, pulse sources, three fading-history units and independent population readout are their original implemented classes; no new wave physics is substituted.

A separate external evaluator supplies a **supervised** scalar reward comparing two slight perturbations, one at *w + delta* and one at *w - delta*. The **same** matched AB/BA pair is presented under both perturbations. The gate updates its own weight when the reward-difference signal arrives at its real `reward_difference` input.

This is **task-directed reward selection**, not an unsupervised local Hebbian rule, a spontaneously developed goal, or a neuron which reads AB and BA directly. The AB/BA labels are used by the **external evaluator**, not by the gate node. The external evaluator's frozen readout is trained before any plasticity.

## Construction and controls

Four matched, loadable host graphs:

| AB | BA | Condition |
|---|---|---|
| [AB plastic](../../workflows/006_AB_plastic_return.json) | [BA plastic](../../workflows/006_BA_plastic_return.json) | C pulse → trainable gate → wave write_4 |
| [AB pruned](../../workflows/006_AB_pruned_return.json) | [BA pruned](../../workflows/006_BA_pruned_return.json) | Same gate and latency; retained weight zero |

A and B returns are fixed at 0.30 and 1.00. C fades at 0.93, arm 0.06781459787754025, release 0.030139821278906784 (exploratory values from 005b). Sources deliver two 2-frame equal-amplitude pulses at separate spatial write ports. AB and BA differ **only in which source fires first** within a matched pair.

- **Reader:** six input features from three fading traces and three readout spike EWMAs, trained once on **eight training AB/BA pairs with the C return fully gated off**. Frozen before gate training, with a fixed measurement floor for every condition.
- **Plasticity:** initial weight 0.50, exploration delta=0.10, learning rate 0.12, bounds [0,1], **no resource cost**. Eight training pairs, each tested at plus and minus perturbation for both orders.
- **Reward:** mean negative softplus classification loss of the frozen external reader, evaluated with the known AB/BA label. This is the explicitly supervised part.
- **Held-out:** eight other matched AB/BA pairs, never used for the reader fit or gate updates (16 runs per final condition).
- **Controls:** learned feedback, frozen initial gain 0.50, pruned gain 0, and inverted reward. **All** have the same extra one-frame gate delay and use the genuine upstream WaveField.
- **Tests:** five regression tests passed, covering port types, matched stimuli, reward persistence, read-port causality and C's ability to fire even with its return suppressed. An initial wiring bug was caught and corrected before measurements.

The node's bounded update uses a two-sided estimate:

```math
w_{n+1} = \operatorname{clip}_{[0,1]}\left(
w_n + \eta\,\frac{R_n(w_n+\delta)-R_n(w_n-\delta)}{2\delta}
-\eta\,\lambda
\right).
```

The resource term is deliberately **zero** in this round. The gate has no built-in bias to prune; only the reward comparison changes the selected weight. Other dynamical state is reset between trials, while gate weight persists across training.

## What actually happened

| Condition | Final C gain | Correct out of 16 unseen examples |
|---|---:|---:|
| Reward-selected plasticity | **0.847595** | **6/16 = 37.5%** |
| No learning, original connection | 0.50 | **14/16 = 87.5%** |
| C return permanently pruned | 0.00 | **14/16 = 87.5%** |
| Inverted-reward update | 0.00 | **14/16 = 87.5%** |

After the first training comparison the gate rose from 0.50 to **1.00**, stayed saturated until the final comparison, and ended at 0.847595. The inverted-reward control took a different trajectory ending at 0. No field clipping occurred at the sampled inspection frames.

Thus the node **does** change its actual return signal, but this learning rule **does not** select a more generalizable memory. It may exploit a brittle training objective, non-smooth threshold dynamics, too few contexts, or limits of the frozen reader. The first experiment does not isolate which cause dominates.

**A changing weight is not proof of useful learning.** The frozen and pruned connections tie in held-out accuracy, and even strengthening the return can impair order information.

## The vine comparison

A vine explores, allocates resources, retains useful supports and lets other shoots stop growing. 006 copies only **one minimal aspect**: allow a possible feedback pathway to vary, and use consequences of experience to adjust its future contribution.

The graph **does not grow topology**, add branches, relocate apertures, simulate nutrient transport, or generate its reward autonomously. It is not a biological model of vine or dendrite growth. The next falsifiable question is whether a more reliable credit assignment across multiple contexts can retain useful pathways **without sacrificing unseen order recognition**.

A stricter follow-up would separate reader fitting, reward-generating episodes, validation experiences and untouched final tests, alongside explicit resource costs and randomly assigned rewards.

## Reproduce

```bat
cd /d D:\anttiluode\PerceptionLab
git pull origin main
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
copy /Y nodes\fading_history_spike_node.py ..\PerceptionLab\nodes\
copy /Y nodes\population_order_readout_node.py ..\PerceptionLab\nodes\
copy /Y nodes\plastic_return_gate_node.py ..\PerceptionLab\nodes\
python -m pip install numpy opencv-python-headless
python -m unittest discover -s tests -p test_006_reward_selection.py -v
python experiments\006_reward_selected_return\run.py --upstream ..\PerceptionLab
```

Restart the GUI after copying the workshop nodes, then load one of the 006 graphs. **The GUI graph contains the gate but not a wired reward source.** The external runner supplies the reward comparison between episodes and holds the gate's weight across them. Interactive 006 playback is **not yet verified**.

## Scientific status

006 establishes that a **physical return connection can be updated across experiences** via a real, testable PerceptionLab node. It does **not** show that the resulting modification improves memory, that the network autonomously values the past, or that growth and pruning have emerged. The first task-directed update made the held-out result considerably worse.
