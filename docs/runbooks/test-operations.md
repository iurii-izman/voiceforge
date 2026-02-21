# Test Operations (alpha0.1)

## Flaky test policy

1. Any flaky test must be triaged within 24h.
2. Do not merge with silent flakes on required checks.
3. Temporary quarantine must be explicit in PR and linked to an issue.
4. Quarantined tests must have a removal deadline.

## CI baseline metrics

Track weekly:
1. Green rate for required checks.
2. Median CI duration.
3. Number of flaky incidents.
