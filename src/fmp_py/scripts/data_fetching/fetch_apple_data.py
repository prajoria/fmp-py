#!/usr/bin/env python3
"""
FMP Apple Data Fetcher
======================
Fetch all fundamental data for Apple (AAPL) using FMP API and store in MySQL cache
"""

import os
import sys
import time
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(project_root / '.env')

# Use relative imports
from ...StockAnalysis.database.connection import get_db

class FMPDataFetcher:
    """Fetch and cache FMP data for Apple"""
    
    def __init__(self):
        self.api_key = os.getenv('FMP_API_KEY')
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.db = get_db()
        self.symbol = "AAPL"
        
        if not self.api_key:
            raise ValueError("FMP_API_KEY not found in environment variables")
    
    def make_request(self, endpoint, params=None):
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        request_params = {'apikey': self.api_key}
        if params:
            request_params.update(params)
        
        try:
            print(f"📡 Fetching: {endpoint}")
            response = requests.get(url, params=request_params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"   ✅ Retrieved {len(data) if isinstance(data, list) else 1} records")
            
            # Log API request
            self.log_api_request(endpoint, response.status_code, len(data) if isinstance(data, list) else 1)
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ API request failed: {e}")
            self.log_api_request(endpoint, getattr(e.response, 'status_code', 0), 0, str(e))
            return None
        except Exception as e:
            print(f"   ❌ Error processing response: {e}")
            return None
    
    def log_api_request(self, endpoint, status_code, record_count, error_message=None):
        """Log API request for monitoring"""
        try:
            self.db.execute_update("""
                INSERT INTO api_request_log (endpoint, symbol, response_status, from_cache, error_message, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (endpoint, self.symbol, status_code, False, error_message))
        except Exception as e:
            print(f"Warning: Could not log API request: {e}")
    
    def fetch_company_profile(self):
        """Fetch and store company profile"""
        print("\n🏢 Fetching Company Profile...")
        
        data = self.make_request(f"profile/{self.symbol}")
        if not data or len(data) == 0:
            return False
        
        profile = data[0]
        
        try:
            # Insert/update company
            self.db.execute_update("""
                INSERT INTO companies (symbol, name, exchange, exchange_short_name, type, currency, country, is_etf, is_actively_trading)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name), exchange = VALUES(exchange), exchange_short_name = VALUES(exchange_short_name),
                type = VALUES(type), currency = VALUES(currency), country = VALUES(country),
                is_etf = VALUES(is_etf), is_actively_trading = VALUES(is_actively_trading), updated_at = NOW()
            """, (
                profile.get('symbol'),
                profile.get('companyName'),
                profile.get('exchangeShortName'),
                profile.get('exchangeShortName'),
                'stock',
                profile.get('currency'),
                profile.get('country'),
                False,
                True
            ))
            
            # Insert/update company profile
            self.db.execute_update("""
                INSERT INTO company_profiles (
                    symbol, company_name, price, beta, vol_avg, mkt_cap, last_div, `range`, changes,
                    cik, isin, cusip, industry, sector, website, description, ceo, full_time_employees,
                    address, city, state, zip, country, phone, image, ipo_date, default_image, is_adr,
                    dcf, dcf_diff, cached_at, expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 24 HOUR))
                ON DUPLICATE KEY UPDATE
                company_name = VALUES(company_name), price = VALUES(price), beta = VALUES(beta),
                vol_avg = VALUES(vol_avg), mkt_cap = VALUES(mkt_cap), last_div = VALUES(last_div),
                `range` = VALUES(`range`), changes = VALUES(changes), industry = VALUES(industry),
                sector = VALUES(sector), website = VALUES(website), description = VALUES(description),
                ceo = VALUES(ceo), full_time_employees = VALUES(full_time_employees),
                cached_at = NOW(), expires_at = DATE_ADD(NOW(), INTERVAL 24 HOUR)
            """, (
                profile.get('symbol'),
                profile.get('companyName'),
                profile.get('price'),
                profile.get('beta'),
                profile.get('volAvg'),
                profile.get('mktCap'),
                profile.get('lastDiv'),
                profile.get('range'),
                profile.get('changes'),
                profile.get('cik'),
                profile.get('isin'),
                profile.get('cusip'),
                profile.get('industry'),
                profile.get('sector'),
                profile.get('website'),
                profile.get('description'),
                profile.get('ceo'),
                profile.get('fullTimeEmployees'),
                profile.get('address'),
                profile.get('city'),
                profile.get('state'),
                profile.get('zip'),
                profile.get('country'),
                profile.get('phone'),
                profile.get('image'),
                profile.get('ipoDate'),
                profile.get('defaultImage', False),
                profile.get('isAdr', False),
                profile.get('dcf'),
                profile.get('dcfDiff')
            ))
            
            print(f"   ✅ Stored profile for {profile.get('companyName')} ({profile.get('symbol')})")
            return True
            
        except Exception as e:
            print(f"   ❌ Error storing company profile: {e}")
            return False
    
    def fetch_quote(self):
        """Fetch and store current quote"""
        print("\n💰 Fetching Current Quote...")
        
        data = self.make_request(f"quote/{self.symbol}")
        if not data or len(data) == 0:
            return False
        
        quote = data[0]
        
        try:
            self.db.execute_update("""
                INSERT INTO quotes (
                    symbol, price, changes_percentage, `change`, day_low, day_high, year_high, year_low,
                    market_cap, price_avg_50, price_avg_200, volume, avg_volume, `open`, previous_close,
                    eps, pe, earnings_announcement, shares_outstanding, timestamp_unix,
                    cached_at, expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 5 MINUTE))
                ON DUPLICATE KEY UPDATE
                price = VALUES(price), changes_percentage = VALUES(changes_percentage),
                `change` = VALUES(`change`), day_low = VALUES(day_low), day_high = VALUES(day_high),
                volume = VALUES(volume), cached_at = NOW(), expires_at = DATE_ADD(NOW(), INTERVAL 5 MINUTE)
            """, (
                quote.get('symbol'),
                quote.get('price'),
                quote.get('changesPercentage'),
                quote.get('change'),
                quote.get('dayLow'),
                quote.get('dayHigh'),
                quote.get('yearHigh'),
                quote.get('yearLow'),
                quote.get('marketCap'),
                quote.get('priceAvg50'),
                quote.get('priceAvg200'),
                quote.get('volume'),
                quote.get('avgVolume'),
                quote.get('open'),
                quote.get('previousClose'),
                quote.get('eps'),
                quote.get('pe'),
                quote.get('earningsAnnouncement'),
                quote.get('sharesOutstanding'),
                quote.get('timestamp')
            ))
            
            print(f"   ✅ Stored quote: ${quote.get('price')} ({quote.get('changesPercentage'):+.2f}%)")
            return True
            
        except Exception as e:
            print(f"   ❌ Error storing quote: {e}")
            return False
    
    def fetch_financial_statements(self):
        """Fetch income statements, balance sheets, and cash flow statements"""
        print("\n📊 Fetching Financial Statements...")
        
        statements = {
            'income-statement': 'income_statements',
            'balance-sheet-statement': 'balance_sheets',
            'cash-flow-statement': 'cash_flow_statements'
        }
        
        for endpoint, table in statements.items():
            print(f"\n📈 Fetching {endpoint.replace('-', ' ').title()}...")
            
            data = self.make_request(f"{endpoint}/{self.symbol}", {'limit': 10})
            if not data:
                continue
            
            for statement in data:
                try:
                    if table == 'income_statements':
                        self.store_income_statement(statement)
                    elif table == 'balance_sheets':
                        self.store_balance_sheet(statement)
                    elif table == 'cash_flow_statements':
                        self.store_cash_flow_statement(statement)
                        
                except Exception as e:
                    print(f"   ⚠️ Error storing {table} record: {e}")
                    continue
            
            print(f"   ✅ Stored {len(data)} {table} records")
            time.sleep(0.2)  # Rate limiting
    
    def store_income_statement(self, data):
        """Store income statement data"""
        self.db.execute_update("""
            INSERT INTO income_statements (
                symbol, date, calendar_year, period, reported_currency, cik, filling_date, accepted_date,
                revenue, cost_of_revenue, gross_profit, gross_profit_ratio, research_and_development_expenses,
                general_and_administrative_expenses, selling_and_marketing_expenses, selling_general_and_administrative_expenses,
                other_expenses, operating_expenses, cost_and_expenses, interest_income, interest_expense,
                depreciation_and_amortization, ebitda, ebitda_ratio, operating_income, operating_income_ratio,
                total_other_income_expenses_net, income_before_tax, income_before_tax_ratio, income_tax_expense,
                net_income, net_income_ratio, eps, eps_diluted, weighted_average_shares_outstanding,
                weighted_average_shares_outstanding_dil, link, final_link, cached_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
            revenue = VALUES(revenue), net_income = VALUES(net_income), eps = VALUES(eps),
            cached_at = NOW()
        """, (
            data.get('symbol'), data.get('date'), data.get('calendarYear'), data.get('period'),
            data.get('reportedCurrency'), data.get('cik'), data.get('fillingDate'), data.get('acceptedDate'),
            data.get('revenue'), data.get('costOfRevenue'), data.get('grossProfit'), data.get('grossProfitRatio'),
            data.get('researchAndDevelopmentExpenses'), data.get('generalAndAdministrativeExpenses'),
            data.get('sellingAndMarketingExpenses'), data.get('sellingGeneralAndAdministrativeExpenses'),
            data.get('otherExpenses'), data.get('operatingExpenses'), data.get('costAndExpenses'),
            data.get('interestIncome'), data.get('interestExpense'), data.get('depreciationAndAmortization'),
            data.get('ebitda'), data.get('ebitdaratio'), data.get('operatingIncome'), data.get('operatingIncomeRatio'),
            data.get('totalOtherIncomeExpensesNet'), data.get('incomeBeforeTax'), data.get('incomeBeforeTaxRatio'),
            data.get('incomeTaxExpense'), data.get('netIncome'), data.get('netIncomeRatio'),
            data.get('eps'), data.get('epsdiluted'), data.get('weightedAverageShsOut'),
            data.get('weightedAverageShsOutDil'), data.get('link'), data.get('finalLink')
        ))
    
    def store_balance_sheet(self, data):
        """Store balance sheet data"""
        self.db.execute_update("""
            INSERT INTO balance_sheets (
                symbol, date, calendar_year, period, reported_currency, cik, filling_date, accepted_date,
                cash_and_cash_equivalents, short_term_investments, cash_and_short_term_investments,
                net_receivables, inventory, other_current_assets, total_current_assets,
                property_plant_equipment_net, goodwill, intangible_assets, goodwill_and_intangible_assets,
                long_term_investments, tax_assets, other_non_current_assets, total_non_current_assets,
                other_assets, total_assets, account_payables, short_term_debt, tax_payables,
                deferred_revenue, other_current_liabilities, total_current_liabilities, long_term_debt,
                deferred_revenue_non_current, deferred_tax_liabilities_non_current, other_non_current_liabilities,
                total_non_current_liabilities, other_liabilities, capital_lease_obligations, total_liabilities,
                preferred_stock, common_stock, retained_earnings, accumulated_other_comprehensive_income_loss,
                othertotal_stockholders_equity, total_stockholders_equity, total_equity,
                total_liabilities_and_stockholders_equity, minority_interest, total_liabilities_and_total_equity,
                total_investments, total_debt, net_debt, link, final_link, cached_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
            total_assets = VALUES(total_assets), total_liabilities = VALUES(total_liabilities),
            cached_at = NOW()
        """, (
            data.get('symbol'), data.get('date'), data.get('calendarYear'), data.get('period'),
            data.get('reportedCurrency'), data.get('cik'), data.get('fillingDate'), data.get('acceptedDate'),
            data.get('cashAndCashEquivalents'), data.get('shortTermInvestments'), data.get('cashAndShortTermInvestments'),
            data.get('netReceivables'), data.get('inventory'), data.get('otherCurrentAssets'), data.get('totalCurrentAssets'),
            data.get('propertyPlantEquipmentNet'), data.get('goodwill'), data.get('intangibleAssets'),
            data.get('goodwillAndIntangibleAssets'), data.get('longTermInvestments'), data.get('taxAssets'),
            data.get('otherNonCurrentAssets'), data.get('totalNonCurrentAssets'), data.get('otherAssets'),
            data.get('totalAssets'), data.get('accountPayables'), data.get('shortTermDebt'), data.get('taxPayables'),
            data.get('deferredRevenue'), data.get('otherCurrentLiabilities'), data.get('totalCurrentLiabilities'),
            data.get('longTermDebt'), data.get('deferredRevenueNonCurrent'), data.get('deferredTaxLiabilitiesNonCurrent'),
            data.get('otherNonCurrentLiabilities'), data.get('totalNonCurrentLiabilities'), data.get('otherLiabilities'),
            data.get('capitalLeaseObligations'), data.get('totalLiabilities'), data.get('preferredStock'),
            data.get('commonStock'), data.get('retainedEarnings'), data.get('accumulatedOtherComprehensiveIncomeLoss'),
            data.get('othertotalStockholdersEquity'), data.get('totalStockholdersEquity'), data.get('totalEquity'),
            data.get('totalLiabilitiesAndStockholdersEquity'), data.get('minorityInterest'),
            data.get('totalLiabilitiesAndTotalEquity'), data.get('totalInvestments'), data.get('totalDebt'),
            data.get('netDebt'), data.get('link'), data.get('finalLink')
        ))
    
    def store_cash_flow_statement(self, data):
        """Store cash flow statement data"""
        self.db.execute_update("""
            INSERT INTO cash_flow_statements (
                symbol, date, calendar_year, period, reported_currency, cik, filling_date, accepted_date,
                net_income, depreciation_and_amortization, deferred_income_tax, stock_based_compensation,
                change_in_working_capital, accounts_receivables, inventory, accounts_payables,
                other_working_capital, other_non_cash_items, net_cash_provided_by_operating_activities,
                investments_in_property_plant_and_equipment, acquisitions_net, purchases_of_investments,
                sales_maturities_of_investments, other_investing_activities, net_cash_used_for_investing_activities,
                debt_repayment, common_stock_issued, common_stock_repurchased, dividends_paid,
                other_financing_activities, net_cash_used_provided_by_financing_activities,
                effect_of_forex_changes_on_cash, net_change_in_cash, cash_at_end_of_period,
                cash_at_beginning_of_period, operating_cash_flow, capital_expenditure, free_cash_flow,
                link, final_link, cached_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
            operating_cash_flow = VALUES(operating_cash_flow), free_cash_flow = VALUES(free_cash_flow),
            cached_at = NOW()
        """, (
            data.get('symbol'), data.get('date'), data.get('calendarYear'), data.get('period'),
            data.get('reportedCurrency'), data.get('cik'), data.get('fillingDate'), data.get('acceptedDate'),
            data.get('netIncome'), data.get('depreciationAndAmortization'), data.get('deferredIncomeTax'),
            data.get('stockBasedCompensation'), data.get('changeInWorkingCapital'), data.get('accountsReceivables'),
            data.get('inventory'), data.get('accountsPayables'), data.get('otherWorkingCapital'),
            data.get('otherNonCashItems'), data.get('netCashProvidedByOperatingActivities'),
            data.get('investmentsInPropertyPlantAndEquipment'), data.get('acquisitionsNet'),
            data.get('purchasesOfInvestments'), data.get('salesMaturitiesOfInvestments'),
            data.get('otherInvestingActivites'), data.get('netCashUsedForInvestingActivites'),
            data.get('debtRepayment'), data.get('commonStockIssued'), data.get('commonStockRepurchased'),
            data.get('dividendsPaid'), data.get('otherFinancingActivites'),
            data.get('netCashUsedProvidedByFinancingActivities'), data.get('effectOfForexChangesOnCash'),
            data.get('netChangeInCash'), data.get('cashAtEndOfPeriod'), data.get('cashAtBeginningOfPeriod'),
            data.get('operatingCashFlow'), data.get('capitalExpenditure'), data.get('freeCashFlow'),
            data.get('link'), data.get('finalLink')
        ))
    
    def fetch_financial_ratios(self):
        """Fetch and store financial ratios"""
        print("\n📈 Fetching Financial Ratios...")
        
        data = self.make_request(f"ratios/{self.symbol}", {'limit': 10})
        if not data:
            return False
        
        for ratio in data:
            try:
                self.db.execute_update("""
                    INSERT INTO financial_ratios (
                        symbol, date, calendar_year, period, current_ratio, quick_ratio, cash_ratio,
                        days_of_sales_outstanding, days_of_inventory_outstanding, operating_cycle,
                        days_of_payables_outstanding, cash_conversion_cycle, gross_profit_margin,
                        operating_profit_margin, pretax_profit_margin, net_profit_margin, effective_tax_rate,
                        return_on_assets, return_on_equity, return_on_capital_employed, net_income_per_ebt,
                        ebt_per_ebit, ebit_per_revenue, debt_ratio, debt_equity_ratio, long_term_debt_to_capitalization,
                        total_debt_to_capitalization, interest_coverage, cash_flow_to_debt_ratio,
                        company_equity_multiplier, receivables_turnover, payables_turnover, inventory_turnover,
                        fixed_asset_turnover, asset_turnover, operating_cash_flow_per_share, free_cash_flow_per_share,
                        cash_per_share, payout_ratio, operating_cash_flow_sales_ratio, free_cash_flow_operating_cash_flow_ratio,
                        cash_flow_coverage_ratios, short_term_coverage_ratios, capital_expenditure_coverage_ratio,
                        dividend_paid_and_capex_coverage_ratio, dividend_payout_ratio, price_book_value_ratio,
                        price_to_book_ratio, price_to_sales_ratio, price_earnings_ratio, price_to_free_cash_flows_ratio,
                        price_to_operating_cash_flows_ratio, price_cash_flow_ratio, price_earnings_to_growth_ratio,
                        price_sales_ratio, dividend_yield, enterprise_value_multiple, price_fair_value, cached_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                    current_ratio = VALUES(current_ratio), return_on_equity = VALUES(return_on_equity),
                    debt_equity_ratio = VALUES(debt_equity_ratio), cached_at = NOW()
                """, (
                    ratio.get('symbol'), ratio.get('date'), ratio.get('calendarYear'), ratio.get('period'),
                    ratio.get('currentRatio'), ratio.get('quickRatio'), ratio.get('cashRatio'),
                    ratio.get('daysOfSalesOutstanding'), ratio.get('daysOfInventoryOutstanding'), ratio.get('operatingCycle'),
                    ratio.get('daysOfPayablesOutstanding'), ratio.get('cashConversionCycle'), ratio.get('grossProfitMargin'),
                    ratio.get('operatingProfitMargin'), ratio.get('pretaxProfitMargin'), ratio.get('netProfitMargin'),
                    ratio.get('effectiveTaxRate'), ratio.get('returnOnAssets'), ratio.get('returnOnEquity'),
                    ratio.get('returnOnCapitalEmployed'), ratio.get('netIncomePerEBT'), ratio.get('ebtPerEbit'),
                    ratio.get('ebitPerRevenue'), ratio.get('debtRatio'), ratio.get('debtEquityRatio'),
                    ratio.get('longTermDebtToCapitalization'), ratio.get('totalDebtToCapitalization'),
                    ratio.get('interestCoverage'), ratio.get('cashFlowToDebtRatio'), ratio.get('companyEquityMultiplier'),
                    ratio.get('receivablesTurnover'), ratio.get('payablesTurnover'), ratio.get('inventoryTurnover'),
                    ratio.get('fixedAssetTurnover'), ratio.get('assetTurnover'), ratio.get('operatingCashFlowPerShare'),
                    ratio.get('freeCashFlowPerShare'), ratio.get('cashPerShare'), ratio.get('payoutRatio'),
                    ratio.get('operatingCashFlowSalesRatio'), ratio.get('freeCashFlowOperatingCashFlowRatio'),
                    ratio.get('cashFlowCoverageRatios'), ratio.get('shortTermCoverageRatios'),
                    ratio.get('capitalExpenditureCoverageRatio'), ratio.get('dividendPaidAndCapexCoverageRatio'),
                    ratio.get('dividendPayoutRatio'), ratio.get('priceBookValueRatio'), ratio.get('priceToBookRatio'),
                    ratio.get('priceToSalesRatio'), ratio.get('priceEarningsRatio'), ratio.get('priceToFreeCashFlowsRatio'),
                    ratio.get('priceToOperatingCashFlowsRatio'), ratio.get('priceCashFlowRatio'),
                    ratio.get('priceEarningsToGrowthRatio'), ratio.get('priceSalesRatio'), ratio.get('dividendYield'),
                    ratio.get('enterpriseValueMultiple'), ratio.get('priceFairValue')
                ))
                
            except Exception as e:
                print(f"   ⚠️ Error storing financial ratio: {e}")
                continue
        
        print(f"   ✅ Stored {len(data)} financial ratio records")
        return True
    
    def fetch_key_metrics(self):
        """Fetch and store key metrics"""
        print("\n🔑 Fetching Key Metrics...")
        
        data = self.make_request(f"key-metrics/{self.symbol}", {'limit': 10})
        if not data:
            return False
        
        for metric in data:
            try:
                self.db.execute_update("""
                    INSERT INTO key_metrics (
                        symbol, date, calendar_year, period, revenue_per_share, net_income_per_share,
                        operating_cash_flow_per_share, free_cash_flow_per_share, cash_per_share, book_value_per_share,
                        tangible_book_value_per_share, shareholders_equity_per_share, interest_debt_per_share,
                        market_cap, enterprise_value, pe_ratio, price_to_sales_ratio, pocf_ratio, pfcf_ratio,
                        pb_ratio, ptb_ratio, ev_to_sales, enterprise_value_over_ebitda, ev_to_operating_cash_flow,
                        ev_to_free_cash_flow, earnings_yield, free_cash_flow_yield, debt_to_equity, debt_to_assets,
                        net_debt_to_ebitda, current_ratio, interest_coverage, income_quality, dividend_yield,
                        payout_ratio, sales_general_and_administrative_to_revenue, research_and_development_to_revenue,
                        intangibles_to_total_assets, capex_to_operating_cash_flow, capex_to_revenue, capex_to_depreciation,
                        stock_based_compensation_to_revenue, graham_number, roic, return_on_tangible_assets,
                        graham_net_net, working_capital, tangible_asset_value, net_current_asset_value, invested_capital,
                        average_receivables, average_payables, average_inventory, days_sales_outstanding,
                        days_payables_outstanding, days_of_inventory_on_hand, receivables_turnover, payables_turnover,
                        inventory_turnover, roe, capex_per_share, cached_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                    pe_ratio = VALUES(pe_ratio), market_cap = VALUES(market_cap), roe = VALUES(roe),
                    cached_at = NOW()
                """, (
                    metric.get('symbol'), metric.get('date'), metric.get('calendarYear'), metric.get('period'),
                    metric.get('revenuePerShare'), metric.get('netIncomePerShare'), metric.get('operatingCashFlowPerShare'),
                    metric.get('freeCashFlowPerShare'), metric.get('cashPerShare'), metric.get('bookValuePerShare'),
                    metric.get('tangibleBookValuePerShare'), metric.get('shareholdersEquityPerShare'),
                    metric.get('interestDebtPerShare'), metric.get('marketCap'), metric.get('enterpriseValue'),
                    metric.get('peRatio'), metric.get('priceToSalesRatio'), metric.get('pocfratio'), metric.get('pfcfRatio'),
                    metric.get('pbRatio'), metric.get('ptbRatio'), metric.get('evToSales'), metric.get('enterpriseValueOverEBITDA'),
                    metric.get('evToOperatingCashFlow'), metric.get('evToFreeCashFlow'), metric.get('earningsYield'),
                    metric.get('freeCashFlowYield'), metric.get('debtToEquity'), metric.get('debtToAssets'),
                    metric.get('netDebtToEBITDA'), metric.get('currentRatio'), metric.get('interestCoverage'),
                    metric.get('incomeQuality'), metric.get('dividendYield'), metric.get('payoutRatio'),
                    metric.get('salesGeneralAndAdministrativeToRevenue'), metric.get('researchAndDevelopmentToRevenue'),
                    metric.get('intangiblesToTotalAssets'), metric.get('capexToOperatingCashFlow'), metric.get('capexToRevenue'),
                    metric.get('capexToDepreciation'), metric.get('stockBasedCompensationToRevenue'), metric.get('grahamNumber'),
                    metric.get('roic'), metric.get('returnOnTangibleAssets'), metric.get('grahamNetNet'),
                    metric.get('workingCapital'), metric.get('tangibleAssetValue'), metric.get('netCurrentAssetValue'),
                    metric.get('investedCapital'), metric.get('averageReceivables'), metric.get('averagePayables'),
                    metric.get('averageInventory'), metric.get('daysSalesOutstanding'), metric.get('daysPayablesOutstanding'),
                    metric.get('daysOfInventoryOnHand'), metric.get('receivablesTurnover'), metric.get('payablesTurnover'),
                    metric.get('inventoryTurnover'), metric.get('roe'), metric.get('capexPerShare')
                ))
                
            except Exception as e:
                print(f"   ⚠️ Error storing key metric: {e}")
                continue
        
        print(f"   ✅ Stored {len(data)} key metric records")
        return True
    
    def fetch_historical_prices(self):
        """Fetch and store historical daily prices"""
        print("\n📈 Fetching Historical Prices (1 year)...")
        
        # Get 1 year of daily prices
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        params = {
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d')
        }
        
        data = self.make_request(f"historical-price-full/{self.symbol}", params)
        if not data or 'historical' not in data:
            return False
        
        historical_data = data['historical']
        
        for price_data in historical_data:
            try:
                self.db.execute_update("""
                    INSERT INTO historical_prices_daily (
                        symbol, date, `open`, high, low, `close`, adj_close, volume, unadjusted_volume,
                        `change`, change_percent, vwap, label, change_over_time, cached_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                    `close` = VALUES(`close`), volume = VALUES(volume), cached_at = NOW()
                """, (
                    self.symbol, price_data.get('date'), price_data.get('open'), price_data.get('high'),
                    price_data.get('low'), price_data.get('close'), price_data.get('adjClose'),
                    price_data.get('volume'), price_data.get('unadjustedVolume'), price_data.get('change'),
                    price_data.get('changePercent'), price_data.get('vwap'), price_data.get('label'),
                    price_data.get('changeOverTime')
                ))
                
            except Exception as e:
                print(f"   ⚠️ Error storing historical price: {e}")
                continue
        
        print(f"   ✅ Stored {len(historical_data)} historical price records")
        return True
    
    def fetch_news(self):
        """Fetch and store recent news"""
        print("\n📰 Fetching Recent News...")
        
        data = self.make_request(f"stock_news", {'tickers': self.symbol, 'limit': 50})
        if not data:
            return False
        
        for article in data:
            try:
                self.db.execute_update("""
                    INSERT INTO stock_news (symbol, published_date, title, image, site, text, url, cached_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                    title = VALUES(title), cached_at = NOW()
                """, (
                    self.symbol, article.get('publishedDate'), article.get('title'),
                    article.get('image'), article.get('site'), article.get('text'), article.get('url')
                ))
                
            except Exception as e:
                if "Duplicate entry" not in str(e):
                    print(f"   ⚠️ Error storing news article: {e}")
                continue
        
        print(f"   ✅ Stored {len(data)} news articles")
        return True
    
    def show_summary(self):
        """Show summary of cached data"""
        print("\n📊 Cache Summary")
        print("=" * 50)
        
        queries = {
            "Companies": "SELECT COUNT(*) as count FROM companies WHERE symbol = %s",
            "Company Profiles": "SELECT COUNT(*) as count FROM company_profiles WHERE symbol = %s",
            "Quotes": "SELECT COUNT(*) as count FROM quotes WHERE symbol = %s",
            "Income Statements": "SELECT COUNT(*) as count FROM income_statements WHERE symbol = %s",
            "Balance Sheets": "SELECT COUNT(*) as count FROM balance_sheets WHERE symbol = %s",
            "Cash Flow Statements": "SELECT COUNT(*) as count FROM cash_flow_statements WHERE symbol = %s",
            "Financial Ratios": "SELECT COUNT(*) as count FROM financial_ratios WHERE symbol = %s",
            "Key Metrics": "SELECT COUNT(*) as count FROM key_metrics WHERE symbol = %s",
            "Historical Prices": "SELECT COUNT(*) as count FROM historical_prices_daily WHERE symbol = %s",
            "News Articles": "SELECT COUNT(*) as count FROM stock_news WHERE symbol = %s",
            "API Requests": "SELECT COUNT(*) as count FROM api_request_log WHERE symbol = %s"
        }
        
        for name, query in queries.items():
            try:
                result = self.db.execute_query(query, (self.symbol,), fetch='one')
                print(f"  {name}: {result['count']} records")
            except Exception as e:
                print(f"  {name}: Error - {e}")

def main():
    """Main function to fetch all Apple data"""
    print("🍎 Apple (AAPL) Fundamental Data Fetcher")
    print("=" * 60)
    
    try:
        fetcher = FMPDataFetcher()
        
        print(f"🎯 Target Symbol: {fetcher.symbol}")
        print(f"🔑 API Key: {fetcher.api_key[:10]}...")
        print(f"🗄️ Database: {os.getenv('FMP_DB_NAME')} @ {os.getenv('FMP_DB_HOST')}")
        print()
        
        # Fetch all data
        success_count = 0
        total_operations = 7
        
        operations = [
            ("Company Profile", fetcher.fetch_company_profile),
            ("Current Quote", fetcher.fetch_quote),
            ("Financial Statements", fetcher.fetch_financial_statements),
            ("Financial Ratios", fetcher.fetch_financial_ratios),
            ("Key Metrics", fetcher.fetch_key_metrics),
            ("Historical Prices", fetcher.fetch_historical_prices),
            ("Recent News", fetcher.fetch_news)
        ]
        
        for name, operation in operations:
            try:
                print(f"\n{'='*60}")
                print(f"🔄 Processing: {name}")
                print(f"{'='*60}")
                
                if operation():
                    success_count += 1
                    print(f"✅ {name} completed successfully")
                else:
                    print(f"❌ {name} failed")
                
                # Rate limiting
                time.sleep(0.3)
                
            except Exception as e:
                print(f"❌ Error in {name}: {e}")
        
        # Show summary
        fetcher.show_summary()
        
        print(f"\n🎉 Data Fetching Complete!")
        print(f"✅ Successfully completed {success_count}/{total_operations} operations")
        print(f"📊 All Apple fundamental data is now cached in your MySQL database")
        
        if success_count == total_operations:
            print("\n🚀 Your FMP cache is ready for high-performance queries!")
        else:
            print(f"\n⚠️ {total_operations - success_count} operations had issues - check logs above")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return False

if __name__ == "__main__":
    main()