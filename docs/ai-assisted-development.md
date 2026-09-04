# AI-assisted development

Factual note, kept short on purpose.

**What was used.** This repository was built with Claude (Anthropic) as a
pair programmer inside Claude Code, working from an approved written plan
with four author-locked decisions (warehouse emulation strategy, BI layer,
no-dbt transform layer, repo name). AI assistance covered code generation,
debugging, and test writing. No LLM appears anywhere in the runtime path —
the matcher is classical Fellegi–Sunter statistics.

**What the author owns.** Scope, the locked decisions, the honesty rules the
repo enforces on itself (synthetic data only; the pipeline never reads ground
truth; metric changes land atomically with regenerated eval reports), review
of external findings, and every merge.

**How correctness is established independently of authorship.** Nothing in
this repo asks to be trusted on the author's or the tool's word:

- The linkage metrics regenerate from committed code and seeds
  (`fanuni evaluate`), run nightly in CI, and are floor-gated.
- Quality gates are themselves tested by breaking the data and watching them
  fail (`tests/integration/test_transform.py`).
- The published dashboards are built in CI from a real pipeline run, with an
  empty-dashboard gate and rendered-page assertions.
- Defects found during development — and by two external LLM reviews on
  2026-08-21 and 2026-09-04 — are recorded in `docs/how-it-was-built.md` and
  fixed in commits that name their source.

The author's working claim is not "written unaided" but "understood,
verified, and defensible line by line" — which is what an interview can and
should test directly.
