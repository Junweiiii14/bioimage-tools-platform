"""The installed-runtime probe rejects altered recovery evidence and protected outputs."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tooling.verify_installed_legacy import digest, prepare

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def fixtures(tmp_path: Path) -> Path:
    root = tmp_path / "合成旧项目"
    prepare(root)
    return root


def run_probe(
    fixtures: Path, output: Path, *, injection: str = ""
) -> subprocess.CompletedProcess[str]:
    arguments = {
        "root": str(fixtures),
        "output": str(output),
        "runtime": sys.executable,
        "site": str(ROOT / "tools/wb/src"),
        "fixtures_sha256": digest((fixtures / "fixtures.json").read_bytes()),
        "installation_root": None,
    }
    code = (
        "import json,runpy,sys\nfrom pathlib import Path\n"
        f"module=runpy.run_path({str(ROOT / 'tooling/verify_installed_legacy.py')!r})\n"
        f"args=json.loads({json.dumps(arguments, ensure_ascii=True)!r})\n"
        "for key in ('root','output','runtime','site'): args[key]=Path(args[key])\n"
        + injection
        + "\nmodule['verify'](**args)\n"
    )
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", code],
        cwd=output.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_real_isolated_probe_checks_six_goldens_and_preserves_existing_report(
    fixtures: Path, tmp_path: Path
) -> None:
    output = tmp_path / "新报告"
    result = run_probe(fixtures, output)
    assert result.returncode == 0, result.stderr
    report_path = output / "legacy-verification.json"
    before = report_path.read_bytes()
    report = json.loads(before)
    assert report["scope"] == "development-self-check"
    assert report["phase"] == "passed" and report["originals_unchanged"] is True
    assert [item["version"] for item in report["versions"]] == list(range(1, 7))
    assert run_probe(fixtures, output).returncode != 0
    assert report_path.read_bytes() == before


def test_real_stage_corruption_cannot_pass_restoration(fixtures: Path, tmp_path: Path) -> None:
    output = tmp_path / "恢复失败"
    result = run_probe(
        fixtures,
        output,
        injection=(
            "import wb_tool.api as api\noriginal=api.stage_project_archive\n"
            "def corrupt(*args, **kwargs):\n"
            "    staged=original(*args, **kwargs)\n"
            "    Path(staged.assets[0].path).write_bytes(b'CORRUPTED')\n"
            "    return staged\n"
            "api.stage_project_archive=corrupt\n"
        ),
    )
    assert result.returncode != 0
    report = json.loads((output / "legacy-verification.json").read_bytes())
    assert report["phase"] == "failed" and report["versions"] == []
    assert "Restored source bytes" in report["error"]


def test_installation_root_reports_are_rejected_before_any_write(
    fixtures: Path, tmp_path: Path
) -> None:
    installation = tmp_path / "模拟安装"
    # Create only the parent for subprocess cwd; no application is copied or executed.
    installation.mkdir()
    output = installation / "reports"
    result = run_probe(
        fixtures,
        output,
        injection=(
            f"install=Path({str(installation)!r})\n"
            "args['installation_root']=install\n"
            "args['runtime']=install/'runtime/python.exe'\n"
            "args['site']=install/'runtime/Lib/site-packages'\n"
            "sys.executable=str(args['runtime'])\n"
        ),
    )
    assert result.returncode != 0
    assert "Reports must be outside" in result.stderr
    assert list(installation.iterdir()) == []


def test_fixture_manifest_must_match_independent_pin(fixtures: Path, tmp_path: Path) -> None:
    output = tmp_path / "错误摘要"
    result = run_probe(fixtures, output, injection="args['fixtures_sha256']='0'*64\n")
    assert result.returncode != 0
    assert "independently pinned SHA256" in result.stderr
    assert not output.exists()
