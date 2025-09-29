#!/usr/bin/env python
"""
CSP Browser Testing Script
Opens your blog in a browser and checks for CSP violations
"""

import webbrowser
import time
import os
import sys

def open_test_pages():
    """Open all important pages in browser for manual CSP testing"""
    
    base_url = "http://127.0.0.1:8000"
    
    test_pages = [
        ("Home Page", f"{base_url}/"),
        ("Login Page", f"{base_url}/accounts/login/"),
        ("Signup Page", f"{base_url}/accounts/signup/"),
        ("Blog List", f"{base_url}/blog/"),
        ("Create Post", f"{base_url}/blog/create/"),
        ("Settings", f"{base_url}/accounts/settings/"),
    ]
    
    print("🌐 CSP Browser Testing Script")
    print("="*50)
    print("This script will open your blog pages in the browser.")
    print("Please check the browser console (F12) for CSP violations.")
    print()
    print("Instructions:")
    print("1. Open browser Developer Tools (F12)")
    print("2. Go to Console tab")
    print("3. Look for CSP violation messages")
    print("4. Check if all icons and features work")
    print()
    
    input("Press Enter to start opening pages...")
    
    for page_name, url in test_pages:
        print(f"Opening: {page_name}")
        webbrowser.open(url)
        time.sleep(2)  # Wait between page opens
    
    print("\n✅ All pages opened!")
    print("\nChecklist:")
    print("□ All pages load without errors")
    print("□ Font Awesome icons display correctly")
    print("□ TinyMCE editor works (on create/edit post pages)")
    print("□ No CSP violations in console")
    print("□ All navigation works")
    print("□ Forms submit correctly")
    
    print("\nIf you see CSP violations, note them and we can fix the CSP configuration.")

if __name__ == '__main__':
    open_test_pages()
