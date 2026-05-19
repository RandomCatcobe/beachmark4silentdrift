# polars_cast_strict_float_to_int

Probe-only record for `polars.Expr.cast(..., strict=True)` from float to integer.

The local flow ran Polars 1.0.0 against 1.30.0. After ignoring version metadata in structured stdout, both versions returned `[1, 5]`.

This case is not packaged under the current old/new silent-drift criteria. It is recorded in `data/reports/python_candidate_flow_report.json` as `drop_reason=no_behavior_diff`.
