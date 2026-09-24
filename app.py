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
        "ac": true,
        "lights": true
    }
    Returns:
    {
        "state": str,
        "observations": list,
        "rules_triggered": list,
        "constraints": list,
        "decision": str,
        "explanation": str
    }
    """
    data = request.get_json(force=True, silent=True) or {}

    try:
        temperature = float(data.get("temperature", 32.0))
        occupants = max(0, int(data.get("occupants", 1)))
        ac = bool(data.get("ac", True))
        lights = bool(data.get("lights", True))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid input data types."}), 400

    result = agent.evaluate(temperature, occupants, ac, lights)
    return jsonify(result), 200


if __name__ == "__main__":
    print("Starting simplified AI Energy Optimization app on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
