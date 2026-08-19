# Auto-merge threshold sweep

- Unifier version: 3 · seed 42 · 17487 records
- One Splink pass scored every pair >= 0.5; each row slices the same
  predictions at a different auto-merge threshold, against ground truth.

| variant | threshold | precision | recall | F1 | merged edges | pairs below |
| --- | --- | --- | --- | --- | --- | --- |
| deterministic | — | 0.8478 | 0.9336 | 0.8887 | 0 | 0 |
| full | 0.9 | 0.7779 | 0.9980 | 0.8743 | 31702 | 5109 |
| full | 0.95 | 0.7786 | 0.9980 | 0.8747 | 31519 | 5292 |
| full | 0.99 | 0.7898 | 0.9975 | 0.8816 | 31185 | 5626 |
| full | 0.999 | 0.7939 | 0.9970 | 0.8839 | 30934 | 5877 |
| full | 0.9999 | 0.8485 | 0.9644 | 0.9028 | 27558 | 9253 |

With many agreeing fields the Fellegi-Sunter posterior saturates near
1.0, so most false positives (households sharing email/surname/zip and
name+geography coincidences) still score above 0.999 — the useful
separation happens in the last decimal places. The default operating
point (`UnifyConfig.auto_merge_threshold`) was chosen from this table;
changing it means bumping UNIFIER_VERSION and regenerating this file
in the same commit.
