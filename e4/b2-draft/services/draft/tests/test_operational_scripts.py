from __future__ import annotations

from pathlib import Path

from scripts.secret_scan import scan_text, scan_worktree


def test_secret_scanner_detects_and_redacts_key(tmp_path: Path):
    fake_key = "sk-" + "A" * 24
    (tmp_path / "bad.txt").write_text(fake_key, encoding="utf-8")
    findings = scan_worktree(tmp_path)
    assert len(findings) == 1
    assert findings[0].prefix == "sk-A..."
    assert fake_key not in findings[0].prefix


def test_secret_scanner_ignores_plain_text():
    assert scan_text("test", "sample", "no credential here") == []


def test_runtime_env_is_not_treated_as_repository_leak(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("DRAFT_API_KEY=" + "sk-" + "A" * 24, encoding="utf-8")
    env_file.chmod(0o600)
    assert scan_worktree(tmp_path) == []
