from config_tests import env_init


@env_init("2024-03-19", "2024-06-19")
def test_coolprop_hex():
    import custom_calculations_scripts.coolprop_examples.heat_exchanger_energy_flow
