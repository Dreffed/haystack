#!/usr/bin/env python3
"""
Simple guide to find the Database Admin interface
"""

import os
import webbrowser
from pathlib import Path

def main():
    print("=" * 60)
    print("HAYSTACK DATABASE ADMIN INTERFACE - LOCATION GUIDE")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('docker/frontend/index.html'):
        print("ERROR: Please run this from the Haystack root directory")
        print("Current directory:", os.getcwd())
        return 1
    
    print("\nSTEPS TO ACCESS THE DATABASE ADMIN INTERFACE:")
    print("-" * 50)
    
    print("\n1. START THE APPLICATION:")
    print("   Option A (Docker): docker-compose up -d")
    print("   Option B (Manual): python docker/backend/main.py")
    
    print("\n2. OPEN YOUR BROWSER:")
    print("   Navigate to: http://localhost")
    print("   (or http://localhost:80)")
    
    print("\n3. LOOK FOR THE NAVIGATION BAR:")
    print("   At the TOP of the page, you should see tabs:")
    print("   - Dashboard")
    print("   - Engines") 
    print("   - Items")
    print("   - Status")
    print("   - Config")
    print("   - Database Admin  <-- CLICK THIS ONE!")
    
    print("\n4. THE DATABASE ADMIN TAB:")
    print("   - Should be the RIGHTMOST tab")
    print("   - Has a database icon")
    print("   - Says 'Database Admin'")
    
    print("\n5. WHAT YOU'LL SEE AFTER CLICKING:")
    print("   Left Panel:")
    print("   - Database Tables (Engines, Items, ItemData, etc.)")
    print("   - Engine Forms (craigslist, webScraper)")
    print("   ")
    print("   Main Area:")
    print("   - Message: 'Select a table or engine'")
    print("   - Click any table name to browse/edit records")
    print("   - Click any engine to configure it")
    
    print("\n" + "=" * 60)
    print("TROUBLESHOOTING:")
    print("=" * 60)
    
    print("\nIf you don't see the 'Database Admin' tab:")
    print("1. Make sure JavaScript is enabled")
    print("2. Refresh the page (Ctrl+F5)")
    print("3. Check if you're using the updated files")
    print("4. Look at the browser console (F12) for errors")
    
    print("\nIf the tab doesn't work:")
    print("1. Ensure backend API is running on port 8000")
    print("2. Test: http://localhost:8000/api/admin/tables")
    print("3. Check browser console for JavaScript errors")
    
    # Offer to open the interface
    html_path = Path("docker/frontend/index.html").resolve()
    print(f"\nHTML File Location: {html_path}")
    
    response = input("\nOpen the interface in your browser now? (y/n): ")
    if response.lower() == 'y':
        try:
            file_url = f"file://{html_path}"
            webbrowser.open(file_url)
            print("\nOpening interface in your browser...")
            print("NOTE: Database functions need the backend API running!")
            print("Look for 'Database Admin' in the top navigation bar!")
        except Exception as e:
            print(f"Error opening browser: {e}")
    
    print("\n" + "=" * 60)
    print("REMEMBER: The 'Database Admin' tab should be clearly visible")
    print("in the TOP navigation bar as the rightmost menu item!")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    main()