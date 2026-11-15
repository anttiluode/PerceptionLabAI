# 010 — Hardening

15 November 2026. Built and run by Claude Fable 5.2 at Antti's request, as the follow-up to [009](../009_morphology_as_memory/README.md).

**Result: the hypothesis as stated is not confirmed, and the control beat it.** Branches that harden *by use* held the first history better than soft branches after ten opposite-order episodes, but not by enough to pass the rule (p = 0.064), and after twenty episodes they were no better than soft. Branches that all harden *equally with age* held it through twenty episodes: **84 of 96** bodies, against 72 for hardening by use and 77 for soft.

[Full receipt](../../results/010_hardening.json) · [runner](run.py) · [node](../../nodes/growing_return_node.py) · [tests](../../tests/test_010_hardening.py) · [design commit, before results](https://github.com/anttiluode/PerceptionLabAI/commit/f2c1a72)

## Question

In 009, grown branch structure recorded the order of past events, but later episodes of the opposite order mostly overwrote it, and pruning did not help. The proposed missing piece: a vine's surviving tendril turns woody. If a branch becomes harder to change the more it has been used, does the first history survive later experience?

## The change

`GrowingReturnNode` gets a hardness $`h_s`$ per branch that only ever grows. Its plasticity is

```math
g_s = \frac{1}{1 + \kappa\, h_s}
```

and both the branch's growth step and its share of the budget correction are multiplied by $`g_s`$. A hard branch neither grows, shrinks nor gives up weight easily. With $`\kappa = 0`$ the node reproduces 009 exactly (checked to 4e-16 on a 009 body).

| Condition | How hardness grows each time the unit fires |
|---|---|
| **soft** | not at all (009 as it was) |
| **use** | each branch by its own weight: what carries more hardens more. *The hypothesis.* |
| **age** | every living branch by the same amount. *Control for plain ageing; same total hardness added.* |

All three use 009's pruning, histories, probe and reader. $`\kappa = 0.2`$ was chosen from a development sweep on a separate seed and locked. Bodies are fresh (new seed): 16 training and 48 held-out per order. After its history each body lives ten and then twenty episodes of the **opposite** order with growth on. The reader is fitted before that and asked for the **first** history.

## Result

Held-out bodies, of 96, in which the first history is read correctly:

| Condition | Before | After 10 opposite episodes | After 20 |
|---|---:|---:|---:|
| soft | 92 | 73 | 77 |
| hardening by use | 90 | 83 | 72 |
| **hardening by age** | 87 | **86** | **84** |

Mean total weight change during interference: soft 1.09 then 1.41; use 0.58 then 0.96; age 0.58 then 0.94. By the end of the first history a living branch's plasticity had fallen to about 0.58 in both hardened conditions. Zero clipped frames.

Paired sign tests (bodies where two conditions disagree):

| Comparison | First right only | Second right only | p |
|---|---:|---:|---:|
| use vs soft, after 10 | 17 | 7 | 0.064 |
| use vs soft, after 20 | 7 | 12 | 0.36 |
| age vs soft, after 10 | 18 | 5 | 0.011 |
| age vs soft, after 20 | 9 | 2 | 0.065 |
| use vs age, after 10 | 1 | 4 | 0.38 |
| **use vs age, after 20** | **0** | **12** | **0.0005** |

## Against the rules set beforehand

1. *Use-hardened bodies still learn the first history, 75% or better.* **Passed**: 90/96.
2. *After ten opposite episodes, use beats soft on the paired test, p < 0.05.* **Failed**: 17 against 7, p = 0.064.

So hardening by use is **not confirmed**. It is close at ten episodes and gone at twenty.

## What the control showed

Ageing was put in as a control, to check whether any benefit was just "everything slows down". It turned out to be the better mechanism. After twenty episodes it lost 3 of the 87 bodies it started with; hardening by use lost 18 of 90. The use-against-age difference at twenty episodes is the one clear result in the table, and it survives correcting for the six comparisons made.

This was not a pre-stated hypothesis, so it should be treated as an observation to be tested again on new bodies, not as a confirmed finding.

**A likely reason, not tested.** Both conditions changed their weights by the same total amount (0.96 and 0.94), so the difference is in *which* branches moved. Hardening by use protects the strong branches and leaves the weak ones soft. The new history can then grow those soft branches freely and change the arrangement around the protected ones. Ageing stiffens every branch a body has, strong and weak, so the whole arrangement holds.

If that is right, what needs protecting is the pattern as a whole, including the branches that are small, and not only the ones that carry the most.

## Limits

- **The price was not measured.** A body that holds its first history may simply be learning less. 010 does not test whether an aged body can still record the second history as well.
- **First learning costs a little.** Before interference: soft 92, use 90, age 87.
- **The soft bodies here held up better than in 009** (73/96 against 64/96 after ten episodes). Same settings, different bodies; body-to-body variation is that large.
- **One hardening rate in the full run.** The development sweep (16 bodies per setting) was too small to rank rates.
- **Same single geometry, three units, deterministic, no noise, imposed wipes between episodes.**
- **Known mechanism.** Slowing plasticity with age is a critical period; protecting important weights is consolidation. Neither is new. The result is about which of them helps in this system.

## Reproduce

```bat
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
python -m unittest discover -s tests -p test_010_hardening.py -v
python experiments\010_hardening\run.py --upstream ..\PerceptionLab
```

The full run took 29 minutes on two cores. `--dev` runs the development sweep (about nine minutes).

**GUI graphs** (copy `growing_return_node.py` and `fading_history_spike_node.py` into PerceptionLab's `nodes` folder first): [one AB episode, hardening by use](../../workflows/010_AB_growing_hardening_by_use.json) · [hardening by age](../../workflows/010_AB_growing_hardening_by_age.json). These show one continuous episode; the multi-episode protocol exists only in the runner. Neither has been run in the GUI.
