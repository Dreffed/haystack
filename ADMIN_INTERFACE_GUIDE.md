# 🗃️ Haystack Database Admin Interface - User Guide

## 🚀 How to Access the Database Admin Interface

### Step 1: Start the Application

**Option A: Using Docker (Recommended)**
```bash
cd D:\users\ms\git\Dreffed\haystack
docker-compose up -d
```

**Option B: Manual Start**
```bash
# Start the backend API
cd D:\users\ms\git\Dreffed\haystack
python docker/backend/main.py

# Serve the frontend (in another terminal)
cd D:\users\ms\git\Dreffed\haystack\docker\frontend
python -m http.server 80
```

### Step 2: Open the Web Interface

1. Open your web browser
2. Navigate to: `http://localhost` (or `http://localhost:80`)
3. You should see the Haystack Web Collector interface

### Step 3: Find the Database Admin Tab

Look at the **navigation bar** at the top of the page. You should see these tabs:
- 📊 Dashboard
- ⚙️ Engines  
- 🗃️ Items
- 📋 Status
- 🔧 Config
- **🗄️ Database Admin** ← Click this one!

### Step 4: Use the Database Admin Interface

Once you click "Database Admin", you'll see:

#### Left Panel - Database Tables:
- **Engines** - Scraping engines
- **Items** - Scraped items  
- **ItemData** - Item details
- **Actions** - Engine actions
- **Config** - System configuration
- **Status** - System messages

#### Left Panel - Engine Forms:
- **craigslist** - Craigslist scraper config
- **webScraper** - Generic web scraper config

#### Main Area:
- **Table browser** - View and edit records
- **Search functionality** - Find specific records
- **Pagination controls** - Navigate through data
- **Edit/Delete buttons** - Modify individual records

## 🔧 Troubleshooting

### "Database Admin tab is missing"
- Make sure you're using the updated `index.html` file
- Check that JavaScript is enabled in your browser
- Try refreshing the page (Ctrl+F5)

### "Database Admin tab doesn't work" 
- Check the browser console for JavaScript errors (F12)
- Ensure the backend API is running on port 8000
- Verify the database connection is working

### "No data appears in tables"
- Make sure the database is initialized and has data
- Check that the backend API endpoints are responding
- Look for error messages in the browser console

### "Cannot edit records"
- Ensure you have proper database permissions
- Check that the backend API is running
- Verify the database connection pooling is working

## 📊 What You Can Do

### Browse Database Tables:
1. Click on any table name (e.g., "Items")  
2. View all records in a paginated table
3. Use the search box to find specific records
4. Navigate with Previous/Next buttons

### Edit Records:
1. Click the **edit icon** (✏️) next to any record
2. Modify the values in the popup form
3. Click **"Save Changes"** to update the record
4. Click **"Delete"** to remove the record (with confirmation)

### Configure Engines:
1. Click on an engine name (e.g., "craigslist")
2. Fill in the configuration form
3. Add keyword arrays or CSS selectors as needed
4. Click **"Save Configuration"** or **"Save & Start Engine"**

### Search and Filter:
1. Use the search box in any table view
2. Search works across all relevant fields
3. Results update automatically as you type
4. Clear search to return to full table view

## 🎯 Key Features

- ✅ **Visual Database Browser** - No SQL knowledge required
- ✅ **Real-time Search** - Find records instantly  
- ✅ **Safe Editing** - Forms prevent invalid data
- ✅ **Bulk Operations** - Efficient data management
- ✅ **Engine Configuration** - Visual scraper setup
- ✅ **Responsive Design** - Works on mobile and desktop

## 📞 Need Help?

If you still cannot find or access the Database Admin interface:

1. **Check the browser console** (F12) for any JavaScript errors
2. **Verify the backend is running** by visiting `http://localhost:8000/health`
3. **Confirm the admin API** is working: `http://localhost:8000/api/admin/tables`
4. **Look for the navigation bar** - it should be at the very top of the page

The Database Admin tab should be clearly visible as the rightmost item in the navigation bar with a database icon (🗄️) and the text "Database Admin".