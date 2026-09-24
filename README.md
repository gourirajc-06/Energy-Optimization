# AI Energy Optimization
### Rule-Based Intelligent Agent Demonstration (Non-ML)

A clean, minimalist academic demonstration of classical Artificial Intelligence concepts: **Perception, Rule-Based Reasoning, Constraint Satisfaction, and Decision Making**.

---

## 1. Core AI Concept

The project implements a **Rule-Based Intelligent Agent** that observes the environment, evaluates rules from a knowledge base, checks human comfort constraints, and makes an energy-saving decision:

```text
USER INPUT
    ↓
PERCEPTION
    ↓
RULE EVALUATION (Knowledge Base)
    ↓
CONSTRAINT CHECK
    ↓
AI DECISION
```

---

## 2. Classical AI Concepts Demonstrated

- **Intelligent Agent**: An entity that perceives its environment and takes rational actions.
- **Perception**: Gathers sensor information (temperature, occupants, appliance states).
- **State Representation**: Formats sensory data into a structured state representation.
- **Knowledge Base / Rules**: Stores domain comfort and efficiency principles as logical IF-THEN rules.
- **Rule-Based Reasoning**: Evaluates state conditions against the rules to infer necessary actions.
- **Constraint Checking**: Rejects actions that violate comfort, safety, or occupancy boundaries.
- **Decision Making**: Selects the optimal valid action.
- **Simple Optimization**: Maximizes energy reduction while strictly honoring all constraints.

---

## 3. Project Structure

```text
Energy_Optimization/
├── app.py              # Flask server and POST /api/optimize endpoint
├── ai_engine.py        # Rule-Based AI Agent (Rules & Constraints logic)
├── test_system.py      # Automated scenario verification tests
├── requirements.txt    # Minimal dependencies (Flask)
├── README.md           # Documentation and viva notes
├── templates/
│   └── index.html      # Minimal single-page academic UI
└── static/
    ├── style.css       # Clean, light academic styling
    └── script.js       # Dynamic reasoning flow visualizer
```

---

## 4. How to Run

1. **Install Flask**:
   ```bash
   pip install Flask
   ```

2. **Start the Application**:
   ```bash
   python app.py
   ```

3. **Open in Browser**:
   ```text
   http://127.0.0.1:5000
   ```

4. **Run Automated Tests**:
   ```bash
   python test_system.py
   ```

---

## 5. Demonstration Scenarios for Viva

### Scenario 1: High Temperature with Occupants
- **Input**: Temperature = 32°C, Occupants = 3, AC = ON, Lights = ON
- **Rule Triggered**: `IF temperature > 30°C AND occupants > 0 THEN cooling must remain active.`
- **Constraint Check**:
  - Turning OFF AC → **REJECTED** (occupants require cooling)
  - Turning OFF lights → **ALLOWED**
- **AI Decision**: *Turn OFF unnecessary lighting while keeping AC active.*

### Scenario 2: Vacant Room (Ghost Load Elimination)
- **Input**: Temperature = 28°C, Occupants = 0, AC = ON, Lights = ON
- **Rule Triggered**: `IF occupants == 0 THEN turn OFF unnecessary appliances.`
- **Constraint Check**:
  - Turning OFF AC → **ALLOWED**
  - Turning OFF lights → **ALLOWED**
- **AI Decision**: *Turn OFF both AC and Lights.*

### Scenario 3: Cool Ambient Temperature (Overcooling Prevention)
- **Input**: Temperature = 21°C, Occupants = 2, AC = ON, Lights = ON
- **Rule Triggered**: `IF temperature <= 24°C AND AC == ON THEN turn OFF AC to prevent overcooling.`
- **Constraint Check**:
  - Turning OFF AC → **ALLOWED** (room is already cool)
  - Turning OFF lights → **REJECTED** (occupants need lighting)
- **AI Decision**: *Turn OFF AC and keep room lighting active.*
