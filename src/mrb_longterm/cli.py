from __future__ import annotations
from .importance_tables import DEFAULT_TABLES

from mrb_longterm.importance_tables import DEFAULT_TABLES
from mrb_longterm.scoring import priority_label


from pathlib import Path

from .io import (
    dump_dataclass_list,
    load_config,
    load_exposures_counts_only,
    load_zone_hazards,
    write_json,
)
from .pipeline import run_all


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="MRB long-term CBA module (Phase 1 & 2)")
    parser.add_argument("--input", type=str, default="input", help="Input folder path")
    parser.add_argument("--output", type=str, default="output", help="Output folder path")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    print("INPUT_DIR =", input_dir.resolve())
    print("OUTPUT_DIR =", output_dir.resolve())
    print("OUTPUT_EXISTS =", output_dir.exists())

    zone_hazards = load_zone_hazards(input_dir)
    assets, counts = load_exposures_counts_only(input_dir)
    # ---- Transparency: what MRB provided (counts-only) ----
    observed_counts_by_zone = {
        c.zone_id: dict(c.counts_by_type) for c in counts
    }

    present_types_by_zone = {
        zid: sorted([t for t, n in ct.items() if int(n) > 0])
        for zid, ct in observed_counts_by_zone.items()
    }

    present_types_global = sorted(
        {t for ct in observed_counts_by_zone.values() for t, n in ct.items() if int(n) > 0}
    )

    cfg = load_config(input_dir)

    outputs = run_all(
        zone_hazards=zone_hazards,
        assets=assets,
        exposure_counts=counts,
        cfg=cfg,
    )

        # ----------------------------
    # Phase 1 Visualization Matrix
    # ----------------------------
    # Full ordered list of types (from Excel / hardcoded)
    phase1_types = list(DEFAULT_TABLES.phase1_new_planification.keys())

    # Count matrix from MRB input
    counts_by_zone = observed_counts_by_zone  # already computed in the "inputs_snapshot" improvement

    # Hazard lookup for zones
    zone_info = {z["zone_id"]: z for z in dump_dataclass_list(outputs.phase1.zoning)}

    # Build per-zone rows with cells
    matrix_rows = []
    for zone_id in sorted(zone_info.keys()):
        z = zone_info[zone_id]
        hazard_class = z["hazard_class"]
        hazard_index = z["hazard_index"]

        row = {
            "zone_id": zone_id,
            "hazard_index": hazard_index,
            "hazard_class": hazard_class,
            "suitability": outputs.phase1.suitability_by_zone.get(zone_id),
            "cells": []
        }

        for etype in phase1_types:
            v = DEFAULT_TABLES.phase1_new_planification[etype]
            c = int(counts_by_zone.get(zone_id, {}).get(etype, 0))
            plabel = priority_label(hazard_class, v)  # uses proposal matrix

            priority_numeric = {
            "Low": 1,
            "Medium": 2,
            "Medium-High": 3,
            "High": 4,
            "Very High": 5
        }[plabel]

        row["cells"].append({
            "element_type": etype,

            # proposal axes
            "hazard_class": hazard_class,
            "value_index": v,

            # proposal result
            "priority_label": plabel,
            "priority_rank": priority_numeric,

            # data context
            "count": c,
            "is_gap": (v >= cfg.phase1_gap_value_threshold and c == 0)
        })


        matrix_rows.append(row)

    # A compact “gaps-only” view for UI toggles
    gaps_only = []
    for row in matrix_rows:
        gaps_only.append({
            "zone_id": row["zone_id"],
            "hazard_class": row["hazard_class"],
            "hazard_index": row["hazard_index"],
            "cells": [c for c in row["cells"] if c["value_index"] >= cfg.phase1_gap_value_threshold],
        })


    write_json(output_dir / "phase1_new_planification.json", {
    "zoning": dump_dataclass_list(outputs.phase1.zoning),
    "suitability_by_zone": outputs.phase1.suitability_by_zone,
    "existing": dump_dataclass_list(outputs.phase1.existing),
    "gaps": dump_dataclass_list(outputs.phase1.gaps),
    "gaps_grouped_by_hazard_class": {
        k: dump_dataclass_list(v) for k, v in outputs.phase1.gaps_grouped_by_hazard_class.items()
    },

    "notes": {
        "mode": "counts-only",
        "phase1_gap_value_threshold": cfg.phase1_gap_value_threshold,
        "phase1_only_nonlow_hazard": cfg.phase1_only_nonlow_hazard,
        "existing_definition": "Existing = element types with count > 0, scored via hazard class × Excel ValueIndex.",
        "gap_definition": "Gap = important type (ValueIndex >= threshold) with count == 0."
    }
    })

    write_json(output_dir / "phase1_matrix.json", {
        "element_types": phase1_types,
        "phase": 1,
        "mode": "counts-only",
        "threshold": {
            "phase1_gap_value_threshold": cfg.phase1_gap_value_threshold,
            "phase1_only_nonlow_hazard": cfg.phase1_only_nonlow_hazard
        },

        # ✅ ADD THIS BLOCK HERE
        "ranking_matrix_definition": {
            "axes": {
                "x": "value_index (1–5, from Excel)",
                "y": "hazard_class (low / medium / high)"
            },
            "cells_meaning": "priority_label / priority_rank",
            "priority_scale": {
                "1": "Low",
                "2": "Medium",
                "3": "Medium-High",
                "4": "High",
                "5": "Very High"
            }
        },

        "matrix_rows": matrix_rows,
        "gaps_only_rows": gaps_only,
        "legend": {
            "cell_fields": ["count", "value_index", "priority_label", "priority_rank", "is_gap"],
            "is_gap_definition": "is_gap = (value_index >= threshold) AND (count == 0)"
        }
    })



    write_json(output_dir / "phase2_risk_mitigation.json", {
        "ranked_elements": dump_dataclass_list(outputs.phase2.ranked_elements),
        "by_priority_label": outputs.phase2.by_priority_label,
        "top_n": outputs.phase2.top_n,
        "notes": {
            "assets": "synthetic IDs generated from counts: zone:type:i",
            "diminishing_returns": {"alpha_min": cfg.alpha_min, "alpha_max": cfg.alpha_max}
        }
    })

    # ----------------------------
    # Phase 2 Aggregated Matrix
    # ----------------------------
    phase2_matrix = {}

    for r in outputs.phase2.ranked_elements:
        z = r.zone_id
        t = r.element_type
        phase2_matrix.setdefault(z, {})
        cell = phase2_matrix[z].setdefault(t, {
            "n_assets": 0,
            "sum_final_score": 0.0,
            "max_final_score": 0.0
        })
        cell["n_assets"] += 1
        cell["sum_final_score"] += float(r.final_score)
        cell["max_final_score"] = max(cell["max_final_score"], float(r.final_score))

    write_json(output_dir / "phase2_matrix.json", {
        "phase": 2,
        "meaning": "Aggregated mitigation importance per (zone, element_type)",
        "cells_definition": {
            "n_assets": "how many assets of this type were ranked",
            "sum_final_score": "total contribution after diminishing returns",
            "max_final_score": "highest-ranked asset of this type"
        },
        "matrix": phase2_matrix
    })



    # ----------------------------
    # Phase 2 Type Summary (UI)
    # ----------------------------
    ranked = outputs.phase2.ranked_elements

    type_stats = {}
    for r in ranked:
        t = r.element_type
        st = type_stats.setdefault(t, {
            "element_type": t,
            "n_assets": 0,
            "sum_final_score": 0.0,
            "avg_final_score": 0.0,
            "max_final_score": None,
            "min_final_score": None,
            "priority_labels": {},
            "zones": set(),
        })

        st["n_assets"] += 1
        st["sum_final_score"] += float(r.final_score)
        st["zones"].add(r.zone_id)

        # min/max
        st["max_final_score"] = float(r.final_score) if st["max_final_score"] is None else max(st["max_final_score"], float(r.final_score))
        st["min_final_score"] = float(r.final_score) if st["min_final_score"] is None else min(st["min_final_score"], float(r.final_score))

        # priority label counts
        pl = r.priority_label
        st["priority_labels"][pl] = st["priority_labels"].get(pl, 0) + 1

    # finalize avg + zones list
    type_summary = []
    for st in type_stats.values():
        st["avg_final_score"] = st["sum_final_score"] / max(st["n_assets"], 1)
        st["zones"] = sorted(list(st["zones"]))
        type_summary.append(st)

    # sort by total contribution (sum_final_score)
    type_summary = sorted(type_summary, key=lambda x: x["sum_final_score"], reverse=True)

    write_json(output_dir / "phase2_type_summary.json", {
        "phase": 2,
        "mode": "counts-only (synthetic assets)",
        "top_n_applied": outputs.phase2.top_n,
        "alpha": {"min": cfg.alpha_min, "max": cfg.alpha_max},
        "summary_by_type": type_summary,
        "legend": {
            "sum_final_score": "Total contribution of this type in the ranked list",
            "avg_final_score": "Average final_score after diminishing returns",
            "priority_labels": "How many items of this type ended up in each PriorityLabel bucket"
        }
    })


    write_json(output_dir / "summary.json", {
        "n_zones": len(outputs.phase1.zoning),
        "n_types_in_table_phase1": len(set(DEFAULT_TABLES.phase1_new_planification.keys())),
        "n_types_in_table_phase2": len(set(DEFAULT_TABLES.phase2_risk_mitigation.keys())),
        "phase1_n_gaps": len(outputs.phase1.gaps),
        "phase2_top_n": outputs.phase2.top_n,
    })



    print("WROTE:", (output_dir / "phase1_new_planification.json").resolve())
    print("WROTE:", (output_dir / "phase2_risk_mitigation.json").resolve())
    print("WROTE:", (output_dir / "summary.json").resolve())

if __name__ == "__main__":
    main()
