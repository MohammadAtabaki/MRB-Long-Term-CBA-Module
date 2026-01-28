from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal

Phase = Literal[1, 2]


@dataclass(frozen=True)
class ImportanceTables:
    """
    Phase-dependent ValueIndex (V) taken from your Excel screenshot.
    Mapping: Very Low=1, Low=2, Medium=3, High=4, Very High=5 (proposal Step 6).
    """
    phase1_new_planification: Dict[str, int]
    phase2_risk_mitigation: Dict[str, int]

    def value_index(self, phase: Phase, element_type: str) -> int:
        table = self.phase1_new_planification if phase == 1 else self.phase2_risk_mitigation
        if element_type not in table:
            raise KeyError(
                f"Unknown element_type={element_type!r}. "
                f"Add it to importance_tables.py (hardcoded from Excel)."
            )
        return int(table[element_type])


# ---- Hardcoded from your uploaded Excel screenshot ----
# NOTE: keep keys stable and MRB-friendly; use snake_case or consistent strings.
DEFAULT_TABLES = ImportanceTables(
    phase1_new_planification={
        "municipality_population": 5,
        "industrial_infrastructure": 3,
        "shelters": 5,
        "buildings_general": 4,
        "hospitals_health_center": 5,
        "emergencies_facilities": 5,
        "schools": 4,
        "minery": 2,
        "roads": 3,
        "aerial_transport": 4,
        "ports": 4,
        "train": 4,
        "power_line": 3,
        "power_central": 4,
        "power_tower": 3,
        "electric_transformation": 4,
        "power_antenna": 3,
        "pipeline": 3,
        "general_tank": 4,
        "fuel_gas_stations": 5,
        "water_storage": 4,
        "water_conduction": 4,
    },
    phase2_risk_mitigation={
        "municipality_population": 5,
        "industrial_infrastructure": 3,
        "shelters": 5,
        "buildings_general": 5,
        "hospitals_health_center": 5,
        "emergencies_facilities": 5,
        "schools": 4,
        "minery": 2,
        "roads": 3,
        "aerial_transport": 3,
        "ports": 3,
        "train": 3,
        "power_line": 3,
        "power_central": 5,
        "power_tower": 3,
        "electric_transformation": 4,
        "power_antenna": 3,
        "pipeline": 3,
        "general_tank": 3,
        "fuel_gas_stations": 4,
        "water_storage": 4,
        "water_conduction": 4,
    },
)
