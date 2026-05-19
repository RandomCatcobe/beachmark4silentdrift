# numpy_choice_shuffle_with_p

Probe-only record for `numpy.random.Generator.choice(..., p=..., shuffle=...)`.

The local flow ran NumPy 2.3.4 against 2.3.5. After ignoring version metadata in structured stdout, both versions showed the same behavior: `weighted_equal` is `true` and `unweighted_equal` is `false`.

This case is not packaged under the current old/new silent-drift criteria. It is recorded in `data/reports/python_candidate_flow_report.json` as `drop_reason=no_behavior_diff`.
