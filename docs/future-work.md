# Future work

The single home for deferred ideas. Recorded, not committed to.

- **Household modeling.** The dominant false-merge source is family members
  sharing an email. Rather than fighting it pairwise, model households as a
  first-class entity (shared address/surname clusters) and resolve persons
  within them. Highest-value next step the eval numbers point at.
- **Splink training coverage.** EM sessions leave some m-values partially
  trained (`last_name_f` warning); a third training block or
  term-frequency adjustments on surnames would tighten scores.
- **Review-band feedback loop.** Clerical decisions on
  `data/review/review_pairs.csv` could feed labeled pairs back as evaluation
  data. Never as training-on-truth — the honesty boundary stays.
- **Late-binding fact rebuilds.** `fact_email_engagement` keeps original
  fan_keys until rebuilt; a periodic scheduled rebuild (or key-remap pass)
  would keep it aligned with re-shaped clusters automatically.
- **Real Redshift burst deploy.** `infra/terraform` is validate-only; a
  short-lived apply + COPY-from-S3 smoke test on AWS credits would upgrade
  the claim from "designed for" to "ran on". Deliberately out of the $0
  scope.
- **Prefect Cloud.** The free tier would add hosted run history, automations,
  and alerting UI; the compose server keeps the repo self-contained. Either
  works; not both needed.
- **Scale test.** Generate 100k fans / ~350k records and measure: COPY
  throughput, Splink blocking counts, model runtimes — the numbers that
  decide when full-rebuild staging stops being right.
- **npm advisory disposition.** `npm audit --omit=dev` in `site/` reports ~31
  transitive advisories inside the Evidence.dev toolchain. Accepted for now:
  the output is a static site over synthetic data with no server runtime.
  Revisit on each Evidence upgrade; an audit gate would mostly fail on
  upstream noise we cannot patch.
- **Versioned lake keys.** Corrected files currently overwrite their lake
  object (replace semantics keep the warehouse clean), so an audit row can
  reference bytes that were later replaced. Content-hashed object keys with
  a latest-pointer would make the lake immutable at the cost of a more
  complex replace path.
- **Run provenance stamps.** Record git commit, generator-manifest hash, and
  seeds in `ops.pipeline_runs.parameters` so any warehouse state can be tied
  to exact inputs.
