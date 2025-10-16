#!/usr/bin/env python3
"""
Security Verification Script
Checks that all API key usage follows security best practices
"""

import os
import re
import glob
from pathlib import Path

def check_file_for_hardcoded_keys(file_path):
    """Check a file for hardcoded API keys"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        # Patterns to look for
        patterns = [
            r'api_key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',  # api_key = "hardcoded_key"
            r'FMP_API_KEY\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',  # FMP_API_KEY = "hardcoded_key"
            r'oTP74s9TxGsnRjac3xRBn3JQcP5qvYwQ',  # Specific API key pattern
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    # Skip if it's in a comment explaining what to avoid
                    if not line.strip().startswith('#') and 'your_api_key_here' not in line:
                        issues.append(f"Line {i}: {line.strip()}")
    
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    
    return issues

def verify_secure_usage(file_path):
    """Verify that API key usage follows secure patterns"""
    secure_patterns = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for secure patterns
        if "os.getenv('FMP_API_KEY')" in content:
            secure_patterns.append("✅ Uses os.getenv()")
        if "load_dotenv()" in content:
            secure_patterns.append("✅ Loads environment variables")
        if "if not api_key:" in content or "if not API_KEY:" in content:
            secure_patterns.append("✅ Has error handling")
            
    except Exception:
        pass
    
    return secure_patterns

def main():
    """Run security verification"""
    print("🔍 FMP Package Security Verification")
    print("=" * 40)
    
    # Get the package root
    package_root = Path(__file__).parent
    
    # File patterns to check
    patterns = [
        "src/**/*.py",
        "*.py",
        "examples/*.py" if (package_root / "examples").exists() else None,
        "notebooks/*.ipynb" if (package_root / "notebooks").exists() else None,
    ]
    
    total_files = 0
    secure_files = 0
    issues_found = 0
    
    for pattern in patterns:
        if pattern is None:
            continue
            
        files = glob.glob(str(package_root / pattern), recursive=True)
        
        for file_path in files:
            if os.path.isfile(file_path):
                total_files += 1
                relative_path = os.path.relpath(file_path, package_root)
                
                # Check for hardcoded keys
                issues = check_file_for_hardcoded_keys(file_path)
                
                if issues:
                    print(f"\n❌ SECURITY ISSUE: {relative_path}")
                    for issue in issues:
                        print(f"   {issue}")
                    issues_found += len(issues)
                else:
                    # Check for secure usage patterns
                    secure_patterns = verify_secure_usage(file_path)
                    
                    if secure_patterns:
                        print(f"\n✅ SECURE: {relative_path}")
                        for pattern in secure_patterns:
                            print(f"   {pattern}")
                        secure_files += 1
                    else:
                        print(f"\n📄 CHECKED: {relative_path}")
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 SECURITY VERIFICATION SUMMARY")
    print("-" * 40)
    print(f"Total files checked: {total_files}")
    print(f"Secure files: {secure_files}")
    print(f"Security issues: {issues_found}")
    
    if issues_found == 0:
        print("\n🎉 SECURITY STATUS: ✅ SECURE")
        print("No hardcoded API keys found!")
    else:
        print(f"\n⚠️  SECURITY STATUS: ❌ ISSUES FOUND")
        print(f"Found {issues_found} security issues that need attention.")
    
    # Check .gitignore
    gitignore_path = package_root / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        
        if '.env' in gitignore_content:
            print("\n✅ .gitignore: .env files are protected")
        else:
            print("\n❌ .gitignore: .env files are NOT protected")
    else:
        print("\n⚠️  .gitignore: File not found")
    
    print("\n🔒 Remember: Never commit API keys to version control!")

if __name__ == "__main__":
    main()