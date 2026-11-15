# 010 — Hardening

15 November 2026. Built by Claude Fable 5.2 at Antti's request, as the follow-up to [009](../009_morphology_as_memory/README.md).

**Status: design committed, full run in progress. No result is claimed yet.**

## Question

In 009, grown branch structure recorded the order of past events, but ten episodes of the opposite order mostly overwrote it, and pruning did not help. The proposed missing piece: a vine's surviving tendril turns woody. If a branch becomes harder to change the more it has been used, does the first history survive later experience?

## Decision rules, fixed before the full run

`GrowingReturnNode` gets an optional hardness per branch; plasticity is `1 / (1 + harden_rate * hardness)`. With `harden_rate = 0` it reproduces 009 exactly (checked to 4e-16 on a 009 body).

Three conditions, all with 009's pruning, on fresh bodies (new seed), 16 training and 48 held-out per order:

- **soft**: no hardening (009 as it was).
- **use**: a branch hardens by its own weight each time its unit fires. This is the hypothesis.
- **age**: every living branch hardens by the same amount per firing. A control for plain ageing, with the same total hardness added.

`harden_rate` was set to 0.2 after a development sweep (0.05, 0.2, 1.0) on 16 held-out development bodies from a separate seed, and locked.

Hardening counts as **confirmed** only if both hold:

1. Use-hardened bodies still learn the first history: readout before interference at 75% or better on the 96 held-out bodies.
2. After ten opposite-order episodes, the first history is read in more use-hardened bodies than soft bodies, paired sign test p < 0.05.

Reported alongside, without a pass rule: the same after twenty opposite-order episodes, and use against age. If age does as well as use, the benefit is slowing down in general, not hardening what was used.
