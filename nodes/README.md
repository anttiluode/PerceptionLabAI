# Workshop nodes

The [Node Manual](../docs/NODE_MANUAL.md) lists every reusable node, ports, caveats, and upstream promotion status. 004 deliberately reuses two instances of [FadingHistorySpikeNode](fading_history_spike_node.py); no duplicate node class is required.

[**005: PopulationOrderReadoutNode**](population_order_readout_node.py) is a non-invasive six-input observer (three traces, three spike EWMAs); it carries no teacher edge. See the [Node Manual](../docs/NODE_MANUAL.md) and [005 study](../experiments/005_order_of_falls/README.md).
