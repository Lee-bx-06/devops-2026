from scripts.doctor import resource_problems


def test_minimum_resources_are_accepted():
    assert resource_problems({"cpus": 2, "memory_gib": 3.5, "disk_free_gib": 40}) == []


def test_underprovisioned_memory_is_reported():
    problems = resource_problems({"cpus": 2, "memory_gib": 1.7, "disk_free_gib": 70})
    assert len(problems) == 1
    assert "memory_gib" in problems[0]
