# Contributing: human and AI collaborators

- Reuse existing PerceptionLab nodes before writing new ones.
- Each experiment needs a falsifiable question, host-loadable saved graph, a baseline, runnable tests, numbers, provenance, and limitations.
- Preserve failed runs. Mark hypotheses as hypotheses; do not rename a display to make a claim true.
- Verify every wiring port and the *effect* of every alleged control.
- Keep experimental scaffolding here. Propose only reusable nodes and tested workflows upstream through review.
- Use branches and PRs when working together. Do not overwrite another contributor's changes.
- Credit code and scientific sources. No unreviewed changes to PerceptionLab main.
- No hype, no invented measurements, no quantum/biological claims from analogies.

Run `python -m unittest discover -s tests -v` and `python experiments/001_causal_age/run.py --upstream PerceptionLab` with upstream checked out beside this repo, or use the included GitHub Actions workflow.
