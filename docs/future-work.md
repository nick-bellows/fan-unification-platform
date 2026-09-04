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
- **npm advisory disposition.** On 2026-09-02, `npm audit --omit=dev` in `site/`
  reported 34 transitive findings (7 critical, 8 high, 18 moderate, 1 low)
  inside the latest available Evidence.dev 40.1.8 toolchain. The force-fix
  recommendation is a breaking downgrade to Evidence 29.0.3, not a safe patch.
  The current risk boundary is narrower—not eliminated—because CI builds a
  static site from trusted synthetic data with no deployed Node server, secrets,
  writes, or user-supplied records. Recheck each upstream release; replace the
  presentation layer if a maintained dependency path does not emerge.
- **Versioned lake keys.** Corrected files currently overwrite their lake
  object (replace semantics keep the warehouse clean), so an audit row can
  reference bytes that were later replaced. Content-hashed object keys with
  a latest-pointer would make the lake immutable at the cost of a more
  complex replace path.
- **Run provenance stamps.** Record git commit, generator-manifest hash, and
  seeds in `ops.pipeline_runs.parameters` so any warehouse state can be tied
  to exact inputs.
- **Supply-chain pinning (2026-09-04 external review).** GitHub Actions use
  mutable major tags rather than commit SHAs, and Python dependencies are
  lower-bounded without a lockfile, so CI installs are not byte-reproducible.
  Portfolio-acceptable, production blocker. The gitleaks download is now
  checksum-verified and container images digest-pinned; SHA-pinning ~10
  action refs and adding a lock/constraints file is the remaining step.
- **Dark-theme contrast.** Independent Axe checks found 4.46:1 (needs 4.5:1)
  on Evidence's blockquote text and pagination inputs in dark mode; light
  mode passes everywhere. The failing styles are Evidence-internal; fix via a
  theme override or upstream, and add a dark-mode pass to the Playwright
  WCAG test when done.
