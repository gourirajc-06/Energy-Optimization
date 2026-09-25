"""Regression and pipeline tests for the AI Energy Optimization project."""

from app import agent, app


client = app.test_client()


def optimize(payload):
    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    return response.get_json()


def assert_valid(result, temperature, occupants, time_of_day, ambient_light):
    valid, reason = agent.check_constraints(
        result["hill_climbing"]["final_state"],
        temperature,
        occupants,
        time_of_day,
        ambient_light,
    )
    assert valid, reason


def test_homepage():
    html = client.get("/").data.decode("utf-8")
    for marker in (
        "AI Energy Optimization", "PERCEPTION", "RULE EVALUATION",
        "CONSTRAINT CHECK", "CSP SEARCH & BACKTRACKING",
        "SIMPLE HILL CLIMBING", "ENERGY OPTIMISATION", "AI DECISION",
        "Time of Day", "Ambient Light (lux)"
    ):
        assert marker in html


def test_scenario_1_hot_day_bright():
    result = optimize({
        "temperature": 32, "occupants": 3, "time_of_day": "14:00",
        "ambient_light": 650, "ac": "HIGH", "lights": "ON"
    })
    perception = result["perception"]
    assert perception["occupied"]
    assert perception["temperature_above_comfort"]
    assert perception["daylight_period"]
    assert perception["ambient_light_sufficient"]
    assert result["hill_climbing"]["final_state"] == {"AC": "HIGH", "Lights": "OFF"}
    assert_valid(result, 32, 3, "14:00", 650)


def test_scenario_2_vacant():
    result = optimize({
        "temperature": 23, "occupants": 0, "time_of_day": "14:00",
        "ambient_light": 700, "ac": "HIGH", "lights": "ON"
    })
    assert result["perception"]["vacant"]
    assert result["hill_climbing"]["final_state"] == {"AC": "OFF", "Lights": "OFF"}
    assert_valid(result, 23, 0, "14:00", 700)


def test_scenario_3_cool_night_dark():
    result = optimize({
        "temperature": 23, "occupants": 2, "time_of_day": "22:00",
        "ambient_light": 20, "ac": "HIGH", "lights": "ON"
    })
    perception = result["perception"]
    assert perception["occupied"]
    assert perception["temperature_within_comfort"]
    assert perception["night_period"]
    assert perception["ambient_light_insufficient"]
    assert result["hill_climbing"]["final_state"] == {"AC": "OFF", "Lights": "ON"}
    assert_valid(result, 23, 2, "22:00", 20)


def test_scenario_4_hot_night_dark():
    result = optimize({
        "temperature": 32, "occupants": 3, "time_of_day": "22:00",
        "ambient_light": 10, "ac": "HIGH", "lights": "ON"
    })
    assert result["hill_climbing"]["final_state"] == {"AC": "HIGH", "Lights": "ON"}
    assert_valid(result, 32, 3, "22:00", 10)


def test_moderate_temperature_and_ambient_light_use_reduced_states():
    result = optimize({
        "temperature": 26, "occupants": 3, "time_of_day": "14:00",
        "ambient_light": 400, "ac": "HIGH", "lights": "ON"
    })
    assert result["perception"]["moderate_temperature"]
    assert result["hill_climbing"]["final_state"] == {
        "AC": "LOW", "Lights": "MEDIUM"
    }
    assert_valid(result, 26, 3, "14:00", 400)


def test_required_output_state_cases():
    cases = [
        (23, 3, "14:00", 700, {"AC": "OFF", "Lights": "OFF"}),
        (26, 3, "14:00", 700, {"AC": "LOW", "Lights": "OFF"}),
        (32, 3, "14:00", 700, {"AC": "HIGH", "Lights": "OFF"}),
        (23, 3, "14:00", 400, {"AC": "OFF", "Lights": "MEDIUM"}),
        (23, 3, "22:00", 50, {"AC": "OFF", "Lights": "ON"}),
        (32, 0, "14:00", 50, {"AC": "OFF", "Lights": "OFF"}),
    ]
    for temperature, occupants, time_of_day, ambient_light, expected in cases:
        result = optimize({
            "temperature": temperature,
            "occupants": occupants,
            "time_of_day": time_of_day,
            "ambient_light": ambient_light,
            "ac": "HIGH",
            "lights": "ON",
        })
        assert result["hill_climbing"]["final_state"] == expected
        assert_valid(result, temperature, occupants, time_of_day, ambient_light)


def test_hill_climbing_trace_and_energy():
    result = optimize({
        "temperature": 32, "occupants": 3, "time_of_day": "14:00",
        "ambient_light": 650, "ac": "HIGH", "lights": "ON"
    })
    hill = result["hill_climbing"]
    assert hill["steps"]
    assert hill["iterations"] == 1
    assert hill["initial_state"] == result["csp"]["best_assignment"]
    assert hill["final_energy"] == result["optimized_energy"]
    assert result["energy_saved"] == result["estimated_energy"] - result["optimized_energy"]
    assert result["energy_reduction_percent"] == 16.67
    assert result["optimized_energy"] <= result["estimated_energy"]
    assert agent.energy_cost({"AC": "LOW", "Lights": "OFF"}) == 3
    assert agent.energy_cost({"AC": "OFF", "Lights": "MEDIUM"}) == 0.5


def test_api_structure_and_zero_energy():
    result = optimize({
        "temperature": 23, "occupants": 0, "time_of_day": "14:00",
        "ambient_light": 700, "ac": "OFF", "lights": "OFF"
    })
    assert result["estimated_energy"] == 0
    assert result["energy_saved"] == 0
    assert result["energy_reduction_percent"] == 0.0
    assert result["csp"]["tree"]
    assert result["csp"]["search_tree"] == result["csp"]["tree"]
    assert result["energy"]["optimized"] == result["optimized_energy"]


def test_invalid_time_and_light_are_rejected():
    assert client.post("/api/optimize", json={"time_of_day": "25:00"}).status_code == 400
    assert client.post("/api/optimize", json={"ambient_light": -1}).status_code == 400


if __name__ == "__main__":
    test_homepage()
    test_scenario_1_hot_day_bright()
    test_scenario_2_vacant()
    test_scenario_3_cool_night_dark()
    test_scenario_4_hot_night_dark()
    test_hill_climbing_trace_and_energy()
    test_api_structure_and_zero_energy()
    test_invalid_time_and_light_are_rejected()
    print("ALL TESTS PASSED SUCCESSFULLY!")
