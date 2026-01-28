from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

HazardClass = Literal["low", "medium", "high"]
Suitability = Literal["Suitable", "Conditionally acceptable", "Not suitable"]

PriorityLabel = Literal["Low", "Medium", "Medium-High", "High", "Very High"]


@dataclass(frozen=True)
class ZoneHazardInputs:
    zone_id: str
    # These are the 1..5 mapped values (proposal Step 4).
    HD: int
    F: int
    I: int
    # Optional extra fields for traceability / future use
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ZoneHazardResult:
    zone_id: str
    hazard_index: int  # 1..5
    hazard_class: HazardClass  # low/medium/high
    HD: int
    F: int
    I: int


@dataclass(frozen=True)
class ExposureItem:
    """
    Represents a single exposed element instance (asset) in a zone.
    For Phase 2 ranking, having stable IDs helps.
    """
    element_id: str
    element_type: str
    zone_id: str
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExposureCounts:
    """
    Alternative representation: aggregated counts per zone/type.
    Used mainly for Phase 1 gap analysis.
    """
    zone_id: str
    counts_by_type: Dict[str, int]


@dataclass(frozen=True)
class Phase1Gap:
    zone_id: str
    hazard_class: HazardClass
    element_type: str
    value_index: int
    observed: int
    expected: int
    gap: int  # expected - observed (>=0)
    note: str


@dataclass(frozen=True)
class Phase1Existing:
    zone_id: str
    hazard_index: int
    hazard_class: HazardClass
    element_type: str
    value_index: int
    priority_label: PriorityLabel
    count: int
    base_score: float


@dataclass(frozen=True)
class Phase1Output:
    zoning: List[ZoneHazardResult]
    suitability_by_zone: Dict[str, Suitability]

    # NEW: assessment list for existing elements (counts-only)
    existing: List[Phase1Existing]

    # gaps list (missing)
    gaps: List[Phase1Gap]
    gaps_grouped_by_hazard_class: Dict[HazardClass, List[Phase1Gap]]



@dataclass(frozen=True)
class ElementPriority:
    element_id: str
    element_type: str
    zone_id: str
    hazard_index: int
    hazard_class: HazardClass
    value_index: int
    priority_label: PriorityLabel
    base_score: float  # numeric proxy for priority_label + tie-breakers


@dataclass(frozen=True)
class RankedElement:
    element_id: str
    element_type: str
    zone_id: str
    hazard_index: int
    hazard_class: HazardClass
    value_index: int
    priority_label: PriorityLabel

    base_score: float
    # diminishing returns debug fields (proposal requests transparency)
    type_count_before: int
    alpha_used: float
    weight_used: float
    final_score: float


@dataclass(frozen=True)
class Phase2Output:
    ranked_elements: List[RankedElement]
    # Convenience summaries
    by_priority_label: Dict[PriorityLabel, int]
    top_n: int


@dataclass(frozen=True)
class RunOutputs:
    phase1: Phase1Output
    phase2: Phase2Output
