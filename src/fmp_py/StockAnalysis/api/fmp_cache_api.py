"""
FMP Cache API
=============
Local API interface that mimics FMP API endpoints but serves data from MySQL cache.
Provides identical interface to FMP API for seamless integration.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import json
from database.connection import get_db
from cache.cache_manager import CacheManager


class FMPCacheAPI:
    """
    Local FMP-compatible API that serves cached data.
    
    Provides the same interface as FMP API endpoints:
    - profile/{symbol}
    - quote/{symbol}
    - historical-price-full/{symbol}
    - income-statement/{symbol}
    - balance-sheet-statement/{symbol}
    - cash-flow-statement/{symbol}
    - ratios/{symbol}
    - key-metrics/{symbol}
    - stock_news
    """
    
    def __init__(self):
        self.db = get_db()
        self.cache_manager = CacheManager()
    
    def profile(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get company profile data from cache.
        Mimics: /api/v3/profile/{symbol}
        """
        try:
            result = self.db.execute_query("""
                SELECT 
                    symbol, company_name as companyName, price, beta, vol_avg as volAvg,
                    mkt_cap as mktCap, last_div as lastDiv, `range`, changes,
                    cik, isin, cusip, industry, sector, website, description,
                    ceo, full_time_employees as fullTimeEmployees, address, city,
                    state, zip, country, phone, image, ipo_date as ipoDate,
                    default_image as defaultImage, is_adr as isAdr, dcf, dcf_diff as dcfDiff
                FROM company_profiles 
                WHERE symbol = %s
            """, (symbol.upper(),), fetch='one')
            
            if result:
                # Convert to FMP format
                profile = dict(result)
                # Convert boolean fields
                profile['defaultImage'] = bool(profile.get('defaultImage', False))
                profile['isAdr'] = bool(profile.get('isAdr', False))
                return [profile]
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching profile for {symbol}: {e}")
            return []
    
    def quote(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get quote data from cache.
        Mimics: /api/v3/quote/{symbol}
        """
        try:
            result = self.db.execute_query("""
                SELECT 
                    symbol, price, changes_percentage as changesPercentage,
                    `change`, day_low as dayLow, day_high as dayHigh,
                    year_high as yearHigh, year_low as yearLow,
                    market_cap as marketCap, price_avg_50 as priceAvg50,
                    price_avg_200 as priceAvg200, volume, avg_volume as avgVolume,
                    `open`, previous_close as previousClose, eps, pe,
                    earnings_announcement as earningsAnnouncement,
                    shares_outstanding as sharesOutstanding, timestamp_unix as timestamp
                FROM quotes 
                WHERE symbol = %s
                ORDER BY cached_at DESC
                LIMIT 1
            """, (symbol.upper(),), fetch='one')
            
            if result:
                quote = dict(result)
                # Format earnings announcement date if exists
                if quote.get('earningsAnnouncement'):
                    # Convert to FMP format if needed
                    pass
                return [quote]
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching quote for {symbol}: {e}")
            return []
    
    def historical_price_full(self, symbol: str, from_date: str = None, 
                            to_date: str = None, **kwargs) -> Dict[str, Any]:
        """
        Get historical price data from cache.
        Mimics: /api/v3/historical-price-full/{symbol}
        """
        try:
            # Build date filter
            date_filter = ""
            params = [symbol.upper()]
            
            if from_date:
                date_filter += " AND date >= %s"
                params.append(from_date)
            
            if to_date:
                date_filter += " AND date <= %s"
                params.append(to_date)
            
            results = self.db.execute_query(f"""
                SELECT 
                    date, `open`, high, low, `close`, adj_close as adjClose,
                    volume, unadjusted_volume as unadjustedVolume, `change`,
                    change_percent as changePercent, vwap, label, change_over_time as changeOverTime
                FROM historical_prices_daily 
                WHERE symbol = %s {date_filter}
                ORDER BY date DESC
            """, params, fetch='all')
            
            if results:
                historical = []
                for row in results:
                    price_data = dict(row)
                    # Convert date to string format
                    if price_data['date']:
                        price_data['date'] = price_data['date'].strftime('%Y-%m-%d')
                    historical.append(price_data)
                
                return {
                    'symbol': symbol.upper(),
                    'historical': historical
                }
            else:
                return {'symbol': symbol.upper(), 'historical': []}
                
        except Exception as e:
            print(f"Error fetching historical prices for {symbol}: {e}")
            return {'symbol': symbol.upper(), 'historical': []}
    
    def income_statement(self, symbol: str, limit: int = 10, period: str = 'annual') -> List[Dict[str, Any]]:
        """
        Get income statement data from cache.
        Mimics: /api/v3/income-statement/{symbol}
        """
        try:
            period_filter = "FY" if period == "annual" else "Q%"
            
            results = self.db.execute_query("""
                SELECT 
                    symbol, date, calendar_year as calendarYear, period,
                    reported_currency as reportedCurrency, cik, filling_date as fillingDate,
                    accepted_date as acceptedDate, revenue, cost_of_revenue as costOfRevenue,
                    gross_profit as grossProfit, gross_profit_ratio as grossProfitRatio,
                    research_and_development_expenses as researchAndDevelopmentExpenses,
                    general_and_administrative_expenses as generalAndAdministrativeExpenses,
                    selling_and_marketing_expenses as sellingAndMarketingExpenses,
                    selling_general_and_administrative_expenses as sellingGeneralAndAdministrativeExpenses,
                    other_expenses as otherExpenses, operating_expenses as operatingExpenses,
                    cost_and_expenses as costAndExpenses, interest_income as interestIncome,
                    interest_expense as interestExpense, depreciation_and_amortization as depreciationAndAmortization,
                    ebitda, ebitda_ratio as ebitdaratio, operating_income as operatingIncome,
                    operating_income_ratio as operatingIncomeRatio, total_other_income_expenses_net as totalOtherIncomeExpensesNet,
                    income_before_tax as incomeBeforeTax, income_before_tax_ratio as incomeBeforeTaxRatio,
                    income_tax_expense as incomeTaxExpense, net_income as netIncome,
                    net_income_ratio as netIncomeRatio, eps, eps_diluted as epsdiluted,
                    weighted_average_shares_outstanding as weightedAverageShsOut,
                    weighted_average_shares_outstanding_dil as weightedAverageShsOutDil,
                    link, final_link as finalLink
                FROM income_statements 
                WHERE symbol = %s AND period LIKE %s
                ORDER BY date DESC
                LIMIT %s
            """, (symbol.upper(), period_filter, limit), fetch='all')
            
            if results:
                statements = []
                for row in results:
                    statement = dict(row)
                    # Convert date fields to string format
                    for date_field in ['date', 'fillingDate', 'acceptedDate']:
                        if statement.get(date_field):
                            statement[date_field] = statement[date_field].strftime('%Y-%m-%d')
                    statements.append(statement)
                return statements
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching income statements for {symbol}: {e}")
            return []
    
    def balance_sheet_statement(self, symbol: str, limit: int = 10, period: str = 'annual') -> List[Dict[str, Any]]:
        """
        Get balance sheet data from cache.
        Mimics: /api/v3/balance-sheet-statement/{symbol}
        """
        try:
            period_filter = "FY" if period == "annual" else "Q%"
            
            results = self.db.execute_query("""
                SELECT 
                    symbol, date, calendar_year as calendarYear, period,
                    reported_currency as reportedCurrency, cik, filling_date as fillingDate,
                    accepted_date as acceptedDate, cash_and_cash_equivalents as cashAndCashEquivalents,
                    short_term_investments as shortTermInvestments, cash_and_short_term_investments as cashAndShortTermInvestments,
                    net_receivables as netReceivables, inventory, other_current_assets as otherCurrentAssets,
                    total_current_assets as totalCurrentAssets, property_plant_equipment_net as propertyPlantEquipmentNet,
                    goodwill, intangible_assets as intangibleAssets, goodwill_and_intangible_assets as goodwillAndIntangibleAssets,
                    long_term_investments as longTermInvestments, tax_assets as taxAssets,
                    other_non_current_assets as otherNonCurrentAssets, total_non_current_assets as totalNonCurrentAssets,
                    other_assets as otherAssets, total_assets as totalAssets, account_payables as accountPayables,
                    short_term_debt as shortTermDebt, tax_payables as taxPayables, deferred_revenue as deferredRevenue,
                    other_current_liabilities as otherCurrentLiabilities, total_current_liabilities as totalCurrentLiabilities,
                    long_term_debt as longTermDebt, deferred_revenue_non_current as deferredRevenueNonCurrent,
                    deferred_tax_liabilities_non_current as deferredTaxLiabilitiesNonCurrent,
                    other_non_current_liabilities as otherNonCurrentLiabilities, total_non_current_liabilities as totalNonCurrentLiabilities,
                    other_liabilities as otherLiabilities, capital_lease_obligations as capitalLeaseObligations,
                    total_liabilities as totalLiabilities, preferred_stock as preferredStock, common_stock as commonStock,
                    retained_earnings as retainedEarnings, accumulated_other_comprehensive_income_loss as accumulatedOtherComprehensiveIncomeLoss,
                    othertotal_stockholders_equity as othertotalStockholdersEquity, total_stockholders_equity as totalStockholdersEquity,
                    total_equity as totalEquity, total_liabilities_and_stockholders_equity as totalLiabilitiesAndStockholdersEquity,
                    minority_interest as minorityInterest, total_liabilities_and_total_equity as totalLiabilitiesAndTotalEquity,
                    total_investments as totalInvestments, total_debt as totalDebt, net_debt as netDebt,
                    link, final_link as finalLink
                FROM balance_sheets 
                WHERE symbol = %s AND period LIKE %s
                ORDER BY date DESC
                LIMIT %s
            """, (symbol.upper(), period_filter, limit), fetch='all')
            
            if results:
                statements = []
                for row in results:
                    statement = dict(row)
                    # Convert date fields to string format
                    for date_field in ['date', 'fillingDate', 'acceptedDate']:
                        if statement.get(date_field):
                            statement[date_field] = statement[date_field].strftime('%Y-%m-%d')
                    statements.append(statement)
                return statements
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching balance sheets for {symbol}: {e}")
            return []
    
    def cash_flow_statement(self, symbol: str, limit: int = 10, period: str = 'annual') -> List[Dict[str, Any]]:
        """
        Get cash flow statement data from cache.
        Mimics: /api/v3/cash-flow-statement/{symbol}
        """
        try:
            period_filter = "FY" if period == "annual" else "Q%"
            
            results = self.db.execute_query("""
                SELECT 
                    symbol, date, calendar_year as calendarYear, period,
                    reported_currency as reportedCurrency, cik, filling_date as fillingDate,
                    accepted_date as acceptedDate, net_income as netIncome,
                    depreciation_and_amortization as depreciationAndAmortization,
                    deferred_income_tax as deferredIncomeTax, stock_based_compensation as stockBasedCompensation,
                    change_in_working_capital as changeInWorkingCapital, accounts_receivables as accountsReceivables,
                    inventory, accounts_payables as accountsPayables, other_working_capital as otherWorkingCapital,
                    other_non_cash_items as otherNonCashItems, net_cash_provided_by_operating_activities as netCashProvidedByOperatingActivities,
                    investments_in_property_plant_and_equipment as investmentsInPropertyPlantAndEquipment,
                    acquisitions_net as acquisitionsNet, purchases_of_investments as purchasesOfInvestments,
                    sales_maturities_of_investments as salesMaturitiesOfInvestments,
                    other_investing_activities as otherInvestingActivites,
                    net_cash_used_for_investing_activities as netCashUsedForInvestingActivites,
                    debt_repayment as debtRepayment, common_stock_issued as commonStockIssued,
                    common_stock_repurchased as commonStockRepurchased, dividends_paid as dividendsPaid,
                    other_financing_activities as otherFinancingActivites,
                    net_cash_used_provided_by_financing_activities as netCashUsedProvidedByFinancingActivities,
                    effect_of_forex_changes_on_cash as effectOfForexChangesOnCash,
                    net_change_in_cash as netChangeInCash, cash_at_end_of_period as cashAtEndOfPeriod,
                    cash_at_beginning_of_period as cashAtBeginningOfPeriod, operating_cash_flow as operatingCashFlow,
                    capital_expenditure as capitalExpenditure, free_cash_flow as freeCashFlow,
                    link, final_link as finalLink
                FROM cash_flow_statements 
                WHERE symbol = %s AND period LIKE %s
                ORDER BY date DESC
                LIMIT %s
            """, (symbol.upper(), period_filter, limit), fetch='all')
            
            if results:
                statements = []
                for row in results:
                    statement = dict(row)
                    # Convert date fields to string format
                    for date_field in ['date', 'fillingDate', 'acceptedDate']:
                        if statement.get(date_field):
                            statement[date_field] = statement[date_field].strftime('%Y-%m-%d')
                    statements.append(statement)
                return statements
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching cash flow statements for {symbol}: {e}")
            return []
    
    def stock_news(self, tickers: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get stock news from cache.
        Mimics: /api/v3/stock_news
        """
        try:
            query = """
                SELECT symbol, published_date as publishedDate, title, image, site, text, url
                FROM stock_news 
            """
            params = []
            
            if tickers:
                # Handle multiple tickers
                ticker_list = [t.strip().upper() for t in tickers.split(',')]
                placeholders = ','.join(['%s'] * len(ticker_list))
                query += f" WHERE symbol IN ({placeholders})"
                params.extend(ticker_list)
            
            query += " ORDER BY published_date DESC LIMIT %s"
            params.append(limit)
            
            results = self.db.execute_query(query, params, fetch='all')
            
            if results:
                news = []
                for row in results:
                    article = dict(row)
                    # Convert date to string format
                    if article.get('publishedDate'):
                        article['publishedDate'] = article['publishedDate'].strftime('%Y-%m-%d %H:%M:%S')
                    news.append(article)
                return news
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def ratios(self, symbol: str, limit: int = 10, period: str = 'annual') -> List[Dict[str, Any]]:
        """
        Get financial ratios from cache.
        Mimics: /api/v3/ratios/{symbol}
        """
        try:
            period_filter = "FY" if period == "annual" else "Q%"
            
            results = self.db.execute_query("""
                SELECT 
                    symbol, date, calendar_year as calendarYear, period,
                    current_ratio as currentRatio, quick_ratio as quickRatio, cash_ratio as cashRatio,
                    days_of_sales_outstanding as daysOfSalesOutstanding,
                    days_of_inventory_outstanding as daysOfInventoryOutstanding,
                    operating_cycle as operatingCycle, days_of_payables_outstanding as daysOfPayablesOutstanding,
                    cash_conversion_cycle as cashConversionCycle, gross_profit_margin as grossProfitMargin,
                    operating_profit_margin as operatingProfitMargin, pretax_profit_margin as pretaxProfitMargin,
                    net_profit_margin as netProfitMargin, effective_tax_rate as effectiveTaxRate,
                    return_on_assets as returnOnAssets, return_on_equity as returnOnEquity,
                    return_on_capital_employed as returnOnCapitalEmployed, net_income_per_ebt as netIncomePerEBT,
                    ebt_per_ebit as ebtPerEbit, ebit_per_revenue as ebitPerRevenue,
                    debt_ratio as debtRatio, debt_equity_ratio as debtEquityRatio,
                    long_term_debt_to_capitalization as longTermDebtToCapitalization,
                    total_debt_to_capitalization as totalDebtToCapitalization,
                    interest_coverage as interestCoverage, cash_flow_to_debt_ratio as cashFlowToDebtRatio,
                    company_equity_multiplier as companyEquityMultiplier,
                    receivables_turnover as receivablesTurnover, payables_turnover as payablesTurnover,
                    inventory_turnover as inventoryTurnover, fixed_asset_turnover as fixedAssetTurnover,
                    asset_turnover as assetTurnover, operating_cash_flow_per_share as operatingCashFlowPerShare,
                    free_cash_flow_per_share as freeCashFlowPerShare, cash_per_share as cashPerShare,
                    payout_ratio as payoutRatio, operating_cash_flow_sales_ratio as operatingCashFlowSalesRatio,
                    free_cash_flow_operating_cash_flow_ratio as freeCashFlowOperatingCashFlowRatio,
                    cash_flow_coverage_ratios as cashFlowCoverageRatios,
                    short_term_coverage_ratios as shortTermCoverageRatios,
                    capital_expenditure_coverage_ratio as capitalExpenditureCoverageRatio,
                    dividend_paid_and_capex_coverage_ratio as dividendPaidAndCapexCoverageRatio,
                    dividend_payout_ratio as dividendPayoutRatio, price_book_value_ratio as priceBookValueRatio,
                    price_to_book_ratio as priceToBookRatio, price_to_sales_ratio as priceToSalesRatio,
                    price_earnings_ratio as priceEarningsRatio, price_to_free_cash_flows_ratio as priceToFreeCashFlowsRatio,
                    price_to_operating_cash_flows_ratio as priceToOperatingCashFlowsRatio,
                    price_cash_flow_ratio as priceCashFlowRatio, price_earnings_to_growth_ratio as priceEarningsToGrowthRatio,
                    price_sales_ratio as priceSalesRatio, dividend_yield as dividendYield,
                    enterprise_value_multiple as enterpriseValueMultiple, price_fair_value as priceFairValue
                FROM financial_ratios 
                WHERE symbol = %s AND period LIKE %s
                ORDER BY date DESC
                LIMIT %s
            """, (symbol.upper(), period_filter, limit), fetch='all')
            
            if results:
                ratios = []
                for row in results:
                    ratio = dict(row)
                    # Convert date to string format
                    if ratio.get('date'):
                        ratio['date'] = ratio['date'].strftime('%Y-%m-%d')
                    ratios.append(ratio)
                return ratios
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching ratios for {symbol}: {e}")
            return []
    
    def key_metrics(self, symbol: str, limit: int = 10, period: str = 'annual') -> List[Dict[str, Any]]:
        """
        Get key metrics from cache.
        Mimics: /api/v3/key-metrics/{symbol}
        """
        try:
            period_filter = "FY" if period == "annual" else "Q%"
            
            results = self.db.execute_query("""
                SELECT 
                    symbol, date, calendar_year as calendarYear, period,
                    revenue_per_share as revenuePerShare, net_income_per_share as netIncomePerShare,
                    operating_cash_flow_per_share as operatingCashFlowPerShare,
                    free_cash_flow_per_share as freeCashFlowPerShare, cash_per_share as cashPerShare,
                    book_value_per_share as bookValuePerShare, tangible_book_value_per_share as tangibleBookValuePerShare,
                    shareholders_equity_per_share as shareholdersEquityPerShare,
                    interest_debt_per_share as interestDebtPerShare, market_cap as marketCap,
                    enterprise_value as enterpriseValue, pe_ratio as peRatio,
                    price_to_sales_ratio as priceToSalesRatio, pocf_ratio as pocfratio,
                    pfcf_ratio as pfcfRatio, pb_ratio as pbRatio, ptb_ratio as ptbRatio,
                    ev_to_sales as evToSales, enterprise_value_over_ebitda as enterpriseValueOverEBITDA,
                    ev_to_operating_cash_flow as evToOperatingCashFlow, ev_to_free_cash_flow as evToFreeCashFlow,
                    earnings_yield as earningsYield, free_cash_flow_yield as freeCashFlowYield,
                    debt_to_equity as debtToEquity, debt_to_assets as debtToAssets,
                    net_debt_to_ebitda as netDebtToEBITDA, current_ratio as currentRatio,
                    interest_coverage as interestCoverage, income_quality as incomeQuality,
                    dividend_yield as dividendYield, payout_ratio as payoutRatio,
                    sales_general_and_administrative_to_revenue as salesGeneralAndAdministrativeToRevenue,
                    research_and_development_to_revenue as researchAndDevelopmentToRevenue,
                    intangibles_to_total_assets as intangiblesToTotalAssets,
                    capex_to_operating_cash_flow as capexToOperatingCashFlow,
                    capex_to_revenue as capexToRevenue, capex_to_depreciation as capexToDepreciation,
                    stock_based_compensation_to_revenue as stockBasedCompensationToRevenue,
                    graham_number as grahamNumber, roic, return_on_tangible_assets as returnOnTangibleAssets,
                    graham_net_net as grahamNetNet, working_capital as workingCapital,
                    tangible_asset_value as tangibleAssetValue, net_current_asset_value as netCurrentAssetValue,
                    invested_capital as investedCapital, average_receivables as averageReceivables,
                    average_payables as averagePayables, average_inventory as averageInventory,
                    days_sales_outstanding as daysSalesOutstanding, days_payables_outstanding as daysPayablesOutstanding,
                    days_of_inventory_on_hand as daysOfInventoryOnHand, receivables_turnover as receivablesTurnover,
                    payables_turnover as payablesTurnover, inventory_turnover as inventoryTurnover,
                    roe, capex_per_share as capexPerShare
                FROM key_metrics 
                WHERE symbol = %s AND period LIKE %s
                ORDER BY date DESC
                LIMIT %s
            """, (symbol.upper(), period_filter, limit), fetch='all')
            
            if results:
                metrics = []
                for row in results:
                    metric = dict(row)
                    # Convert date to string format
                    if metric.get('date'):
                        metric['date'] = metric['date'].strftime('%Y-%m-%d')
                    metrics.append(metric)
                return metrics
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching key metrics for {symbol}: {e}")
            return []
    
    def get_available_symbols(self) -> List[str]:
        """Get list of all symbols available in cache"""
        try:
            results = self.db.execute_query("""
                SELECT DISTINCT symbol 
                FROM companies 
                ORDER BY symbol
            """, fetch='all')
            
            return [row['symbol'] for row in results] if results else []
            
        except Exception as e:
            print(f"Error getting available symbols: {e}")
            return []
    
    def get_cache_info(self, symbol: str = None) -> Dict[str, Any]:
        """Get cache information and statistics"""
        return self.cache_manager.get_cache_statistics(symbol)
    
    def health_check(self) -> Dict[str, Any]:
        """API health check with cache status"""
        try:
            # Test database connection
            test_result = self.db.execute_query("SELECT 1 as test", fetch='one')
            db_status = "healthy" if test_result else "error"
            
            # Get cache statistics
            stats = self.get_cache_info()
            
            return {
                'status': 'healthy' if db_status == 'healthy' else 'error',
                'database': db_status,
                'cache_stats': stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }