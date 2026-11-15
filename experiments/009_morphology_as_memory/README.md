# 009 — Morphology as memory

15 November 2026. Built by Claude Fable 5.2 at Antti's request, from Sol's "Morphology as Memory" proposal.

**Status: design committed, full run in progress. No result is claimed yet.**

## Question

Experiments 006 and 008 tried to make a connection learn what to keep by adjusting one number per edge. Both failed. 009 changes what is allowed to change: each unit has **eight candidate return branches** sharing a fixed budget. Branches grow toward sites that were recently busy, lose out to each other, and are **pruned for good** when they fall below a threshold. The rule is local: a unit's own pulse and the field value at each branch tip.

A body is grown by a history: twenty episodes of two equal pulses, A then B, or B then A. Between episodes every fast state is wiped. Only branch weights carry over.

## Decision rules, fixed before the full run

Settings were chosen on four-plus-eight development bodies from a separate seed and then locked (learning rate 0.2, site-trace decay 0.97, prune threshold 0.02, budget 1.0, 20 episodes of 400 frames, probe at site 3). The full run uses 16 training and 48 held-out bodies per order from a different seed.

- **Q2, structure carries readable history.** Shown only if all three hold on the 96 held-out bodies at frame 300 after one identical neutral probe pulse: grown bodies decode at 75% or better; bodies with growth switched off decode at chance; bodies with the same branches in scrambled positions decode at 65% or worse.
- **Q3, behaviour without a reader.** Predicted: cue A alone evokes more activity near B's site in AB-grown bodies than in BA-grown bodies with the same parameters, and the mirror image for cue B. Shown only if both paired sign tests reach p < 0.05 in the predicted direction.
- **Q4, pruning and durability.** After ten further episodes of the opposite order, is the first history still read by the reader fitted before interference? Pruning "helps" only if its paired sign test against the no-pruning bodies reaches p < 0.05.

Development runs already suggest Q3 will fail. It stays in as stated.
