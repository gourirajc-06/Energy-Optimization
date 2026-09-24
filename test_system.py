"""
test_system.py
==============
Automated tests for the simplified AI Energy Optimization project:
1. GET / (Homepage rendering and presence of required sections)
2. Scenario 1 (Hot Day / Comfort Constraint / Lights Reduced)
3. Scenario 2 (Vacant Room / Shutdown)
4. Scenario 3 (Cool Temperature / AC turned OFF)
5. Decision differentiation across different inputs
"""

import json
from app import app

client = app.test_client()


def test_homepage():
    print("Testing GET / ...")
    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "AI Energy Optimization" in html
    assert "Environment Input" in html
    assert "AI Reasoning Flow" in html
    assert "PERCEPTION" in html
    assert "RULE EVALUATION" in html
    assert "CONSTRAINT CHECK" in html
    assert "AI DECISION" in html
    assert "AI Concepts Demonstrated" not in html
    print("[PASS] Homepage contains all required visualizer sections.")


def test_scenario_1_hot():
    print("\nTesting Scenario 1: Temperature = 32C, Occupants = 3, AC = ON, Lights = ON...")
    payload = {
        "temperature": 32.0,
        "occupants": 3,
        "ac": True,
        "lights": True
    }
    res = client.post("/api/optimize", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()

    print(f"  Perception: {data['state']}")
    print(f"  Rules: {data['rules_triggered']}")
    print(f"  Constraints: {data['constraints']}")
    print(f"  Decision: {data['decision']}")
    print(f"  Explanation: {data['explanation']}")

    # Verify rule 1 fired
    assert any("RULE 1" in r for r in data["rules_triggered"])
    # Verify turning OFF AC is REJECTED
    assert any("Turning OFF AC -> REJECTED" in c for c in data["constraints"])
    # Verify decision
    assert "unnecessary lighting" in data["decision"]
    print("[PASS] Scenario 1 verified: AC cooling preserved, lights reduced.")


def test_scenario_2_vacant():
    print("\nTesting Scenario 2: Temperature = 28C, Occupants = 0, AC = ON, Lights = ON...")
    payload = {
        "temperature": 28.0,
        "occupants": 0,
        "ac": True,
        "lights": True
    }
    res = client.post("/api/optimize", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()

    print(f"  Rules: {data['rules_triggered']}")
    print(f"  Constraints: {data['constraints']}")
    print(f"  Decision: {data['decision']}")

    # Verify rule 2 fired
    assert any("RULE 2" in r for r in data["rules_triggered"])
    # Verify both allowed
    assert any("Turning OFF AC -> ALLOWED" in c for c in data["constraints"])
    assert any("Turning OFF lights -> ALLOWED" in c for c in data["constraints"])
    assert "Turn OFF both AC and Lights" in data["decision"]
    print("[PASS] Scenario 2 verified: Vacant room shuts down all appliances.")


def test_scenario_3_cool():
    print("\nTesting Scenario 3: Temperature = 21C, Occupants = 2, AC = ON, Lights = ON...")
    payload = {
        "temperature": 21.0,
        "occupants": 2,
        "ac": True,
        "lights": True
    }
    res = client.post("/api/optimize", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()

    print(f"  Rules: {data['rules_triggered']}")
    print(f"  Constraints: {data['constraints']}")
    print(f"  Decision: {data['decision']}")

    # Verify rule 3 fired
    assert any("RULE 3" in r for r in data["rules_triggered"])
    assert any("Turning OFF AC -> ALLOWED" in c for c in data["constraints"])
    assert any("Turning OFF lights -> REJECTED" in c for c in data["constraints"])
    assert "Turn OFF AC and keep room lighting active" in data["decision"]
    print("[PASS] Scenario 3 verified: Cool room turns off AC, preserves occupant lighting.")


def test_differentiation():
    print("\nTesting Decision Differentiation...")
    r1 = client.post("/api/optimize", data=json.dumps({"temperature": 32, "occupants": 3, "ac": True, "lights": True}), content_type="application/json").get_json()
    r2 = client.post("/api/optimize", data=json.dumps({"temperature": 28, "occupants": 0, "ac": True, "lights": True}), content_type="application/json").get_json()
    r3 = client.post("/api/optimize", data=json.dumps({"temperature": 21, "occupants": 2, "ac": True, "lights": True}), content_type="application/json").get_json()

    assert r1["decision"] != r2["decision"]
    assert r2["decision"] != r3["decision"]
    assert r1["decision"] != r3["decision"]
    print("[PASS] All scenarios produce distinct, rational decisions.")


if __name__ == "__main__":
    print("==================================================")
    print("TESTING SIMPLIFIED AI ENERGY OPTIMIZATION")
    print("==================================================")
    test_homepage()
    test_scenario_1_hot()
    test_scenario_2_vacant()
    test_scenario_3_cool()
    test_differentiation()
    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
