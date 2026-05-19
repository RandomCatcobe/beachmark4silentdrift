# pydantic_field_alias_none

Real Python silent-drift candidate for `pydantic` field alias metadata.

Source: https://pydantic.dev/docs/validation/2.11/get-started/migration/

The migration guide says: "In Pydantic V1, the alias property returns the field's name when no alias is set. In Pydantic V2, this behavior has changed to return None when no alias is set."

The hand-authored client reads `field.alias` for an unaliased model field.

Reproduction commands:

```bash
py310="$(uv python find 3.10)"
silent-drift-miner reproduce plan --candidate-id pydantic-field-alias-none --library pydantic --old-version 1.10.15 --new-version 2.7.4 --client-file cases/pydantic_field_alias_none/client.py --old-python-executable "$py310" --new-python-executable "$py310" --out data/reproductions/pydantic-field-alias-none/spec.json
silent-drift-miner reproduce run --spec data/reproductions/pydantic-field-alias-none/spec.json --out data/reproductions/pydantic-field-alias-none --install --venv-root .repro_venvs --build-timeout 300 --timeout 60
```

Observed diff from `attempt_001`:

- old `pydantic==1.10.15`: `field.alias == "name"`
- new `pydantic==2.7.4`: `field.alias is None`

This case is deterministic: no network, clock, randomness, or filesystem input is used by the client.
