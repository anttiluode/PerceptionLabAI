# 011 — Old wood, new history: can one body remember two independent orders?

**Pre-result protocol committed 15 November 2026.** Follows [009 (history stored in structure)](../009_morphology_as_memory/README.md) and [010 (uniform hardening protected the first history in one exploratory result)](../010_hardening/README.md). This is **not** a new neuron/node; it tests an unresolved tradeoff in the actual GrowingReturnNode.

## Question

Does uniform age-related branch hardening merely **freeze the first history**, or can a body preserve its first event order **and still learn an independently chosen second order**?

010 always trained the opposite order second. Since BA was completely determined by AB and vice versa, it could not independently test what was retained about the second sequence. 011 fixes that.

## Locked experimental design (before seeing 011 results)

- **Four equiprobable, crossed histories:** AB→AB, AB→BA, BA→AB, BA→BA. The first and second labels are independently varied for every body seed. Same paired body seeds, pulse amplitudes, gap and jitter schedule under all conditions; only order changes. Every trial runs on the original upstream PerceptionLab WaveField and workshop FadingHistorySpike/GrowingReturn nodes.
- **First stage:** 20 episodes of the first order, with fresh fast state each episode. Initial branch weights are equal; the total budget is 1.0 per unit.
- **Second stage:** 20 episodes of the independently chosen second order, preserving **only** the first-stage structural weights, alive mask and hardness across episode resets. Observe at 10 and 20 second episodes.
- **Conditions:** **soft** (009, no hardening), **use-hardening** (010, rate 0.20, each branch hardened in proportion to its own weight), **age-hardening** (010, rate 0.20, all living branches hardened equally per firing), and **fully frozen** after the first stage (learning disabled throughout the second stage; the correct strong memory-preservation control).
- **Main sample:** eight different seed IDs for reader training and 16 untouched seed IDs for testing. Each ID is run under all four first/second combinations: **32 training and 64 held-out two-history bodies per condition**. That is modest; small effects remain uncertain.
- **Development smoke check:** separate seed, two training IDs and two held-out IDs with shorter episode schedules. Smoke results are *not* scientific evidence or used to tune parameters.
- **Complete fast-state wipe before every episode and probe:** each episode instantiates a new WaveField, fades, spike histories and source generators. Only structural weights, branch survival and hardness travel between episodes. After development, a neutral single pulse at site 3 tests the structure. All probes have **growth disabled**.
- **Two separately fitted frozen linear readouts:** old-history probe fitted ONLY on training IDs *after first stage*, then applied unchanged after second stage; new-history probe fitted ONLY on training IDs *after twenty second-stage episodes*, then applied to untouched final bodies. A separate new reader is allowed per condition, but **no reader ever sees held-out labels during fitting**.
- **Input representation and sensor floors:** six features, three fade traces and three spike EWMAs from the single neutral probe at frame 300, with trace resolution floor 1% of pooled open-loop peak and spike-memory floor 0.001 (same as 009/010); ridge penalty 0.25 as in 009.
- **Primary readout:** after twenty episodes, report old accuracy, new accuracy, and **joint** old-and-new accuracy for each condition, on the **same 64 held-out bodies** per condition. Repeat after ten episodes as a secondary observation using the same frozen models. Report pairwise discordant-body exact sign tests for age vs soft, age vs use, age vs frozen on joint accuracy. The per-condition first-stage accuracy is a separate baseline.
- **Resource and change measures:** living branch count, absolute total weight change, clipped frames, and mean plasticity. No task reward, no AB/BA label or reader output is connected to the growth rule.

**Precommitted interpretation gate:**
011 is a *positive* result for old+new retention only if the age-hardened condition has (a) old accuracy ≥75%, (b) new accuracy ≥70%, and (c) joint correctness greater than soft with paired two-sided sign-test p<0.05. If any fails, the specified claim fails. Comparing age vs frozen is essential: a completely frozen body should retain the old history but cannot acquire an independently chosen second history. A good old score alone is **not** evidence of two-memory learning. Analysis of the other conditions and 10-episode checkpoint is exploratory.

An independent final task, environmental shifts, recurrent task usefulness, and biological interpretations are **not** tested by 011. A higher joint score is still structural readout performance, not necessarily useful routing.

## Files and running

- [Runner](run.py) — actual 009/010 host-node simulation, no new surrogate dynamics
- [Tests](../../tests/test_011_dual_history.py) — balanced crossing, all labels independent, reader frozen, freeze/no-learn control, original graph ports
- [CI](../../.github/workflows/011-dual-history.yml) — full benchmark and separately labeled smoke; attaches machine-readable receipts
- After run: [full result](../../results/011_dual_history.json); do not assume it exists until the full GitHub CI job has completed and its exact output is committed.
- [Node manual](../../docs/NODE_MANUAL.md) · [Workflow manual](../../docs/WORKFLOW_MANUAL.md).

From your sibling PerceptionLab checkout:

```bat
cd /d D:\anttiluode\PerceptionLabAI
git pull origin main
python -m unittest discover -s tests -p test_011_dual_history.py -v
python experiments\011_dual_history\run.py --upstream ..\PerceptionLab --workers 4 --smoke
python experiments\011_dual_history\run.py --upstream ..\PerceptionLab --workers 4
```

The complete two-stage experiment **cannot be reproduced merely by loading one GUI graph**: graph loading does not automatically execute twenty separate trials, wipe fast states, carry forward structural configuration and repeat twenty more trials. The preexisting 010 one-episode GUI graphs remain useful for visual inspection, but the 011 scientific results come from the scripted real-node replay.

## Why this is a strict gate

009 proved event order can remain in changed structural routing after a full state wipe. 010 found uniform hardening sometimes preserves that structure better than use-biased hardening. Both successes could be satisfied by a body becoming difficult to change. **011 asks what it costs to stay old.** We cannot call hardening useful continual learning if the same body cannot write a second independent distinction.
