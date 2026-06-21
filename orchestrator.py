from google import genai
import database
from agents.security import SecurityAgent
from agents.planner import PlannerAgent
from agents.research import ResearchAgent
from agents.finance import FinanceAgent
from agents.marketing import MarketingAgent
from agents.reviewer import ReviewerAgent
import json
import uuid

class DreamForgeOrchestrator:
    def __init__(self, api_key, tavily_key=None, status_callback=None, mock_mode=False):
        """
        Coordinates the multi-agent execution pipeline.
        :param api_key: Gemini API key.
        :param tavily_key: Tavily API key (optional).
        :param status_callback: Callable to update Streamlit UI state in real-time.
        :param mock_mode: Whether to run in mock demonstration mode without calling the Gemini API.
        """
        self.mock_mode = mock_mode
        self.status_callback = status_callback
        
        if self.mock_mode:
            self.client = None
            self.security_agent = None
            self.planner_agent = None
            self.research_agent = None
            self.finance_agent = None
            self.marketing_agent = None
            self.reviewer_agent = None
        else:
            self.client = genai.Client(api_key=api_key)
            # Initialize agents with gemini-flash-latest which has a 1500 RPD free tier limit
            # instead of gemini-2.5-flash which is limited to 20 RPD on free accounts.
            model_name = "gemini-flash-latest"
            self.security_agent = SecurityAgent(self.client, model=model_name)
            self.planner_agent = PlannerAgent(self.client, model=model_name)
            self.research_agent = ResearchAgent(self.client, model=model_name, tavily_api_key=tavily_key)
            self.finance_agent = FinanceAgent(self.client, model=model_name)
            self.marketing_agent = MarketingAgent(self.client, model=model_name)
            self.reviewer_agent = ReviewerAgent(self.client, model=model_name)

    def _log_status(self, session_id, agent_name, step_name, thoughts, output_data=None, agent=None):
        """Helper to save log to SQLite and trigger UI callback."""
        output_str = json.dumps(output_data) if output_data else ""
        tokens_used = agent.last_tokens_used if agent else 0
        latency_ms = agent.last_latency_ms if agent else 0
        database.save_agent_log(session_id, agent_name, step_name, thoughts, output_str, tokens_used, latency_ms)
        if self.status_callback:
            self.status_callback(agent_name, step_name, thoughts)

    def run_pipeline(self, idea, target_market="Global", session_id=None):
        """
        Runs the complete multi-agent validation and blueprinting flow.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            
        # 1. Initialize session in DB
        database.save_session(session_id, idea, target_market, "started")
        self._log_status(session_id, "System", "Initialization", "Started DreamForge AI agent workflow session.")

        if self.mock_mode:
            import time
            class MockTelemetry:
                def __init__(self, tokens, latency):
                    self.last_tokens_used = tokens
                    self.last_latency_ms = latency

            # 2. Security Pre-Check
            self._log_status(session_id, "Security Agent", "Pre-Screening", "Scanning the user pitch for policy violations, dangerous products, and legal compliance.")
            database.update_session_status(session_id, "security_checking")
            time.sleep(1.5)
            security_res = {"is_safe": True, "violation_reason": None, "suggestions": None}
            self._log_status(session_id, "Security Agent", "Approval", "Startup idea passed safety verification. Proceeding to CEO planning phase.", security_res, agent=MockTelemetry(1450, 1500))

            # 3. Planner
            database.update_session_status(session_id, "planning")
            self._log_status(session_id, "Planner Agent", "Deconstruction", "CEO is proposing a brand name, writing an executive summary, and organizing task briefs.")
            time.sleep(2.0)
            
            # Generate startup name
            words = [w.strip(".,!-()").capitalize() for w in idea.split() if len(w) > 3]
            base_name = words[0] if words else "DreamForge"
            startup_name = f"{base_name} AI" if "ai" not in base_name.lower() else base_name
            
            plan = {
                "startup_name": startup_name,
                "one_liner": f"AI-Powered platform designed to optimize {startup_name} solutions.",
                "executive_summary": f"A revolutionary MVP designed to streamline operations and deliver next-generation insights. Scalable, secure, and user-centric.",
                "tasks": []
            }
            self._log_status(session_id, "Planner Agent", "Plan Created", f"CEO proposed company name '{plan['startup_name']}' and set core tasks.", plan, agent=MockTelemetry(1890, 2000))

            # 4. Research
            database.update_session_status(session_id, "researching_c1")
            self._log_status(session_id, "Research Agent", "Competitor Profiling", "Querying search databases and building market matrices.")
            time.sleep(2.5)
            research_draft = {
                "market_size_estimate": "Global market is valued at $12.5B, growing at 14.2% CAGR. TAM is estimated at $2.1B in target regions.",
                "market_trends": [
                    "Rapid adoption of automation and intelligent micro-services.",
                    "Increased focus on security, privacy, and low-friction integrations.",
                    "Shift towards hyper-personalized consumer experiences."
                ],
                "competitors": [
                    {"name": f"{startup_name} Competitor A", "market_share": "15%", "pros": "Established distribution", "cons": "High pricing"},
                    {"name": "Legacy solutions", "market_share": "45%", "pros": "Broad feature set", "cons": "Slow customer service"},
                    {"name": "Niche startups", "market_share": "5%", "pros": "Modern interface", "cons": "Lack of enterprise tools"}
                ],
                "target_persona": "Tech-savvy early adopters aged 22-45 who value efficiency, high personalization, and seamless workflow integration.",
                "industry_barriers": [
                    "Initial high trust threshold for security validation.",
                    "Established incumbents with high switching costs.",
                    "Localization and regional regulatory variations."
                ]
            }
            self._log_status(session_id, "Research Agent", "Research Completed", "Sized TAM/SAM/SOM and identified direct market competitors.", research_draft, agent=MockTelemetry(3120, 2500))

            # 5. Finance
            database.update_session_status(session_id, "financing_c1")
            self._log_status(session_id, "Finance Agent", "Financial Modeling", "Running compounding equations via cash flow simulation sandbox.")
            time.sleep(2.5)
            finance_draft = {
                "revenue_model_description": "Tiered monthly subscription model: Basic ($19/mo), Pro ($49/mo), and Enterprise custom licensing.",
                "pricing_model_selected": "Subscription",
                "pricing_point": 49.00,
                "fixed_monthly_costs": 1500.00,
                "break_even_month": "Month 4",
                "initial_funding_required": "$25,000 for server infrastructure, tooling, and initial user acquisition.",
                "year_1_revenue": 58800.00,
                "year_1_profit": 12000.00,
                "year_2_revenue": 147000.00,
                "year_2_profit": 65000.00,
                "year_3_revenue": 352800.00,
                "year_3_profit": 194000.00,
                "unit_economics": "LTV is estimated at $588.00 based on a 12-month customer lifetime. CAC is bounded at $120.00, yielding a healthy LTV:CAC ratio of 4.9x."
            }
            self._log_status(session_id, "Finance Agent", "Finance Completed", "Completed 3-year P&L sheet and break-even calculations.", finance_draft, agent=MockTelemetry(2450, 2500))

            # 6. Marketing
            database.update_session_status(session_id, "marketing_c1")
            self._log_status(session_id, "Marketing Agent", "GTM Formulating", "Drafting organic growth channels, brand messaging, and CAC boundaries.")
            time.sleep(2.0)
            marketing_draft = {
                "brand_positioning": f"The premier automated partner designed specifically for optimizing {idea[:50]}...",
                "value_propositions": [
                    "Zero-friction onboarding: Go live in less than 5 minutes.",
                    "Hyper-personalized analytics reporting out-of-the-box.",
                    "Affordable pricing with enterprise-grade data security checks."
                ],
                "growth_channels": [
                    {"channel": "SEO & Content Marketing", "expected_percentage": "35%", "cac": "$15.00"},
                    {"channel": "Developer Communities", "expected_percentage": "25%", "cac": "$0.00"},
                    {"channel": "Targeted LinkedIn Ads", "expected_percentage": "20%", "cac": "$85.00"},
                    {"channel": "Strategic Partnerships", "expected_percentage": "20%", "cac": "$50.00"}
                ],
                "gtm_milestones": [
                    "Month 1: Closed beta release with 50 selected community users.",
                    "Month 2: Public launch and integration directories submission.",
                    "Month 3: Rollout of self-serve pro features and referral programs."
                ],
                "estimated_cac_ltv_context": "Blended target CAC is $42.50 across channels, well below the $588.00 customer lifetime value target."
            }
            self._log_status(session_id, "Marketing Agent", "Marketing Completed", "Mapped growth milestones and customer acquisition strategy.", marketing_draft, agent=MockTelemetry(2890, 2000))

            # 7. Reviewer
            database.update_session_status(session_id, "reviewing_c1")
            self._log_status(session_id, "Reviewer Agent", "Cross-Audit Check", "Auditing draft packages for logical alignment, realistic targets, and financial consistency.")
            time.sleep(1.5)
            review_res = {
                "passed": True,
                "rework_needed": False,
                "completeness_score": 9.2,
                "feasibility_score": 8.7,
                "alignment_score": 9.5,
                "feedback_comments": [],
                "target_agent": None
            }
            self._log_status(session_id, "Reviewer Agent", "Audit Cleared", "All drafts are consistent and approved. Compiling final blueprint.", review_res, agent=MockTelemetry(1950, 1500))

            # 8. Blueprint Assembly
            database.update_session_status(session_id, "finalizing")
            self._log_status(session_id, "Planner Agent", "Blueprint Assembly", "Compiling agent segments into final structured startup blueprint.")
            time.sleep(1.0)
            
            final_blueprint = {
                "startup_name": plan.get("startup_name"),
                "one_liner": plan.get("one_liner"),
                "executive_summary": plan.get("executive_summary"),
                "market_research": research_draft,
                "financial_plan": finance_draft,
                "marketing_plan": marketing_draft,
                "audit_log": {
                    "reviewer_passed": True,
                    "cycles_run": 1,
                    "completeness_score": review_res.get("completeness_score", 0.0),
                    "feasibility_score": review_res.get("feasibility_score", 0.0),
                    "alignment_score": review_res.get("alignment_score", 0.0),
                    "feedback": review_res.get("feedback_comments", [])
                }
            }
            database.save_blueprint(session_id, final_blueprint)
            database.update_session_status(session_id, "completed")
            self._log_status(session_id, "System", "Workflow Finalized", "Startup blueprint generated successfully and archived to database.", final_blueprint, agent=MockTelemetry(500, 1000))
            
            return {
                "session_id": session_id,
                "status": "completed",
                "blueprint": final_blueprint
            }

        # 2. Security Pre-Check
        self._log_status(session_id, "Security Agent", "Pre-Screening", "Scanning the user pitch for policy violations, dangerous products, and legal compliance.")
        database.update_session_status(session_id, "security_checking")
        
        security_res = self.security_agent.check_idea(idea, target_market)
        
        if not security_res.get("is_safe", True):
            self._log_status(
                session_id, 
                "Security Agent", 
                "Rejection", 
                f"Startup idea rejected. Reason: {security_res.get('violation_reason')}",
                security_res,
                agent=self.security_agent
            )
            database.update_session_status(session_id, "failed_security")
            return {
                "session_id": session_id,
                "status": "failed_security",
                "error": security_res.get("violation_reason"),
                "suggestions": security_res.get("suggestions")
            }
            
        self._log_status(session_id, "Security Agent", "Approval", "Startup idea passed safety verification. Proceeding to CEO planning phase.", security_res, agent=self.security_agent)

        # 3. CEO Planner Phase
        self._log_status(session_id, "Planner Agent", "Deconstruction", "CEO is proposing a brand name, writing an executive summary, and organizing task briefs.")
        database.update_session_status(session_id, "planning")
        
        plan = self.planner_agent.plan_blueprint(idea, target_market)
        self._log_status(session_id, "Planner Agent", "Plan Created", f"CEO proposed company name '{plan.get('startup_name')}' and set core tasks.", plan, agent=self.planner_agent)
        
        # Prepare execution tasks instructions
        tasks_map = {t["agent_name"]: t["instructions"] for t in plan.get("tasks", [])}
        research_instr = tasks_map.get("Research Agent", "Research competitors and TAM/SAM/SOM.")
        finance_instr = tasks_map.get("Finance Agent", "Determine billing pricing model and calculate 3-year cash projections.")
        marketing_instr = tasks_map.get("Marketing Agent", "Build organic user acquisition channel strategy.")

        # 4. Drafting and Reviewer Feedback Loop
        max_cycles = 3
        current_cycle = 1
        
        research_draft = None
        finance_draft = None
        marketing_draft = None
        
        reviewer_critique = None
        
        while current_cycle <= max_cycles:
            # Stage logs depending on cycle
            cycle_desc = f" (Iteration {current_cycle})" if current_cycle > 1 else ""
            
            # --- Research Agent ---
            if not research_draft or (reviewer_critique and reviewer_critique.get("target_agent") == "Research Agent"):
                self._log_status(session_id, "Research Agent", f"Competitor Profiling{cycle_desc}", "Querying search databases and building market matrices.")
                database.update_session_status(session_id, f"researching_c{current_cycle}")
                
                # Append critique context if reworking
                mod_instr = research_instr
                if reviewer_critique and reviewer_critique.get("target_agent") == "Research Agent":
                    mod_instr += f"\n\n[REWORK DIRECTIVE] Address the following audit concerns: {', '.join(reviewer_critique.get('feedback_comments', []))}"
                    
                research_draft = self.research_agent.perform_research(idea, target_market, mod_instr)
                self._log_status(session_id, "Research Agent", f"Research Completed{cycle_desc}", "Sized TAM/SAM/SOM and identified direct market competitors.", research_draft, agent=self.research_agent)

            # --- Finance Agent ---
            if not finance_draft or (reviewer_critique and reviewer_critique.get("target_agent") == "Finance Agent"):
                self._log_status(session_id, "Finance Agent", f"Financial Modeling{cycle_desc}", "Running compounding equations via cash flow simulation sandbox.")
                database.update_session_status(session_id, f"financing_c{current_cycle}")
                
                mod_instr = finance_instr
                if reviewer_critique and reviewer_critique.get("target_agent") == "Finance Agent":
                    mod_instr += f"\n\n[REWORK DIRECTIVE] Address the following audit concerns: {', '.join(reviewer_critique.get('feedback_comments', []))}"
                
                finance_draft = self.finance_agent.generate_projections(idea, mod_instr, research_draft)
                self._log_status(session_id, "Finance Agent", f"Finance Completed{cycle_desc}", "Completed 3-year P&L sheet and break-even calculations.", finance_draft, agent=self.finance_agent)

            # --- Marketing Agent ---
            if not marketing_draft or (reviewer_critique and reviewer_critique.get("target_agent") == "Marketing Agent"):
                self._log_status(session_id, "Marketing Agent", f"GTM Formulating{cycle_desc}", "Drafting organic growth channels, brand messaging, and CAC boundaries.")
                database.update_session_status(session_id, f"marketing_c{current_cycle}")
                
                mod_instr = marketing_instr
                if reviewer_critique and reviewer_critique.get("target_agent") == "Marketing Agent":
                    mod_instr += f"\n\n[REWORK DIRECTIVE] Address the following audit concerns: {', '.join(reviewer_critique.get('feedback_comments', []))}"
                
                marketing_draft = self.marketing_agent.formulate_gtm(idea, mod_instr, research_draft, finance_draft)
                self._log_status(session_id, "Marketing Agent", f"Marketing Completed{cycle_desc}", "Mapped growth milestones and customer acquisition strategy.", marketing_draft, agent=self.marketing_agent)

            # --- Reviewer Agent ---
            self._log_status(session_id, "Reviewer Agent", f"Cross-Audit Check{cycle_desc}", "Auditing draft packages for logical alignment, realistic targets, and financial consistency.")
            database.update_session_status(session_id, f"reviewing_c{current_cycle}")
            
            review_res = self.reviewer_agent.audit_drafts(
                idea, 
                plan.get("executive_summary"), 
                research_draft, 
                finance_draft, 
                marketing_draft
            )
            
            if review_res.get("passed", True) or not review_res.get("rework_needed", False):
                self._log_status(session_id, "Reviewer Agent", "Audit Cleared", "All drafts are consistent and approved. Compiling final blueprint.", review_res, agent=self.reviewer_agent)
                break
            else:
                target = review_res.get("target_agent", "None")
                critique_msg = f"Audit flagged issues in {target}. Requesting revision. Comments: {', '.join(review_res.get('feedback_comments', []))}"
                self._log_status(session_id, "Reviewer Agent", f"Audit Flagged{cycle_desc}", critique_msg, review_res, agent=self.reviewer_agent)
                
                reviewer_critique = review_res
                current_cycle += 1
                database.update_session_status(session_id, f"reworking_{target.lower().replace(' ', '_')}")
                
        # 5. Compiled Package Generation
        database.update_session_status(session_id, "finalizing")
        self._log_status(session_id, "Planner Agent", "Blueprint Assembly", "Compiling agent segments into final structured startup blueprint.")
        
        final_blueprint = {
            "startup_name": plan.get("startup_name"),
            "one_liner": plan.get("one_liner"),
            "executive_summary": plan.get("executive_summary"),
            "market_research": research_draft,
            "financial_plan": finance_draft,
            "marketing_plan": marketing_draft,
            "audit_log": {
                "reviewer_passed": True,
                "cycles_run": current_cycle,
                "completeness_score": review_res.get("completeness_score", 0.0),
                "feasibility_score": review_res.get("feasibility_score", 0.0),
                "alignment_score": review_res.get("alignment_score", 0.0),
                "feedback": review_res.get("feedback_comments", [])
            }
        }
        
        # Save blueprint to SQLite
        database.save_blueprint(session_id, final_blueprint)
        database.update_session_status(session_id, "completed")
        self._log_status(session_id, "System", "Workflow Finalized", "Startup blueprint generated successfully and archived to database.", final_blueprint)
        
        return {
            "session_id": session_id,
            "status": "completed",
            "blueprint": final_blueprint
        }
