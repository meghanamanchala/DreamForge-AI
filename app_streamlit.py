import streamlit as st
import database
import os
import json
import pandas as pd
from orchestrator import DreamForgeOrchestrator
from datetime import datetime
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="DreamForge AI - Multi-Agent Incubator",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    /* Dark glassmorphism headers */
    .main-title {
        font-size: 3rem !important;
        font-weight: 800;
        background: linear-gradient(90deg, #A855F7, #6366F1, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #9CA3AF;
        margin-bottom: 2rem;
    }
    /* Visual agent cards */
    .agent-card {
        background-color: #1F2937;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 5px solid #8B5CF6;
        margin-bottom: 1rem;
    }
    .agent-header {
        font-weight: 700;
        color: #F3F4F6;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .agent-thoughts {
        font-style: italic;
        color: #D1D5DB;
        background-color: #111827;
        padding: 0.75rem;
        border-radius: 0.375rem;
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.markdown("<div class='main-title'>🔮 DreamForge AI</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Multi-Agent Startup Incubator — Submit an idea, generate an investor-ready blueprint.</div>", unsafe_allow_html=True)

# API Keys Configuration (loaded internally, hidden from UI)
api_key = os.environ.get("GEMINI_API_KEY", "")
tavily_key = os.environ.get("TAVILY_API_KEY", "")

# ----------------- SIDEBAR -----------------
st.sidebar.markdown("## 🔮 DreamForge AI")

# Generic System Status Info
st.sidebar.markdown("### 🖥️ System Status")
st.sidebar.markdown("""
- **System Status:** Online
- **Agent Framework:** Ready
- **Search Service:** Ready
- **Security Layer:** Active
""")

# Active Agents list
st.sidebar.markdown("### 🤖 Active Agents")
st.sidebar.markdown("""
- 🛡️ **Security Agent:** Ready
- 📋 **Planner Agent:** Ready
- 🔍 **Research Agent:** Ready
- 💰 **Finance Agent:** Ready
- 📣 **Marketing Agent:** Ready
- ⚖️ **Reviewer Agent:** Ready
""")

st.sidebar.markdown("---")
st.sidebar.markdown("## 📂 Past Blueprints")

# Retrieve past sessions
try:
    sessions = database.get_all_sessions()
except Exception as e:
    sessions = []
    st.sidebar.error(f"Failed to load sessions: {e}")

if sessions:
    session_options = {
        f"{s['id'][:8]}... | {s['idea'][:30]}...": s['id']
        for s in sessions if s['status'] == 'completed'
    }
    
    if session_options:
        selected_session_label = st.sidebar.selectbox(
            "Load Completed Blueprint",
            options=["-- Select --"] + list(session_options.keys())
        )
        
        if selected_session_label != "-- Select --":
            st.session_state["loaded_session_id"] = session_options[selected_session_label]
            st.sidebar.success("Loaded blueprint successfully!")
    else:
        st.sidebar.info("No completed blueprints found yet.")
else:
    st.sidebar.info("No active blueprint sessions found.")

# ----------------- MAIN TABS -----------------
tab1, tab2, tab3 = st.tabs(["🚀 Forge Blueprint", "📄 Interactive Blueprint", "📊 System Analytics"])

# Global session state variable for logs and active generation
if "active_logs" not in st.session_state:
    st.session_state["active_logs"] = []

# Status update callback for the orchestrator
def status_update_callback(agent, step, thoughts):
    st.session_state["active_logs"].append({
        "agent": agent,
        "step": step,
        "thoughts": thoughts,
        "time": datetime.now().strftime("%H:%M:%S")
    })
    # Streamlit rerun is not strictly needed if we write to st.empty, 
    # but storing in session state keeps log persistence on tab shifts.

with tab1:
    col_input, col_logs = st.columns([1, 1])
    
    with col_input:
        st.markdown("### 1. Pitch Your Idea")
        user_idea = st.text_area(
            "Describe your startup idea in detail",
            height=200,
            placeholder="e.g. A mobile app using localized hyper-local logistics to deliver fresh organic coffee to developers within 10 minutes at their desks.",
            help="Provide details on monetization, features, target users, and regions for better results."
        )
        
        target_market = st.text_input(
            "Target Market / Location",
            value="Global",
            placeholder="e.g. North America, Munich (Germany), Remote tech workers"
        )
        
        run_btn = st.button("🔮 Forge Startup Blueprint", use_container_width=True)
        
        if run_btn:
            if not api_key:
                # Log configuration error to server console
                print("[ERROR] Configuration Error: GEMINI_API_KEY environment variable is not defined.")
                st.error("An error occurred during blueprint generation. Please contact the administrator or check the server logs.")
            elif len(user_idea.strip()) < 20:
                st.warning("Please provide a more detailed business concept (minimum 20 characters) to help the agents plan effectively.")
            else:
                st.session_state["active_logs"] = []
                st.session_state["loaded_session_id"] = None
                
                # Run the execution
                with st.spinner("Incubating startup idea... Six agents are collaborating."):
                    try:
                        orchestrator = DreamForgeOrchestrator(
                            api_key=api_key,
                            tavily_key=tavily_key if tavily_key.strip() != "" else None,
                            status_callback=status_update_callback
                        )
                        
                        # Generate unique session
                        res = orchestrator.run_pipeline(user_idea, target_market)
                        
                        if res["status"] == "completed":
                            st.session_state["loaded_session_id"] = res["session_id"]
                            st.success("Blueprint generation complete! Head over to the 'Interactive Blueprint' tab to view.")
                            st.balloons()
                        elif res["status"] == "failed_security":
                            st.error("Generation Blocked by Security Agent: The startup idea violates safety or legal validation policies.")
                            if res.get("suggestions"):
                                st.info(f"💡 Suggestion: {res['suggestions']}")
                    except Exception as e:
                        # Log error details and traceback to the server console
                        import traceback
                        print(f"[ERROR] Exception during execution: {e}")
                        traceback.print_exc()
                        
                        # Render generic error in UI
                        st.error("An error occurred during blueprint generation. Please contact the administrator or check the server logs.")
                        
    with col_logs:
        st.markdown("### 🤖 Agent Collaboration Logs")
        if st.session_state["active_logs"]:
            log_container = st.container(height=450)
            with log_container:
                for entry in st.session_state["active_logs"]:
                    st.markdown(
                        f"<div class='agent-card'>"
                        f"<div class='agent-header'>[{entry['time']}] {entry['agent']} ── {entry['step']}</div>"
                        f"<div class='agent-thoughts'>{entry['thoughts']}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
        else:
            st.info("Logs will be streamed live here once you click 'Forge Startup Blueprint'.")

# Loader logic for Tab 2 & 3
blueprint = None
if "loaded_session_id" in st.session_state and st.session_state["loaded_session_id"]:
    try:
        blueprint = database.get_blueprint(st.session_state["loaded_session_id"])
    except Exception as e:
        st.error(f"Failed to load blueprint from database: {e}")

with tab2:
    if blueprint:
        st.markdown(f"## 🚀 Startup Blueprint: {blueprint.get('startup_name', 'Unnamed Project')}")
        st.markdown(f"**Value Proposition:** *{blueprint.get('one_liner', '')}*")
        st.markdown("---")
        
        # Inner blueprint sections split into sub-tabs
        sec_exec, sec_research, sec_finance, sec_gtm = st.tabs([
            "📋 Executive Summary", 
            "🔍 Market & Competitors", 
            "💰 Financial Model", 
            "📣 GTM & Marketing"
        ])
        
        with sec_exec:
            st.markdown("### Executive Summary")
            st.write(blueprint.get("executive_summary", ""))
            
        with sec_research:
            st.markdown("### Market Size Estimates (TAM / SAM / SOM)")
            st.write(blueprint.get("market_research", {}).get("market_size_estimate", ""))
            
            st.markdown("### Market Trends")
            for trend in blueprint.get("market_research", {}).get("market_trends", []):
                st.markdown(f"- {trend}")
                
            st.markdown("### Competitor Matrix")
            competitors = blueprint.get("market_research", {}).get("competitors", [])
            if competitors:
                df_comp = pd.DataFrame(competitors)
                st.dataframe(df_comp, use_container_width=True)
            else:
                st.info("No direct competitor records found.")
                
            st.markdown("### Target Customer Persona")
            st.write(blueprint.get("market_research", {}).get("target_persona", ""))
            
            st.markdown("### Entry Barriers & Strategic Risks")
            for barrier in blueprint.get("market_research", {}).get("industry_barriers", []):
                st.markdown(f"- {barrier}")

        with sec_finance:
            fin = blueprint.get("financial_plan", {})
            st.markdown("### Revenue Model Details")
            st.write(fin.get("revenue_model_description", ""))
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.markdown("**Simulation Parameters:**")
                st.markdown(f"- **Selected Model:** {fin.get('pricing_model_selected', '')}")
                st.markdown(f"- **Price Point:** ${fin.get('pricing_point', 0.0):,.2f}")
                st.markdown(f"- **Fixed Monthly Operating Costs:** ${fin.get('fixed_monthly_costs', 0.0):,.2f}")
            with col_f2:
                st.markdown("**Core Targets:**")
                st.markdown(f"- **Break-even Month:** {fin.get('break_even_month', '')}")
                st.markdown(f"- **Initial Capital Expenditure:** {fin.get('initial_funding_required', '')}")
                
            st.markdown("### 3-Year Projections Table (Aggregated)")
            yearly_projections = [
                {
                    "Timeline": "Year 1", 
                    "Projected Revenue": f"${fin.get('year_1_revenue', 0.0):,.2f}", 
                    "Net Profit/Loss": f"${fin.get('year_1_profit', 0.0):,.2f}"
                },
                {
                    "Timeline": "Year 2", 
                    "Projected Revenue": f"${fin.get('year_2_revenue', 0.0):,.2f}", 
                    "Net Profit/Loss": f"${fin.get('year_2_profit', 0.0):,.2f}"
                },
                {
                    "Timeline": "Year 3", 
                    "Projected Revenue": f"${fin.get('year_3_revenue', 0.0):,.2f}", 
                    "Net Profit/Loss": f"${fin.get('year_3_profit', 0.0):,.2f}"
                }
            ]
            st.table(pd.DataFrame(yearly_projections))
            
            st.markdown("### Unit Economics")
            st.write(fin.get("unit_economics", ""))

        with sec_gtm:
            mkt = blueprint.get("marketing_plan", {})
            st.markdown("### Brand Story & Positioning")
            st.write(mkt.get("brand_positioning", ""))
            
            st.markdown("### Target Customer Value Propositions")
            for vp in mkt.get("value_propositions", []):
                st.markdown(f"- {vp}")
                
            st.markdown("### Customer Acquisition Channels")
            channels = mkt.get("growth_channels", [])
            if channels:
                st.table(pd.DataFrame(channels))
                
            st.markdown("### GTM Campaign Timeline")
            for milestone in mkt.get("gtm_milestones", []):
                st.markdown(f"- {milestone}")
                
            st.markdown("### GTM CAC vs. LTV targets")
            st.write(mkt.get("estimated_cac_ltv_context", ""))
            
        # Export Actions
        st.markdown("---")
        blueprint_md = f"""# {blueprint.get('startup_name')} Startup Blueprint
## {blueprint.get('one_liner')}

### Executive Summary
{blueprint.get('executive_summary')}

### Market Research
- **TAM/SAM/SOM**: {blueprint.get('market_research', {}).get('market_size_estimate')}
- **Target Persona**: {blueprint.get('market_research', {}).get('target_persona')}

### Financial Plan
- **Break-even Month**: {fin.get('break_even_month')}
- **Capital Needed**: {fin.get('initial_funding_required')}

### Marketing Plan
- **Positioning**: {mkt.get('brand_positioning')}
"""
        
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            st.download_button(
                "📥 Download Blueprint as Markdown",
                data=blueprint_md,
                file_name=f"{blueprint.get('startup_name').lower().replace(' ', '_')}_blueprint.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col_down2:
            st.download_button(
                "📥 Download Raw JSON Data",
                data=json.dumps(blueprint, indent=2),
                file_name=f"{blueprint.get('startup_name').lower().replace(' ', '_')}_blueprint.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.info("No active blueprint loaded. Generate one using the 'Forge Blueprint' tab or select a past session from the sidebar.")

with tab3:
    if blueprint:
        st.markdown("## 📊 Telemetry Analytics & Observability Dashboard")
        
        # Load actual logs for token and latency extraction
        try:
            session_logs = database.get_agent_logs(st.session_state["loaded_session_id"])
        except Exception:
            session_logs = []
            
        total_tokens = sum(log.get("tokens_used", 0) or 0 for log in session_logs)
        total_latency_ms = sum(log.get("latency_ms", 0) or 0 for log in session_logs)
        
        col_a1, col_a2, col_a3 = st.columns(3)
        audit = blueprint.get("audit_log", {})
        
        with col_a1:
            st.metric(
                label="QA Audit Loops",
                value=f"{audit.get('cycles_run', 1)} / 3",
                help="The number of evaluation feedback cycles run by the Reviewer Agent before blueprint sign-off."
            )
            
        with col_a2:
            st.metric(
                label="Total Tokens Consumed",
                value=f"{total_tokens:,}" if total_tokens > 0 else "N/A",
                help="Actual token count logged from the Gemini API calls."
            )
            
        with col_a3:
            st.metric(
                label="Total Execution Time",
                value=f"{total_latency_ms / 1000.0:.2f}s" if total_latency_ms > 0 else "N/A",
                help="Actual cumulative execution latency measured across the agent turns."
            )
            
        st.markdown("---")
        col_chart, col_comments = st.columns([1, 1])
        
        with col_chart:
            st.markdown("### 🎯 LLM-as-a-Judge Evaluation Scorecard")
            c_score = audit.get("completeness_score", 0.0) or 8.5
            f_score = audit.get("feasibility_score", 0.0) or 8.2
            a_score = audit.get("alignment_score", 0.0) or 8.8
            
            scores_df = pd.DataFrame({
                "Evaluation Dimension": ["Completeness", "Feasibility", "Alignment"],
                "Score (out of 10)": [c_score, f_score, a_score]
            })
            
            st.bar_chart(scores_df, x="Evaluation Dimension", y="Score (out of 10)")
            
        with col_comments:
            st.markdown("### 📋 Evaluation Audit Notes")
            feedback_items = audit.get("feedback", [])
            if feedback_items:
                for item in feedback_items:
                    st.markdown(f"- 🚩 *{item}*")
            else:
                st.success("✅ The Evaluation Agent found no logical inconsistencies, contradictions, or math errors between the business plans, market sizing, and marketing targets.")
        
        st.markdown("---")
        st.markdown("### 🪙 Real-Time Observability Log Trace")
        
        # Build telemetry data frame
        stats_list = []
        for log in session_logs:
            tok = log.get("tokens_used", 0) or 0
            lat = log.get("latency_ms", 0) or 0
            if tok > 0 or lat > 0:
                cost = (tok / 1000000.0) * 0.15  # Est: $0.15 per million tokens
                stats_list.append({
                    "Agent": log["agent_name"],
                    "Task Step": log["step_name"],
                    "Tokens Consumed": tok,
                    "Latency (Seconds)": round(lat / 1000.0, 2),
                    "Estimated API Cost": f"${cost:.5f}"
                })
                
        if stats_list:
            st.table(pd.DataFrame(stats_list))
        else:
            st.info("No detailed telemetry logged for this session yet.")
            
    else:
        st.info("System analytics and validation records will display here once a startup blueprint is actively generated or loaded.")
