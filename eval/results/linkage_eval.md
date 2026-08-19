# Linkage evaluation

- Unifier version: 3
- Evaluated: 2026-08-19T14:55:29.880521+00:00
- Records: 17487 · Review band: 3376 pairs
- Config: {"auto_merge_threshold": 0.9999, "review_threshold": 0.999, "em_max_pairs": 4000000.0, "seed": 42}

| variant | precision | recall | F1 | TP | FP | FN | clusters | true entities |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic | 0.8478 | 0.9336 | 0.8887 | 28717 | 5154 | 2042 | 5307 | 5000 |
| full | 0.8485 | 0.9644 | 0.9028 | 29664 | 5295 | 1095 | 5031 | 5000 |

## Recall by mess tag

| tag | true pairs | det recall | full recall | det FP | full FP |
| --- | --- | --- | --- | --- | --- |
| case | 4946 | 0.9414 | 0.9687 | 798 | 827 |
| diacritics | 1431 | 0.9196 | 0.9623 | 937 | 962 |
| late_arrival | 611 | 0.9836 | 0.9935 | 108 | 110 |
| missing_dob | 1199 | 0.9475 | 0.9733 | 233 | 233 |
| name_format | 6466 | 0.9692 | 0.9858 | 1434 | 1451 |
| nickname | 7739 | 0.9315 | 0.9610 | 1153 | 1180 |
| resubscribed_new_email | 377 | 0.6048 | 0.7427 | 20 | 22 |
| shared_email | 2796 | 0.7346 | 0.7650 | 2247 | 2290 |
| stale_email | 2207 | 0.7367 | 0.8106 | 397 | 397 |
| typo | 3644 | 0.7300 | 0.9495 | 470 | 582 |
| within_source_dup | 301 | 0.9635 | 0.9867 | 35 | 35 |
