"""
Jupyter Notebooks for FMP Stock Analysis

This directory contains Jupyter notebooks that demonstrate interactive
financial analysis using the Financial Modeling Prep API.

Available Notebooks:
- fmp_stock_analysis.ipynb: Comprehensive stock analysis with visualizations
- quick_analysis.ipynb: Quick stock analysis and market overview

To use these notebooks:
1. Install Jupyter: pip install jupyter
2. Start Jupyter: jupyter notebook
3. Navigate to this directory and open the desired notebook

Prerequisites:
- FMP API key (get one at https://financialmodelingprep.com/)
- Required packages: pandas, numpy, matplotlib, seaborn, jupyter

Note: Make sure to update the API key in the notebook cells before running.
"""

__version__ = "1.0.0"

NOTEBOOKS = [
    "fmp_stock_analysis.ipynb",
    "quick_analysis.ipynb"
]

def list_notebooks():
    """List available notebooks"""
    print("📓 Available Jupyter Notebooks:")
    print("-" * 35)
    print("1. fmp_stock_analysis.ipynb - Comprehensive analysis with charts")
    print("2. quick_analysis.ipynb - Quick stock analysis")
    print()
    print("To run: jupyter notebook [notebook_name]")

if __name__ == "__main__":
    list_notebooks()