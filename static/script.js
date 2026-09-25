/**
 * script.js
 * Frontend controller for AI Energy Optimization.
 * Submits environment state to Flask /api/optimize and visualizes the vertical reasoning flow.
 */

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ai-form");

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        runAI();
    });

    // Run automatically on load with initial default values
    runAI();

    async function runAI() {
        const temperature = parseFloat(document.getElementById("temperature").value);
        const occupants = parseInt(document.getElementById("occupants").value, 10);
        const timeOfDay = document.getElementById("time-of-day").value;
        const ambientLight = parseFloat(document.getElementById("ambient-light").value);
        const ac = document.querySelector('input[name="ac"]:checked').value;
        const lights = document.querySelector('input[name="lights"]:checked').value;

        const payload = {
            temperature: temperature,
            occupants: occupants,
            time_of_day: timeOfDay,
            ambient_light: ambientLight,
            ac: ac,
            lights: lights
        };

        const runBtn = document.getElementById("run-btn");
        runBtn.disabled = true;
        runBtn.textContent = "Reasoning...";

        try {
            const response = await fetch("/api/optimize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                alert("Error executing AI decision.");
                return;
            }

            const data = await response.json();
            renderReasoningFlow(data, payload);

        } catch (error) {
            console.error("Failed to connect to AI backend:", error);
            alert("Could not reach backend API.");
        } finally {
            runBtn.disabled = false;
            runBtn.textContent = "Run AI";
        }
    }

    function renderReasoningFlow(data, inputState) {
        // -------------------------------------------------------------
        // CARD 1: PERCEPTION
        // -------------------------------------------------------------
        const perceptionContainer = document.getElementById("perception-content");
        perceptionContainer.innerHTML = `
            <div class="state-pill-group">
                <span class="state-pill">Temperature: ${inputState.temperature}°C</span>
                <span class="state-pill">Occupants: ${inputState.occupants}</span>
                <span class="state-pill">Time: ${inputState.time_of_day}</span>
                <span class="state-pill">Ambient Light: ${inputState.ambient_light} lux</span>
                <span class="state-pill">AC: ${inputState.ac}</span>
                <span class="state-pill">Lights: ${inputState.lights}</span>
            </div>
            <ul class="observations-list">
                ${data.observations.map(obs => `<li>${obs}</li>`).join('')}
            </ul>
            <div class="perception-facts">
                ${Object.entries(data.perception || {})
                    .filter(([key]) => !["temperature", "occupants", "time_of_day", "ambient_light"].includes(key))
                    .map(([key, value]) => `<span class="state-pill">${key.replaceAll("_", " ")}: ${value}</span>`)
                    .join("")}
            </div>
        `;

        // -------------------------------------------------------------
        // CARD 2: RULE EVALUATION
        // -------------------------------------------------------------
        const rulesContainer = document.getElementById("rules-content");
        if (!data.rules_triggered || data.rules_triggered.length === 0) {
            rulesContainer.innerHTML = `<p class="placeholder-text">No rules triggered for current state.</p>`;
        } else {
            rulesContainer.innerHTML = data.rules_triggered.map(rule => `
                <div class="rule-box">${rule}</div>
            `).join('');
        }

        // -------------------------------------------------------------
        // CARD 3: CONSTRAINT CHECK
        // -------------------------------------------------------------
        const constraintsContainer = document.getElementById("constraints-content");
        if (!data.constraints || data.constraints.length === 0) {
            constraintsContainer.innerHTML = `<p class="placeholder-text">No active constraints evaluated.</p>`;
        } else {
            constraintsContainer.innerHTML = data.constraints.map(c => {
                let cssClass = "constraint-na";
                if (c.includes("REJECTED")) {
                    cssClass = "constraint-rejected";
                } else if (c.includes("ALLOWED")) {
                    cssClass = "constraint-allowed";
                }
                return `<div class="constraint-item ${cssClass}">${c}</div>`;
            }).join('');
        }

// -------------------------------------------------------------
// CARD 4: GRAPHICAL CSP SEARCH TREE
// -------------------------------------------------------------

const cspContainer = document.getElementById("csp-content");

if (data.csp) {

    const csp = data.csp;

    // ---------------------------------------------------------
    // Remove BACKTRACK records from the actual tree.
    // Backtracking is shown as a status on the rejected branch.
    // ---------------------------------------------------------

    const searchNodes = csp.tree.filter(
        node => node.status !== "BACKTRACK"
    );

    // ---------------------------------------------------------
    // Build hierarchical tree from depth information
    // ---------------------------------------------------------

    const root = {
        children: []
    };

    const stack = [root];

    searchNodes.forEach(node => {

        const treeNode = {
            ...node,
            children: []
        };

        // Find parent based on depth
        const parentDepth = node.depth;

        while (stack.length > parentDepth + 1) {
            stack.pop();
        }

        const parent = stack[stack.length - 1];

        parent.children.push(treeNode);

        stack.push(treeNode);
    });


    // ---------------------------------------------------------
    // Recursive HTML generator
    // ---------------------------------------------------------

    function renderTreeNode(node) {

        let statusClass = "tree-expanded";
        let statusIcon = "→";

        if (node.status === "VALID") {
            statusClass = "tree-valid";
            statusIcon = "✓";
        }

        else if (node.status === "REJECTED") {
            statusClass = "tree-rejected";
            statusIcon = "✗";
        }

        const assignment =
            Object.entries(node.assignment)
                .map(([key, value]) => `${key} = ${value}`)
                .join(", ");

        const childConnector = node.children && node.children.length > 0
            ? `<div class="csp-child-connector" aria-hidden="true"></div>`
            : "";

        let html = `
            <li class="csp-tree-node">

                <div class="csp-branch-line">

                    <div class="csp-node-card ${statusClass}">

                        <div class="csp-node-header">

                            <span class="csp-node-icon">
                                ${statusIcon}
                            </span>

                            <span class="csp-node-assignment">
                                ${assignment}
                            </span>

                            <span class="csp-node-status">
                                ${node.status}
                            </span>

                        </div>

                        <div class="csp-node-reason">
                            ${node.reason}
                        </div>

                        ${
                            node.status === "REJECTED"
                            ? `
                                <div class="csp-backtrack-label">
                                    ↩ BACKTRACK
                                </div>
                            `
                            : ""
                        }

                    </div>

                </div>
                ${childConnector}
        `;

        // Render children recursively
        if (node.children && node.children.length > 0) {

            html += `
                <ul class="csp-tree-children">
            `;

            node.children.forEach(child => {
                html += renderTreeNode(child);
            });

            html += `
                </ul>
            `;
        }

        html += `
            </li>
        `;

        return html;
    }


    // ---------------------------------------------------------
    // Generate tree HTML
    // ---------------------------------------------------------

    let treeHTML = `

        <div class="csp-summary">

            <div class="csp-info">
                <strong>Variables:</strong>
                AC, Lights
            </div>

            <div class="csp-info">
                <strong>Domains:</strong>
                AC = {OFF, LOW, HIGH},
                Lights = {OFF, MEDIUM, ON}
            </div>

            <div class="csp-info">
                <strong>Backtracking Events:</strong>
                ${csp.backtracks}
            </div>

            <div class="csp-info">
                <strong>Valid Assignments:</strong>
                ${csp.valid_assignments.length}
            </div>

        </div>


        <div class="graphical-tree-section">

            <div class="tree-title">
                CSP SEARCH TREE
            </div>

            <div class="csp-tree-container">

                <div class="csp-root">
                    <span class="root-icon">●</span>
                    CSP ROOT
                </div>

                <div class="root-vertical-line"></div>

                <ul class="csp-tree-root">
    `;


    root.children.forEach(node => {
        treeHTML += renderTreeNode(node);
    });


    treeHTML += `

                </ul>

            </div>

        </div>


        <div class="best-assignment">

            <strong>Best CSP Assignment:</strong>

            AC = ${csp.best_assignment.AC},
            Lights = ${csp.best_assignment.Lights}

        </div>

    `;

    cspContainer.innerHTML = treeHTML;

}
else {

    cspContainer.innerHTML = `
        <p class="placeholder-text">
            CSP data unavailable.
        </p>
    `;
}


// -------------------------------------------------------------
// CARD 5: SIMPLE HILL CLIMBING
// -------------------------------------------------------------

const hillClimbingContainer =
    document.getElementById("hill-climbing-content");
const hillClimbing = data.hill_climbing;

if (hillClimbing) {
    const steps = hillClimbing.steps.map((step, index) => `
        <div class="hill-step ${step.accepted ? "hill-accepted" : "hill-rejected"}">
            <div class="hill-step-header">
                <strong>Neighbour ${index + 1}</strong>
                <span>${step.accepted ? "ACCEPTED" : "REJECTED"}</span>
            </div>
            <div class="hill-step-state">
                Current: AC = ${step.current_state.AC}, Lights = ${step.current_state.Lights}
                → Candidate: AC = ${step.candidate_state.AC}, Lights = ${step.candidate_state.Lights}
            </div>
            <div>Candidate energy: ${step.candidate_energy} units</div>
            <div>Valid: ${step.valid ? "Yes" : "No"}</div>
            <div class="hill-step-reason">${step.reason}</div>
        </div>
    `).join("");

    hillClimbingContainer.innerHTML = `
        <div class="hill-summary">
            <div><strong>Initial configuration:</strong>
                AC = ${hillClimbing.initial_state.AC},
                Lights = ${hillClimbing.initial_state.Lights}
            </div>
            <div><strong>Initial energy:</strong> ${hillClimbing.initial_energy} units</div>
        </div>
        <div class="hill-neighbours">
            <strong>Neighbours considered:</strong>
            ${steps || '<p class="placeholder-text">No neighbours evaluated.</p>'}
        </div>
        <div class="hill-summary">
            <div><strong>Final configuration:</strong>
                AC = ${hillClimbing.final_state.AC},
                Lights = ${hillClimbing.final_state.Lights}
            </div>
            <div><strong>Final energy:</strong> ${hillClimbing.final_energy} units</div>
            <div><strong>Iterations:</strong> ${hillClimbing.iterations}</div>
            <div><strong>Termination:</strong> ${hillClimbing.termination_reason || hillClimbing.reason}</div>
        </div>
    `;
} else {
    hillClimbingContainer.innerHTML =
        '<p class="placeholder-text">Hill Climbing data unavailable.</p>';
}

// -------------------------------------------------------------
// ENERGY COMPARISON
// -------------------------------------------------------------

const energyContainer = document.getElementById("energy-content");
energyContainer.innerHTML = `
    <div class="energy-grid">
        <div><span>Estimated Energy</span><strong>${data.estimated_energy} units</strong></div>
        <div><span>CSP Energy</span><strong>${data.csp_energy} units</strong></div>
        <div><span>Optimised Energy</span><strong>${data.optimized_energy} units</strong></div>
        <div><span>Energy Saved</span><strong>${data.energy_saved} units</strong></div>
        <div class="energy-reduction"><span>Reduction</span><strong>${data.energy_reduction_percent}%</strong></div>
    </div>
`;

// -------------------------------------------------------------
// FINAL AI DECISION
// -------------------------------------------------------------

const decisionContainer =
    document.getElementById("decision-content");

decisionContainer.innerHTML = `
    <div class="decision-action">
        ${data.decision}
    </div>

    <div class="decision-reason">
        <strong>Reason:</strong>
        ${data.explanation}
    </div>
`;
    }
});
