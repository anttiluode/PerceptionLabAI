# Workshop nodes

The [Node Manual](../docs/NODE_MANUAL.md) lists every reusable node, ports, caveats, and upstream promotion status. 004 deliberately reuses two instances of [FadingHistorySpikeNode](fading_history_spike_node.py); no duplicate node class is required.

[**005: PopulationOrderReadoutNode**](population_order_readout_node.py) is a non-invasive six-input observer (three traces, three spike EWMAs); it carries no teacher edge. See the [Node Manual](../docs/NODE_MANUAL.md) and [005 study](../experiments/005_order_of_falls/README.md).

**005 fitted probe:** [PopulationOrderReadoutNode](population_order_readout_node.py) now has trained weights only in the primary AB/BA (and C-off) experimental graphs. It has no teacher label input, and its weights do not modify the physical wave field. [Frozen model and validation](../results/005_frozen_readout_360.json). The exploratory C=.93 graphs remain untrained; see [three-active negative result](../experiments/005_order_of_falls/THREE_ACTIVE.md).

[**006 PlasticReturnGateNode**](plastic_return_gate_node.py) inserts a physically weighted, changeable link between C's pulse and the field. The weight changes only when an externally supplied reward comparison reaches its typed input. The [006](../experiments/006_reward_selected_return/README.md) and [006b](../experiments/006b_bounded_selection/README.md) experiments both found that the simple update **degraded** held-out AB/BA memory; full controls and numerical receipts are archived. [Node Manual](../docs/NODE_MANUAL.md).

[**007 HomeostaticReturnGateNode**](homeostatic_return_gate_node.py) (added by Claude Fable 5.2) is a return edge that adjusts its own weight from its unit's firing rate alone: no reward port, no label, no reader. In [007](../experiments/007_homeostatic_return/README.md) it moved A's return from 1.00 to 0.41 and released the suppressed unit B into turn-taking; an isolated loop dies under the same rule. [Node Manual](../docs/NODE_MANUAL.md).

**008:** three `HomeostaticReturnGateNode` gates on the 005b circuit made order decoding worse (60/96 against 81/96). No new node. [Report](../experiments/008_self_tuned_order/README.md).

[**009 GrowingReturnNode**](growing_return_node.py) (added by Claude Fable 5.2) gives a unit eight return branches under one budget, grown toward recently busy sites and pruned when weak, using only local signals. In [009](../experiments/009_morphology_as_memory/README.md) the grown arrangement kept event order after all activity was wiped (89/96 held-out bodies); cue recall and pruning-for-durability both failed. [Node Manual](../docs/NODE_MANUAL.md).

**010:** `GrowingReturnNode` gained optional per-branch hardening (off by default). Hardening by use was not confirmed as protecting memory; equal ageing did better. [Report](../experiments/010_hardening/README.md).
