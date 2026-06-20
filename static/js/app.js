let activeSessionId = null;
let pollingInterval = null;
let chartInstance = null;

// Initialize layout items
document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide Icons
    lucide.createIcons();
    
    // Load historical blueprints on start
    loadDashboardData();
});

// ----------------- VIEW MANAGER -----------------
function navigateTo(targetView) {
    // View groups
    const landing = document.getElementById("landingPage");
    const appShell = document.getElementById("appShell");
    
    if (targetView === 'landing') {
        landing.classList.add("active");
        appShell.classList.remove("active");
        return;
    }
    
    // Show app sheel
    landing.classList.remove("active");
    appShell.classList.add("active");
    
    // Deactivate all sub views
    const subViews = document.querySelectorAll(".sub-view");
    subViews.forEach(v => v.classList.remove("active"));
    
    // Deactivate all sidebar items
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(i => i.classList.remove("active"));
    
    // Show specific view
    const targetDiv = document.getElementById(targetView + "View");
    if (targetDiv) {
        targetDiv.classList.add("active");
    }
    
    // Set active nav item highlight
    const targetNav = document.querySelector(`.nav-item[data-target="${targetView}"]`);
    if (targetNav) {
        targetNav.classList.add("active");
    }
    
    // Trigger sub-view specific loads
    if (targetView === 'dashboard') {
        loadDashboardData();
    } else if (targetView === 'history') {
        loadHistoryTable();
    }
}

// ----------------- DASHBOARD LOADER -----------------
async function loadDashboardData() {
    try {
        const response = await fetch("/api/sessions");
        const data = await response.json();
        const sessions = data.sessions || [];
        
        // Update stats
        document.getElementById("statAnalyses").innerText = sessions.length;
        
        // Populate dashboard table
        const tbody = document.querySelector("#projectsTable tbody");
        tbody.innerHTML = "";
        
        if (sessions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-secondary);">No startups forged yet. Start one under New Analysis!</td></tr>`;
            return;
        }
        
        // Display top 3 recent
        const recent = sessions.slice(0, 3);
        recent.forEach(s => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${s.idea.substring(0, 45)}...</strong></td>
                <td>${s.target_market || 'Global'}</td>
                <td><span class="status-pill ${s.status}">${s.status.toUpperCase()}</span></td>
                <td><button class="glass-btn" onclick="viewSessionBlueprint('${s.id}')">View</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load dashboard statistics:", e);
    }
}

// ----------------- HISTORY TABLE LOADER -----------------
async function loadHistoryTable() {
    try {
        const response = await fetch("/api/sessions");
        const data = await response.json();
        const sessions = data.sessions || [];
        const tbody = document.querySelector("#historyTable tbody");
        tbody.innerHTML = "";
        
        if (sessions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-secondary);">No historical records found.</td></tr>`;
            return;
        }
        
        sessions.forEach(s => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${s.idea.substring(0, 60)}...</strong></td>
                <td>${s.target_market || 'Global'}</td>
                <td><span class="status-pill ${s.status}">${s.status.toUpperCase()}</span></td>
                <td><button class="glass-btn" onclick="viewSessionBlueprint('${s.id}')">View Blueprint</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load history list:", e);
    }
}

// ----------------- NEW ANALYSIS FORM -----------------
function useExample(exampleText) {
    document.getElementById("startupIdea").value = exampleText;
}

async function submitStartupAnalysis() {
    const idea = document.getElementById("startupIdea").value;
    const market = document.getElementById("ideaMarket").value;
    const industry = document.getElementById("ideaIndustry").value;
    
    if (idea.trim().length < 20) {
        alert("Please describe your business idea in more detail (at least 20 characters).");
        return;
    }
    
    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                idea: idea,
                target_market: market,
                industry: industry
            })
        });
        
        if (!response.ok) {
            const err = await response.json();
            alert(`Error: ${err.detail || 'Could not queue generation.'}`);
            return;
        }
        
        const data = await response.json();
        activeSessionId = data.session_id;
        
        // Redirect to agent workspace and start tracking
        navigateTo("agentWorkspace");
        startWorkspaceTracking(activeSessionId);
    } catch (e) {
        console.error("Analyze request failed:", e);
        alert("Server connection failed. Make sure your .env has GEMINI_API_KEY.");
    }
}

// ----------------- AGENT WORKSPACE POLLE -----------------
function startWorkspaceTracking(sessionId) {
    // Reset workspace UI nodes
    resetWorkspaceNodes();
    
    const consoleLogs = document.getElementById("consoleLogs");
    consoleLogs.innerHTML = `<div class="log-entry system-log">Initializing context session pipeline for session: ${sessionId}...</div>`;
    
    // Clear existing interval
    if (pollingInterval) clearInterval(pollingInterval);
    
    // Poll logs every 1.5 seconds
    pollingInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/session/${sessionId}/logs`);
            const data = await res.json();
            const logs = data.logs || [];
            const status = data.status || "started";
            
            updateWorkspaceUI(logs, status);
            
            if (status === "completed") {
                clearInterval(pollingInterval);
                setTimeout(() => {
                    viewSessionBlueprint(sessionId);
                }, 2000);
            } else if (status === "failed_security" || status === "failed") {
                clearInterval(pollingInterval);
                alert("Agent validation failed. The startup idea violates safety or configuration policies.");
            }
        } catch (e) {
            console.error("Logs tracking error:", e);
        }
    }, 1500);
}

function resetWorkspaceNodes() {
    const nodes = ["nodeSecurity", "nodePlanner", "nodeResearch", "nodeFinance", "nodeMarketing", "nodeReviewer"];
    nodes.forEach(n => {
        const node = document.getElementById(n);
        node.className = "pipeline-node";
        node.querySelector(".node-status").innerText = "Waiting";
    });
    
    const conns = ["conn1", "conn2", "conn3", "conn4", "conn5", "conn6", "conn7"];
    conns.forEach(c => {
        document.getElementById(c).className = "pipeline-connection";
    });
    document.getElementById("consoleProgress").innerText = "0% Complete";
}

function updateWorkspaceUI(logs, status) {
    const logBox = document.getElementById("consoleLogs");
    logBox.innerHTML = "";
    
    let activeAgent = null;
    let completedAgents = [];
    
    logs.forEach(log => {
        const time = new Date(log.timestamp).toLocaleTimeString();
        const entry = document.createElement("div");
        entry.className = "log-entry";
        entry.innerHTML = `<strong>[${time}] ${log.agent_name} ── ${log.step_name}:</strong> ${log.thoughts}`;
        logBox.appendChild(entry);
        
        // Track states
        const name = log.agent_name;
        if (log.thoughts.includes("Completed") || log.thoughts.includes("Approved") || log.thoughts.includes("Cleared")) {
            completedAgents.push(name);
        } else {
            activeAgent = name;
        }
    });
    
    // Auto-scroll console
    logBox.scrollTop = logBox.scrollHeight;
    
    // Node selectors map
    const nodeMap = {
        "Security Agent": "nodeSecurity",
        "Planner Agent": "nodePlanner",
        "Research Agent": "nodeResearch",
        "Finance Agent": "nodeFinance",
        "Marketing Agent": "nodeMarketing",
        "Reviewer Agent": "nodeReviewer"
    };

    // Update node colors & connection lines based on logs
    const completedNodeIds = completedAgents.map(name => nodeMap[name]).filter(Boolean);
    const activeNodeId = nodeMap[activeAgent];
    
    // Highlight completed
    completedNodeIds.forEach(id => {
        const node = document.getElementById(id);
        node.classList.add("completed");
        node.classList.remove("running");
        node.querySelector(".node-status").innerText = "Completed";
    });
    
    // Highlight active running
    if (activeNodeId && !completedNodeIds.includes(activeNodeId)) {
        const node = document.getElementById(activeNodeId);
        node.classList.add("running");
        node.classList.remove("completed");
        node.querySelector(".node-status").innerText = "Running";
    }
    
    // Connect pipeline animations based on flow
    if (completedNodeIds.includes("nodeSecurity")) {
        document.getElementById("conn1").classList.add("flowing");
    }
    if (completedNodeIds.includes("nodePlanner")) {
        document.getElementById("conn2").classList.add("flowing");
    }
    if (completedNodeIds.includes("nodeResearch")) {
        document.getElementById("conn3").classList.add("flowing");
    }
    if (completedNodeIds.includes("nodeFinance")) {
        document.getElementById("conn4").classList.add("flowing");
    }
    if (completedNodeIds.includes("nodeMarketing")) {
        document.getElementById("conn5").classList.add("flowing");
    }
    if (completedNodeIds.includes("nodeReviewer")) {
        document.getElementById("conn6").classList.add("flowing");
        document.getElementById("conn7").classList.add("flowing");
        document.getElementById("nodeBlueprint").classList.add("completed");
    }
    
    // Progress calculation estimate
    let progress = Math.min(completedNodeIds.length * 16, 95);
    if (status === "completed") progress = 100;
    document.getElementById("consoleProgress").innerText = `${progress}% Complete`;
}

// ----------------- LOAD & VIEW REPORT -----------------
async function viewSessionBlueprint(sessionId) {
    try {
        const response = await fetch(`/api/session/${sessionId}/blueprint`);
        if (!response.ok) {
            alert("This blueprint is still generating. Check progress on the Agent Workspace tab!");
            return;
        }
        
        const data = await response.json();
        
        // Show report panel view
        navigateTo("report");
        
        // Populate header details
        document.getElementById("repStartupName").innerText = data.startup_name || "Unnamed Project";
        document.getElementById("repOneLiner").innerText = data.one_liner || "Innovation Value Pitch";
        
        // Tab 1: Executive Summary
        document.getElementById("repVisionText").innerText = data.executive_summary || "";
        
        // Tab 2: Market & Competitors
        const rkt = data.market_research || {};
        document.getElementById("repMarketSize").innerText = rkt.market_size_estimate || "";
        document.getElementById("repPersona").innerText = rkt.target_persona || "";
        
        const barriersUl = document.getElementById("repBarriersList");
        barriersUl.innerHTML = "";
        (rkt.industry_barriers || []).forEach(b => {
            const li = document.createElement("li");
            li.innerText = b;
            barriersUl.appendChild(li);
        });
        
        // Tab 3: Financial Projections
        const fin = data.financial_plan || {};
        document.getElementById("repRevenueModel").innerText = fin.revenue_model_description || "";
        document.getElementById("repBreakEven").innerText = fin.break_even_month || "";
        document.getElementById("repFunding").innerText = fin.initial_funding_required || "";
        document.getElementById("repUnitEconomics").innerText = fin.unit_economics || "";
        
        // Tab 4: Marketing Go-to-Market
        const mkt = data.marketing_plan || {};
        document.getElementById("repPositioning").innerText = mkt.brand_positioning || "";
        
        const vpUl = document.getElementById("repValueProps");
        vpUl.innerHTML = "";
        (mkt.value_propositions || []).forEach(vp => {
            const li = document.createElement("li");
            li.innerText = vp;
            vpUl.appendChild(li);
        });
        
        const milestoneUl = document.getElementById("repGtmTimeline");
        milestoneUl.innerHTML = "";
        (mkt.gtm_milestones || []).forEach(m => {
            const li = document.createElement("li");
            li.innerText = m;
            milestoneUl.appendChild(li);
        });
        
        // Tab 5: Telemetry stats
        const audit = data.audit_log || {};
        document.getElementById("repCycles").innerText = audit.cycles_run || 1;
        
        // Pull actual token usage logs from SQLite
        const logsRes = await fetch(`/api/session/${sessionId}/logs`);
        const logsData = await logsRes.json();
        const logsList = logsData.logs || [];
        
        const totalTokens = logsList.reduce((sum, log) => sum + (log.tokens_used || 0), 0);
        const totalTimeMs = logsList.reduce((sum, log) => sum + (log.latency_ms || 0), 0);
        
        document.getElementById("repTokens").innerText = totalTokens.toLocaleString();
        document.getElementById("repTime").innerText = `${(totalTimeMs / 1000).toFixed(2)}s`;
        
        // Render Chart.js Scorecard
        renderEvaluationChart(audit);
        
        // Save globally to support download export
        window.currentBlueprintExportData = data;
    } catch (e) {
        console.error("View blueprint failed:", e);
    }
}

// Switch inner tabs on report view
function switchReportTab(event, tabId) {
    const sections = document.querySelectorAll(".rep-section-content");
    sections.forEach(s => s.classList.remove("active"));
    
    const tabs = document.querySelectorAll(".rep-tab");
    tabs.forEach(t => t.classList.remove("active"));
    
    document.getElementById(tabId).classList.add("active");
    event.currentTarget.classList.add("active");
}

// Render chart metrics using Chart.js
function renderEvaluationChart(audit) {
    const ctx = document.getElementById("scoresChart").getContext("2d");
    
    // Destroy previous instance if it exists to prevent overlay glitches
    if (chartInstance) {
        chartInstance.destroy();
    }
    
    const completeness = audit.completeness_score || 8.5;
    const feasibility = audit.feasibility_score || 8.2;
    const alignment = audit.alignment_score || 8.8;
    
    chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Completeness", "Feasibility", "Alignment"],
            datasets: [{
                label: "Auditor Score (out of 10)",
                data: [completeness, feasibility, alignment],
                backgroundColor: [
                    "rgba(168, 85, 247, 0.6)", // purple
                    "rgba(99, 102, 241, 0.6)", // indigo
                    "rgba(59, 130, 246, 0.6)"  // blue
                ],
                borderColor: [
                    "rgb(168, 85, 247)",
                    "rgb(99, 102, 241)",
                    "rgb(59, 130, 246)"
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    grid: { color: "rgba(255, 255, 255, 0.08)" },
                    ticks: { color: "#9CA3AF" }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: "#9CA3AF" }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// Export formatted Markdown blueprint
function exportBlueprintMarkdown() {
    const data = window.currentBlueprintExportData;
    if (!data) return;
    
    const md = `# ${data.startup_name} Startup Blueprint
## ${data.one_liner}

### 1. Executive Summary
${data.executive_summary}

### 2. Market Research
- **TAM/SAM/SOM opportunity**: ${data.market_research?.market_size_estimate}
- **Target Persona Profile**: ${data.market_research?.target_persona}

### 3. Financial Projections
- **Pricing Scheme Model**: ${data.financial_plan?.revenue_model_description}
- **Break-even timeline**: ${data.financial_plan?.break_even_month}
- **Setup Capital Allocations**: ${data.financial_plan?.initial_funding_required}

### 4. Marketing & GTM Timeline
- **Brand Position Narrative**: ${data.marketing_plan?.brand_positioning}
`;

    const blob = new Blob([md], { type: "text/markdown" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${data.startup_name.toLowerCase().replace(/ /g, '_')}_blueprint.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
