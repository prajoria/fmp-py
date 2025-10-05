"""
Documentation for FMP Stock Analysis Package

This directory contains comprehensive documentation for the Financial Modeling Prep
(FMP) Stock Analysis package, including guides, examples, and best practices.

Available Documentation:
- STOCK_ANALYSIS_GUIDE.md: Comprehensive guide with analysis prompts and examples

Usage:
    The documentation in this directory provides detailed guidance for:
    - Fundamental analysis techniques
    - Valuation methodologies  
    - Risk assessment frameworks
    - Portfolio analysis workflows
    - Professional prompt examples

For the latest documentation, refer to the markdown files in this directory.
"""

__version__ = "1.0.0"
__author__ = "FMP Stock Analysis Team"

# Available documentation files
DOCUMENTATION_FILES = [
    "STOCK_ANALYSIS_GUIDE.md"
]

def list_documentation():
    """List all available documentation files"""
    print("📚 Available Documentation:")
    print("-" * 30)
    for doc in DOCUMENTATION_FILES:
        print(f"📄 {doc}")
    print()
    print("Access documentation files in this directory for detailed guidance.")

if __name__ == "__main__":
    list_documentation()