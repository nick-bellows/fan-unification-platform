# Roadmap

Last verified: 2026-09-02

## Handoff snapshot

| Field | Current state |
| --- | --- |
| Lifecycle | `PORTFOLIO-READY` |
| Portfolio role | Primary data-engineering and identity-resolution evidence |
| Public presentation | Generated GitHub Pages dashboards at <https://nick-bellows.github.io/fan-unification-platform/> |
| Public claim | Synthetic pipeline run, measured linkage, dimensional warehouse, and CI-generated dashboards |
| Data boundary | Seeded fictional fan records; no real people or member data |

This repository already covers the highest-value Junior Data Engineer signals: heterogeneous ingestion, a Salesforce-shaped API, Prefect orchestration, incremental/idempotent loads, quarantine, explainable entity resolution, SCD2, data-quality checks, Redshift-oriented DDL, and BI marts. Do not replace that depth with a generic dashboard project.

## Completed milestone - five-minute data lineage tour

Delivered and locally verified from a fresh 5,000-person synthetic generation on 2026-09-02.
The site now includes a SQL-generated identity-to-mart trace, direct implementation links,
rendered-data assertions at the GitHub Pages base path, and an automated WCAG A/AA check.
The build hardening step also makes Evidence table scroll regions keyboard reachable. CI must
pass before the refreshed Pages artifact is treated as deployed.

Goal: make the existing implementation legible to a recruiter who will not run Docker or inspect every SQL model.

### Work

1. Add a `Start here` route to the existing Evidence site with two paths: data engineer and analytics consumer.
2. Build one generated, synthetic record trace:
   source rows -> validation/normalization -> deterministic/probabilistic match reasons -> canonical fan -> `dim_fan` history -> one fact -> one BI mart.
3. Surface reason codes, confidence/threshold, source-system lineage, and manual-review disposition without exposing raw generated datasets as a download requirement.
4. Link each step directly to the relevant flow, matcher, SQL model, quality check, and evaluation report on GitHub.
5. Add a pipeline-run panel showing freshness, quarantined rows, failed quality gates, and the exact git/data-generation provenance when that provenance is implemented.
6. Verify mobile layout, color contrast, keyboard navigation, loading performance, broken links, and logged-out access.

### Acceptance criteria

- The site is rebuilt from a real synthetic pipeline run; no hiring metric is hand-entered into presentation code.
- A reviewer can explain why a selected pair matched, how it became a golden record, and which warehouse rows depend on it in under three minutes.
- The deterministic baseline and probabilistic result remain shown side by side, including the negative result.
- Site CI fails if the generated data sources or claim-bearing summaries drift.
- The README screenshot and live route correspond to the current deployed site.

## Hosting decision

Keep GitHub Pages. It opens quickly, costs nothing, and the current CI-generated static architecture is itself evidence of a good publishing boundary. Do not expose PostgreSQL, the mock Salesforce API, Prefect UI, credentials, or a mutation endpoint merely to make the project feel interactive.

Vercel could host the same static output but adds no material hiring signal. Replit would require a second runtime/deployment shape and is not justified. A local Compose path remains the correct full-system demonstration.

## Next engineering milestone

Take one evidence-led item from `docs/future-work.md`: household modeling, because shared contact details are the dominant observed false-merge source. Lock the current generator, splits, metrics, and thresholds before the experiment; publish the result even if it does not improve the baseline.

Deferred work, including Redshift burst deployment, Prefect Cloud, scale testing, and lake-key versioning, remains in `docs/future-work.md` and is not silently approved by this roadmap.

## Stop conditions

- Do not call the synthetic dataset production data or the validate-only AWS shape a deployed warehouse.
- Do not add dbt, a dashboard framework, or another cloud solely for a keyword.
- Do not tune on the held-out truth after reviewing results.
- Do not host a public database or orchestration control plane.

## Verification before changing status

Run the repository checks in `README.md`, rebuild the pipeline and site from a clean state, confirm generated evidence drift checks, inspect the published logged-out Pages site, and distinguish local/CI/AWS execution claims explicitly.
