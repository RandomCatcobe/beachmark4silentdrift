"""PHP adapter entry points."""
from __future__ import annotations

from .adapter import (
    PhpAdapter,
    PhpEnvironmentDefinition,
    PhpReproductionSpec,
    create_php_reproduction_spec,
    load_php_reproduction_spec,
    run_php_reproduction_spec,
    write_php_reproduction_spec,
)

__all__ = [
    "PhpAdapter",
    "PhpEnvironmentDefinition",
    "PhpReproductionSpec",
    "create_php_reproduction_spec",
    "load_php_reproduction_spec",
    "run_php_reproduction_spec",
    "write_php_reproduction_spec",
]
