#!/usr/bin/env python3
"""
FMP Cache System - Portfolio Analysis Example
=============================================

This example demonstrates how to use the FMP Cache System for 
real-world portfolio analysis and comparison.

Features demonstrated:
- Portfolio composition analysis
- Performance comparison
- Risk metrics calculation
- Sector diversification analysis
- Financial health assessment
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import statistics

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.fmp_cache_api import FMPCacheAPI
    from cache.stock_data_fetcher import StockDataFetcher
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the StockAnalysis directory")
    sys.exit(1)


class PortfolioAnalyzer:
    """Portfolio analysis using cached FMP data"""
    
    def __init__(self):
        self.api = FMPCacheAPI()
        self.fetcher = StockDataFetcher()
    
    def ensure_data_available(self, symbols: list, days: int = 365):
        """Ensure data is available for analysis"""
        print(f"📊 Ensuring data availability for {len(symbols)} symbols...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        results = self.fetcher.fetch_batch(symbols, start_date, end_date)
        
        print(f"✅ Data preparation complete")
        print(f"  API Calls: {self.fetcher.stats['api_calls']}")
        print(f"  Cache Hits: {self.fetcher.stats['cache_hits']}")
        
        return results
    
    def get_portfolio_overview(self, symbols: list):
        """Get basic portfolio overview"""
        print(f"\n📋 Portfolio Overview")
        print("-" * 50)
        
        portfolio_data = {}
        total_market_cap = 0
        
        for symbol in symbols:
            profile = self.api.profile(symbol)
            quote = self.api.quote(symbol)
            
            if profile and quote:
                p = profile[0]
                q = quote[0]
                
                data = {
                    'name': p.get('companyName', 'N/A'),
                    'sector': p.get('sector', 'N/A'),
                    'industry': p.get('industry', 'N/A'),
                    'price': q.get('price', 0),
                    'market_cap': q.get('marketCap', 0),
                    'change_pct': q.get('changesPercentage', 0),
                    'pe_ratio': q.get('pe', 0),
                    'volume': q.get('volume', 0)
                }
                
                portfolio_data[symbol] = data
                total_market_cap += data['market_cap']
                
                print(f"{symbol}: {data['name']}")
                print(f"  Price: ${data['price']:.2f} ({data['change_pct']:+.2f}%)")
                print(f"  Market Cap: ${data['market_cap']:,.0f}")
                print(f"  P/E: {data['pe_ratio']}")
                print()
        
        return portfolio_data, total_market_cap
    
    def analyze_performance(self, symbols: list, days: int = 30):
        """Analyze portfolio performance"""
        print(f"\n📈 Performance Analysis (Last {days} Days)")
        print("-" * 50)
        
        performance_data = {}
        
        for symbol in symbols:
            historical = self.api.historical_price_full(symbol)
            
            if historical and historical.get('historical'):
                prices = historical['historical'][:days+1]
                
                if len(prices) >= 2:
                    current_price = prices[0]['close']
                    old_price = prices[-1]['close']
                    
                    total_return = ((current_price - old_price) / old_price) * 100
                    
                    # Calculate daily returns for volatility
                    daily_returns = []
                    for i in range(len(prices)-1):
                        today = prices[i]['close']
                        yesterday = prices[i+1]['close']
                        daily_return = ((today - yesterday) / yesterday) * 100
                        daily_returns.append(daily_return)
                    
                    volatility = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0
                    
                    performance_data[symbol] = {
                        'total_return': total_return,
                        'volatility': volatility,
                        'daily_returns': daily_returns
                    }
                    
                    print(f"{symbol}:")
                    print(f"  Total Return: {total_return:+.2f}%")
                    print(f"  Volatility: {volatility:.2f}%")
                    print(f"  Risk-Adjusted Return: {total_return/volatility:.2f}" if volatility > 0 else "  Risk-Adjusted Return: N/A")
                    print()
        
        return performance_data
    
    def analyze_sectors(self, portfolio_data: dict, total_market_cap: float):
        """Analyze sector diversification"""
        print(f"\n🏭 Sector Diversification")
        print("-" * 50)
        
        sectors = {}
        industries = {}
        
        for symbol, data in portfolio_data.items():
            sector = data['sector']
            industry = data['industry']
            market_cap = data['market_cap']
            
            if sector not in sectors:
                sectors[sector] = {'market_cap': 0, 'symbols': []}
            sectors[sector]['market_cap'] += market_cap
            sectors[sector]['symbols'].append(symbol)
            
            if industry not in industries:
                industries[industry] = {'market_cap': 0, 'symbols': []}
            industries[industry]['market_cap'] += market_cap
            industries[industry]['symbols'].append(symbol)
        
        print("Sector Allocation:")
        for sector, data in sorted(sectors.items(), key=lambda x: x[1]['market_cap'], reverse=True):
            percentage = (data['market_cap'] / total_market_cap) * 100
            print(f"  {sector}: {percentage:.1f}% ({', '.join(data['symbols'])})")
        
        print(f"\nDiversification Score: {len(sectors)}/10 sectors")
        
        return sectors, industries
    
    def analyze_financial_health(self, symbols: list):
        """Analyze financial health metrics"""
        print(f"\n💰 Financial Health Analysis")
        print("-" * 50)
        
        health_data = {}
        
        for symbol in symbols:
            # Get latest financial statements
            income = self.api.income_statement(symbol, limit=1)
            balance = self.api.balance_sheet_statement(symbol, limit=1)
            ratios = self.api.financial_ratios(symbol, limit=1)
            
            health_metrics = {}
            
            if income:
                stmt = income[0]
                health_metrics['revenue'] = stmt.get('revenue', 0)
                health_metrics['net_income'] = stmt.get('netIncome', 0)
                health_metrics['gross_margin'] = (stmt.get('grossProfit', 0) / stmt.get('revenue', 1)) * 100 if stmt.get('revenue', 0) > 0 else 0
            
            if balance:
                stmt = balance[0]
                health_metrics['total_debt'] = stmt.get('totalDebt', 0)
                health_metrics['cash'] = stmt.get('cashAndCashEquivalents', 0)
                health_metrics['total_assets'] = stmt.get('totalAssets', 0)
                
                # Debt-to-equity ratio
                total_equity = stmt.get('totalStockholdersEquity', 0)
                health_metrics['debt_to_equity'] = (health_metrics['total_debt'] / total_equity) if total_equity > 0 else 0
            
            if ratios:
                ratio_data = ratios[0]
                health_metrics['roe'] = ratio_data.get('returnOnEquity', 0)
                health_metrics['roa'] = ratio_data.get('returnOnAssets', 0)
                health_metrics['current_ratio'] = ratio_data.get('currentRatio', 0)
            
            health_data[symbol] = health_metrics
            
            print(f"{symbol}:")
            if health_metrics.get('revenue'):
                print(f"  Revenue: ${health_metrics['revenue']:,.0f}")
                print(f"  Net Income: ${health_metrics['net_income']:,.0f}")
                print(f"  Gross Margin: {health_metrics['gross_margin']:.1f}%")
            
            if health_metrics.get('cash') is not None:
                print(f"  Cash: ${health_metrics['cash']:,.0f}")
                print(f"  Debt-to-Equity: {health_metrics['debt_to_equity']:.2f}")
            
            if health_metrics.get('roe'):
                print(f"  ROE: {health_metrics['roe']:.1f}%")
                print(f"  ROA: {health_metrics['roa']:.1f}%")
                print(f"  Current Ratio: {health_metrics['current_ratio']:.2f}")
            
            print()
        
        return health_data
    
    def generate_recommendations(self, portfolio_data: dict, performance_data: dict, health_data: dict):
        """Generate portfolio recommendations"""
        print(f"\n💡 Portfolio Recommendations")
        print("-" * 50)
        
        recommendations = []
        
        # Performance analysis
        if performance_data:
            returns = [data['total_return'] for data in performance_data.values()]
            volatilities = [data['volatility'] for data in performance_data.values()]
            
            avg_return = statistics.mean(returns)
            avg_volatility = statistics.mean(volatilities)
            
            print(f"Portfolio Performance Summary:")
            print(f"  Average Return: {avg_return:+.2f}%")
            print(f"  Average Volatility: {avg_volatility:.2f}%")
            print(f"  Sharpe Ratio: {avg_return/avg_volatility:.2f}" if avg_volatility > 0 else "  Sharpe Ratio: N/A")
            
            # Find best and worst performers
            best_performer = max(performance_data.items(), key=lambda x: x[1]['total_return'])
            worst_performer = min(performance_data.items(), key=lambda x: x[1]['total_return'])
            
            print(f"\n  🏆 Best Performer: {best_performer[0]} ({best_performer[1]['total_return']:+.2f}%)")
            print(f"  📉 Worst Performer: {worst_performer[0]} ({worst_performer[1]['total_return']:+.2f}%)")
            
            # Risk analysis
            high_risk_stocks = [symbol for symbol, data in performance_data.items() if data['volatility'] > avg_volatility * 1.5]
            if high_risk_stocks:
                recommendations.append(f"Consider reducing exposure to high-volatility stocks: {', '.join(high_risk_stocks)}")
        
        # Financial health analysis
        if health_data:
            high_debt_stocks = []
            low_roe_stocks = []
            
            for symbol, data in health_data.items():
                if data.get('debt_to_equity', 0) > 1.0:
                    high_debt_stocks.append(symbol)
                if data.get('roe', 0) < 10:
                    low_roe_stocks.append(symbol)
            
            if high_debt_stocks:
                recommendations.append(f"Monitor high-debt companies: {', '.join(high_debt_stocks)}")
            
            if low_roe_stocks:
                recommendations.append(f"Consider companies with low ROE: {', '.join(low_roe_stocks)}")
        
        # Sector diversification
        sector_count = len(set(data['sector'] for data in portfolio_data.values()))
        if sector_count < 3:
            recommendations.append("Consider diversifying across more sectors (currently only {sector_count} sectors)")
        
        print(f"\nRecommendations:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("  ✅ Portfolio looks well-balanced!")
        
        return recommendations


def main():
    """Run portfolio analysis example"""
    print("="*70)
    print("🚀 FMP CACHE SYSTEM - PORTFOLIO ANALYSIS EXAMPLE")
    print("="*70)
    
    # Sample tech-heavy portfolio
    portfolio = [
        "AAPL",  # Apple
        "MSFT",  # Microsoft
        "GOOGL", # Alphabet
        "AMZN",  # Amazon
        "TSLA",  # Tesla
        "NVDA",  # NVIDIA
        "META",  # Meta
        "NFLX"   # Netflix
    ]
    
    print(f"📊 Analyzing portfolio of {len(portfolio)} stocks:")
    print(f"   {', '.join(portfolio)}")
    
    try:
        analyzer = PortfolioAnalyzer()
        
        # Ensure data is available
        analyzer.ensure_data_available(portfolio, days=365)
        
        # Portfolio overview
        portfolio_data, total_market_cap = analyzer.get_portfolio_overview(portfolio)
        
        if not portfolio_data:
            print("❌ No portfolio data available. Try fetching data first.")
            return 1
        
        # Performance analysis
        performance_data = analyzer.analyze_performance(portfolio, days=30)
        
        # Sector analysis
        sectors, industries = analyzer.analyze_sectors(portfolio_data, total_market_cap)
        
        # Financial health
        health_data = analyzer.analyze_financial_health(portfolio)
        
        # Recommendations
        recommendations = analyzer.generate_recommendations(portfolio_data, performance_data, health_data)
        
        print("\n" + "="*70)
        print("✅ PORTFOLIO ANALYSIS COMPLETE")
        print("="*70)
        
        print(f"\n💡 Key Insights:")
        print(f"  • Portfolio Value: ${total_market_cap:,.0f}")
        print(f"  • Sector Diversification: {len(sectors)} sectors")
        print(f"  • Performance Range: {min(data['total_return'] for data in performance_data.values()):+.1f}% to {max(data['total_return'] for data in performance_data.values()):+.1f}%")
        print(f"  • Recommendations: {len(recommendations)} items")
        
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())