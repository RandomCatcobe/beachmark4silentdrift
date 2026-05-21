# SilentDrift Case Bank

This directory is the self-contained case-bank layout described in `docs/case-bank-restructure/final-plan.md`.

Each case lives under `cases/<primary-scenario>/<case-id-slug>/` and contains public task files, a minimal probe client, and hidden oracle material.

Public evaluation packaging strips every `hidden/` directory without parsing file contents.

## Commands

```bash
python -m case_bank index build --out docs/case-bank/indexes/
python -m case_bank pack --src docs/case-bank/cases/ --out eval_package/
```

The generated indexes are views over `metadata.json` files and should be regenerated after any case metadata change.
