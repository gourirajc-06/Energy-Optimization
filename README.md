# AI Energy Optimization
### Rule-Based Intelligent Agent Demonstration (Non-ML)

A clean, minimalist academic demonstration of classical Artificial Intelligence concepts: **Perception, Rule-Based Reasoning, Constraint Satisfaction, Simple Hill Climbing, Energy Comparison, and Decision Making**.

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
CSP BACKTRACKING
    ↓
SIMPLE HILL CLIMBING
    ↓
ENERGY COMPARISON
    ↓
FINAL AI DECISION
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
- **CSP Search**: Finds a feasible appliance configuration through deterministic backtracking.
- **Simple Hill Climbing**: Changes one appliance at a time and accepts only valid lower-energy neighbours.
- **Energy Comparison**: Reports estimated, CSP, and optimized energy plus savings and percentage reduction.

### Environmental inputs and thresholds

The agent accepts temperature, occupancy, time of day, and ambient light intensity.
Time values use `HH:MM`; 06:00 through 17:59 is treated as daylight and the
remaining hours as night. The comfort range is 20–24°C, and 300 lux is the
minimum sufficient ambient-light threshold. These thresholds are centralized in
`ai_engine.py` and are used by perception, rules, constraints, and CSP search.

The controllable devices now use a small deterministic state domain:

- AC: OFF, LOW, or HIGH
- Lights: OFF, MEDIUM, or ON

Energy costs are centralized in `ai_engine.py`: AC OFF/LOW/HIGH costs
0/3/5 units, while Lights OFF/MEDIUM/ON costs 0/0.5/1 units. Hill Climbing
can accept lower-energy states when they remain valid; high-temperature rooms
specifically require AC HIGH for thermal comfort.
Moderate temperatures above 24°C and up to 28°C require AC LOW. Ambient light
below 200 lux requires Lights ON; 200–500 lux requires at least Lights MEDIUM;
above 500 lux permits Lights OFF.

Rules explain cooling and lighting demand. Hard constraints require both devices
OFF in vacant rooms, require AC ON for occupied rooms above 24°C, and require
Lights ON for occupied rooms below 300 lux. Otherwise, the CSP may select OFF
states to reduce energy.

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

## 5. Optimization Pipeline and API Metrics

The CSP remains the first search stage. Its valid configuration becomes the initial state for Simple Hill Climbing. Hill Climbing evaluates neighbours created by changing one appliance at a time, rejects invalid configurations, accepts only lower-energy states, and stops at a local optimum.

The API exposes `perception`, the existing flat energy fields
(`estimated_energy`, `csp_energy`, `hill_climbing_initial_energy`,
`optimized_energy`, `energy_saved`, and `energy_reduction_percent`), a grouped
`energy` object, the CSP search tree, and a `hill_climbing` object containing the
initial and final states, energies, evaluated steps, iteration count, and
termination reason.

## 6. Demonstration Scenarios for Viva

### Scenario 1: Hot Day with Bright Ambient Light
- **Input**: Temperature = 32°C, Occupants = 3, Time = 14:00, Ambient Light = 650 lux
- **Reasoning**: The room is occupied and hot, while daylight and ambient light make artificial lighting unnecessary.
- **Constraint Check**:
  - Turning OFF AC → **REJECTED** (occupants require cooling)
  - Turning OFF lights → **ALLOWED**
- **AI Decision**: *Turn OFF unnecessary lighting while keeping AC active.*

### Scenario 2: Vacant Room
- **Input**: Temperature = 23°C, Occupants = 0, Time = 14:00, Ambient Light = 700 lux
- **Reasoning**: Vacancy requires both devices to be OFF.
- **Constraint Check**:
  - Turning OFF AC → **ALLOWED**
  - Turning OFF lights → **ALLOWED**
- **AI Decision**: *Turn OFF both AC and Lights.*

### Scenario 3: Cool Night with Low Ambient Light
- **Input**: Temperature = 23°C, Occupants = 2, Time = 22:00, Ambient Light = 20 lux
- **Reasoning**: The temperature is comfortable, but occupied low-light conditions require Lights ON.
- **Constraint Check**:
  - Turning OFF AC → **ALLOWED** (room is already cool)
  - Turning OFF lights → **REJECTED** (occupants need lighting)
- **AI Decision**: *Turn OFF AC and keep room lighting active.*

### Scenario 4: Hot Night with Low Ambient Light
- **Input**: Temperature = 32°C, Occupants = 3, Time = 22:00, Ambient Light = 10 lux
- **Reasoning**: High temperature requires AC and occupied low-light conditions require Lights.
