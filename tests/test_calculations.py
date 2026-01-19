from .config_tests import env_init


# COOLPROP EXAMPLES
@env_init("2024-04-01", "2024-05-01")
def test_coolprop_hex():
    import custom_calculations_scripts.coolprop_examples.heat_exchanger_energy_flow


# REGULAR INTERVAL EXAMPLES
@env_init("2025-01-01", "2025-02-01")
def test_regular_block_aggregation():
    import custom_calculations_scripts.regular_intervals_examples.block_aggregation


@env_init("2025-01-01", "2025-02-01")
def test_regular_event_counter():
    import custom_calculations_scripts.regular_intervals_examples.event_counter


@env_init("2025-01-01", "2025-02-01")
def test_regular_incrementing_counter():
    import custom_calculations_scripts.regular_intervals_examples.incrementing_counter


@env_init("2025-01-01", "2025-02-01")
def test_regular_incrementing_totalizer():
    import custom_calculations_scripts.regular_intervals_examples.incrementing_totalizer


@env_init(start="2025-04-01", end="2025-05-01")
def test_incrementing_duration_totalizer():
    import custom_calculations_scripts.regular_intervals_examples.incrementing_duration_totalizer


# SEARCH RESULT EXAMPLES
@env_init("2025-01-01", "2025-02-01")
def test_search_block_aggregation():
    import custom_calculations_scripts.search_results_examples.block_aggregations_calc_search_results


@env_init("2025-01-01", "2025-02-01")
def test_search_event_counter():
    import custom_calculations_scripts.search_results_examples.event_counter_for_search_results


@env_init("2025-01-01", "2025-02-01")
def test_search_incrementing_counter():
    import custom_calculations_scripts.search_results_examples.incrementing_event_counter_search_results


@env_init("2025-01-01", "2025-02-01")
def test_search_incrementing_totalizer():
    import custom_calculations_scripts.search_results_examples.incrementing_value_totalizer_search_results


@env_init(start="2024-04-01", end="2025-05-01")
def test_search_ignore_gaps():
    import custom_calculations_scripts.search_results_examples.ignore_short_gaps


# CUSTOM EXAMPLES
@env_init(start="2025-04-01", end="2025-05-01")
def test_startup_downtime():
    import custom_calculations_scripts.custom_examples.downtime_before_startup


@env_init(start="2025-04-01", end="2025-05-01")
def test_kwh_totalizer():
    import custom_calculations_scripts.custom_examples.kwh_totalizer

@env_init(start="2025-04-01", end="2025-05-01")
def test_power_factor_calculation():
    import custom_calculations_scripts.custom_examples.perpetual_totalizer
