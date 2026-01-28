from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .config import ModuleConfig
from .models import ExposureCounts, ExposureItem, ZoneHazardInputs


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_zone_hazards(input_dir: Path) -> List[ZoneHazardInputs]:
    """
    input/hazard_zones.json
    {
      "zones": [
        {"zone_id":"Zone_Yellow", "HD":5, "F":5, "I":5},
        ...
      ]
    }
    """
    obj = read_json(input_dir / "hazard_zones.json")
    zones = obj.get("zones", [])
    out: List[ZoneHazardInputs] = []
    for z in zones:
        out.append(
            ZoneHazardInputs(
                zone_id=str(z["zone_id"]),
                HD=int(z["HD"]),
                F=int(z["F"]),
                I=int(z["I"]),
                meta={k: v for k, v in z.items() if k not in {"zone_id", "HD", "F", "I"}},
            )
        )
    return out


def load_exposures_counts_only(input_dir: Path) -> Tuple[List[ExposureItem], List[ExposureCounts]]:
    """
    input/exposure_by_zone.json
    MRB provides ONLY counts per zone and per type:

    {
      "counts": [
        {"zone_id":"Zone_Yellow",
         "counts_by_type":{"shelters":0, "hospitals_health_center":2, "roads":5}},
        ...
      ]
    }

    We also build synthetic ExposureItem list for Phase 2.
    """
    obj = read_json(input_dir / "exposure_by_zone.json")

    if "counts" not in obj:
        raise ValueError(
            "Expected 'counts' in exposure_by_zone.json. "
            "MRB contract here is counts-only."
        )

    counts: List[ExposureCounts] = []
    for c in obj["counts"]:
        counts.append(
            ExposureCounts(
                zone_id=str(c["zone_id"]),
                counts_by_type={str(k): int(v) for k, v in c["counts_by_type"].items()},
            )
        )

    # Build synthetic assets from counts for Phase 2 ranking
    assets: List[ExposureItem] = []
    for c in counts:
        for etype, n in c.counts_by_type.items():
            for i in range(int(n)):
                assets.append(
                    ExposureItem(
                        element_id=f"{c.zone_id}:{etype}:{i+1}",
                        element_type=etype,
                        zone_id=c.zone_id,
                        meta={"synthetic_id": True},
                    )
                )

    return assets, counts


def load_config(input_dir: Path) -> ModuleConfig:
    path = input_dir / "config.json"
    if not path.exists():
        return ModuleConfig.default()

    obj = read_json(path)
    return ModuleConfig(
        phase1_gap_value_threshold=int(obj.get("phase1_gap_value_threshold", 4)),
        phase1_only_nonlow_hazard=bool(obj.get("phase1_only_nonlow_hazard", True)),
        alpha_min=float(obj.get("alpha_min", 0.55)),
        alpha_max=float(obj.get("alpha_max", 0.92)),
        phase2_top_n=int(obj.get("phase2_top_n", 50)),
    )


def dump_dataclass_list(items: List[Any]) -> List[Dict[str, Any]]:
    return [asdict(x) for x in items]
