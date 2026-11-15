# Workshop nodes

The [Node Manual](../docs/NODE_MANUAL.md) lists every reusable node, ports, caveats, and upstream promotion status. 004 deliberately reuses two instances of [FadingHistorySpikeNode](fading_history_spike_node.py); no duplicate node class is required.

[**005: PopulationOrderReadoutNode**](population_order_readout_node.py) is a non-invasive six-input observer (three traces, three spike EWMAs); it carries no teacher edge. See the [Node Manual](../docs/NODE_MANUAL.md) and [005 study](../experiments/005_order_of_falls/README.md).

**005 fitted probe:** [PopulationOrderReadoutNode](population_order_readout_node.py) now has trained weights only in the primary AB/BA (and C-off) experimental graphs. It has no teacher label input, and its weights do not modify the physical wave field. [Frozen model and validation](../results/005_frozen_readout_360.json). The exploratory C=.93 graphs remain untrained; see [three-active negative result](../experiments/005_order_of_falls/THREE_ACTIVE.md).

[**006 PlasticReturnGateNode**](plastic_return_gate_node.py) inserts a physically weighted, changeable link between C's pulse and the field. The weight changes only when an externally supplied reward comparison reaches its typed input. The [006](../experiments/006_reward_selected_return/README.md) and [006b](../experiments/006b_bounded_selection/README.md) experiments both found that the simple update **degraded** held-out AB/BA memory; full controls and numerical receipts are archived. [Node Manual](../docs/NODE_MANUAL.md).
