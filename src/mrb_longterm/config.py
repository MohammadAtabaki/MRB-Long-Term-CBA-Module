from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleConfig:
    """
    JSON-serializable config for MRB integration.

    Phase 1:
      - No population / standards. "Gap" means: important types missing (count == 0)
        in zones with non-low hazard (or all zones depending on threshold).
    Phase 2:
      - Diminishing returns / duplication handling as in proposal.
    """
    # Phase 1: only consider element types with ValueIndex >= threshold
    phase1_gap_value_threshold: int = 4

    # If True: only compute gaps for medium/high hazard zones (recommended)
    phase1_only_nonlow_hazard: bool = True

    # Phase 2 diminishing returns (proposal defaults)
    alpha_min: float = 0.55
    alpha_max: float = 0.92

    # For Phase 2 outputs
    phase2_top_n: int = 50

    @staticmethod
    def default() -> "ModuleConfig":
        return ModuleConfig(
            phase1_gap_value_threshold=4,
            phase1_only_nonlow_hazard=True,
            alpha_min=0.55,
            alpha_max=0.92,
            phase2_top_n=50,
        )
