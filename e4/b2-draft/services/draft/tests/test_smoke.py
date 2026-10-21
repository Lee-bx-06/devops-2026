from __future__ import annotations

from pathlib import Path

from draft.smoke import EXPECTED_MARKER, assess


def test_expected_failure_is_a_successful_smoke_check():
    result = assess(Path("fixture"), ["docker", "build"], 1, f"shell: {EXPECTED_MARKER}", 1.25)
    assert result.passed is True
    assert result.marker_found is True
    assert result.make_not_found is True
    assert result.make_error_line == f"shell: {EXPECTED_MARKER}"
    assert result.log_tail == [f"shell: {EXPECTED_MARKER}"]


def test_unexpected_build_success_is_rejected():
    result = assess(Path("fixture"), ["docker", "build"], 0, "build complete", 1.0)
    assert result.passed is False


def test_wrong_failure_is_rejected():
    result = assess(Path("fixture"), ["docker", "build"], 1, "network unavailable", 1.0)
    assert result.passed is False


def test_timeout_is_rejected_even_if_marker_was_seen():
    result = assess(
        Path("fixture"),
        ["docker", "build"],
        None,
        EXPECTED_MARKER,
        180.0,
        timed_out=True,
    )
    assert result.passed is False
