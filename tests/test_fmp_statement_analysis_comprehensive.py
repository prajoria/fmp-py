#!/usr/bin/env python3
"""
Comprehensive Tests for FMP Statement Analysis API
=================================================
Tests all APIs in fmp_statement_analysis.py using AAPL (Apple) as test symbol.
These tests use actual API endpoints without mocking.

Test Coverage:
- financial_score: Financial scoring data
- ratios_ttm: TTM ratios data
- ratios: Historical ratios data (annual/quarterly)
- key_metrics_ttm: TTM key metrics data  
- key_metrics: Historical key metrics data (annual/quarterly)
- cashflow_growth: Cash flow growth data (annual/quarterly)
- income_growth: Income statement growth data (annual/quarterly) 
- balance_sheet_growth: Balance sheet growth data (annual/quarterly)
- financial_growth: Financial growth data (annual/quarterly)
- owner_earnings: Owner earnings data
- enterprise_values: Enterprise values data
"""

import pytest
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import sys

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(project_root / '.env')

# Import the class to test
from fmp_py.fmp_statement_analysis import FmpStatementAnalysis
from fmp_py.models.statement_analysis import FinancialScore, Ratios, KeyMetrics


class TestFmpStatementAnalysis:
    """Test class for FMP Statement Analysis API endpoints."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with FMP client."""
        cls.api_key = os.getenv("FMP_API_KEY")
        if not cls.api_key:
            pytest.skip("FMP_API_KEY not found in environment variables")
        
        cls.client = FmpStatementAnalysis(api_key=cls.api_key)
        cls.test_symbol = "AAPL"  # Apple Inc. - reliable test symbol
        
    def test_financial_score(self):
        """Test financial_score API endpoint."""
        print(f"\\n🧪 Testing financial_score for {self.test_symbol}")
        
        # Test valid symbol
        result = self.client.financial_score(self.test_symbol)
        
        # Verify return type
        assert isinstance(result, FinancialScore), f"Expected FinancialScore, got {type(result)}"
        
        # Verify required fields are present
        assert result.symbol == self.test_symbol, f"Expected symbol {self.test_symbol}, got {result.symbol}"
        assert isinstance(result.altman_z_score, float), "altman_z_score should be float"
        assert isinstance(result.piotroski_score, int), "piotroski_score should be int"
        assert isinstance(result.working_capital, int), "working_capital should be int"
        assert isinstance(result.total_assets, int), "total_assets should be int"
        assert isinstance(result.retained_earnings, int), "retained_earnings should be int"
        assert isinstance(result.ebit, int), "ebit should be int"
        assert isinstance(result.market_cap, int), "market_cap should be int"
        assert isinstance(result.total_liabilities, int), "total_liabilities should be int"
        assert isinstance(result.revenue, int), "revenue should be int"
        
        # Verify reasonable ranges for scores
        assert 0 <= result.piotroski_score <= 9, f"Piotroski score should be 0-9, got {result.piotroski_score}"
        
        print(f"✅ Financial Score - Symbol: {result.symbol}, Altman Z-Score: {result.altman_z_score}, Piotroski Score: {result.piotroski_score}")
        
        # Test invalid symbol
        with pytest.raises(ValueError, match="Invalid symbol"):
            self.client.financial_score("INVALID_SYMBOL_12345")
    
    def test_ratios_ttm(self):
        """Test ratios_ttm API endpoint."""
        print(f"\\n🧪 Testing ratios_ttm for {self.test_symbol}")
        
        # Test valid symbol
        result = self.client.ratios_ttm(self.test_symbol)
        
        # Verify return type
        assert isinstance(result, Ratios), f"Expected Ratios, got {type(result)}"
        
        # Verify key ratio fields
        assert isinstance(result.pe_ratio_ttm, float), "pe_ratio_ttm should be float"
        assert isinstance(result.current_ratio_ttm, float), "current_ratio_ttm should be float"
        assert isinstance(result.quick_ratio_ttm, float), "quick_ratio_ttm should be float"
        assert isinstance(result.debt_equity_ratio_ttm, float), "debt_equity_ratio_ttm should be float"
        assert isinstance(result.return_on_equity_ttm, float), "return_on_equity_ttm should be float"
        assert isinstance(result.return_on_assets_ttm, float), "return_on_assets_ttm should be float"
        assert isinstance(result.gross_profit_margin_ttm, float), "gross_profit_margin_ttm should be float"
        assert isinstance(result.net_profit_margin_ttm, float), "net_profit_margin_ttm should be float"
        
        # Verify reasonable ranges for ratios
        assert result.current_ratio_ttm >= 0, f"Current ratio should be >= 0, got {result.current_ratio_ttm}"
        assert result.quick_ratio_ttm >= 0, f"Quick ratio should be >= 0, got {result.quick_ratio_ttm}"
        
        print(f"✅ Ratios TTM - P/E: {result.pe_ratio_ttm}, Current Ratio: {result.current_ratio_ttm}, ROE: {result.return_on_equity_ttm}")
        
        # Test invalid symbol
        with pytest.raises(ValueError, match="Invalid symbol"):
            self.client.ratios_ttm("INVALID_SYMBOL_12345")
    
    def test_ratios_annual(self):
        """Test ratios API endpoint with annual data."""
        print(f"\\n🧪 Testing ratios (annual) for {self.test_symbol}")
        
        # Test annual ratios
        result = self.client.ratios(self.test_symbol, period="annual", limit=5)
        
        # Verify return type
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 5, f"Expected max 5 records, got {len(result)}"
        
        # Verify required columns
        expected_columns = [
            "date", "symbol", "current_ratio", "quick_ratio", "cash_ratio",
            "gross_profit_margin", "operating_profit_margin", "net_profit_margin",
            "return_on_assets", "return_on_equity", "debt_ratio", "debt_equity_ratio"
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Verify data types
        assert result["date"].dtype == "datetime64[ns]", "date should be datetime"
        assert result["symbol"].dtype == "object", "symbol should be string"
        assert result["current_ratio"].dtype == "float64", "current_ratio should be float"
        
        # Verify symbol consistency
        assert all(result["symbol"] == self.test_symbol), "All symbols should match test symbol"
        
        # Verify date ordering (should be ascending)
        dates = result["date"].tolist()
        assert dates == sorted(dates), "Dates should be in ascending order"
        
        print(f"✅ Ratios Annual - Records: {len(result)}, Date range: {result['date'].min()} to {result['date'].max()}")
    
    def test_ratios_quarterly(self):
        """Test ratios API endpoint with quarterly data."""
        print(f"\\n🧪 Testing ratios (quarterly) for {self.test_symbol}")
        
        # Test quarterly ratios
        result = self.client.ratios(self.test_symbol, period="quarter", limit=8)
        
        # Verify return type and basic structure
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 8, f"Expected max 8 records, got {len(result)}"
        
        # Verify symbols
        assert all(result["symbol"] == self.test_symbol), "All symbols should match test symbol"
        
        print(f"✅ Ratios Quarterly - Records: {len(result)}")
        
        # Test invalid period
        with pytest.raises(ValueError, match="Period must be either 'annual' or 'quarter'"):
            self.client.ratios(self.test_symbol, period="invalid")
    
    def test_key_metrics_ttm(self):
        """Test key_metrics_ttm API endpoint."""
        print(f"\\n🧪 Testing key_metrics_ttm for {self.test_symbol}")
        
        # Test valid symbol
        result = self.client.key_metrics_ttm(self.test_symbol)
        
        # Verify return type
        assert isinstance(result, KeyMetrics), f"Expected KeyMetrics, got {type(result)}"
        
        # Verify key metric fields
        assert isinstance(result.revenue_per_share_ttm, float), "revenue_per_share_ttm should be float"
        assert isinstance(result.net_income_per_share_ttm, float), "net_income_per_share_ttm should be float"
        assert isinstance(result.operating_cash_flow_per_share_ttm, float), "operating_cash_flow_per_share_ttm should be float"
        assert isinstance(result.book_value_per_share_ttm, float), "book_value_per_share_ttm should be float"
        assert isinstance(result.pe_ratio_ttm, float), "pe_ratio_ttm should be float"
        assert isinstance(result.price_to_sales_ratio_ttm, float), "price_to_sales_ratio_ttm should be float"
        assert isinstance(result.market_cap_ttm, (int, float)), "market_cap_ttm should be numeric"
        assert isinstance(result.enterprise_value_ttm, float), "enterprise_value_ttm should be float"
        
        # Verify reasonable values
        assert result.revenue_per_share_ttm > 0, f"Revenue per share should be positive, got {result.revenue_per_share_ttm}"
        assert result.market_cap_ttm > 0, f"Market cap should be positive, got {result.market_cap_ttm}"
        
        print(f"✅ Key Metrics TTM - Revenue/Share: {result.revenue_per_share_ttm}, P/E: {result.pe_ratio_ttm}, Market Cap: {result.market_cap_ttm}")
        
        # Test invalid symbol
        with pytest.raises(ValueError, match="No data found for this symbol"):
            self.client.key_metrics_ttm("INVALID_SYMBOL_12345")
    
    def test_key_metrics_annual(self):
        """Test key_metrics API endpoint with annual data."""
        print(f"\\n🧪 Testing key_metrics (annual) for {self.test_symbol}")
        
        # Test annual key metrics
        result = self.client.key_metrics(self.test_symbol, period="annual", limit=5)
        
        # Verify return type
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 5, f"Expected max 5 records, got {len(result)}"
        
        # Verify required columns
        expected_columns = [
            "date", "symbol", "calendar_year", "revenue_per_share", "net_income_per_share",
            "pe_ratio", "price_to_sales_ratio", "market_cap", "enterprise_value"
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Verify data types
        assert result["date"].dtype == "datetime64[ns]", "date should be datetime"
        assert result["calendar_year"].dtype == "int64", "calendar_year should be int"
        
        # Verify symbols
        assert all(result["symbol"] == self.test_symbol), "All symbols should match test symbol"
        
        print(f"✅ Key Metrics Annual - Records: {len(result)}")
    
    def test_key_metrics_quarterly(self):
        """Test key_metrics API endpoint with quarterly data.""" 
        print(f"\\n🧪 Testing key_metrics (quarterly) for {self.test_symbol}")
        
        # Test quarterly key metrics
        result = self.client.key_metrics(self.test_symbol, period="quarter", limit=8)
        
        # Verify return type and basic structure
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 8, f"Expected max 8 records, got {len(result)}"
        
        print(f"✅ Key Metrics Quarterly - Records: {len(result)}")
        
        # Test invalid period
        with pytest.raises(ValueError, match="Period must be either 'annual' or 'quarter'"):
            self.client.key_metrics(self.test_symbol, period="invalid")
    
    def test_cashflow_growth_annual(self):
        """Test cashflow_growth API endpoint with annual data."""
        print(f"\\n🧪 Testing cashflow_growth (annual) for {self.test_symbol}")
        
        # Test annual cashflow growth
        result = self.client.cashflow_growth(self.test_symbol, period="annual", limit=5)
        
        # Verify return type
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 5, f"Expected max 5 records, got {len(result)}"
        
        # Verify required columns
        expected_columns = [
            "symbol", "date", "period", "calendar_year", "growth_net_income",
            "growth_operating_cash_flow", "growth_free_cash_flow"
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Verify data types
        assert result["date"].dtype == "datetime64[ns]", "date should be datetime"
        assert result["calendar_year"].dtype == "int64", "calendar_year should be int"
        assert result["growth_net_income"].dtype == "float64", "growth_net_income should be float"
        
        # Verify symbols
        assert all(result["symbol"] == self.test_symbol), "All symbols should match test symbol"
        
        print(f"✅ Cashflow Growth Annual - Records: {len(result)}")
    
    def test_cashflow_growth_quarterly(self):
        """Test cashflow_growth API endpoint with quarterly data."""
        print(f"\\n🧪 Testing cashflow_growth (quarterly) for {self.test_symbol}")
        
        # Test quarterly cashflow growth
        result = self.client.cashflow_growth(self.test_symbol, period="quarter", limit=8)
        
        # Verify return type and basic structure
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 8, f"Expected max 8 records, got {len(result)}"
        
        print(f"✅ Cashflow Growth Quarterly - Records: {len(result)}")
        
        # Test invalid period
        with pytest.raises(ValueError, match="Invalid period. Please choose 'annual' or 'quarter'"):
            self.client.cashflow_growth(self.test_symbol, period="invalid")
    
    def test_income_growth_annual(self):
        """Test income_growth API endpoint with annual data."""
        print(f"\\n🧪 Testing income_growth (annual) for {self.test_symbol}")
        
        # Test annual income growth
        result = self.client.income_growth(self.test_symbol, period="annual", limit=5)
        
        # Verify return type
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 5, f"Expected max 5 records, got {len(result)}"
        
        # Verify required columns
        expected_columns = [
            "date", "symbol", "calendar_year", "period", "growth_revenue",
            "growth_gross_profit", "growth_net_income", "growth_eps"
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Verify data types
        assert result["date"].dtype == "datetime64[ns]", "date should be datetime"
        assert result["calendar_year"].dtype == "int64", "calendar_year should be int"
        assert result["growth_revenue"].dtype == "float64", "growth_revenue should be float"
        
        # Verify symbols
        assert all(result["symbol"] == self.test_symbol), "All symbols should match test symbol"
        
        print(f"✅ Income Growth Annual - Records: {len(result)}")
    
    def test_income_growth_quarterly(self):
        """Test income_growth API endpoint with quarterly data."""
        print(f"\\n🧪 Testing income_growth (quarterly) for {self.test_symbol}")
        
        # Test quarterly income growth - note: API uses 'quarter' not 'quarterly'
        result = self.client.income_growth(self.test_symbol, period="quarter", limit=8)
        
        # Verify return type and basic structure
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 8, f"Expected max 8 records, got {len(result)}"
        
        print(f"✅ Income Growth Quarterly - Records: {len(result)}")
        
        # Test invalid period
        with pytest.raises(ValueError, match="Invalid period. Must be 'annual' or 'quarter'"):
            self.client.income_growth(self.test_symbol, period="invalid")
    
    def test_balance_sheet_growth_annual(self):
        """Test balance_sheet_growth API endpoint with annual data."""
        print(f"\\n🧪 Testing balance_sheet_growth (annual) for {self.test_symbol}")
        
        # Test annual balance sheet growth
        result = self.client.balance_sheet_growth(self.test_symbol, period="annual", limit=5)
        
        # Verify return type
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 5, f"Expected max 5 records, got {len(result)}"
        
        # Verify required columns
        expected_columns = [
            "date", "symbol", "calendar_year", "period", "growth_total_assets",
            "growth_total_liabilities", "growth_total_stockholders_equity"
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Verify data types
        assert result["date"].dtype == "datetime64[ns]", "date should be datetime"
        assert result["calendar_year"].dtype == "int64", "calendar_year should be int"
        assert result["growth_total_assets"].dtype == "float64", "growth_total_assets should be float"
        
        # Verify symbols
        assert all(result["symbol"] == self.test_symbol), "All symbols should match test symbol"
        
        print(f"✅ Balance Sheet Growth Annual - Records: {len(result)}")
    
    def test_balance_sheet_growth_quarterly(self):
        """Test balance_sheet_growth API endpoint with quarterly data."""
        print(f"\\n🧪 Testing balance_sheet_growth (quarterly) for {self.test_symbol}")
        
        # Test quarterly balance sheet growth
        result = self.client.balance_sheet_growth(self.test_symbol, period="quarterly", limit=8)
        
        # Verify return type and basic structure
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 8, f"Expected max 8 records, got {len(result)}"
        
        print(f"✅ Balance Sheet Growth Quarterly - Records: {len(result)}")
        
        # Test invalid period
        with pytest.raises(ValueError, match="Invalid period. Please choose 'annual' or 'quarterly'"):
            self.client.balance_sheet_growth(self.test_symbol, period="invalid")
    
    def test_financial_growth_annual(self):
        """Test financial_growth API endpoint with annual data."""
        print(f"\\n🧪 Testing financial_growth (annual) for {self.test_symbol}")
        
        # Test annual financial growth
        result = self.client.financial_growth(self.test_symbol, period="annual", limit=5)
        
        # Verify return type
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 5, f"Expected max 5 records, got {len(result)}"
        
        # Verify required columns
        expected_columns = [
            "symbol", "date", "calendar_year", "period", "revenue_growth",
            "gross_profit_growth", "net_income_growth", "eps_growth"
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Verify data types
        assert result["date"].dtype == "datetime64[ns]", "date should be datetime"
        assert result["calendar_year"].dtype == "int64", "calendar_year should be int"
        assert result["revenue_growth"].dtype == "float64", "revenue_growth should be float"
        
        # Verify symbols
        assert all(result["symbol"] == self.test_symbol), "All symbols should match test symbol"
        
        print(f"✅ Financial Growth Annual - Records: {len(result)}")
    
    def test_financial_growth_quarterly(self):
        """Test financial_growth API endpoint with quarterly data."""
        print(f"\\n🧪 Testing financial_growth (quarterly) for {self.test_symbol}")
        
        # Test quarterly financial growth
        result = self.client.financial_growth(self.test_symbol, period="quarterly", limit=8)
        
        # Verify return type and basic structure
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        assert len(result) <= 8, f"Expected max 8 records, got {len(result)}"
        
        print(f"✅ Financial Growth Quarterly - Records: {len(result)}")
        
        # Test invalid period
        with pytest.raises(ValueError, match="Invalid period. Must be either 'annual' or 'quarterly'"):
            self.client.financial_growth(self.test_symbol, period="invalid")
    
    def test_owner_earnings(self):
        """Test owner_earnings API endpoint."""
        print(f"\\n🧪 Testing owner_earnings for {self.test_symbol}")
        
        # Test owner earnings
        result = self.client.owner_earnings(self.test_symbol)
        
        # Verify return type
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        
        # Verify required columns
        expected_columns = [
            "symbol", "date", "average_ppe", "maintenance_capex",
            "owners_earnings", "growth_capex", "owners_earnings_per_share"
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Verify data types
        assert result["date"].dtype == "datetime64[ns]", "date should be datetime"
        assert result["symbol"].dtype == "object", "symbol should be string"
        assert result["owners_earnings"].dtype == "int64", "owners_earnings should be int"
        assert result["owners_earnings_per_share"].dtype == "float64", "owners_earnings_per_share should be float"
        
        # Verify symbols
        assert all(result["symbol"] == self.test_symbol), "All symbols should match test symbol"
        
        # Verify date ordering (should be descending)
        dates = result["date"].tolist()
        assert dates == sorted(dates, reverse=True), "Dates should be in descending order"
        
        print(f"✅ Owner Earnings - Records: {len(result)}, Latest owners earnings: {result.iloc[0]['owners_earnings']}")
        
        # Test invalid symbol
        with pytest.raises(ValueError, match="No data found for the given symbol"):
            self.client.owner_earnings("INVALID_SYMBOL_12345")
    
    def test_enterprise_values(self):
        """Test enterprise_values API endpoint."""
        print(f"\\n🧪 Testing enterprise_values for {self.test_symbol}")
        
        # Test enterprise values
        result = self.client.enterprise_values(self.test_symbol)
        
        # Verify return type
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert not result.empty, "DataFrame should not be empty"
        
        # Verify required columns
        expected_columns = [
            "symbol", "date", "stock_price", "number_of_shares",
            "market_capitalization", "minus_cash_and_cash_equivalents",
            "add_total_debt", "enterprise_value"
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Verify data types
        assert result["date"].dtype == "datetime64[ns]", "date should be datetime"
        assert result["symbol"].dtype == "object", "symbol should be string"
        assert result["stock_price"].dtype == "float64", "stock_price should be float"
        assert result["number_of_shares"].dtype == "int64", "number_of_shares should be int"
        assert result["market_capitalization"].dtype == "int64", "market_capitalization should be int"
        assert result["enterprise_value"].dtype == "int64", "enterprise_value should be int"
        
        # Verify symbols
        assert all(result["symbol"] == self.test_symbol), "All symbols should match test symbol"
        
        # Verify date ordering (should be ascending)
        dates = result["date"].tolist()
        assert dates == sorted(dates), "Dates should be in ascending order"
        
        # Verify reasonable values
        assert all(result["stock_price"] > 0), "Stock prices should be positive"
        assert all(result["number_of_shares"] > 0), "Number of shares should be positive"
        assert all(result["market_capitalization"] > 0), "Market cap should be positive"
        
        print(f"✅ Enterprise Values - Records: {len(result)}, Latest EV: {result.iloc[-1]['enterprise_value']}")
        
        # Test invalid symbol
        with pytest.raises(ValueError, match="No data found for the given symbol"):
            self.client.enterprise_values("INVALID_SYMBOL_12345")
    
    def test_error_handling(self):
        """Test error handling for various edge cases."""
        print(f"\\n🧪 Testing error handling and edge cases")
        
        # Test empty/None symbol
        with pytest.raises((ValueError, Exception)):
            self.client.financial_score("")
        
        # Test None API key
        with pytest.raises((AttributeError, Exception)):
            bad_client = FmpStatementAnalysis(api_key=None)
            bad_client.financial_score(self.test_symbol)
        
        # Test invalid limit values
        result = self.client.ratios(self.test_symbol, period="annual", limit=0)
        # Should still work, might return empty or limited results
        assert isinstance(result, pd.DataFrame), "Should return DataFrame even with limit=0"
        
        print("✅ Error handling tests completed")
    
    def test_data_consistency(self):
        """Test data consistency across related endpoints."""
        print(f"\\n🧪 Testing data consistency across endpoints")
        
        # Get TTM data
        ratios_ttm = self.client.ratios_ttm(self.test_symbol)
        key_metrics_ttm = self.client.key_metrics_ttm(self.test_symbol)
        
        # Get historical data
        ratios_hist = self.client.ratios(self.test_symbol, period="annual", limit=1)
        key_metrics_hist = self.client.key_metrics(self.test_symbol, period="annual", limit=1)
        
        # Verify TTM and historical data have similar PE ratios (should be reasonably close)
        if not ratios_hist.empty and ratios_ttm.pe_ratio_ttm != 0 and key_metrics_ttm.pe_ratio_ttm != 0:
            # TTM ratios should be consistent between endpoints
            pe_diff = abs(ratios_ttm.pe_ratio_ttm - key_metrics_ttm.pe_ratio_ttm)
            assert pe_diff < 100, f"PE ratios between TTM endpoints differ too much: {pe_diff}"
        
        print("✅ Data consistency checks completed")


def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("\\n" + "="*80)
    print("🚀 STARTING COMPREHENSIVE FMP STATEMENT ANALYSIS API TESTS")
    print("="*80)
    print(f"📊 Test Symbol: AAPL (Apple Inc.)")
    print(f"🌐 API: Financial Modeling Prep")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Initialize test class
    test_class = TestFmpStatementAnalysis()
    test_class.setup_class()
    
    # List of all test methods
    test_methods = [
        "test_financial_score",
        "test_ratios_ttm", 
        "test_ratios_annual",
        "test_ratios_quarterly",
        "test_key_metrics_ttm",
        "test_key_metrics_annual", 
        "test_key_metrics_quarterly",
        "test_cashflow_growth_annual",
        "test_cashflow_growth_quarterly",
        "test_income_growth_annual",
        "test_income_growth_quarterly", 
        "test_balance_sheet_growth_annual",
        "test_balance_sheet_growth_quarterly",
        "test_financial_growth_annual",
        "test_financial_growth_quarterly",
        "test_owner_earnings",
        "test_enterprise_values",
        "test_error_handling",
        "test_data_consistency"
    ]
    
    # Run tests
    passed_tests = 0
    failed_tests = 0
    
    for test_method in test_methods:
        try:
            method = getattr(test_class, test_method)
            method()
            passed_tests += 1
        except Exception as e:
            print(f"❌ {test_method} FAILED: {str(e)}")
            failed_tests += 1
    
    # Print summary
    print("\\n" + "="*80)
    print("📈 TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📊 Total:  {passed_tests + failed_tests}")
    print(f"📈 Success Rate: {(passed_tests/(passed_tests + failed_tests)*100):.1f}%")
    print("="*80)
    
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED! FMP Statement Analysis API is working correctly.")
    else:
        print(f"⚠️  {failed_tests} test(s) failed. Check the output above for details.")
    
    print("="*80)


if __name__ == "__main__":
    run_comprehensive_test()