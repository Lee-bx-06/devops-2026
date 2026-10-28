from draft.autobuild import classify_failure


def test_student_make_command_not_found_variant():
    """Recognize the alternate shell wording emitted by some base images."""
    log = "docker build: /bin/sh: 1: make: command not found"
    assert classify_failure(log) == "MISSING_MAKE"
