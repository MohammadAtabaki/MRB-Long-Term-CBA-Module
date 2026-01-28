from __future__ import annotations

from typing import Dict, List
from .models import Phase1Existing

from .config import ModuleConfig
from .importance_tables import DEFAULT_TABLES
from .models import (
    ElementPriority,
    ExposureCounts,
    ExposureItem,
    Phase1Gap,
    Phase1Output,
    Phase2Output,
    RunOutputs,
    ZoneHazardInputs,
)
from .scoring import (
    PRIORITY_NUMERIC,
    base_score_from_priority,
    diminishing_returns_rank,
    priority_label,
    suitability_from_hazard_class,
    zoning_from_inputs,
)


def _index_zones(zoning):
    return {z.zone_id: z for z in zoning}


def _counts_lookup(counts: List[ExposureCounts]) -> Dict[str, Dict[str, int]]:
    return {c.zone_id: dict(c.counts_by_type) for c in counts}


def run_phase1(
    *,
    zone_hazards: List[ZoneHazardInputs],
    exposure_counts: List[ExposureCounts],
    cfg: ModuleConfig,
) -> Phase1Output:
    """
    Phase 1 (New planification) in counts-only mode:

    Outputs:
      A) existing: assessment of existing element-types (count>0) using:
         - HazardIndex / hazard class
         - Excel ValueIndex (Phase 1 table)
         - Priority matrix => PriorityLabel
      B) gaps: missing important element-types (count==0) using the same logic

    No population or planning standards are used.
    """
    zoning = zoning_from_inputs(zone_hazards)
    zone_idx = _index_zones(zoning)
    counts_by_zone = _counts_lookup(exposure_counts)

    suitability_by_zone = {z.zone_id: suitability_from_hazard_class(z.hazard_class) for z in zoning}

    threshold = cfg.phase1_gap_value_threshold

    existing: List[Phase1Existing] = []
    gaps: List[Phase1Gap] = []

    for zone_id, zinfo in zone_idx.items():
        if cfg.phase1_only_nonlow_hazard and zinfo.hazard_class == "low":
            # still include zoning/suitability, but skip “planning outputs” if you want
            continue

        observed_counts = counts_by_zone.get(zone_id, {})

        # Iterate over ALL known types from the Excel Phase 1 table
        for etype, v in DEFAULT_TABLES.phase1_new_planification.items():
            observed = int(observed_counts.get(etype, 0))

            # Compute priority for this (zone,type) regardless of missing/existing
            label = priority_label(zinfo.hazard_class, v)
            base = base_score_from_priority(zinfo.hazard_index, zinfo.hazard_class, v)

            if observed > 0:
                existing.append(
                    Phase1Existing(
                        zone_id=zone_id,
                        hazard_index=zinfo.hazard_index,
                        hazard_class=zinfo.hazard_class,
                        element_type=etype,
                        value_index=v,
                        priority_label=label,
                        count=observed,
                        base_score=base,
                    )
                )
            else:
                # Gap only for "important" types (ValueIndex >= threshold)
                if v >= threshold:
                    gaps.append(
                        Phase1Gap(
                            zone_id=zone_id,
                            hazard_class=zinfo.hazard_class,
                            element_type=etype,
                            value_index=v,
                            observed=0,
                            expected=1,  # placeholder in counts-only mode
                            gap=1,
                            note="Missing (counts-only mode)",
                        )
                    )

    # Rank existing: highest priority bucket, then hazard index, then value, then count
    existing_sorted = sorted(
        existing,
        key=lambda e: (PRIORITY_NUMERIC[e.priority_label], e.hazard_index, e.value_index, e.count),
        reverse=True,
    )

    # Rank gaps: high hazard first, then value_index
    hazard_order = {"high": 3, "medium": 2, "low": 1}
    gaps_sorted = sorted(
        gaps,
        key=lambda g: (hazard_order[g.hazard_class], g.value_index),
        reverse=True,
    )

    grouped: Dict[str, List[Phase1Gap]] = {"low": [], "medium": [], "high": []}
    for g in gaps_sorted:
        grouped[g.hazard_class].append(g)

    return Phase1Output(
        zoning=zoning,
        suitability_by_zone=suitability_by_zone,
        existing=existing_sorted,
        gaps=gaps_sorted,
        gaps_grouped_by_hazard_class=grouped,  # type: ignore
    )



def run_phase2(
    *,
    zone_hazards: List[ZoneHazardInputs],
    assets: List[ExposureItem],
    cfg: ModuleConfig,
) -> Phase2Output:
    zoning = zoning_from_inputs(zone_hazards)
    zone_idx = _index_zones(zoning)

    candidates: List[ElementPriority] = []
    for a in assets:
        z = zone_idx.get(a.zone_id)
        if z is None:
            continue

        v = DEFAULT_TABLES.phase2_risk_mitigation.get(a.element_type)
        if v is None:
            raise KeyError(
                f"Unknown element_type={a.element_type!r} for asset {a.element_id!r}. "
                f"Add it to importance_tables.py."
            )

        label = priority_label(z.hazard_class, v)
        base = base_score_from_priority(z.hazard_index, z.hazard_class, v)

        candidates.append(
            ElementPriority(
                element_id=a.element_id,
                element_type=a.element_type,
                zone_id=a.zone_id,
                hazard_index=z.hazard_index,
                hazard_class=z.hazard_class,
                value_index=v,
                priority_label=label,
                base_score=base,
            )
        )

    ranked = diminishing_returns_rank(candidates, cfg)

    by_label: Dict[str, int] = {k: 0 for k in PRIORITY_NUMERIC.keys()}  # type: ignore
    for r in ranked:
        by_label[r.priority_label] = by_label.get(r.priority_label, 0) + 1  # type: ignore

    top_n = max(1, int(cfg.phase2_top_n))
    ranked = ranked[:top_n]

    return Phase2Output(
        ranked_elements=ranked,
        by_priority_label=by_label,  # type: ignore
        top_n=top_n,
    )


def run_all(
    *,
    zone_hazards: List[ZoneHazardInputs],
    assets: List[ExposureItem],
    exposure_counts: List[ExposureCounts],
    cfg: ModuleConfig,
) -> RunOutputs:
    p1 = run_phase1(zone_hazards=zone_hazards, exposure_counts=exposure_counts, cfg=cfg)
    p2 = run_phase2(zone_hazards=zone_hazards, assets=assets, cfg=cfg)
    return RunOutputs(phase1=p1, phase2=p2)
