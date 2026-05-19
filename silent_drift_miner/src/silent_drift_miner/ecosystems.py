"""Ecosystem expansion gate checks."""
from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .curation import load_curated_case


@dataclass
class AdapterGateReport:
    target_ecosystem: str
    pass_: bool
    audited_python_cases: int
    required_python_cases: int
    checks: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> str:
        payload = asdict(self)
        payload["pass"] = payload.pop("pass_")
        return json.dumps(payload, indent=2, ensure_ascii=False)


@dataclass
class EcosystemEnvReport:
    target_ecosystem: str
    pass_: bool
    required_tools: list[dict[str, Any]] = field(default_factory=list)
    optional_tools: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> str:
        payload = asdict(self)
        payload["pass"] = payload.pop("pass_")
        return json.dumps(payload, indent=2, ensure_ascii=False)


ECOSYSTEM_TOOLS = {
    "jvm": {
        "required": ["java", "javac"],
        "optional": ["mvn", "gradle"],
    },
    "go": {
        "required": ["go"],
        "optional": [],
    },
    "js": {
        "required": ["node"],
        "optional": ["npm", "pnpm", "yarn"],
    },
    "php": {
        "required": ["php"],
        "optional": ["composer"],
    },
    "ruby": {
        "required": ["ruby"],
        "optional": ["bundle"],
    },
    "rust": {
        "required": ["cargo", "rustc"],
        "optional": [],
    },
    "dotnet": {
        "required": ["dotnet"],
        "optional": ["nuget"],
    },
    "python": {
        "required": ["python"],
        "optional": [],
    },
}


def evaluate_adapter_gates(
    packages_root: Path,
    audit_root: Path,
    target_ecosystem: str,
    required_python_cases: int = 3,
) -> AdapterGateReport:
    target = target_ecosystem.lower()
    audited_python_cases = count_audited_python_cases(packages_root, audit_root)
    checks = [
        {
            "name": "same_lifecycle_required",
            "pass": True,
            "message": "new adapters must use candidate -> reproduction -> curation -> oracle -> package -> audit",
        },
        {
            "name": "one_ecosystem_at_a_time",
            "pass": True,
            "message": "gate report targets exactly one ecosystem",
        },
    ]
    if target != "python":
        enough_python = audited_python_cases >= required_python_cases
        checks.append(
            {
                "name": "python_audited_real_cases",
                "pass": enough_python,
                "message": (
                    f"{audited_python_cases} audited Python case(s) found; "
                    f"{required_python_cases} required before enabling {target}"
                ),
            }
        )
    else:
        checks.append(
            {
                "name": "python_lifecycle_available",
                "pass": audited_python_cases > 0,
                "message": f"{audited_python_cases} audited Python case(s) found",
            }
        )
    return AdapterGateReport(
        target_ecosystem=target,
        pass_=all(item["pass"] for item in checks),
        audited_python_cases=audited_python_cases,
        required_python_cases=required_python_cases,
        checks=checks,
    )


def check_ecosystem_environment(target_ecosystem: str) -> EcosystemEnvReport:
    target = target_ecosystem.lower()
    tools = ECOSYSTEM_TOOLS.get(target, {"required": [], "optional": []})
    required = [_tool_status(tool) for tool in tools["required"]]
    optional = [_tool_status(tool) for tool in tools["optional"]]
    return EcosystemEnvReport(
        target_ecosystem=target,
        pass_=all(item["found"] for item in required),
        required_tools=required,
        optional_tools=optional,
    )


def count_audited_python_cases(packages_root: Path, audit_root: Path) -> int:
    count = 0
    if not audit_root.exists():
        return count
    for audit_path in sorted(audit_root.glob("*.json")):
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not audit.get("pass"):
            continue
        package_dir = _package_dir_from_audit(audit, packages_root)
        case_path = package_dir / "case.yaml"
        if not case_path.exists():
            continue
        try:
            case = load_curated_case(case_path)
        except Exception:
            continue
        ecosystem = getattr(case, "ecosystem", None) or "python"
        if ecosystem == "python" and _has_real_case_provenance(case):
            count += 1
    return count


def _package_dir_from_audit(audit: dict[str, Any], packages_root: Path) -> Path:
    raw_package = audit.get("package")
    if isinstance(raw_package, str) and raw_package:
        path = Path(raw_package)
        if path.is_absolute():
            return path
        if path.exists():
            return path
        return packages_root / path.name
    return packages_root


def _has_real_case_provenance(case) -> bool:
    return all(
        [
            case.keep,
            getattr(case, "source_url", None),
            getattr(case, "source_excerpt", None),
            getattr(case, "version_old", None),
            getattr(case, "version_new", None),
            getattr(case, "api_surface", None),
        ]
    )


def _tool_status(tool: str) -> dict[str, Any]:
    path = shutil.which(tool)
    return {
        "name": tool,
        "found": path is not None,
        "path": path,
    }
