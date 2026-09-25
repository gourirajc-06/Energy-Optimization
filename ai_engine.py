"""Deterministic rule-based energy optimization with CSP and hill climbing."""

from datetime import datetime
from typing import Any, Dict, List, Tuple


COMFORT_MIN_TEMPERATURE = 20.0
COMFORT_MAX_TEMPERATURE = 24.0
HIGH_TEMPERATURE_THRESHOLD = 28.0
DAY_START_HOUR = 6
DAY_END_HOUR = 18
LIGHTS_MEDIUM_THRESHOLD = 200.0
LIGHTS_OFF_THRESHOLD = 500.0
AC_DOMAIN = ["OFF", "LOW", "HIGH"]
LIGHTS_DOMAIN = ["OFF", "MEDIUM", "ON"]
ENERGY_COSTS = {
    "AC": {"OFF": 0, "LOW": 3, "HIGH": 5},
    "Lights": {"OFF": 0, "MEDIUM": 0.5, "ON": 1},
}


class RuleBasedEnergyAgent:
    def perceive(
        self,
        temperature: float,
        occupants: int,
        time_of_day: str,
        ambient_light: float
    ) -> Dict[str, Any]:
        hour = datetime.strptime(time_of_day, "%H:%M").hour
        occupied = occupants > 0
        daylight_period = DAY_START_HOUR <= hour < DAY_END_HOUR
        temperature_above_comfort = temperature > COMFORT_MAX_TEMPERATURE
        high_temperature = temperature > HIGH_TEMPERATURE_THRESHOLD
        temperature_within_comfort = (
            COMFORT_MIN_TEMPERATURE <= temperature <= COMFORT_MAX_TEMPERATURE
        )
        ambient_light_sufficient = ambient_light > LIGHTS_OFF_THRESHOLD
        ambient_light_insufficient = ambient_light < LIGHTS_MEDIUM_THRESHOLD

        return {
            "temperature": temperature,
            "occupants": occupants,
            "time_of_day": time_of_day,
            "ambient_light": ambient_light,
            "occupied": occupied,
            "vacant": not occupied,
            "daylight_period": daylight_period,
            "night_period": not daylight_period,
            "temperature_above_comfort": temperature_above_comfort,
            "high_temperature": high_temperature,
            "moderate_temperature": (
                COMFORT_MAX_TEMPERATURE < temperature <= HIGH_TEMPERATURE_THRESHOLD
            ),
            "temperature_within_comfort": temperature_within_comfort,
            "ambient_light_sufficient": ambient_light_sufficient,
            "ambient_light_insufficient": ambient_light_insufficient,
            "ambient_light_moderate": (
                LIGHTS_MEDIUM_THRESHOLD <= ambient_light <= LIGHTS_OFF_THRESHOLD
            ),
            "cooling_demand": occupied and temperature_above_comfort,
            "lighting_demand": occupied and not ambient_light_sufficient,
        }

    def evaluate(
        self,
        temperature: float,
        occupants: int,
        ac: str,
        lights: str,
        time_of_day: str = "14:00",
        ambient_light: float = 650.0
    ) -> Dict[str, Any]:
        perception = self.perceive(
            temperature, occupants, time_of_day, ambient_light
        )
        state_str = (
            f"Temperature = {temperature}°C | Occupants = {occupants} | "
            f"Time = {time_of_day} | Ambient Light = {ambient_light:g} lux | "
            f"AC = {ac} | Lights = {lights}"
        )

        observations = [
            self._temperature_observation(temperature),
            (
                "Room is vacant (0 occupants)."
                if not perception["occupied"]
                else f"{occupants} occupant(s) present in the room."
            ),
            (
                f"{time_of_day} is in the daylight period."
                if perception["daylight_period"]
                else f"{time_of_day} is in the night period."
            ),
            (
                f"Ambient light is sufficient ({ambient_light:g} lux)."
                if perception["ambient_light_sufficient"]
                else f"Ambient light is insufficient ({ambient_light:g} lux)."
            ),
            f"Air conditioning is currently {ac}.",
            f"Lighting is currently {lights}.",
        ]

        rules_triggered = self.evaluate_rules(perception, ac, lights)
        csp_result = self.solve_csp(
            temperature, occupants, time_of_day, ambient_light, ac, lights
        )
        csp_assignment = csp_result["best_assignment"]
        hill_climbing = self.simple_hill_climbing(
            csp_assignment, temperature, occupants, time_of_day, ambient_light
        )
        optimized_assignment = hill_climbing["final_state"]

        estimated_energy = self.energy_cost({
            "AC": ac,
            "Lights": lights
        })
        csp_energy = self.energy_cost(csp_assignment)
        optimized_energy = hill_climbing["final_energy"]
        energy_saved = max(0, estimated_energy - optimized_energy)
        reduction = (
            (energy_saved / estimated_energy) * 100
            if estimated_energy else 0.0
        )
        decision = self.generate_decision(optimized_assignment)
        moved = hill_climbing["iterations"] > 0
        explanation = (
            "CSP backtracking identified a feasible configuration. "
            "Simple Hill Climbing evaluated valid neighbouring configurations "
            "and selected a lower-energy configuration."
            if moved else
            "CSP backtracking identified a feasible configuration. "
            "Simple Hill Climbing evaluated neighbouring configurations but "
            "found no valid lower-energy move."
        )

        return {
            "state": state_str,
            "observations": observations,
            "perception": perception,
            "rules_triggered": rules_triggered,
            "constraints": csp_result["constraints"],
            "decision": decision,
            "explanation": explanation,
            "estimated_energy": estimated_energy,
            "csp_energy": csp_energy,
            "hill_climbing_initial_energy": hill_climbing["initial_energy"],
            "optimized_energy": optimized_energy,
            "energy_saved": energy_saved,
            "energy_reduction_percent": round(reduction, 2),
            "energy": {
                "estimated": estimated_energy,
                "csp": csp_energy,
                "hill_climbing_initial": hill_climbing["initial_energy"],
                "optimized": optimized_energy,
                "saved": energy_saved,
                "reduction_percent": round(reduction, 2),
            },
            "csp": {
                "variables": ["AC", "Lights"],
                "domains": {"AC": AC_DOMAIN, "Lights": LIGHTS_DOMAIN},
                "tree": csp_result["tree"],
                "search_tree": csp_result["tree"],
                "valid_assignments": csp_result["valid_assignments"],
                "feasible_configurations": csp_result["valid_assignments"],
                "best_assignment": csp_assignment,
                "backtracks": csp_result["backtracks"],
                "energy": csp_energy,
            },
            "hill_climbing": hill_climbing,
        }

    @staticmethod
    def _temperature_observation(temperature: float) -> str:
        if temperature > COMFORT_MAX_TEMPERATURE:
            return f"Temperature is above comfort range ({temperature}°C)."
        if temperature < COMFORT_MIN_TEMPERATURE:
            return f"Temperature is below comfort range ({temperature}°C)."
        return f"Temperature is within comfort range ({temperature}°C)."

    def evaluate_rules(
        self, perception: Dict[str, Any], ac: str, lights: str
    ) -> List[str]:
        rules = []
        if perception["vacant"]:
            rules.extend([
                "RULE A: IF the room is unoccupied THEN AC should be OFF.",
                "RULE B: IF the room is unoccupied THEN Lights should be OFF.",
            ])
        if perception["high_temperature"] and perception["occupied"]:
            rules.append(
                "RULE C: IF occupied and temperature is high "
                "THEN AC must remain HIGH."
            )
        elif perception["moderate_temperature"] and perception["occupied"]:
            rules.append(
                "RULE C: IF occupied and temperature is moderate "
                "THEN AC should operate at LOW."
            )
        if perception["temperature_within_comfort"] and ac:
            rules.append(
                "RULE D: IF temperature is within comfort range "
                "THEN AC can be OFF."
            )
        if perception["ambient_light_sufficient"]:
            rules.append(
                "RULE F: IF ambient light is sufficient THEN Lights can be OFF."
            )
        if perception["lighting_demand"]:
            rules.append(
                "RULE E: IF occupied and ambient light is insufficient "
                "THEN Lights may need to remain ON."
            )
        if perception["night_period"]:
            rules.append(
                "RULE G: Night period is considered when evaluating lighting."
            )
        if lights and not rules:
            rules.append("Current lighting is recorded for energy comparison.")
        return rules

    def simple_hill_climbing(
        self,
        initial_state: Dict[str, str],
        temperature: float,
        occupants: int,
        time_of_day: str = "14:00",
        ambient_light: float = 650.0
    ) -> Dict[str, Any]:
        current_state = initial_state.copy()
        initial_energy = self.energy_cost(current_state)
        steps = []
        iterations = 0

        while True:
            improved = False
            current_energy = self.energy_cost(current_state)
            domains = {"AC": AC_DOMAIN, "Lights": LIGHTS_DOMAIN}
            for appliance in ("AC", "Lights"):
                for candidate_value in domains[appliance]:
                    if candidate_value == current_state[appliance]:
                        continue
                    candidate = current_state.copy()
                    candidate[appliance] = candidate_value
                    valid, constraint_reason = self.check_constraints(
                        candidate, temperature, occupants,
                        time_of_day, ambient_light
                    )
                    candidate_energy = self.energy_cost(candidate)
                    accepted = valid and candidate_energy < current_energy
                    reason = (
                        "Accepted: candidate has lower energy than the current state."
                        if accepted else
                        constraint_reason if not valid else
                        "Rejected: candidate does not improve the current state."
                    )
                    steps.append({
                        "current_state": current_state.copy(),
                        "candidate_state": candidate,
                        "candidate_energy": candidate_energy,
                        "valid": valid,
                        "accepted": accepted,
                        "reason": reason,
                    })
                    if accepted:
                        current_state = candidate
                        iterations += 1
                        improved = True
                        break
                if improved:
                    break
            if not improved:
                break

        return {
            "initial_state": initial_state.copy(),
            "initial_energy": initial_energy,
            "steps": steps,
            "final_state": current_state,
            "final_energy": self.energy_cost(current_state),
            "iterations": iterations,
            "reason": "No valid neighbouring configuration improves the final state.",
            "termination_reason": "No valid neighbouring configuration improves the final state.",
        }

    def solve_csp(
        self,
        temperature: float,
        occupants: int,
        time_of_day: str,
        ambient_light: float,
        current_ac: str,
        current_lights: str
    ) -> Dict[str, Any]:
        variables = ["AC", "Lights"]
        domains = {"AC": AC_DOMAIN, "Lights": LIGHTS_DOMAIN}
        tree: List[Dict[str, Any]] = []
        valid_assignments: List[Dict[str, str]] = []
        backtracks = 0

        def backtrack(assignment: Dict[str, str], depth: int = 0) -> None:
            nonlocal backtracks
            if len(assignment) == len(variables):
                valid, reason = self.check_constraints(
                    assignment, temperature, occupants,
                    time_of_day, ambient_light
                )
                tree.append({
                    "depth": depth,
                    "assignment": assignment.copy(),
                    "status": "VALID" if valid else "REJECTED",
                    "reason": reason,
                })
                if valid:
                    valid_assignments.append(assignment.copy())
                else:
                    backtracks += 1
                return

            variable = variables[len(assignment)]
            for value in domains[variable]:
                candidate = assignment.copy()
                candidate[variable] = value
                valid, reason = self.check_partial_constraints(
                    candidate, temperature, occupants,
                    time_of_day, ambient_light
                )
                tree.append({
                    "depth": depth,
                    "assignment": candidate.copy(),
                    "status": "EXPANDED" if valid else "REJECTED",
                    "reason": reason,
                })
                if not valid:
                    backtracks += 1
                    tree.append({
                        "depth": depth,
                        "assignment": candidate.copy(),
                        "status": "BACKTRACK",
                        "reason": "Constraint violated. Backtracking.",
                    })
                    continue
                backtrack(candidate, depth + 1)

        backtrack({})
        current_assignment = {
            "AC": current_ac,
            "Lights": current_lights,
        }
        best_assignment = (
            current_assignment if current_assignment in valid_assignments
            else valid_assignments[0] if valid_assignments
            else current_assignment
        )
        return {
            "tree": tree,
            "valid_assignments": valid_assignments,
            "best_assignment": best_assignment,
            "backtracks": backtracks,
            "constraints": self.generate_constraint_messages(
                temperature, occupants, time_of_day, ambient_light
            ),
        }

    def check_partial_constraints(
        self,
        assignment: Dict[str, str],
        temperature: float,
        occupants: int,
        time_of_day: str = "14:00",
        ambient_light: float = 650.0
    ) -> Tuple[bool, str]:
        if occupants == 0:
            if assignment.get("AC") is not None and assignment.get("AC") != "OFF":
                return False, "REJECTED: Vacant room must have AC OFF."
            if assignment.get("Lights") is not None and assignment.get("Lights") != "OFF":
                return False, "REJECTED: Vacant room must have Lights OFF."
        if occupants > 0 and temperature > COMFORT_MAX_TEMPERATURE:
            required_ac = (
                "HIGH" if temperature > HIGH_TEMPERATURE_THRESHOLD else "LOW"
            )
            if assignment.get("AC") is not None and assignment.get("AC") not in {
                required_ac, "HIGH"
            }:
                return False, "REJECTED: High temperature requires AC HIGH."
        if occupants > 0:
            if ambient_light < LIGHTS_MEDIUM_THRESHOLD:
                if assignment.get("Lights") is not None and assignment.get("Lights") != "ON":
                    return False, "REJECTED: Very low ambient light requires Lights ON."
            elif ambient_light <= LIGHTS_OFF_THRESHOLD:
                if assignment.get("Lights") is not None and assignment.get("Lights") == "OFF":
                    return False, "REJECTED: Moderate ambient light requires Lights MEDIUM or ON."
        return True, "Constraint satisfied. Continue searching."

    def check_constraints(
        self,
        assignment: Dict[str, str],
        temperature: float,
        occupants: int,
        time_of_day: str = "14:00",
        ambient_light: float = 650.0
    ) -> Tuple[bool, str]:
        valid, reason = self.check_partial_constraints(
            assignment, temperature, occupants, time_of_day, ambient_light
        )
        if not valid:
            return False, reason
        return True, "VALID: Configuration satisfies all constraints."

    def generate_constraint_messages(
        self,
        temperature: float,
        occupants: int,
        time_of_day: str = "14:00",
        ambient_light: float = 650.0
    ) -> List[str]:
        messages = []
        ac_off_valid, ac_reason = self.check_constraints(
            {"AC": "OFF", "Lights": "MEDIUM" if occupants else "OFF"},
            temperature, occupants, time_of_day, ambient_light
        )
        lights_off_valid, lights_reason = self.check_constraints(
            {"AC": (
                "HIGH" if temperature > HIGH_TEMPERATURE_THRESHOLD
                else "LOW" if temperature > COMFORT_MAX_TEMPERATURE and occupants
                else "OFF"
            ),
             "Lights": "OFF"},
            temperature, occupants, time_of_day, ambient_light
        )
        messages.append(
            "Turning OFF AC -> ALLOWED (" + ac_reason.replace("VALID: ", "") + ")"
            if ac_off_valid else
            "Turning OFF AC -> REJECTED (" + ac_reason.replace("REJECTED: ", "") + ")"
        )
        messages.append(
            "Turning OFF lights -> ALLOWED (" + lights_reason.replace("VALID: ", "") + ")"
            if lights_off_valid else
            "Turning OFF lights -> REJECTED (" + lights_reason.replace("REJECTED: ", "") + ")"
        )
        return messages

    @staticmethod
    def energy_cost(assignment: Dict[str, str]) -> float:
        return (
            ENERGY_COSTS["AC"][assignment["AC"]]
            + ENERGY_COSTS["Lights"][assignment["Lights"]]
        )

    @staticmethod
    def generate_decision(assignment: Dict[str, str]) -> str:
        ac_state = assignment["AC"]
        lights_state = assignment["Lights"]
        if ac_state == "OFF" and lights_state == "OFF":
            return "Turn OFF both AC and Lights."
        if ac_state != "OFF" and lights_state == "OFF":
            return f"Keep AC at {ac_state} and turn OFF unnecessary lighting."
        if ac_state == "OFF" and lights_state != "OFF":
            return f"Keep AC OFF and set Lights to {lights_state}."
        return f"Keep AC at {ac_state} and Lights at {lights_state}."
