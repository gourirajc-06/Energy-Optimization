
"""
AI Energy Optimization
Rule-Based Intelligent Agent + CSP + Backtracking

Classical AI — No Machine Learning.

CSP:
    Variables : AC, Lights
    Domains   : ON, OFF

Backtracking searches the possible appliance configurations,
rejects configurations that violate constraints, and selects
the valid energy-saving configuration.
"""

from typing import Dict, Any, List


class RuleBasedEnergyAgent:

    def evaluate(
        self,
        temperature: float,
        occupants: int,
        ac: bool,
        lights: bool
    ) -> Dict[str, Any]:

        # =========================================================
        # 1. PERCEPTION / STATE REPRESENTATION
        # =========================================================

        state_str = (
            f"Temperature = {temperature}°C | "
            f"Occupants = {occupants} | "
            f"AC = {'ON' if ac else 'OFF'} | "
            f"Lights = {'ON' if lights else 'OFF'}"
        )

        observations = []

        if temperature > 30.0:
            observations.append(
                f"High temperature detected ({temperature}°C)."
            )
        elif temperature <= 24.0:
            observations.append(
                f"Cool temperature detected ({temperature}°C)."
            )
        else:
            observations.append(
                f"Moderate temperature detected ({temperature}°C)."
            )

        if occupants == 0:
            observations.append(
                "Room is vacant (0 occupants)."
            )
        else:
            observations.append(
                f"{occupants} occupant(s) present in the room."
            )

        observations.append(
            f"Air conditioning is currently {'ON' if ac else 'OFF'}."
        )

        observations.append(
            f"Lighting is currently {'ON' if lights else 'OFF'}."
        )

        # =========================================================
        # 2. RULE EVALUATION
        # =========================================================

        rules_triggered = []

        if temperature > 30.0 and occupants > 0:
            rules_triggered.append(
                "RULE 1: IF temperature > 30°C AND occupants > 0 "
                "THEN cooling must remain active for human comfort."
            )

        if occupants == 0 and (ac or lights):
            rules_triggered.append(
                "RULE 2: IF occupants == 0 "
                "THEN turn OFF all active appliances to prevent standby waste."
            )

        if temperature <= 24.0 and ac:
            rules_triggered.append(
                "RULE 3: IF temperature <= 24°C AND AC == ON "
                "THEN turn OFF AC to prevent overcooling discomfort."
            )

        if lights and occupants > 0:
            rules_triggered.append(
                "RULE 4: IF lights == ON AND occupants > 0 "
                "THEN evaluate whether artificial lighting can be reduced."
            )

        # =========================================================
        # 3. CSP + BACKTRACKING
        # =========================================================

        csp_result = self.solve_csp(
            temperature,
            occupants,
            ac,
            lights
        )

        # =========================================================
        # 4. CONSTRAINT OUTPUT
        # =========================================================

        constraints = csp_result["constraints"]

        best_assignment = csp_result["best_assignment"]

        action_ac = best_assignment["AC"] == "ON"
        action_lights = best_assignment["Lights"] == "ON"

        # =========================================================
        # 5. DECISION
        # =========================================================

        if not action_ac and not action_lights:
            decision = "Turn OFF both AC and Lights."

        elif action_ac and not action_lights:
            decision = "Keep AC ON and turn OFF Lights."

        elif not action_ac and action_lights:
            decision = "Turn OFF AC and keep Lights ON."

        else:
            decision = "Keep both AC and Lights ON."

        explanation = (
            f"CSP backtracking explored {len(csp_result['tree'])} "
            f"search nodes and selected the valid configuration "
            f"with the highest energy saving while satisfying all constraints."
        )

        return {
            "state": state_str,
            "observations": observations,
            "rules_triggered": rules_triggered,
            "constraints": constraints,
            "decision": decision,
            "explanation": explanation,

            # NEW
            "csp": {
                "variables": ["AC", "Lights"],
                "domains": {
                    "AC": ["ON", "OFF"],
                    "Lights": ["ON", "OFF"]
                },
                "tree": csp_result["tree"],
                "valid_assignments": csp_result["valid_assignments"],
                "best_assignment": best_assignment,
                "backtracks": csp_result["backtracks"]
            }
        }

    # =============================================================
    # CSP SOLVER
    # =============================================================

    def solve_csp(
        self,
        temperature: float,
        occupants: int,
        current_ac: bool,
        current_lights: bool
    ) -> Dict[str, Any]:

        variables = ["AC", "Lights"]

        domains = {
            "AC": ["OFF", "ON"],
            "Lights": ["OFF", "ON"]
        }

        tree = []
        valid_assignments = []
        backtracks = 0

        # ---------------------------------------------------------
        # Backtracking function
        # ---------------------------------------------------------

        def backtrack(assignment: Dict[str, str], depth: int = 0):

            nonlocal backtracks

            # -----------------------------------------------------
            # Complete assignment
            # -----------------------------------------------------

            if len(assignment) == len(variables):

                valid, reason = self.check_constraints(
                    assignment,
                    temperature,
                    occupants
                )

                node = {
                    "depth": depth,
                    "assignment": assignment.copy(),
                    "status": "VALID" if valid else "REJECTED",
                    "reason": reason
                }

                tree.append(node)

                if valid:
                    valid_assignments.append(assignment.copy())
                else:
                    backtracks += 1

                return valid

            # -----------------------------------------------------
            # Select next variable
            # -----------------------------------------------------

            variable = variables[len(assignment)]

            # -----------------------------------------------------
            # Try each value in the domain
            # -----------------------------------------------------

            for value in domains[variable]:

                new_assignment = assignment.copy()
                new_assignment[variable] = value

                # Check partial assignment first
                valid, reason = self.check_partial_constraints(
                    new_assignment,
                    temperature,
                    occupants
                )

                node = {
                    "depth": depth,
                    "assignment": new_assignment.copy(),
                    "status": "EXPANDED" if valid else "REJECTED",
                    "reason": reason
                }

                tree.append(node)

                # -------------------------------------------------
                # Constraint violation → BACKTRACK
                # -------------------------------------------------

                if not valid:
                    backtracks += 1

                    tree.append({
                        "depth": depth,
                        "assignment": new_assignment.copy(),
                        "status": "BACKTRACK",
                        "reason": "Constraint violated. Backtracking."
                    })

                    continue

                # -------------------------------------------------
                # Continue recursively
                # -------------------------------------------------

                backtrack(new_assignment, depth + 1)

        # Start search
        backtrack({})

        # =========================================================
        # Select best valid assignment
        # =========================================================

        if valid_assignments:

            best_assignment = min(
                valid_assignments,
                key=lambda x: self.energy_cost(x)
            )

        else:

            # Safety fallback
            best_assignment = {
                "AC": "ON" if current_ac else "OFF",
                "Lights": "ON" if current_lights else "OFF"
            }

        # =========================================================
        # Generate human-readable constraint results
        # =========================================================

        constraints = self.generate_constraint_messages(
            temperature,
            occupants,
            current_ac,
            current_lights
        )

        return {
            "tree": tree,
            "valid_assignments": valid_assignments,
            "best_assignment": best_assignment,
            "backtracks": backtracks,
            "constraints": constraints
        }

    # =============================================================
    # PARTIAL CSP CONSTRAINT CHECK
    # =============================================================

    def check_partial_constraints(
        self,
        assignment: Dict[str, str],
        temperature: float,
        occupants: int
    ):

        # ---------------------------------------------------------
        # Constraint 1:
        # High temperature + occupants requires AC ON
        # ---------------------------------------------------------

        if (
            temperature > 30.0
            and occupants > 0
            and assignment.get("AC") == "OFF"
        ):
            return (
                False,
                "REJECTED: High temperature with occupants "
                "requires AC to remain ON."
            )

        # ---------------------------------------------------------
        # Constraint 2:
        # Vacant room requires both appliances OFF
        # ---------------------------------------------------------

        if occupants == 0:

            if assignment.get("AC") == "ON":
                return (
                    False,
                    "REJECTED: Vacant room must have AC OFF."
                )

            if assignment.get("Lights") == "ON":
                return (
                    False,
                    "REJECTED: Vacant room must have Lights OFF."
                )

        # ---------------------------------------------------------
        # Constraint 3:
        # Cool temperature requires AC OFF
        # ---------------------------------------------------------

        if (
            temperature <= 24.0
            and assignment.get("AC") == "ON"
        ):
            return (
                False,
                "REJECTED: Temperature <= 24°C; "
                "AC should be OFF."
            )

        return (
            True,
            "Constraint satisfied. Continue searching."
        )

    # =============================================================
    # COMPLETE CSP CONSTRAINT CHECK
    # =============================================================

    def check_constraints(
        self,
        assignment: Dict[str, str],
        temperature: float,
        occupants: int
    ):

        valid, reason = self.check_partial_constraints(
            assignment,
            temperature,
            occupants
        )

        if not valid:
            return False, reason

        # ---------------------------------------------------------
        # Lighting constraint
        #
        # For occupied rooms, lighting may remain ON.
        # Turning it OFF is permitted.
        # ---------------------------------------------------------

        if occupants > 0 and assignment["Lights"] == "OFF":
            return (
                True,
                "VALID: Lighting can be reduced while occupants "
                "remain comfortable."
            )

        return (
            True,
            "VALID: Configuration satisfies all constraints."
        )

    # =============================================================
    # ENERGY COST FUNCTION
    # =============================================================

    def energy_cost(self, assignment: Dict[str, str]) -> int:

        """
        Lower cost = lower energy consumption.

        Approximate relative energy costs:
            AC     = 5
            Lights = 1
        """

        cost = 0

        if assignment["AC"] == "ON":
            cost += 5

        if assignment["Lights"] == "ON":
            cost += 1

        return cost

    # =============================================================
    # HUMAN-READABLE CONSTRAINT MESSAGES
    # =============================================================

    def generate_constraint_messages(
        self,
        temperature: float,
        occupants: int,
        current_ac: bool,
        current_lights: bool
    ):

        constraints = []

        # AC
        if occupants == 0:

            constraints.append(
                "Turning OFF AC -> ALLOWED "
                "(No occupants present)."
            )

        elif temperature > 30:

            constraints.append(
                "Turning OFF AC -> REJECTED "
                "(Occupants require cooling in high temperature)."
            )

        elif temperature <= 24:

            constraints.append(
                "Turning OFF AC -> ALLOWED "
                "(Temperature is already cool)."
            )

        else:

            constraints.append(
                "Turning OFF AC -> ALLOWED "
                "(Moderate temperature; cooling can be reduced)."
            )

        # Lights
        if occupants == 0:

            constraints.append(
                "Turning OFF lights -> ALLOWED "
                "(No occupants present)."
            )

        else:

            constraints.append(
                "Turning OFF lights -> ALLOWED "
                "(Lighting can be reduced without violating "
                "thermal comfort)."
            )

        return constraints


### What this adds
""""
For example, with:

```text
Temperature = 32
Occupants = 3
AC = ON
Lights = ON
```

the CSP starts with:

```text
                    {}
                  /    \
              AC=OFF   AC=ON
                X        |
                     /         \
              Lights=OFF    Lights=ON
                  |              |
                VALID          VALID
```

The `AC=OFF` branch is immediately rejected because:

```text
Temperature > 30 AND occupants > 0
→ AC must remain ON
```

So the algorithm **backtracks** and explores `AC=ON`.

That is an actual CSP search rather than simply writing:

```python
if temperature > 30:
    action_ac = True
```

---

## 2. Update `app.py`

Your current Flask endpoint simply calls `agent.evaluate()` and returns its result.

You actually don't need to change much. The new `evaluate()` already returns the CSP information.

I recommend only changing the docstring so it documents the new response:"""