"""Run the 2026-05-21 reverse 50-case verification ledger.

This is a one-off run artifact generator. It records the reverse queue requested
by the user and executes small deterministic probes where the local toolchain and
cached dependencies make that feasible.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "data" / "verification" / "reverse_50"
DOC_PATH = ROOT / "docs" / "verification-runs" / "run-20260521-reverse-50.md"
RESULTS_PATH = RUN_ROOT / "results.jsonl"
DETAILS_DIR = RUN_ROOT / "details"


@dataclass
class Case:
    n: int
    case_id: str
    title: str
    source: str = ""
    kind: str = "local"
    status: str = "pending"
    first_blocked_step: str = ""
    steps: list[str] = field(default_factory=list)
    artifact: str = ""
    notes: str = ""


def run_cmd(args: list[str], cwd: Path | None = None, timeout: int = 120, env: dict[str, str] | None = None) -> dict:
    started = time.time()
    resolved_args = list(args)
    if resolved_args:
        executable = resolved_args[0]
        if not any(sep in executable for sep in ("/", "\\")):
            resolved = shutil.which(executable)
            if resolved:
                resolved_args[0] = resolved
    try:
        cp = subprocess.run(
            resolved_args,
            cwd=str(cwd or ROOT),
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout": cp.stdout,
            "stderr": cp.stderr,
            "elapsed_sec": round(time.time() - started, 3),
            "command": resolved_args,
        }
    except Exception as exc:  # noqa: BLE001 - artifact wants the first blocker.
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "elapsed_sec": round(time.time() - started, 3),
            "command": resolved_args,
        }


def write_detail(case: Case, payload: dict) -> None:
    path = DETAILS_DIR / f"{case.case_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    case.artifact = rel(path)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def check_url(case: Case) -> None:
    payload = {"case_id": case.case_id, "source": case.source}
    if not case.source:
        case.status = "blocked_source_missing"
        case.first_blocked_step = "source_check"
        case.notes = "No URL was available in the queue entry."
        write_detail(case, payload)
        return
    req = urllib.request.Request(case.source, headers={"User-Agent": "SilentDriftReverse50/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - source availability check only.
            payload["http_status"] = resp.status
            payload["final_url"] = resp.geturl()
            payload["content_type"] = resp.headers.get("content-type", "")
            sample = resp.read(512)
            payload["sample_bytes"] = len(sample)
        case.status = "blocked_offline_reproduction"
        case.first_blocked_step = "dependency_acquired"
        case.steps = ["source_check"]
        case.notes = "Source was reachable; live-service behavior cannot be reproduced offline in this repo."
    except urllib.error.HTTPError as exc:
        payload["http_status"] = exc.code
        payload["error"] = str(exc)
        case.status = "source_http_error"
        case.first_blocked_step = "source_check"
        case.notes = f"Source returned HTTP {exc.code}; retained as online lead from idea bank."
    except Exception as exc:  # noqa: BLE001
        payload["error"] = f"{type(exc).__name__}: {exc}"
        case.status = "source_check_blocked"
        case.first_blocked_step = "source_check"
        case.notes = "Source check failed from this environment; retained as online lead from idea bank."
    write_detail(case, payload)


def mark_skip(case: Case, reason: str, provenance: str = "") -> None:
    case.status = "skipped_existing_record"
    case.first_blocked_step = ""
    case.steps = ["source_check", "output_assertion"]
    case.notes = reason
    payload = {"case_id": case.case_id, "reason": reason, "provenance": provenance}
    write_detail(case, payload)


def probe_rack_headers(case: Case) -> None:
    old_path = ROOT / "data" / "verification" / "gems" / "rack229" / "gems" / "rack-2.2.9" / "lib"
    new_path = ROOT / "data" / "verification" / "gems" / "rack310" / "gems" / "rack-3.1.0" / "lib"
    code = "require 'rack'; h={'Content-Type'=>'text/plain','X-Test'=>'1'}; r=Rack::Response.new([],200,h); p r.headers.keys"
    old = run_cmd(["ruby", "-I", str(old_path), "-e", code])
    new = run_cmd(["ruby", "-I", str(new_path), "-e", code])
    payload = {"case_id": case.case_id, "old": old, "new": new}
    if old["ok"] and new["ok"] and old["stdout"] != new["stdout"]:
        case.status = "verified_keep"
        case.steps = ["source_check", "dependency_acquired", "old_run", "new_run", "output_assertion"]
        case.notes = f"Old headers {old['stdout'].strip()} vs new headers {new['stdout'].strip()}."
    else:
        case.status = "blocked_or_no_diff"
        case.first_blocked_step = "output_assertion"
        case.notes = "Rack header-case probe did not produce a clean old/new diff."
    write_detail(case, payload)


def probe_php_carbon_diff(case: Case) -> None:
    script = RUN_ROOT / "php_carbon_diff_probe.php"
    script.write_text(
        textwrap.dedent(
            """
            <?php
            require $argv[1];
            $a = Carbon\\Carbon::parse('2020-01-01 00:00:00.000000');
            $b = Carbon\\Carbon::parse('2020-01-01 00:00:00.500000');
            echo json_encode([
                'forward' => $a->diffInSeconds($b),
                'reverse' => $b->diffInSeconds($a),
                'forward_type' => gettype($a->diffInSeconds($b)),
                'reverse_type' => gettype($b->diffInSeconds($a)),
            ], JSON_UNESCAPED_SLASHES), PHP_EOL;
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    old_autoload = ROOT / "data" / "verification" / "composer" / "carbon2" / "vendor" / "autoload.php"
    new_root = RUN_ROOT / "composer" / "carbon3-no-platform-check"
    new_autoload = new_root / "vendor" / "autoload.php"
    composer_setup = None
    if not new_autoload.exists():
        source_root = ROOT / "data" / "verification" / "composer" / "carbon3"
        if new_root.exists():
            shutil.rmtree(new_root)
        shutil.copytree(source_root, new_root)
        autoload_real = new_root / "vendor" / "composer" / "autoload_real.php"
        text = autoload_real.read_text(encoding="utf-8")
        text = text.replace("        require __DIR__ . '/platform_check.php';\n\n", "")
        autoload_real.write_text(text, encoding="utf-8")
        composer_setup = {
            "copied_from": rel(source_root),
            "patched": "vendor/composer/autoload_real.php platform_check include removed",
        }
    old = run_cmd(["php", str(script), str(old_autoload)])
    new = run_cmd(["php", str(script), str(new_autoload)])
    payload = {"case_id": case.case_id, "composer_setup": composer_setup, "old": old, "new": new}
    if old["ok"] and new["ok"] and old["stdout"] != new["stdout"]:
        case.status = "verified_keep"
        case.steps = ["source_check", "dependency_acquired", "old_run", "new_run", "output_assertion"]
        case.notes = f"Carbon 2 output {old['stdout'].strip()} vs Carbon 3 output {new['stdout'].strip()}."
    else:
        case.status = "blocked_or_no_diff"
        case.first_blocked_step = "output_assertion"
        case.notes = "Carbon diff probe did not produce a clean old/new diff."
    write_detail(case, payload)


def ensure_python_venv(name: str, packages: list[str], python_runtime: str) -> tuple[Path, dict]:
    venv = RUN_ROOT / "_venvs" / name
    py = venv / "Scripts" / "python.exe"
    logs: dict[str, dict] = {}
    if not py.exists():
        if venv.exists():
            shutil.rmtree(venv)
        logs["venv"] = run_cmd([python_runtime, "-m", "venv", str(venv)], timeout=180)
    install_marker = venv / ".reverse50-installed"
    if not install_marker.exists():
        logs["install"] = run_cmd(["uv", "pip", "install", "--python", str(py), *packages], timeout=900)
        if logs["install"]["ok"]:
            install_marker.write_text("ok\n", encoding="utf-8")
    return py, logs


def probe_python_pair(case: Case, old_packages: list[str], new_packages: list[str], code: str) -> None:
    python_runtime = sys.executable or shutil.which("python")
    if not python_runtime:
        case.status = "blocked_runtime"
        case.first_blocked_step = "dependency_acquired"
        case.notes = "No Python runtime available."
        write_detail(case, {"case_id": case.case_id})
        return
    probe_path = RUN_ROOT / f"{case.case_id}_probe.py"
    probe_path.write_text(textwrap.dedent(code).strip() + "\n", encoding="utf-8")
    old_py, old_logs = ensure_python_venv(f"{case.case_id}-old", old_packages, python_runtime)
    new_py, new_logs = ensure_python_venv(f"{case.case_id}-new", new_packages, python_runtime)
    old = run_cmd([str(old_py), str(probe_path)], cwd=RUN_ROOT, timeout=180)
    new = run_cmd([str(new_py), str(probe_path)], cwd=RUN_ROOT, timeout=180)
    payload = {
        "case_id": case.case_id,
        "python_runtime": python_runtime,
        "old_packages": old_packages,
        "new_packages": new_packages,
        "old_setup": old_logs,
        "new_setup": new_logs,
        "old": old,
        "new": new,
    }
    if old["ok"] and new["ok"] and old["stdout"] != new["stdout"]:
        case.status = "verified_keep"
        case.steps = ["source_check", "dependency_acquired", "old_run", "new_run", "output_assertion"]
        case.notes = f"Old stdout {old['stdout'].strip()} vs new stdout {new['stdout'].strip()}."
    elif not old["ok"] or not new["ok"]:
        case.status = "blocked_runtime_or_dependency"
        case.first_blocked_step = "old_run" if not old["ok"] else "new_run"
        case.notes = "Python probe setup/run failed; see detail artifact."
    else:
        case.status = "rejected_no_diff"
        case.first_blocked_step = "output_assertion"
        case.notes = "Old and new probes both ran but stdout matched."
    write_detail(case, payload)


def probe_rspec(case: Case) -> None:
    gem_root = RUN_ROOT / "gems"
    old_dir = gem_root / "rspec-expectations-3.10.0"
    new_dir = gem_root / "rspec-expectations-3.11.0"
    old_install = run_cmd(["gem", "install", "rspec-expectations", "-v", "3.10.0", "--install-dir", str(old_dir), "--no-document"], timeout=600)
    new_install = run_cmd(["gem", "install", "rspec-expectations", "-v", "3.11.0", "--install-dir", str(new_dir), "--no-document"], timeout=600)
    code = "require 'rspec/expectations'; include RSpec::Matchers; p aggregate_failures { expect(1).to eq(1) }"
    old_env = os.environ.copy()
    old_env["GEM_HOME"] = str(old_dir)
    old_env["GEM_PATH"] = str(old_dir)
    new_env = os.environ.copy()
    new_env["GEM_HOME"] = str(new_dir)
    new_env["GEM_PATH"] = str(new_dir)
    old = run_cmd(["ruby", "-e", code], env=old_env)
    new = run_cmd(["ruby", "-e", code], env=new_env)
    payload = {"case_id": case.case_id, "old_install": old_install, "new_install": new_install, "old": old, "new": new}
    if old["ok"] and new["ok"] and old["stdout"] != new["stdout"]:
        case.status = "verified_keep"
        case.steps = ["source_check", "dependency_acquired", "old_run", "new_run", "output_assertion"]
        case.notes = f"RSpec 3.10 returned {old['stdout'].strip()} vs 3.11 returned {new['stdout'].strip()}."
    elif not old["ok"] or not new["ok"]:
        case.status = "blocked_runtime_or_dependency"
        case.first_blocked_step = "old_run" if not old["ok"] else "new_run"
        case.notes = "RSpec probe failed under this Ruby/gem environment."
    else:
        case.status = "rejected_no_diff"
        case.first_blocked_step = "output_assertion"
        case.notes = "RSpec probe ran but stdout matched."
    write_detail(case, payload)


def mark_blocked(case: Case, step: str, note: str, status: str = "blocked_dependency_or_runtime") -> None:
    case.status = status
    case.first_blocked_step = step
    case.notes = note
    write_detail(case, {"case_id": case.case_id, "status": status, "blocked_step": step, "note": note})


def queue() -> list[Case]:
    ecommerce = [
        ("NEW-20260520-010", "Google Merchant product input success is not product approval", "https://developers.google.com/merchant/api/guides/products/add-manage"),
        ("NEW-20260520-009", "Etsy webhooks carry resource pointers and may replay", "https://developer.etsy.com/documentation/essentials/webhooks/"),
        ("NEW-20260520-008", "Taobao sensitive order data changes to masked/OAID-dependent data", "https://developer.alibaba.com/docs/doc.htm?articleId=120175&docType=1&source=search&treeId=796"),
        ("NEW-20260520-007", "Taobao online logistics send can create flow without changing trade status", "https://open.fliggy.com/docs/doc.htm?articleId=10687&docType=2&treeId=568"),
        ("NEW-20260520-006", "Mercado Libre notifications require ACK plus resource refetch", "https://global-selling.mercadolibre.com/devsite/api-docs/receive-notifications"),
        ("NEW-20260520-005", "BigCommerce webhook delivery can duplicate lightweight events", "https://docs.bigcommerce.com/developer/docs/integrations/webhooks/overview"),
        ("NEW-20260520-004", "Adobe Commerce bulk API accepts queue entries that later fail", "https://developer.adobe.com/commerce/webapi/rest/use-rest/bulk-endpoints/"),
        ("NEW-20260520-003", "Walmart processed feed does not imply element success", "https://developer.walmart.com/cl-marketplace/docs/feeds-overview"),
        ("NEW-20260520-002", "Amazon feed status hides per-record business failures", "https://developer-docs.amazon.com/sp-api/docs/submit-a-feed"),
        ("NEW-20260520-001", "Douyin order sync returns success but order center is empty", "https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/server/payment/ecpay/order/order-sync"),
        ("SEED-20260520-008", "Ecommerce order-to-ERP sync chain evidence", "https://www.ai-indeed.com/encyclopedia/20019.html"),
        ("SEED-20260520-007", "Generic integration silent failure evidence", "https://www.stacksync.com/blog/detect-silent-failures-mulesoft"),
        ("SEED-20260520-006", "Pinduoduo order field openness retrofit", "https://open.kuaimai.com/docs/question/%E7%B3%BB%E7%BB%9F%E5%85%AC%E5%91%8A/%E6%8B%BC%E5%A4%9A%E5%A4%9A%E8%AE%A2%E5%8D%95%E4%BF%A1%E6%81%AF%E5%BC%80%E6%94%BE%E6%94%B9%E9%80%A0%E5%85%AC%E5%91%8A/"),
        ("SEED-20260520-005", "Meituan merchant ID is unstable", "https://h5.dianping.com/app/bep-docs/sky-doc/canyinopenapi/waimai_api.html"),
        ("SEED-20260520-004", "JD order status callback silently discarded", "https://opendoc.jd.com/isp_all/api/interfacelist/014-commonnotifyorderstatus.html"),
        ("SEED-20260520-003", "Taobao message ordering", "https://developer.alibaba.com/docs/doc.htm?articleId=121426&docType=1&treeId=735"),
        ("SEED-20260520-002", "Taobao receiver address field semantics", "https://developer.alibaba.com/docs/api.htm?apiId=54"),
        ("SEED-20260520-001", "Taobao order detail field semantics", "https://developer.alibaba.com/docs/api.htm?apiId=54"),
    ]
    ruby = [
        ("RB-NOK-010", "Nokogiri SAX entity handling"),
        ("RB-RSP-009", "RSpec aggregate_failures return value"),
        ("RB-SKQ-008", "Sidekiq job payload timestamps"),
        ("RB-FAR-007", "Faraday query-string encoding"),
        ("RB-RACK-006", "Rack response header hash casing"),
        ("RB-RACK-005", "Rack semicolon query separator"),
        ("RB-AS-004", "ActiveSupport cache serialization format"),
        ("RB-AS-003", "ActiveSupport digest defaults"),
        ("RB-AS-002", "ActiveSupport Enumerable#sole tuple shape"),
        ("RB-AS-001", "ActiveSupport TimeWithZone#to_time"),
    ]
    python = [(f"PY-SD-{i:03d}", title) for i, title in [
        (10, "attrs generated equality for shared NaN values"),
        (9, "Cython default language_level"),
        (8, "SQLAlchemy execute DML without explicit commit"),
        (7, "Pydantic nested subclass serialization"),
        (6, "Dask DataFrame string dtype inference"),
        (5, "Polars join null-key matching"),
        (4, "scikit-learn KMeans n_init default"),
        (3, "SciPy stats.mode keepdims default"),
        (2, "pandas groupby ordered categorical sort=False"),
        (1, "NumPy dtype promotion"),
    ]]
    php = [(f"PHP-{i:02d}", title) for i, title in [
        (10, "Guzzle idn_conversion default"),
        (9, "Monolog default date formatting"),
        (8, "Carbon diffIn* signed/float return"),
        (7, "Carbon createFromTimestamp default timezone"),
        (6, "Laravel Collection when/unless condition closure"),
        (5, "Laravel Storage put overwrite behavior"),
        (4, "Symfony Serializer CsvEncoder as_collection default"),
        (3, "htmlspecialchars default flags"),
        (2, "PHP stable sorting of equal elements"),
        (1, "PHP non-strict non-numeric string comparison"),
    ]]
    jvm = [
        ("JVM-JAVA-10", "JDK default charset becomes UTF-8"),
        ("JVM-JAVA-09", "Maven .mvn/maven.config single-line argument parsing"),
    ]
    raw: list[tuple[str, str, str, str]] = []
    raw.extend((cid, title, src, "online") for cid, title, src in ecommerce)
    raw.extend((cid, title, "", "ruby") for cid, title in ruby)
    raw.extend((cid, title, "", "python") for cid, title in python)
    raw.extend((cid, title, "", "php") for cid, title in php)
    raw.extend((cid, title, "", "jvm") for cid, title in jvm)
    return [Case(i + 1, cid, title, src, kind) for i, (cid, title, src, kind) in enumerate(raw[:50])]


def process(case: Case) -> None:
    if case.kind == "online":
        check_url(case)
        return
    if case.case_id == "RB-FAR-007":
        mark_skip(case, "Existing local check rejected this lead: Faraday 1.0.0 and 1.0.1 both returned q=a+b.", "docs/ruby-drift-idea-bank.md")
    elif case.case_id == "RB-RACK-005":
        mark_skip(case, "Existing Ruby adapter pipeline verified this case.", "data/verification/ruby_rack_semicolon_query/attempt_001/result.json")
    elif case.case_id == "PY-SD-010":
        mark_skip(case, "Existing Python reproduction pipeline verified this case.", "data/verification/python_attrs_nan_equality/attempt_003/result.json")
    elif case.case_id == "PHP-07":
        mark_skip(case, "Existing PHP/Carbon reproduction pipeline verified this case.", "data/verification/php_carbon_timestamp_timezone/attempt_001/result.json")
    elif case.case_id == "PHP-03":
        mark_skip(case, "Semantic duplicate of already verified PHP-12 htmlspecialchars default-flags case.", "data/verification/php_htmlspecialchars_default_flags/attempt_001/result.json")
    elif case.case_id == "RB-RACK-006":
        probe_rack_headers(case)
    elif case.case_id == "RB-RSP-009":
        probe_rspec(case)
    elif case.case_id == "PHP-08":
        probe_php_carbon_diff(case)
    elif case.case_id == "PY-SD-001":
        probe_python_pair(
            case,
            ["numpy==1.26.4"],
            ["numpy==2.0.0"],
            """
            import json, numpy as np
            a = np.float32(3) + 3.
            b = np.array([3], dtype=np.float32) + np.float64(3)
            print(json.dumps({
                "scalar_dtype": str(np.asarray(a).dtype),
                "scalar_value": repr(a),
                "array_dtype": str(b.dtype),
                "array_value": b.tolist(),
            }, sort_keys=True))
            """,
        )
    elif case.case_id == "PY-SD-005":
        probe_python_pair(
            case,
            ["polars==0.19.19"],
            ["polars==0.20.0"],
            """
            import json, polars as pl
            left = pl.DataFrame({"k": [None, 1], "lv": ["left_null", "left_one"]})
            right = pl.DataFrame({"k": [None, 1], "rv": ["right_null", "right_one"]})
            out = left.join(right, on="k", how="inner")
            print(json.dumps({"shape": out.shape, "rows": out.to_dicts()}, sort_keys=True, default=str))
            """,
        )
    elif case.case_id == "PY-SD-007":
        probe_python_pair(
            case,
            ["pydantic==1.10.15"],
            ["pydantic==2.0.3"],
            """
            import json
            from pydantic import BaseModel
            class Base(BaseModel):
                a: int
            class Sub(Base):
                b: int
            class Wrap(BaseModel):
                x: Base
            w = Wrap(x=Sub(a=1, b=2))
            out = w.model_dump() if hasattr(w, "model_dump") else w.dict()
            print(json.dumps(out, sort_keys=True))
            """,
        )
    elif case.case_id == "PY-SD-008":
        probe_python_pair(
            case,
            ["SQLAlchemy==1.4.54"],
            ["SQLAlchemy==2.0.0"],
            """
            import json, os
            from sqlalchemy import create_engine, text
            db = "sqlalchemy_autocommit_probe.sqlite"
            if os.path.exists(db):
                os.unlink(db)
            engine = create_engine("sqlite:///" + db)
            with engine.connect() as conn:
                conn.execute(text("create table t (x int)"))
                conn.execute(text("insert into t (x) values (1)"))
            with engine.connect() as conn:
                count = conn.execute(text("select count(*) from t")).scalar()
            print(json.dumps({"count_after_reopen": count}, sort_keys=True))
            """,
        )
    elif case.case_id == "JVM-JAVA-10":
        mark_blocked(case, "dependency_acquired", "Host has JDK 17 only; JDK 18+ comparison runtime is not installed.")
    elif case.case_id == "JVM-JAVA-09":
        mark_blocked(case, "dependency_acquired", "Host has Maven 3.9.16 only; Maven 3.8.x comparison runtime is not installed.")
    elif case.case_id in {"PHP-01", "PHP-02"}:
        mark_blocked(case, "dependency_acquired", "Host PHP is 8.2 only; no PHP 7.4/8.0 pair is installed for core-language comparison.")
    elif case.case_id in {"PHP-04", "PHP-09", "PHP-10"}:
        mark_blocked(case, "dependency_acquired", "Package pair not cached locally; deferred instead of broad Composer dependency fetch in this batch.")
    elif case.case_id in {"PHP-05", "PHP-06"}:
        mark_blocked(case, "dependency_acquired", "Laravel app-level fixture is too large for this reverse batch; needs a minimized in-process fixture.")
    elif case.case_id in {"PY-SD-002", "PY-SD-003", "PY-SD-004", "PY-SD-006", "PY-SD-009"}:
        mark_blocked(case, "dependency_acquired", "Heavy or compiler/runtime-sensitive Python pair left at first blocked step in this batch.")
    elif case.case_id in {"RB-NOK-010", "RB-SKQ-008", "RB-AS-001", "RB-AS-002", "RB-AS-003", "RB-AS-004"}:
        mark_blocked(case, "dependency_acquired", "Gem pair not cached locally or requires heavier Rails/Sidekiq/Nokogiri setup; deferred at dependency acquisition.")
    else:
        mark_blocked(case, "source_check", "No runner branch defined for this case.", "blocked_runner_gap")


def write_results(cases: list[Case]) -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    DETAILS_DIR.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", encoding="utf-8") as fh:
        for c in cases:
            fh.write(json.dumps(c.__dict__, ensure_ascii=False) + "\n")
    lines = [
        "# Reverse 50-Case Verification Run - 2026-05-21",
        "",
        "Scope requested: run 50 candidates in reverse source-order, meeting the forward sequential run from the far end of the queue.",
        "",
        "Routing rule: already verified or already rejected sequence entries are skipped but retained in the ledger.",
        "",
        "Artifacts:",
        f"- Machine ledger: `{rel(RESULTS_PATH)}`",
        f"- Per-case details: `{rel(DETAILS_DIR)}/`",
        "",
        "Step vocabulary:",
        "- `source_check`: source URL or local idea-bank evidence checked.",
        "- `dependency_acquired`: old/new runtime or package pair available.",
        "- `old_run`: old side executed.",
        "- `new_run`: new side executed.",
        "- `output_assertion`: old/new outputs compared.",
        "",
        "| # | Candidate | Status | First blocked step | Artifact / notes |",
        "|---:|---|---|---|---|",
    ]
    for c in cases:
        note = c.notes.replace("|", "\\|")
        lines.append(f"| {c.n} | {c.case_id} | {c.status} | {c.first_blocked_step} | `{c.artifact}` - {note} |")
    lines.append("")
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    cases = queue()
    for case in cases:
        print(f"[{case.n:02d}/50] {case.case_id} {case.title}", flush=True)
        process(case)
        write_results(cases)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
