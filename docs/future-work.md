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
