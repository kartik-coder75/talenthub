"""Unit tests for the pure eligibility rules, including boundary values."""
from types import SimpleNamespace as NS

import pytest

from app.services.eligibility import check_eligibility


def job(min_cgpa=7.0, max_backlogs=2, branches=()):
    return NS(min_cgpa=min_cgpa, max_active_backlogs=max_backlogs, allowed_branches=list(branches))


def student(cgpa, backlogs, branch="CSE"):
    return NS(cgpa=cgpa, active_backlogs=backlogs, branch=branch)


def test_example_scenario_rahul_is_eligible():
    assert check_eligibility(student(8.2, 1), job()).eligible


@pytest.mark.parametrize("cgpa,expected", [(7.0, True), (7.01, True), (6.99, False), (0.0, False)])
def test_cgpa_boundary(cgpa, expected):
    assert check_eligibility(student(cgpa, 0), job()).eligible is expected


@pytest.mark.parametrize("backlogs,expected", [(0, True), (2, True), (3, False)])
def test_backlog_boundary(backlogs, expected):
    assert check_eligibility(student(8.0, backlogs), job()).eligible is expected


def test_branch_restriction():
    j = job(branches=["CSE", "IT"])
    assert check_eligibility(student(8, 0, "it"), j).eligible
    result = check_eligibility(student(8, 0, "MECH"), j)
    assert not result.eligible and "Branch" in result.reasons[0]


def test_empty_branch_list_means_all_branches():
    assert check_eligibility(student(8, 0, "CIVIL"), job(branches=[])).eligible


def test_all_failing_reasons_are_reported():
    result = check_eligibility(student(5.0, 5, "MECH"), job(branches=["CSE"]))
    assert len(result.reasons) == 3
