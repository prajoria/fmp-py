"""
Financial Modeling Prep (FMP) API Examples

This package contains practical examples demonstrating how to use the FMP API
for various financial analysis tasks.

Available Examples:
- apple_analysis.py: Comprehensive analysis of Apple (AAPL) stock
- stock_screener.py: Screen stocks based on various financial criteria
- portfolio_analysis.py: Analyze portfolio performance and risk metrics

Usage:
    python -m examples.apple_analysis
    python -m examples.stock_screener
    python -m examples.portfolio_analysis

Note: Make sure to set your FMP API key in the environment or update
the examples with your API key.
"""

__version__ = "1.0.0"
__author__ = "FMP API Examples"

# Available example modules
EXAMPLES = [
    "apple_analysis",
    "stock_screener", 
    "portfolio_analysis"
]

def list_examples():
    """List all available examples"""
    print("📚 Available FMP API Examples:")
    print("-" * 30)
    print("1. apple_analysis.py - Comprehensive Apple stock analysis")
    print("2. stock_screener.py - Multi-criteria stock screening")
    print("3. portfolio_analysis.py - Portfolio performance & risk analysis")
    print()
    print("Run examples with: python examples/[example_name].py")

if __name__ == "__main__":
    list_examples()