# Deterministic security scan policy

CI runs Bandit against the Python application and `pip-audit` against the
runtime and development dependency manifests. It preserves JSON reports even
if a scanner finds
an issue, publishes a per-run pull-request audit summary, and fails the job
when a scanner reports a finding.

Review findings before suppressing them. Any accepted exception must include a
specific justification, scope, and follow-up issue; avoid broad global
exclusions. Scanner databases and results can change over time, so compare
reports from the same workflow run when reproducing a finding.

Run locally from `pubg-analytics`:

```powershell
bandit -r app -ll
pip-audit -r requirements.txt
```

Machine-readable CI reports are uploaded as the `security-and-ops-reports`
workflow artifact; scan reports are generated per run rather than committed as
stale snapshots.
