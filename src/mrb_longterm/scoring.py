from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple

from .config import ModuleConfig
from .models import (
    ElementPriority,
    HazardClass,
    PriorityLabel,
    RankedElement,
    ZoneHazardInputs,
    ZoneHazardResult,
)

# --- Proposal Step 5: HazardIndex = round((HD+F+I)/3) ---
def compute_hazard_index(HD: int, F: int, I: int) -> int:
    if not all(1 <= x <= 5 for x in (HD, F, I)):
        raise ValueError(f"HD,F,I must be in 1..5. Got HD={HD}, F={F}, I={I}")
    return int(round((HD + F + I) / 3.0))


# --- Proposal Step 5 classification ---
def classify_hazard(hazard_index: int) -> HazardClass:
    if hazard_index <= 2:
        return "low"
    if hazard_index <= 3:
        return "medium"
    return "high"


# --- Proposal Step 7 priority matrix ---
PriorityMatrixValue = Dict[Tuple[HazardClass, int], PriorityLabel]

PRIORITY_MATRIX: PriorityMatrixValue = {
    # Low hazard (1–2)
    ("low", 1): "Low",
    ("low", 2): "Low",
    ("low", 3): "Medium",
    ("low", 4): "Medium",
    ("low", 5): "High",
    # Medium hazard (3)
    ("medium", 1): "Low",
    ("medium", 2): "Medium",
    ("medium", 3): "Medium-High",
    ("medium", 4): "High",
    ("medium", 5): "Very High",
    # High hazard (4–5)
    ("high", 1): "Medium",
    ("high", 2): "Medium-High",
    ("high", 3): "High",
    ("high", 4): "Very High",
    ("high", 5): "Very High",
}

PRIORITY_NUMERIC: Dict[PriorityLabel, int] = {
    "Low": 1,
    "Medium": 2,
    "Medium-High": 3,
    "High": 4,
    "Very High": 5,
}


def priority_label(hazard_class: HazardClass, value_index: int) -> PriorityLabel:
    if not (1 <= value_index <= 5):
        raise ValueError(f"value_index must be 1..5, got {value_index}")
    return PRIORITY_MATRIX[(hazard_class, value_index)]


def base_score_from_priority(
    hazard_index: int, hazard_class: HazardClass, value_index: int
) -> float:
    """
    Numeric proxy for ordering before diminishing returns.
    We keep it explainable:
      - priority_label bucket dominates
      - within bucket, higher hazard_index and value_index slightly higher
    """
    label = priority_label(hazard_class, value_index)
    bucket = PRIORITY_NUMERIC[label]
    return float(bucket * 100 + hazard_index * 10 + value_index)


# --- Proposal Phase 2: alpha(V) mapping and repetition weights ---
def alpha_from_value(value_index: int, alpha_min: float, alpha_max: float) -> float:
    if not (1 <= value_index <= 5):
        raise ValueError("value_index must be 1..5")
    # Linear mapping: value 1 -> alpha_min, value 5 -> alpha_max
    t = (value_index - 1) / 4.0
    return alpha_min + t * (alpha_max - alpha_min)


def repetition_weight(alpha: float, k: int) -> float:
    if k < 0:
        raise ValueError("k must be >= 0")
    return float(alpha ** k)


def zoning_from_inputs(zone_inputs: List[ZoneHazardInputs]) -> List[ZoneHazardResult]:
    out: List[ZoneHazardResult] = []
    for z in zone_inputs:
        hi = compute_hazard_index(z.HD, z.F, z.I)
        out.append(
            ZoneHazardResult(
                zone_id=z.zone_id,
                hazard_index=hi,
                hazard_class=classify_hazard(hi),
                HD=z.HD,
                F=z.F,
                I=z.I,
            )
        )
    return out


def suitability_from_hazard_class(hc: HazardClass) -> str:
    # Proposal Phase 1 outputs: suitability categories (not prescriptive actions)
    if hc == "low":
        return "Suitable"
    if hc == "medium":
        return "Conditionally acceptable"
    return "Not suitable"


def diminishing_returns_rank(
    candidates: List[ElementPriority],
    cfg: ModuleConfig,
) -> List[RankedElement]:
    """
    Proposal algorithm: greedy reranking with exponential decay by type repetition.
    Deterministic and transparent: includes debug fields.
    """
    remaining = candidates[:]
    ranked: List[RankedElement] = []
    type_counts: Dict[str, int] = {}

    while remaining:
        best_idx = None
        best_final = None
        best_debug = None

        for i, e in enumerate(remaining):
            k = type_counts.get(e.element_type, 0)
            a = alpha_from_value(e.value_index, cfg.alpha_min, cfg.alpha_max)
            w = repetition_weight(a, k)
            final = float(e.base_score * w)

            if (best_final is None) or (final > best_final):
                best_final = final
                best_idx = i
                best_debug = (k, a, w, final)

        assert best_idx is not None and best_debug is not None
        chosen = remaining.pop(best_idx)
        k, a, w, final = best_debug

        ranked.append(
            RankedElement(
                element_id=chosen.element_id,
                element_type=chosen.element_type,
                zone_id=chosen.zone_id,
                hazard_index=chosen.hazard_index,
                hazard_class=chosen.hazard_class,
                value_index=chosen.value_index,
                priority_label=chosen.priority_label,
                base_score=chosen.base_score,
                type_count_before=k,
                alpha_used=a,
                weight_used=w,
                final_score=final,
            )
        )
        type_counts[chosen.element_type] = k + 1

    return ranked
