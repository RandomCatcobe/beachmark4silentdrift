""".NET adapter entry points."""
from __future__ import annotations

from .adapter import (
    DotnetAdapter,
    DotnetEnvironmentDefinition,
    DotnetReproductionSpec,
    create_dotnet_reproduction_spec,
    load_dotnet_reproduction_spec,
    run_dotnet_reproduction_spec,
    write_dotnet_reproduction_spec,
)

__all__ = [
    "DotnetAdapter",
    "DotnetEnvironmentDefinition",
    "DotnetReproductionSpec",
    "create_dotnet_reproduction_spec",
    "load_dotnet_reproduction_spec",
    "run_dotnet_reproduction_spec",
    "write_dotnet_reproduction_spec",
]
