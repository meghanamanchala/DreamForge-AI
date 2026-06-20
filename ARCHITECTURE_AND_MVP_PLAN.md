# Architecture and MVP Plan: DreamForge AI Streamlit Application

This document provides a comprehensive technical blueprint of the implemented DreamForge AI MVP. It describes how the high-level startup incubator requirements are mapped to a secure, lightweight, and single-developer Streamlit + Python application.

---

## 1. Directory Structure

The project code is organized to decouple orchestration, agent personas, programmatic tools, and state storage:

```
DreamForge-AI/
├── agents/
│   ├── __init__.py
│   ├── base.py            # Gemini client API & structured output extraction
│   ├── security.py        # Input policy, safety, and toxicity screening
│   ├── planner.py         # CEO agent proposing startup names and assigning task briefs
│   ├── research.py        # Web search query generation and data synthesis
│   ├── finance.py         # Parameter extraction and financial simulation reporting
│   ├── marketing.py       # Positioning, brand narratives, and GTM milestones
│   └── reviewer.py        # Coherence validator and rework feedback director
├── tools/
│   ├── __init__.py
│   ├── calculator.py      # Deterministic 36-month P&L cash projections
│   ├── scraper.py         # BeautifulSoup HTML-to-text landing page parser
│   └── search.py          # Unified search (Tavily Premium with DuckDuckGo fallback)
├── app.py                 # Streamlit dashboard UI
├── database.py            # SQLite session, log, and blueprint repository
├── memory.py              # Local SQLite vector storage with NumPy cosine similarity
├── test_agents.py         # Offline test validation scripts
├── requirements.txt       # Unified Python dependencies
├── .env.example           # Environment template file
└── .gitignore             # Git exclusion rules (.env, dreamforge.db, __pycache__)
```

---

## 2. Agent Orchestration Flow

DreamForge AI utilizes an **Orchestrator-Worker hybrid design** directed by the **Planner Agent (CEO)**.

```mermaid
graph TD
    A[User Submits Startup Idea] --> B{1. Security Pre-Screen}
    B -- Rejection (Toxicity/Illegal) --> C[Show Generic Error & Log to Console]
    B -- Approval --> D[2. Planner CEO Deconstruction]
    D --> E[Create Task Briefs]
    E --> F[3. Execute Worker Agents]
    
    subgraph Execution Loop (Max 3 Iterations)
        F --> G[Research Agent]
        G --> H[Finance Agent]
        H --> I[Marketing Agent]
        I --> J[4. Reviewer Agent Audit]
        
        J -- Fail (Rework Required) --> K{Iteration Limit < 3?}
        K -- Yes --> L[Update Prompt with Critique]
        L --> F
        K -- No --> M[Assemble Best Compilation]
    end
    
    J -- Pass --> M
    M --> N{5. Security Post-Screen}
    N -- Clear --> O[6. Finalize SQLite Archive]
    O --> P[Render Dashboard Blueprint & Enable Downloads]
```

---

## 3. Class Design

### 3.1 BaseAgent Class
Located in [agents/base.py], this class wraps the modern Google GenAI SDK.
- **Methods**:
  - `generate_text(system_instruction, user_content)`: Performs unstructured chat/completion tasks.
  - `generate_structured(system_instruction, user_content, response_schema)`: Generates strict JSON outputs matching a defined Pydantic validation schema.

### 3.2 Structured Output Schemas (Pydantic Models)
To ensure agents return standardized JSON schemas, the following Pydantic formats are declared:
- **Security Check Schema**: `{is_safe: bool, violation_reason: str, risk_score: float, suggestions: str}`
- **Planner Output Schema**: `{startup_name: str, one_liner: str, executive_summary: str, tasks: List[PlannerTask]}`
- **Research Output Schema**: `{market_size_estimate: str, market_trends: List[str], competitors: List[Competitor], target_persona: str, industry_barriers: List[str]}`
- **Finance Projections Parameter Schema**: `{pricing_model: str, pricing_point: float, fixed_monthly_costs: float, variable_cost_margin: float, estimated_growth_rate: float, initial_investment: float, starting_customers: int}`
- **Finance Output Schema**: `{revenue_model_description: str, pricing_model_selected: str, pricing_point: float, fixed_monthly_costs: float, break_even_month: str, initial_funding_required: str, year_1_revenue: float, year_1_profit: float, year_2_revenue: float, year_2_profit: float, year_3_revenue: float, year_3_profit: float, unit_economics: str}`
- **Marketing Output Schema**: `{brand_positioning: str, value_propositions: List[str], growth_channels: List[GrowthChannel], gtm_milestones: List[str], estimated_cac_ltv_context: str}`
- **Reviewer Output Schema**: `{passed: bool, feedback_comments: List[str], rework_needed: bool, target_agent: str}`

---

## 4. Tool Interfaces & Skills Architecture

Agents execute specific tools programmatically to fetch external data or run math models:

| Tool Module | Function Interface | Purpose | Fallback / Logic |
| :--- | :--- | :--- | :--- |
| `tools/search.py` | `web_search(query, tavily_api_key, max_results)` | Crawl web for competitors and market trends. | Uses Tavily Search API if a key is provided, falling back to DuckDuckGo search if missing. |
| `tools/scraper.py` | `scrape_page(url)` | Extract textual copy from landing pages. | Uses `BeautifulSoup` to parse HTML, strip script nodes, and limit text length to 15,000 characters. |
| `tools/calculator.py` | `run_financial_simulation(...)` | Project 36-month business ledger sheets. | Performs compounding calculations in native Python, outputs summary statistics and 3-year aggregated profit margins. |

---

## 5. Memory Handling

Memory operates at three levels to maintain consistency throughout the simulation:

1. **Short-Term Session memory**: Controlled by Streamlit's `st.session_state` and a local dictionary during execution. It collects outputs from the active session and feeds them dynamically to downstream agents.
2. **Episodic Execution Log**: Managed inside the `agent_logs` SQLite table. Every agent's internal reasoning process, parameters, and generated drafts are logged chronologically.
3. **Semantic Reference Memory**: Handled in `memory.py` via local SQLite tables. It embeds past blueprints using Gemini `text-embedding-004` and queries similar business structures using NumPy cosine similarity.

---

## 6. Logging & Error Handling

To maintain secure, production-grade security standards, all logs and errors are isolated:

### 6.1 Server Console Logging
- Configuration warnings (e.g. missing API keys) are logged strictly to the standard console output:
  `[ERROR] Configuration Error: GEMINI_API_KEY environment variable is not defined.`
- Runtime errors and exception stack traces are printed to the server standard error output using Python's `traceback.print_exc()`.

### 6.2 Frontend User Protection
- No raw stack traces, file paths, variable environments, or API key strings are exposed in the user interface.
- If generation fails, the user is shown a clean notification:
  `"An error occurred during blueprint generation. Please contact the administrator or check the server logs."`

---

## 7. Deployment Strategy

### 7.1 Local Deployment
1. **Requirements**: Python 3.10+ installed.
2. **Configuration**: Copy `.env.example` to `.env` and configure your API keys.
3. **Execution**:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

### 7.2 Docker Deployment (Production Sandbox)
Create a `Dockerfile` to host the application inside an isolated container:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
Run container locally or on AWS/GCP:
```bash
docker build -t dreamforge-ai-mvp .
docker run -p 8501:8501 --env-file .env dreamforge-ai-mvp
```

---
*End of Architecture and MVP Plan.*
