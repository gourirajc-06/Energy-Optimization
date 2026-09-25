"""
app.py
======
Flask backend for the simple AI Energy Optimization System.
Demonstrates Rule-Based Reasoning and Constraint Checking without Machine Learning.
"""

from flask import Flask, render_template, request, jsonify
from ai_engine import RuleBasedEnergyAgent

app = Flask(__name__)
agent = RuleBasedEnergyAgent()


@app.route("/")
def index():
    """Renders the single-page academic interface."""
    return render_template("index.html")


@app.route("/api/optimize", methods=["POST"])
def optimize():
    """
    POST /api/optimize
    Accepts:
    {
        "temperature": 32,
        "occupants": 3,
        "time_of_day": "14:00",
        "ambient_light": 650,
        "ac": "HIGH",
        "lights": "ON"
    }
    Returns:
    {
        "state": str,
        "observations": list,
        "rules_triggered": list,
        "constraints": list,
        "csp": dict,
        "hill_climbing": dict,
        "estimated_energy": number,
        "optimized_energy": number,
        "energy": dict,
        "decision": str,
        "explanation": str
    }
    """
    data = request.get_json(force=True, silent=True) or {}

    try:
        temperature = float(data.get("temperature", 32.0))
        occupants = max(0, int(data.get("occupants", 1)))
        time_of_day = str(data.get("time_of_day", "14:00"))
        ambient_light = float(data.get("ambient_light", 650.0))
        ac = _parse_device_state(
            data.get("ac", "HIGH"), {"OFF", "LOW", "HIGH"}, "HIGH"
        )
        lights = _parse_device_state(
            data.get("lights", "ON"), {"OFF", "MEDIUM", "ON"}, "ON"
        )
        if not 0 <= ambient_light:
            raise ValueError
        from datetime import datetime
        datetime.strptime(time_of_day, "%H:%M")
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid input data types."}), 400

    result = agent.evaluate(
        temperature, occupants, ac, lights, time_of_day, ambient_light
    )
    return jsonify(result), 200


def _parse_device_state(value, allowed_states, legacy_on_state):
    if isinstance(value, bool):
        legacy_state = legacy_on_state if value else "OFF"
        if legacy_state in allowed_states:
            return legacy_state
    if isinstance(value, str) and value.upper() in allowed_states:
        return value.upper()
    raise ValueError


if __name__ == "__main__":
    print("Starting simplified AI Energy Optimization app on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
