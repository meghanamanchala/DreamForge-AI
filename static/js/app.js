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
const VIEW_LABELS = {
    dashboard: 'Dashboard',
    newAnalysis: 'New Analysis',
    agentWorkspace: 'Agent Workspace',
    liveExecution: 'Live Execution',
    report: 'Reports',
    agents: 'Agents',
    history: 'History',
    settings: 'Settings',
};

function navigateTo(targetView) {
    // View groups
    const landing = document.getElementById("landingPage");
    const appShell = document.getElementById("appShell");
    
    if (targetView === 'landing') {
        landing.classList.add("active");
        appShell.classList.remove("active");
        return;
    }
    
    // Show app shell
    landing.classList.remove("active");
    appShell.classList.add("active");
    
    // Update topbar breadcrumb
    const breadcrumb = document.getElementById("topbarBreadcrumb");
    if (breadcrumb) breadcrumb.textContent = VIEW_LABELS[targetView] || targetView;
    
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
    } else if (targetView === 'report') {
        const reportEmpty = document.getElementById("reportEmptyState");
        const reportContent = document.getElementById("reportContentWrapper");
        if (window.currentBlueprintExportData) {
            reportEmpty.style.display = "none";
            reportContent.style.display = "block";
        } else {
            reportEmpty.style.display = "flex";
            reportContent.style.display = "none";
        }
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
        document.getElementById("statReports").innerText = sessions.filter(s => s.status === 'completed').length;
        
        // Calculate average readiness
        let totalScore = 0;
        let completedCount = 0;
        sessions.forEach(s => {
            if (s.status === 'completed') {
                totalScore += (s.score || 84);
                completedCount++;
            }
        });
        const avgScore = completedCount > 0 ? Math.round(totalScore / completedCount) : 84;
        document.getElementById("statReadiness").innerText = avgScore + "%";
        
        // Render Chart.js line chart for throughput
        renderThroughputChart();
        
        // Populate dashboard table
        const tbody = document.querySelector("#projectsTable tbody");
        tbody.innerHTML = "";
        
        if (sessions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-secondary);">No startups forged yet. Start one under New Analysis!</td></tr>`;
            return;
        }
        
        // Display top 3 recent
        const recent = sessions.slice(0, 3);
        recent.forEach(s => {
            const tr = document.createElement("tr");
            const score = s.score || 85;
            const dateStr = s.created_at ? new Date(s.created_at).toISOString().split('T')[0] : '2026-06-18';
            tr.innerHTML = `
                <td><strong>${s.idea.substring(0, 45)}...</strong></td>
                <td>${dateStr}</td>
                <td>
                    <div class="table-progress-cell">
                        <div class="metric-bar mini-bar"><div class="metric-bar-fill purple-fill" style="width: ${score}%;"></div></div>
                        <span class="score-num">${score}</span>
                    </div>
                </td>
                <td><span class="status-pill ${s.status}">${s.status.toUpperCase()}</span></td>
                <td><a href="#" class="open-link" onclick="viewSessionBlueprint('${s.id}'); event.preventDefault();">Open</a></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load dashboard statistics:", e);
    }
}

// Render Dashboard line chart for pipeline throughput
function renderThroughputChart() {
    const ctx = document.getElementById("throughputChart").getContext("2d");
    
    if (window.throughputChartInstance) {
        window.throughputChartInstance.destroy();
    }
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 160);
    gradient.addColorStop(0, "rgba(168, 85, 247, 0.4)");
    gradient.addColorStop(1, "rgba(168, 85, 247, 0.0)");
    
    window.throughputChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: ["M1", "M3", "M6", "M9", "M12", "M15", "M18", "M24"],
            datasets: [{
                data: [4, 12, 28, 45, 80, 128, 200, 320],
                borderColor: "#a855f7",
                borderWidth: 2,
                fill: true,
                backgroundColor: gradient,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "#71717a", font: { size: 10 } }
                },
                y: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#71717a", font: { size: 10 } },
                    border: { dash: [4, 4] }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// ----------------- HISTORY TABLE LOADER -----------------
async function loadHistoryTable() {
    try {
        const response = await fetch("/api/sessions");
        const data = await response.json();
        const sessions = data.sessions || [];
        const tbody = document.querySelector("#historyTable tbody");
        tbody.innerHTML = "";

        // Inject/update the Clear All toolbar button
        let toolbar = document.getElementById("historyToolbar");
        if (!toolbar) {
            const historyView = document.getElementById("historyView");
            const tableWrapper = historyView ? historyView.querySelector(".table-wrapper, table") : null;
            toolbar = document.createElement("div");
            toolbar.id = "historyToolbar";
            toolbar.style.cssText = "display:flex;justify-content:flex-end;align-items:center;gap:10px;margin-bottom:12px;";
            if (tableWrapper) {
                tableWrapper.parentNode.insertBefore(toolbar, tableWrapper);
            }
        }
        toolbar.innerHTML = sessions.length > 0
            ? `<button id="clearAllHistoryBtn" onclick="clearAllHistory()" style="
                display:flex;align-items:center;gap:6px;padding:7px 14px;
                background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.35);
                color:#f87171;border-radius:8px;cursor:pointer;font-size:13px;
                font-weight:600;transition:all .2s;
               " onmouseover="this.style.background='rgba(239,68,68,0.25)'" onmouseout="this.style.background='rgba(239,68,68,0.12)'">
                <svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='3 6 5 6 21 6'></polyline><path d='M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2'></path></svg>
                Clear All History
              </button>`
            : ``;
        
        if (sessions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-secondary);">No historical records found.</td></tr>`;
            return;
        }
        
        sessions.forEach(s => {
            const tr = document.createElement("tr");
            const score = s.score || 85;
            const dateStr = s.created_at ? new Date(s.created_at).toISOString().split('T')[0] : '2026-06-18';
            tr.innerHTML = `
                <td><strong>${s.idea.substring(0, 60)}...</strong></td>
                <td>${s.industry || 'SaaS'}</td>
                <td>
                    <div class="table-progress-cell">
                        <div class="metric-bar mini-bar"><div class="metric-bar-fill purple-fill" style="width: ${score}%;"></div></div>
                        <span class="score-num">${score}</span>
                    </div>
                </td>
                <td>${dateStr}</td>
                <td><a href="#" class="view-report-link" onclick="viewSessionBlueprint('${s.id}'); event.preventDefault();">View ↗</a></td>
                <td>
                    <button onclick="deleteSession('${s.id}', this)" title="Delete this entry" style="
                        background:rgba(239,68,68,0.10);border:1px solid rgba(239,68,68,0.25);
                        color:#f87171;border-radius:6px;padding:4px 8px;cursor:pointer;
                        font-size:12px;transition:all .2s;display:inline-flex;align-items:center;gap:4px;
                    " onmouseover="this.style.background='rgba(239,68,68,0.28)'" onmouseout="this.style.background='rgba(239,68,68,0.10)'">
                        <svg xmlns='http://www.w3.org/2000/svg' width='13' height='13' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='3 6 5 6 21 6'></polyline><path d='M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2'></path></svg>
                        Delete
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load history list:", e);
    }
}

// Delete a single history session
async function deleteSession(sessionId, btnEl) {
    if (!confirm("Delete this analysis? This cannot be undone.")) return;
    try {
        btnEl.disabled = true;
        btnEl.textContent = "Deleting...";
        const res = await fetch(`/api/session/${sessionId}`, { method: "DELETE" });
        if (!res.ok) throw new Error("Delete failed");
        // Animate row out
        const row = btnEl.closest("tr");
        row.style.transition = "opacity .3s, transform .3s";
        row.style.opacity = "0";
        row.style.transform = "translateX(20px)";
        setTimeout(() => loadHistoryTable(), 320);
    } catch (e) {
        console.error("Delete session error:", e);
        alert("Failed to delete. Please try again.");
        btnEl.disabled = false;
        btnEl.textContent = "Delete";
    }
}

// Delete ALL history sessions
async function clearAllHistory() {
    if (!confirm("Clear ALL history? Every analysis record will be permanently deleted. This cannot be undone.")) return;
    try {
        const res = await fetch("/api/sessions", { method: "DELETE" });
        if (!res.ok) throw new Error("Clear all failed");
        loadHistoryTable();
    } catch (e) {
        console.error("Clear all history error:", e);
        alert("Failed to clear history. Please try again.");
    }
}

// History search filter
function filterHistoryTable() {
    const input = document.getElementById("historySearchInput");
    const filter = input.value.toLowerCase();
    const rows = document.querySelectorAll("#historyTable tbody tr");
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(filter)) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}

// ----------------- NEW ANALYSIS FORM -----------------
function useExample(exampleText) {
    document.getElementById("startupIdea").value = exampleText;
}

async function submitStartupAnalysis() {
    const idea = document.getElementById("startupIdea").value;
    const market = document.getElementById("ideaMarketType").value;
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

// ----------------- AGENT WORKSPACE POLLING -----------------
function startWorkspaceTracking(sessionId) {
    // Reset workspace UI nodes
    resetWorkspaceNodes();
    
    const consoleLogs = document.getElementById("consoleLogs");
    consoleLogs.innerHTML = `<div class="log-entry system-log">Initializing context session pipeline for session: ${sessionId}...</div>`;
    
    // Clear existing interval
    if (pollingInterval) clearInterval(pollingInterval);
    
    // Fetch the idea text to show in the workspace pipeline header
    fetch("/api/sessions")
        .then(res => res.json())
        .then(data => {
            const session = (data.sessions || []).find(s => s.id === sessionId);
            if (session) {
                document.getElementById("pipeIdeaText").innerText = session.idea.substring(0, 100) + (session.idea.length > 100 ? "..." : "");
            }
        })
        .catch(err => console.error("Error fetching sessions for idea label:", err));

    // Poll logs every 1.5 seconds
    pollingInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/session/${sessionId}/logs`);
            const data = await res.json();
            const logs = data.logs || [];
            const status = data.status || "started";
            
            updateWorkspaceUI(logs, status, sessionId);
            
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
    const agents = ["Security", "Planner", "Research", "Finance", "Marketing", "Reviewer"];
    agents.forEach(agent => {
        const node = document.getElementById("pipeNode-" + agent);
        if (node) {
            node.className = "pipeline-card-agent";
            const indicator = node.querySelector(".status-indicator-icon");
            if (indicator) indicator.innerHTML = `<i data-lucide="circle"></i>`;
        }
        
        const card = document.getElementById("execCard-" + agent);
        if (card) {
            card.className = "exec-card glass-card waiting";
            const pill = card.querySelector(".exec-status-pill");
            if (pill) pill.textContent = "Waiting";
            const fill = card.querySelector(".exec-progress-bar-fill");
            if (fill) fill.style.width = "0%";
            const logBox = document.getElementById("execLogs-" + agent);
            if (logBox) logBox.innerText = agent === "Security" ? "Awaiting pipeline start..." : "Awaiting upstream outputs...";
        }
    });
    
    const arrows = ["arrow1", "arrow2", "arrow3", "arrow4", "arrow5", "arrow6", "arrow7"];
    arrows.forEach(arrow => {
        const arrowEl = document.getElementById(arrow);
        if (arrowEl) arrowEl.className = "vertical-arrow";
    });
    
    const blueprintNode = document.getElementById("pipeNode-Blueprint");
    if (blueprintNode) blueprintNode.className = "pipeline-card-blueprint";
    
    const blueprintStatus = document.getElementById("pipeBlueprintStatus");
    if (blueprintStatus) blueprintStatus.innerText = "Final report assembling...";
    
    document.getElementById("consoleProgress").innerText = "0% Complete";
    const footerBtnRow = document.getElementById("workspaceFooterBtnRow");
    if (footerBtnRow) footerBtnRow.style.display = "none";
    
    lucide.createIcons();
}

function updateWorkspaceUI(logs, status, sessionId) {
    const logBox = document.getElementById("consoleLogs");
    logBox.innerHTML = "";
    
    const agentKeys = ["Security", "Planner", "Research", "Finance", "Marketing", "Reviewer"];
    const agentLogsMap = {
        "Security Agent": [],
        "Planner Agent": [],
        "Research Agent": [],
        "Finance Agent": [],
        "Marketing Agent": [],
        "Reviewer Agent": []
    };
    
    logs.forEach(log => {
        const time = new Date(log.timestamp).toLocaleTimeString();
        const entry = document.createElement("div");
        entry.className = "log-entry";
        entry.innerHTML = `<strong>[${time}] ${log.agent_name} ── ${log.step_name}:</strong> ${log.thoughts}`;
        logBox.appendChild(entry);
        
        if (agentLogsMap[log.agent_name]) {
            agentLogsMap[log.agent_name].push(
                `<div class="log-entry"><strong>[${time}] ${log.step_name}:</strong> ${log.thoughts}</div>`
            );
        }
    });
    
    logBox.scrollTop = logBox.scrollHeight;
    
    // Determine active index
    let activeIndex = -1;
    if (status === "started" || status === "security_checking") activeIndex = 0;
    else if (status === "planning") activeIndex = 1;
    else if (status.startsWith("researching_c")) activeIndex = 2;
    else if (status.startsWith("financing_c")) activeIndex = 3;
    else if (status.startsWith("marketing_c")) activeIndex = 4;
    else if (status.startsWith("reviewing_c")) activeIndex = 5;
    else if (status === "finalizing" || status === "completed") activeIndex = 6;
    else if (status === "failed_security") activeIndex = 0;
    
    // Infer active index from logs to make it responsive
    logs.forEach(log => {
        let idx = -1;
        if (log.agent_name === "Security Agent") idx = 0;
        else if (log.agent_name === "Planner Agent") idx = 1;
        else if (log.agent_name === "Research Agent") idx = 2;
        else if (log.agent_name === "Finance Agent") idx = 3;
        else if (log.agent_name === "Marketing Agent") idx = 4;
        else if (log.agent_name === "Reviewer Agent") idx = 5;
        
        if (idx > activeIndex && activeIndex !== -1 && status !== "failed_security" && status !== "failed") {
            activeIndex = idx;
        }
    });
    
    // Update individual agents status and logs
    agentKeys.forEach((agent, i) => {
        const leftNode = document.getElementById("pipeNode-" + agent);
        const rightCard = document.getElementById("execCard-" + agent);
        if (!leftNode || !rightCard) return;
        
        const statusPill = rightCard.querySelector(".exec-status-pill");
        const progressFill = rightCard.querySelector(".exec-progress-bar-fill");
        const indicatorIcon = leftNode.querySelector(".status-indicator-icon");
        
        let state = "waiting";
        if (i < activeIndex) {
            state = "completed";
        } else if (i === activeIndex) {
            if (status === "failed_security" || status === "failed") {
                state = "failed";
            } else {
                state = "running";
            }
        }
        
        // Classes update
        leftNode.className = "pipeline-card-agent " + state;
        rightCard.className = "exec-card glass-card " + state;
        
        // Status text and icon
        if (state === "completed") {
            if (statusPill) statusPill.textContent = "Completed";
            if (progressFill) progressFill.style.width = "100%";
            if (indicatorIcon) indicatorIcon.innerHTML = `<i data-lucide="check-circle-2"></i>`;
        } else if (state === "running") {
            if (statusPill) statusPill.textContent = "Running";
            if (progressFill) progressFill.style.width = "60%";
            if (indicatorIcon) indicatorIcon.innerHTML = `<i data-lucide="clock"></i>`;
        } else if (state === "failed") {
            if (statusPill) statusPill.textContent = "Failed";
            if (progressFill) progressFill.style.width = "0%";
            if (indicatorIcon) indicatorIcon.innerHTML = `<i data-lucide="alert-circle"></i>`;
        } else {
            if (statusPill) statusPill.textContent = "Waiting";
            if (progressFill) progressFill.style.width = "0%";
            if (indicatorIcon) indicatorIcon.innerHTML = `<i data-lucide="circle"></i>`;
        }
        
        // Update logs for this agent
        const logsArray = agentLogsMap[agent + " Agent"];
        const individualLogBox = document.getElementById("execLogs-" + agent);
        if (individualLogBox) {
            if (logsArray && logsArray.length > 0) {
                individualLogBox.innerHTML = logsArray.join("");
                individualLogBox.scrollTop = individualLogBox.scrollHeight;
            } else {
                if (state === "waiting") {
                    individualLogBox.innerText = agent === "Security" ? "Awaiting pipeline start..." : "Awaiting upstream outputs...";
                } else if (state === "running") {
                    individualLogBox.innerText = "Initializing...";
                }
            }
        }
    });
    
    // Connect pipeline animations based on flow
    for (let i = 1; i <= 7; i++) {
        const arrow = document.getElementById("arrow" + i);
        if (arrow) {
            if (activeIndex >= i) {
                arrow.classList.add("flowing");
            } else {
                arrow.classList.remove("flowing");
            }
        }
    }
    
    const blueprintNode = document.getElementById("pipeNode-Blueprint");
    const blueprintStatus = document.getElementById("pipeBlueprintStatus");
    if (activeIndex >= 6) {
        if (blueprintNode) blueprintNode.classList.add("completed");
        if (blueprintStatus) blueprintStatus.innerText = "Blueprint Sealed";
        
        // Show report button
        const footerBtnRow = document.getElementById("workspaceFooterBtnRow");
        if (footerBtnRow) {
            footerBtnRow.style.display = "flex";
            const btn = document.getElementById("btnViewReport");
            if (btn) btn.onclick = () => viewSessionBlueprint(sessionId);
        }
    } else {
        if (blueprintNode) blueprintNode.classList.remove("completed");
        if (blueprintStatus) blueprintStatus.innerText = "Final report assembling...";
        const footerBtnRow = document.getElementById("workspaceFooterBtnRow");
        if (footerBtnRow) footerBtnRow.style.display = "none";
    }
    
    // Progress calculation estimate
    let progress = Math.min(activeIndex * 16, 95);
    if (status === "completed") progress = 100;
    const consoleProg = document.getElementById("consoleProgress");
    if (consoleProg) consoleProg.innerText = `${progress}% Complete`;
    
    // Re-render updated indicator icons
    lucide.createIcons();
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
        
        // Save globally to support download export
        window.currentBlueprintExportData = data;
        
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
