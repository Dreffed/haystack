#!/usr/bin/env python3
"""
Simple test to verify the admin interface is accessible
"""

import os
import sys
import webbrowser
from pathlib import Path

def check_admin_interface():
    """Check if the admin interface files are in place"""
    print("🔍 Checking Haystack Database Admin Interface...")
    
    # Check HTML file
    html_path = Path("docker/frontend/index.html")
    if not html_path.exists():
        print("❌ Frontend HTML file not found!")
        return False
    
    # Check for admin section in HTML
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    if 'Database Admin' not in html_content:
        print("❌ Database Admin tab not found in HTML!")
        return False
    
    if 'id="admin"' not in html_content:
        print("❌ Admin section not found in HTML!")
        return False
    
    print("✅ HTML admin interface: Found")
    
    # Check JavaScript file
    js_path = Path("docker/frontend/js/app.js")
    if not js_path.exists():
        print("❌ JavaScript file not found!")
        return False
    
    with open(js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    if 'loadAdminInterface' not in js_content:
        print("❌ Admin JavaScript functions not found!")
        return False
    
    print("✅ JavaScript admin functions: Found")
    
    # Check backend API
    api_path = Path("docker/backend/main.py")
    if not api_path.exists():
        print("❌ Backend API file not found!")
        return False
    
    with open(api_path, 'r', encoding='utf-8') as f:
        api_content = f.read()
    
    if '/api/admin/tables' not in api_content:
        print("❌ Admin API endpoints not found!")
        return False
    
    print("✅ Backend admin API: Found")
    
    return True

def show_access_instructions():
    """Show instructions for accessing the admin interface"""
    print("\n" + "="*60)
    print("🎯 HOW TO ACCESS THE DATABASE ADMIN INTERFACE")
    print("="*60)
    
    print("\n1. 🚀 START THE APPLICATION:")
    print("   Using Docker (recommended):")
    print("   > docker-compose up -d")
    print("\n   OR manually:")
    print("   > python docker/backend/main.py  # (in one terminal)")
    print("   > cd docker/frontend && python -m http.server 80  # (in another terminal)")
    
    print("\n2. 🌐 OPEN YOUR WEB BROWSER:")
    print("   > Navigate to: http://localhost")
    
    print("\n3. 📋 FIND THE DATABASE ADMIN TAB:")
    print("   > Look for the navigation bar at the top")
    print("   > Click the rightmost tab: '🗄️ Database Admin'")
    
    print("\n4. 🗃️ YOU SHOULD SEE:")
    print("   > Left panel: List of database tables (Engines, Items, etc.)")
    print("   > Left panel: List of engine forms (craigslist, webScraper)")
    print("   > Main area: 'Select a table or engine' message")
    
    print("\n5. 🎯 TO BROWSE RECORDS:")
    print("   > Click any table name (e.g., 'Items')")
    print("   > View records in a data table")
    print("   > Use edit/delete buttons on each row")
    print("   > Search using the search box")
    
    print("\n6. ⚙️ TO CONFIGURE ENGINES:")
    print("   > Click any engine name (e.g., 'craigslist')")
    print("   > Fill out the configuration form")
    print("   > Click 'Save Configuration'")

def test_local_access():
    """Test if we can access the files locally"""
    print("\n🧪 Testing local file access...")
    
    try:
        # Try to open the HTML file directly
        html_path = Path("docker/frontend/index.html").resolve()
        if html_path.exists():
            print(f"✅ Can access HTML at: {html_path}")
            
            # Try to open in browser
            file_url = f"file://{html_path}"
            print(f"📄 Direct file URL: {file_url}")
            
            response = input("\n🌐 Open the admin interface in your browser now? (y/n): ")
            if response.lower() == 'y':
                webbrowser.open(file_url)
                print("🚀 Opening admin interface in your default browser...")
                print("🔍 Look for the 'Database Admin' tab in the navigation bar!")
        else:
            print("❌ Cannot access HTML file")
            
    except Exception as e:
        print(f"❌ Error testing local access: {e}")

def main():
    """Main test function"""
    print("Haystack Database Admin Interface - Access Test")
    print("="*55)
    
    # Change to the correct directory
    if not os.path.exists('docker/frontend/index.html'):
        print("❌ Please run this script from the Haystack root directory")
        print("   Current directory:", os.getcwd())
        print("   Expected structure: docker/frontend/index.html")
        return 1
    
    # Check if admin interface is properly installed
    if not check_admin_interface():
        print("\n❌ Admin interface is not properly installed!")
        return 1
    
    print("\n✅ Admin interface is properly installed!")
    
    # Show access instructions
    show_access_instructions()
    
    # Test local access
    test_local_access()
    
    print("\n" + "="*60)
    print("📞 STILL CAN'T FIND IT?")
    print("="*60)
    print("1. Make sure JavaScript is enabled in your browser")
    print("2. Try refreshing the page (Ctrl+F5 or Cmd+R)")
    print("3. Check browser console for errors (F12)")
    print("4. Ensure you're looking at the TOP navigation bar")
    print("5. The tab should say 'Database Admin' with a database icon")
    print("\nThe admin interface should be the RIGHTMOST tab in the navigation!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())