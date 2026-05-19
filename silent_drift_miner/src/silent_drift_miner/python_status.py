"""Python lifecycle completion status."""
from __future__ import annotations

import json
import py_compile
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .audit import audit_package
from .curation import load_curated_case
from .schema import ARTIFACT_SCHEMA_VERSION, utc_now_iso


@dataclass
class PythonCaseStatus:
    case_id: str
    candidate_id: str
    library: str
    version_old: str
    version_new: str
    source_url: str
    package_dir: str
    audit_pass: bool
    client_compiles: bool
    reproduction_result_exists: bool
    candidate_manifest_exists: bool
    readme_exists: bool


@dataclass
class PythonStatusReport:
    ecosystem: str
    pass_: bool
    audited_case_count: int
    min_audited_cases: int
    cases: list[PythonCaseStatus]
    checks: list[dict[str, Any]]
    findings: list[dict[str, str]]
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)

    def to_json(self) -> str:
        payload = asdict(self)
        payload["pass"] = payload.pop("pass_")
        return json.dumps(payload, indent=2, ensure_ascii=False)


def build_python_status_report(
    cases_root: Path,
    packages_root: Path,
    min_audited_cases: int = 3,
) -> PythonStatusReport:
    findings: list[dict[str, str]] = []
    cases: list[PythonCaseStatus] = []

    for package_dir in sorted(path for path in packages_root.glob("*") if path.is_dir()):
        case_path = package_dir / "case.yaml"
        if not case_path.exists():
            continue
        case = load_curated_case(case_path)
        if case.ecosystem and case.ecosystem != "python":
            continue

        audit = audit_package(package_dir)
        candidate = _load_candidate_manifest(cases_root / case.case_id / "candidate.json")
        client_path = cases_root / case.case_id / str(candidate.get("client_file", "client.py"))
        client_compiles = _client_compiles(client_path)
        reproduction_result = package_dir / "reproduction_result.json"
        readme_exists = (cases_root / case.case_id / "README.md").exists()
        candidate_manifest_exists = bool(candidate)

        status = PythonCaseStatus(
            case_id=case.case_id,
            candidate_id=case.candidate_id,
            library=str(candidate.get("library", "")),
            version_old=case.version_old or "",
            version_new=case.version_new or "",
            source_url=case.source_url or "",
            package_dir=str(package_dir),
            audit_pass=bool(audit.get("pass")),
            client_compiles=client_compiles,
            reproduction_result_exists=reproduction_result.exists(),
            candidate_manifest_exists=candidate_manifest_exists,
            readme_exists=readme_exists,
        )
        cases.append(status)
        _append_case_findings(status, audit, findings)

    audited_case_count = sum(1 for case in cases if _case_is_complete(case))
    checks = [
        {
            "name": "min_audited_real_cases",
            "pass": audited_case_count >= min_audited_cases,
            "message": f"{audited_case_count} complete audited Python case(s); {min_audited_cases} required",
        },
        {
            "name": "all_packages_audit_pass",
            "pass": all(case.audit_pass for case in cases),
            "message": "all discovered Python packages pass live audit",
        },
        {
            "name": "all_case_sources_present",
            "pass": all(case.candidate_manifest_exists and case.readme_exists for case in cases),
            "message": "each package has matching cases/<case_id>/candidate.json and README.md",
        },
        {
            "name": "all_clients_compile",
            "pass": all(case.client_compiles for case in cases),
            "message": "each hand-authored client.py compiles",
        },
    ]
    return PythonStatusReport(
        ecosystem="python",
        pass_=all(check["pass"] for check in checks) and not findings,
        audited_case_count=audited_case_count,
        min_audited_cases=min_audited_cases,
        cases=cases,
        checks=checks,
        findings=findings,
    )


def _load_candidate_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _client_compiles(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            py_compile.compile(str(path), cfile=str(Path(tmp) / "client.pyc"), doraise=True)
    except Exception:
        return False
    return True


def _case_is_complete(case: PythonCaseStatus) -> bool:
    return all(
        [
            case.audit_pass,
            case.client_compiles,
            case.reproduction_result_exists,
            case.candidate_manifest_exists,
            case.readme_exists,
            case.library,
            case.version_old,
            case.version_new,
            case.source_url,
        ]
    )


def _append_case_findings(
    status: PythonCaseStatus,
    audit: dict[str, Any],
    findings: list[dict[str, str]],
) -> None:
    if not status.audit_pass:
        for finding in audit.get("findings", []):
            findings.append({
                "case_id": status.case_id,
                "check": str(finding.get("check", "audit")),
                "message": str(finding.get("message", "audit failed")),
            })
    for field in [
        "client_compiles",
        "reproduction_result_exists",
        "candidate_manifest_exists",
        "readme_exists",
    ]:
        if not getattr(status, field):
            findings.append({
                "case_id": status.case_id,
                "check": field,
                "message": f"{field} is false",
            })
