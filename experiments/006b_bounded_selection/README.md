# 006b — Conservative plasticity: does a bounded update generalize?

15 November 2026. **Exploratory follow-up, developed after seeing 006 fail.** See [006](../006_reward_selected_return/README.md), [the full original 006 receipt](../../results/006_reward_selected_return.json), and [Fable's V30 paper](https://github.com/anttiluode/GeometricNeuronV30).

The original reward-selected C-return gate moved from weight 0.50 straight to 1.00 on its first comparison and finished at 0.848, producing **6/16** correct held-out AB/BA labels versus **14/16** with the initial connection. 006b asks whether that failure was merely an overlarge weight update.

We changed the training rule **before running 006b**: a smaller learning rate of 0.02, a maximum single update magnitude of 0.05, and an average reward difference over **two matched AB/BA contexts** per update. Four updates process eight contexts. No other connection, wave equation, fade dynamics, calibration, or teacher/readout feature changes.

The same six-feature diagnostic reader was trained only on 006's separate C-pruned reader-fit contexts and frozen before this learning trial. The 006b reward experience contexts and **eight new final held-out AB/BA pairs** are disjoint from each other and from the original 006 final pairs. As in 006, AB/BA labels are known to the **external reward evaluator**, never wired into the gate. This is supervised training of a physical return gain, not autonomous goal generation or a local neural learning theorem.

[Run script](run.py) · [Permanent full receipt](../../results/006b_bounded_selection.json) · [Passing Actions run](https://github.com/anttiluode/PerceptionLabAI/actions/runs/43698479884).

## Weight trajectory

| Update | C-return weight |
|---|---:|
| Initial | 0.500000 |
| After 2 input contexts | 0.550000 |
| After 4 contexts | 0.502120 |
| After 6 contexts | 0.466936 |
| After 8 contexts | **0.419569** |

The catastrophic first-step saturation was prevented. The reward differences were heterogeneous across contexts: positive for the first pair of contexts and negative for the next three pairs. This demonstrates why averaging across experiences matters to the update's direction.

## Fresh final test — 16 previously unseen AB/BA examples

| Condition | Weight | Correct | Accuracy |
|---|---:|---:|---:|
| **Bounded multi-context reward learning** | **0.419569** | **8/16** | **50.0%** |
| Same connection, **learning disabled** | 0.500000 | 10/16 | 62.5% |
| **C return pruned** | 0.000000 | **14/16** | **87.5%** |
| Deliberately **inverted rewards** | 0.303980 | 7/16 | 43.75% |

The improved update control did **not** produce useful generalizing selection. It moved the synapse, but held-out memory performance was still worse than either the frozen or fully pruned connection. The final comparison was not used to choose the update rate or select a checkpoint. This result remains exploratory because the update procedure was designed after observing the first failed test.

All four conditions use the same physical gate and one-step transfer latency. The wave engine is the original upstream `WaveFieldNode`; the real A/B/C fading units and their field coupling remain. No clipping was observed at the sampled field-inspection steps.

## What this says about the vine analogy

The vine's tendrils do more than change a connection's gain. They explore physical space, contact a support, redistribute resources and abandon unsuccessful branches. Our 006/006b gate only adjusts one scalar, using a reward supplied by an outside observer. Even a conservative gradient of that reward does not establish what should survive across new contexts.

The central next question is **credit assignment with persistent consequences**: can a living graph assess its own delayed usefulness and alter *where* resources and connections grow, instead of receiving one externally calculated gradient from an AB/BA classifier? This is a research program, not a result established by 006b.

## Reproduce

```bat
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
python -m unittest discover -s tests -p test_006_reward_selection.py -v
python experiments\006b_bounded_selection\run.py --upstream ..\PerceptionLab
```

[Node Manual](../../docs/NODE_MANUAL.md) · [Workflow Manual](../../docs/WORKFLOW_MANUAL.md) · [006 GUI graphs](../../workflows/006_AB_plastic_return.json). GUI playback of 006 and 006b has not been verified; the measured results are headless host-node replays.
