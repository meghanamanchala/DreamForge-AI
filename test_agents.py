import unittest
import os
import database
from tools.calculator import run_financial_simulation
from tools.search import web_search
from tools.scraper import scrape_page

class TestDreamForgeMVP(unittest.TestCase):
    def test_database_init(self):
        """Verifies database initializes and tables exist."""
        database.init_db()
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # Check sessions table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        self.assertIsNotNone(cursor.fetchone(), "sessions table should exist")
        
        # Check blueprints table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blueprints'")
        self.assertIsNotNone(cursor.fetchone(), "blueprints table should exist")
        
        # Check agent_logs table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_logs'")
        self.assertIsNotNone(cursor.fetchone(), "agent_logs table should exist")
        
        conn.close()

    def test_financial_calculator(self):
        """Verifies programmatic math projections are correct and deterministic."""
        res = run_financial_simulation(
            pricing_model="subscription",
            pricing_point=10.0,
            fixed_monthly_costs=100.0,
            variable_cost_margin=0.10,
            estimated_growth_rate=0.0, # no growth for constant math
            initial_investment=1000.0,
            starting_customers=20 # 20 * 10 = 200 revenue
        )
        
        self.assertNotIn("error", res)
        summary = res["summary"]
        
        # Revenue = 20 * 10 * 36 months = 7200
        self.assertEqual(summary["total_revenue"], 7200.0)
        
        # Fixed costs = 100 * 36 = 3600
        # Variable costs = 7200 * 0.10 = 720
        # Total Expenses = 4320
        self.assertEqual(summary["total_expenses"], 4320.0)
        
        # Total Profit = 7200 - 4320 = 2880
        self.assertEqual(summary["total_profit"], 2880.0)
        
        # Break even should happen on Month 1 since: Month 1 profit = 200 - (100 + 20) = 80 > 0
        self.assertEqual(summary["break_even_month"], "Month 1")

    def test_web_search_fallback(self):
        """Verifies web search doesn't crash without keys and falls back gracefully."""
        # DuckDuckGo fallback testing
        res = web_search("AI startup validation", tavily_api_key=None, max_results=2)
        self.assertIsInstance(res, list)

    def test_web_scraper_error_handling(self):
        """Verifies web scraper returns error dict on bad URLs instead of raising exceptions."""
        res = scrape_page("https://invalid-subdomain-does-not-exist-12345.com")
        self.assertIn("content", res)
        self.assertEqual(res["title"], "")
        self.assertNotEqual(res["status"], "success")

    def test_mcp_registry(self):
        """Verifies MCP registry compiles valid JSON-RPC style tool schemas."""
        from tools.mcp_registry import mcp_registry
        schemas = mcp_registry.get_mcp_schemas()
        
        # Verify tools are registered
        self.assertTrue(len(schemas) >= 3, "Should have registered web_search, scrape_page, and run_financial_simulation")
        
        # Validate schema keys
        for s in schemas:
            self.assertIn("name", s)
            self.assertIn("description", s)
            self.assertIn("inputSchema", s)
            self.assertEqual(s["inputSchema"]["type"], "object")

    def test_market_sizing_skill(self):
        """Verifies that TAM/SAM/SOM sizing calculations are correct."""
        from skills.market_sizing import compute_tam_sam_som
        res = compute_tam_sam_som(
            total_population=10000,
            target_segment_percentage=0.10,
            penetration_rate=0.05,
            average_deal_size=100
        )
        # TAM = 10000 * 100 = 1,000,000
        # SAM = 1,000,000 * 0.10 = 100,000
        # SOM = 100,000 * 0.05 = 5,000
        self.assertEqual(res["tam"], 1000000.0)
        self.assertEqual(res["sam"], 100000.0)
        self.assertEqual(res["som"], 5000.0)

    def test_unit_economics_skill(self):
        """Verifies LTV/CAC ratios and unit health thresholds."""
        from skills.unit_economics import calculate_ltv_cac_ratio
        
        # Healthy case: Ratio >= 3
        res_healthy = calculate_ltv_cac_ratio(
            pricing_point=50.0,
            variable_cost_margin=0.20,
            monthly_churn_rate=0.05,
            target_cac=100.0
        )
        # margin = 50 * 0.80 = 40
        # ltv = 40 / 0.05 = 800
        # ratio = 800 / 100 = 8.0
        self.assertEqual(res_healthy["monthly_gross_margin"], 40.0)
        self.assertEqual(res_healthy["ltv"], 800.0)
        self.assertEqual(res_healthy["ltv_cac_ratio"], 8.0)
        self.assertTrue(res_healthy["is_healthy"])

        # Unhealthy case: Ratio < 3
        res_unhealthy = calculate_ltv_cac_ratio(
            pricing_point=10.0,
            variable_cost_margin=0.50,
            monthly_churn_rate=0.10,
            target_cac=50.0
        )
        # margin = 5
        # ltv = 50
        # ratio = 50 / 50 = 1.0
        self.assertEqual(res_unhealthy["ltv_cac_ratio"], 1.0)
        self.assertFalse(res_unhealthy["is_healthy"])

if __name__ == '__main__':
    unittest.main()
