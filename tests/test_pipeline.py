from mrb_longterm.config import ModuleConfig
from mrb_longterm.models import ExposureCounts, ZoneHazardInputs
from mrb_longterm.pipeline import run_phase1

def test_phase1_outputs_existing_and_gaps():
    cfg = ModuleConfig.default()
    zones = [ZoneHazardInputs("Z1", 5, 5, 5)]  # high hazard
    counts = [ExposureCounts("Z1", {"shelters": 0, "hospitals_health_center": 2})]

    out = run_phase1(zone_hazards=zones, exposure_counts=counts, cfg=cfg)

    # Existing list should include hospitals
    assert any(e.zone_id == "Z1" and e.element_type == "hospitals_health_center" and e.count == 2
               for e in out.existing)

    # Gaps should include shelters (value 5 in phase1 table)
    assert any(g.zone_id == "Z1" and g.element_type == "shelters" for g in out.gaps)
