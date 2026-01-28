import json

from mrb_longterm.cli import main as cli_main

def test_e2e(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    (input_dir / "hazard_zones.json").write_text(json.dumps({
        "zones": [
            {"zone_id": "Zone_Yellow", "HD": 5, "F": 5, "I": 5},
            {"zone_id": "Zone_Green", "HD": 2, "F": 2, "I": 2}
        ]
    }), encoding="utf-8")

    (input_dir / "exposure_by_zone.json").write_text(json.dumps({
        "counts": [
            {"zone_id": "Zone_Yellow", "counts_by_type": {
                "hospitals_health_center": 2,
                "shelters": 1,
                "fuel_gas_stations": 1
            }},
            {"zone_id": "Zone_Green", "counts_by_type": {
                "water_storage": 1
            }}
        ]
    }), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["mrb-longterm", "--input", str(input_dir), "--output", str(output_dir)])
    cli_main()

    assert (output_dir / "phase1_new_planification.json").exists()
    assert (output_dir / "phase2_risk_mitigation.json").exists()
    assert (output_dir / "summary.json").exists()
