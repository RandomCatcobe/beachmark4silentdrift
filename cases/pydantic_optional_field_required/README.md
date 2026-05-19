# pydantic_optional_field_required

Real Python silent-drift candidate for `pydantic.BaseModel` field required semantics.

Source: https://pydantic.dev/docs/validation/2.11/get-started/migration/

The migration guide says: "A field annotated as typing.Optional[T] will be required, and will allow for a value of None. It does not mean that the field has a default value of None. (This is a breaking change from V1.)"

The hand-authored client defines:

```python
class Profile(BaseModel):
    nickname: Optional[str]
```

Reproduction commands:

```bash
py310="$(uv python find 3.10)"
silent-drift-miner reproduce plan --candidate-id pydantic-optional-field-required --library pydantic --old-version 1.10.15 --new-version 2.7.4 --client-file cases/pydantic_optional_field_required/client.py --old-python-executable "$py310" --new-python-executable "$py310" --out data/reproductions/pydantic-optional-field-required/spec.json
silent-drift-miner reproduce run --spec data/reproductions/pydantic-optional-field-required/spec.json --out data/reproductions/pydantic-optional-field-required --install --venv-root .repro_venvs --build-timeout 300 --timeout 60
```

Observed diff from `attempt_001`:

- old `pydantic==1.10.15`: model creation succeeds with `{"nickname": null}`
- new `pydantic==2.7.4`: model creation fails with `nickname` missing

This case is deterministic: no network, clock, randomness, or filesystem input is used by the client.
