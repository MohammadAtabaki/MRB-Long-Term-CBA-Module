from mrb_longterm.importance_tables import DEFAULT_TABLES

def test_importance_keys_exist():
    assert DEFAULT_TABLES.value_index(1, "shelters") == 5
    assert DEFAULT_TABLES.value_index(2, "power_central") == 5
