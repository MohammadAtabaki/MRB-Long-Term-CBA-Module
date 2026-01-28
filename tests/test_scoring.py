import pytest

from mrb_longterm.scoring import (
    alpha_from_value,
    classify_hazard,
    compute_hazard_index,
    priority_label,
    base_score_from_priority,
)

def test_hazard_index_rounding():
    assert compute_hazard_index(5, 5, 5) == 5
    assert compute_hazard_index(1, 1, 1) == 1
    assert compute_hazard_index(1, 2, 3) == 2  # round(2.0)=2
    assert compute_hazard_index(2, 3, 4) == 3  # round(3.0)=3

def test_hazard_class():
    assert classify_hazard(1) == "low"
    assert classify_hazard(2) == "low"
    assert classify_hazard(3) == "medium"
    assert classify_hazard(4) == "high"
    assert classify_hazard(5) == "high"

def test_priority_matrix_examples():
    assert priority_label("low", 1) == "Low"
    assert priority_label("low", 5) == "High"
    assert priority_label("medium", 5) == "Very High"
    assert priority_label("high", 1) == "Medium"
    assert priority_label("high", 5) == "Very High"

def test_base_score_monotonic():
    a = base_score_from_priority(3, "medium", 5)
    b = base_score_from_priority(4, "high", 5)
    assert b > a

def test_alpha_mapping():
    assert alpha_from_value(1, 0.55, 0.92) == pytest.approx(0.55)
    assert alpha_from_value(5, 0.55, 0.92) == pytest.approx(0.92)
