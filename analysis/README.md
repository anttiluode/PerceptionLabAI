# 011 statistical audit — crossed trials are clustered by seed

The 011 benchmark has **16 independent held-out seed IDs**, each evaluated
under four first/second history combinations. Its 64 held-out examples are
balanced and useful for accuracy, but the four variants of one seed share
geometry, parameters and perturbation schedule: they are **not independent
replications for a paired significance test**.

The 011 runner's initial "two-sided sign_p" counts discordant *examples*.
It is retained in the raw receipt for reproducibility but must **not** be
interpreted as a valid independent-replicate p-value.

Run [011_clustered_pairs.py](011_clustered_pairs.py) on the full result to
aggregate all four binary outcomes per seed, then compare the total
correct per seed with exact two-sided sign tests over the 16 independent
seed IDs. Ties do not contribute to the binomial test.

```bash
python analysis/011_clustered_pairs.py results/011_dual_history.json
```

This audit was committed while the full run was still executing, before
its numerical result was available. It does not modify weights, labels,
data splits or readouts. For any superiority claim, require the
**clustered**, rather than naive per-example, comparison to support it.

The predefined 75% old and 70% new absolute accuracy thresholds are
unchanged. More seeds would be preferable for small-effect inference.
