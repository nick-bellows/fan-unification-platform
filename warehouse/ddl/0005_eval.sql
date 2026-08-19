-- Linkage evaluation results (written by `fanuni evaluate`, read by the
-- dashboard). The eval harness is the ONLY thing that reads ground truth;
-- pipeline code never touches it.

CREATE TABLE IF NOT EXISTS ops.linkage_eval (
  id                 bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  evaluated_at       timestamptz NOT NULL DEFAULT now(),
  unifier_version    text NOT NULL,
  variant            text NOT NULL,      -- deterministic | full
  pair_precision     real NOT NULL,
  pair_recall        real NOT NULL,
  pair_f1            real NOT NULL,
  tp                 bigint NOT NULL,
  fp                 bigint NOT NULL,
  fn                 bigint NOT NULL,
  predicted_clusters integer NOT NULL,
  true_entities      integer NOT NULL,
  review_band        integer NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ops.linkage_eval_tags (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  evaluated_at    timestamptz NOT NULL DEFAULT now(),
  unifier_version text NOT NULL,
  variant         text NOT NULL,
  tag             text NOT NULL,
  true_pairs      integer NOT NULL,
  pair_recall     real,
  fp_pairs        integer NOT NULL
);
