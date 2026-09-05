# Roadmap

Last verified: 2026-09-04

## Handoff snapshot

| Field | Current state |
| --- | --- |
| Lifecycle | `PORTFOLIO-READY` — one author-side checklist away from `FINAL` |
| Portfolio role | Primary data-engineering and identity-resolution evidence |
| Public presentation | Generated GitHub Pages dashboards at <https://nick-bellows.github.io/fan-unification-platform/> |
| Public claim | Synthetic pipeline run, measured linkage, dimensional warehouse, and CI-generated dashboards |
| Data boundary | Seeded fictional fan records; no real people or member data |
| External review | Two independent LLM reviews (2026-08-21, 2026-09-04): both ADVANCE; every verified finding fixed the same day |

This repository already covers the highest-value Junior Data Engineer signals: heterogeneous ingestion, a Salesforce-shaped API, Prefect orchestration, incremental/idempotent loads, quarantine, explainable entity resolution, SCD2, data-quality checks, Redshift-oriented DDL, and BI marts. Do not replace that depth with a generic dashboard project.

## Completed milestone - five-minute data lineage tour

Delivered and locally verified from a fresh 5,000-person synthetic generation on 2026-09-02.
The site now includes a SQL-generated identity-to-mart trace, direct implementation links,
rendered-data assertions at the GitHub Pages base path, and an automated WCAG A/AA check.
The build hardening step also makes Evidence table scroll regions keyboard reachable. CI must
pass before the refreshed Pages artifact is treated as deployed.

Goal: make the existing implementation legible to a recruiter who will not run Docker or inspect every SQL model.

### Acceptance criteria (all held as of 2026-09-04)

- The site is rebuilt from a real synthetic pipeline run; no hiring metric is hand-entered into presentation code.
- A reviewer can explain why a selected pair matched, how it became a golden record, and which warehouse rows depend on it in under three minutes.
- The deterministic baseline and probabilistic result remain shown side by side, including the negative result.
- Site CI fails if the generated data sources or claim-bearing summaries drift.
- The README screenshot and live route correspond to the current deployed site.

## Completed milestone - external-review remediation (2026-09-04)

Two independent reviews (Codex, Cursor) were verified claim-by-claim against the
repo; every confirmed finding was fixed the same day:

- The tour's featured cluster is now verified **truth-pure at build time**
  (`ops.linkage_cluster_truth`, written only by the eval harness), and the tour
  gained a deliberately labeled **"Anatomy of a false merge"** section — the
  previous selection preferred the largest probabilistic cluster, which
  showcased a household false merge as one fan. Playwright asserts both; an
  unverifiable cluster fails the deploy.
- Correctness: the CRM watermark honors a rejected-row ceiling
  (`next_watermark`, boundary-tested); the incremental fact stores the natural
  campaign key; an integration stage pins persisted `identity.fan_xref` to the
  exact cluster partition the published metrics score.
- Honest presentation: right-censored crossover cohorts are excluded rather
  than charted as 0%; the homepage carries the measured linkage KPIs and names
  the retained 0.90 loss; the README quickstart uses the Linux-safe CI order.
- Supply chain: gitleaks download checksum-verified; mock image digest-pinned
  and non-root; `docs/ai-assisted-development.md` states the authorship and
  verification model.

## Hosting decision

Keep GitHub Pages. It opens quickly, costs nothing, and the current CI-generated static architecture is itself evidence of a good publishing boundary. Do not expose PostgreSQL, the mock Salesforce API, Prefect UI, credentials, or a mutation endpoint merely to make the project feel interactive.

Vercel could host the same static output but adds no material hiring signal. Replit would require a second runtime/deployment shape and is not justified. A local Compose path remains the correct full-system demonstration.

## Path to FINAL — remaining work, by owner

Nothing in the repository blocks FINAL. The remaining items split cleanly by
who must do them.

### Author — input or approval required (these gate FINAL)

1. Work the private completion checklist end to end: personally run the
   quickstart and narrate the system; rehearse the interview material
   (architecture and star schema from memory, the threshold-sweep and
   review-round stories, the headline numbers); upload social-preview images;
   decide the profile pin set; review the profile README.
2. Declare completion. FINAL is an author decision, not an automated one.
3. Approve or decline each optional engineering item below — silence means
   declined; this roadmap does not self-authorize work.

### Claude Code — executable on approval (none required for FINAL)

1. **Flip lifecycle to `FINAL — maintenance only`** once the author declares
   the checklist done: update this snapshot, the workspace records, and the
   change gate (new code only for household modeling or an observed weakness).
2. **Household modeling** — the single sanctioned engineering experiment:
   shared contact details are the dominant measured false-merge source (227
   impure clusters; the tour now displays the worst one). Lock the current
   generator, splits, metrics, and thresholds before the experiment; publish
   the result even if it does not beat the baseline.
3. **Supply-chain finishers** (~half day): SHA-pin GitHub Actions, add a
   Python lock/constraints file. Dispositioned in `docs/future-work.md`;
   portfolio-acceptable as-is.
4. **Dark-mode contrast fix** (Evidence-internal 4.46:1 vs 4.5:1 on
   blockquote/pagination) plus a dark-mode pass in the Playwright WCAG test.

All other deferred work (Redshift burst deployment, Prefect Cloud, scale
testing, lake-key versioning, adversarial CRM-timestamp fixtures) remains in
`docs/future-work.md` and is not silently approved by this roadmap.

## Stop conditions

- Do not call the synthetic dataset production data or the validate-only AWS shape a deployed warehouse.
- Do not add dbt, a dashboard framework, or another cloud solely for a keyword.
- Do not tune on the held-out truth after reviewing results.
- Do not host a public database or orchestration control plane.
- After FINAL: no non-essential pushes while an application is under active review.

## Verification before changing status

Run the repository checks in `README.md`, rebuild the pipeline and site from a clean state, confirm generated evidence drift checks, inspect the published logged-out Pages site, and distinguish local/CI/AWS execution claims explicitly.
