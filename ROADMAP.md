# Roadmap

Last verified: 2026-09-15

## Status snapshot

| Field | Current state |
| --- | --- |
| Lifecycle | `PORTFOLIO-READY` — one maintainer checklist away from `FINAL` |
| Portfolio role | Primary data-engineering and identity-resolution evidence |
| Public presentation | Generated GitHub Pages dashboards at <https://nick-bellows.github.io/fan-unification-platform/> |
| Public claim | Synthetic pipeline run, measured linkage, dimensional warehouse, and CI-generated dashboards |
| Data boundary | Seeded fictional fan records; no real people or member data |
| External review | Two independent LLM reviews (2026-08-21, 2026-09-04): both ADVANCE; every verified finding fixed the same day |

2026-09-15: wording pass; no state change.

2026-09-30: recurring GitHub automation switched off, and an upstream
registry change now breaks every compose-dependent job. See
"Done 2026-09-30" — this one does change what the badges mean.

This repository already covers the highest-value Junior Data Engineer signals: heterogeneous ingestion, a Salesforce-shaped API, Prefect orchestration, incremental/idempotent loads, quarantine, explainable entity resolution, SCD2, data-quality checks, Redshift-oriented DDL, and BI marts. Do not replace that depth with a generic dashboard project.

## Completed milestone - three-minute data lineage tour

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

## Path to FINAL

Nothing in the repository blocks FINAL. Each remaining item is listed with
what it needs.

### Open items that gate FINAL

1. Open; needs the maintainer's time. Work the private completion checklist
   end to end: run the quickstart and narrate the system; rehearse the
   interview material (architecture and star schema from memory, the
   threshold-sweep and review-round stories, the headline numbers); upload
   social-preview images; decide the profile pin set; review the profile
   README.
2. Open; needs a decision. Declare completion. FINAL is a maintainer
   decision, not an automated one.
3. Open; needs a design decision. Accept or decline each optional engineering
   item below — an undecided item stays declined; this roadmap does not
   schedule work on its own.

### Optional engineering items (none required for FINAL)

1. Open; follows the completion declaration. **Flip lifecycle to
   `FINAL — maintenance only`** once the checklist is declared done: update
   this snapshot, the workspace records, and the change gate (new code only
   for household modeling or an observed weakness).
2. Open; needs a design decision. **Household modeling** — the single
   sanctioned engineering experiment: shared contact details are the dominant
   measured false-merge source (227 impure clusters on the 2026-09-04 seed-42
   run, from `ops.linkage_cluster_truth`; the tour displays the worst one).
   Lock the current generator, splits, metrics, and thresholds before the
   experiment; publish the result even if it does not beat the baseline.

### Done 2026-09-10

Closing hardening for the project (no behavior, number, or claim changed):

- **Supply-chain finishers.** Every GitHub Action ref is SHA-pinned with its
  version in a comment (Dependabot keeps them current); `constraints.txt`
  locks CI, the nightly run, and the mock image to one reviewed dependency
  set, generated with `uv pip compile` and regenerated deliberately.
- **Dark-mode contrast.** The 4.46:1 failure (Evidence's derived muted text
  on the blockquote background) is fixed with a `base-content-muted` theme
  override; the Playwright WCAG test now runs every reviewer route in both
  light and dark and asserts the shell is really in each theme.

### Done 2026-09-12 — finish-line review

A three-part code review (Python, SQL and site, CI and docs) with every
finding verified in the source before it was fixed; no published metric
changed:

- **Registry move.** Docker Hub stopped serving `minio/minio`, which turned
  the nightly red and would have failed every push; compose now pulls the
  same digest from quay.io.
- **Workflows fail when the pipeline fails.** The nightly piped through
  `tee` without pipefail; every workflow now runs bash with pipefail, the
  Pages deploy is serialized, and the pip cache is keyed on the lock.
- **Correctness.** `fan_360` rolls email engagement up by identity instead
  of by SCD2 version key (a version change used to zero a fan's email
  history); failed runs roll back before their status update; a
  non-numeric merch cell quarantines its row, not the file; a CRM reject
  without a modstamp holds the watermark; re-extracted CRM Ids supersede
  their older quarantine rows; phone `''` is now NULL in staging; merch
  gains a staging→fact reconcile and giving an orphan-opportunity warning.
- **Claims.** The tour's false-merge text now says what its SQL selects;
  stale counts and the pre-v3 review-band description were corrected.

All other deferred work (Redshift burst deployment, Prefect Cloud, scale
testing, lake-key versioning, adversarial CRM-timestamp fixtures) remains in
`docs/future-work.md` and is not silently accepted by this roadmap.

### Done 2026-09-30 — recurring automation off, compose blocked upstream

Owner decision, plus a defect found while carrying it out. No pipeline code,
metric, or published number changed.

- **The nightly cron is removed;** `nightly-pipeline` is `workflow_dispatch`
  only and its README badge is gone. On a maintenance-only repository an
  unattended daily run reports upstream rot rather than regressions in this
  code — which is exactly what it had been doing. The job body is unchanged,
  so the "operating the pipeline" evidence is still runnable on demand; the
  README now says "on demand" instead of "nightly" in both places it claimed
  a schedule.
- **Dependabot version updates are removed** (`.github/dependabot.yml`
  deleted). Action refs stay SHA-pinned; the note in "Done 2026-09-10" that
  Dependabot keeps them current is history, and no longer describes today —
  they are bumped by hand if this repository is reopened.
- **Known broken, not yet fixed: the MinIO image is unreachable.**
  `compose.yml` pins
  `quay.io/minio/minio@sha256:14cea493…`, which now returns
  `unauthorized: access to the requested resource is not authorized`. This is
  the second registry move for the same image: Docker Hub dropped
  `minio/minio` (fixed 2026-09-12 by moving to quay.io), and as of this check
  Docker Hub returns 404 for the repository and quay.io requires
  authentication, so there is no public pull path left. The nightly failed on
  it for six consecutive days (2026-09-25 through 2026-09-30). The push that
  carried this entry confirmed the blast radius: on `405f0a1`, `ci`'s
  `integration` job and `site`'s `build` job both fail at the same image
  pull, while `lint`, `typecheck`, `test`, `docker`, `gitleaks` and
  `terraform` all pass. `site`'s `deploy` is skipped rather than run, so the
  published Pages dashboards are the last good build and remain live and
  unaffected (logged-out HTTP 200 checked 2026-09-30).

  **This is not fixed here.** Replacing MinIO means choosing an S3-compatible
  substitute and re-running the integration suite and linkage eval to show
  the numbers are unchanged, which needs a working Docker daemon; it is not a
  pin bump. Until then, treat the `ci` badge as red for an environment reason
  and the unit/lint/typecheck evidence as unaffected — the failure is a
  registry pull, before any project code runs, and every job that does not
  need an object store is green. Tracked in `docs/future-work.md`.

  **FINAL should not be declared while this is red.** It is the one
  repository-side thing now standing between `PORTFOLIO-READY` and the
  maintainer's FINAL decision.

## Stop conditions

- Do not call the synthetic dataset production data or the validate-only AWS shape a deployed warehouse.
- Do not add dbt, a dashboard framework, or another cloud solely for a keyword.
- Do not tune on the held-out truth after reviewing results.
- Do not host a public database or orchestration control plane.
- After FINAL: no non-essential pushes while an application is under active review.

## Verification before changing status

Run the repository checks in `README.md`, rebuild the pipeline and site from a clean state, confirm generated evidence drift checks, inspect the published logged-out Pages site, and distinguish local/CI/AWS execution claims explicitly.
