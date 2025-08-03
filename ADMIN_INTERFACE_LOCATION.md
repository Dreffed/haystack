# 🔍 Where to Find the Database Admin Interface

## 📍 **EXACT LOCATION:**

The Database Admin interface is located in the **top navigation bar** of the Haystack web interface.

### Navigation Bar Layout:
```
[🕷️ Haystack Web Collector]    [📊 Dashboard] [⚙️ Engines] [🗃️ Items] [📋 Status] [🔧 Config] [🗄️ Database Admin]
```

## 🎯 **STEP-BY-STEP INSTRUCTIONS:**

### 1. Start the Application
```bash
# Use Docker (recommended)
docker-compose up -d

# OR start manually
python docker/backend/main.py
```

### 2. Open Your Browser
- Navigate to: **http://localhost**
- The Haystack interface should load

### 3. Find the Navigation Bar
- Look at the **very top** of the page
- You should see a blue navigation bar with the Haystack logo
- There are several tabs in this navigation bar

### 4. Click "Database Admin"
- It's the **rightmost tab** in the navigation
- Has a database icon (🗄️) 
- Says "Database Admin"
- **This is what you're looking for!**

## 📋 **What You'll See After Clicking:**

### Left Panel - Two Sections:

**Database Tables:**
- Engines
- Items  
- ItemData
- Actions
- EngineActions
- ItemEvents
- ItemLinks
- LinkTypes
- Status
- Config

**Engine Forms:**
- craigslist
- webScraper

### Main Area:
- Initially shows: "Select a table or engine"
- Click any table name to browse/edit records
- Click any engine name to configure it

## 🛠️ **How to Browse/Edit Records:**

### To Browse Database Records:
1. Click any table name (e.g., "Items")
2. You'll see a data table with all records
3. Use the search box to find specific records
4. Navigate with Previous/Next buttons

### To Edit a Record:
1. Click the **edit icon** (✏️) next to any record
2. A popup form will appear
3. Modify the values
4. Click "Save Changes"

### To Delete a Record:
1. Click the **trash icon** (🗑️) next to any record
2. Confirm the deletion
3. Record will be removed from the database

## ❗ **TROUBLESHOOTING:**

### "I don't see the Database Admin tab"
- **Check:** Make sure you're looking at the TOP navigation bar
- **Try:** Refresh the page (Ctrl+F5 or Cmd+R)
- **Verify:** JavaScript is enabled in your browser
- **Look for:** The rightmost tab with a database icon

### "The tab is there but doesn't work"
- **Check:** Backend API is running on port 8000
- **Test:** Visit http://localhost:8000/api/admin/tables
- **Look at:** Browser console (F12) for JavaScript errors
- **Ensure:** Database connection is working

### "I see the tab but no data"
- **Verify:** Database is initialized and has data
- **Check:** Backend API endpoints are responding
- **Look for:** Error messages in browser console
- **Test:** Visit http://localhost:8000/health

## 🖼️ **Visual Reference:**

```
┌─────────────────────────────────────────────────────────────────┐
│ 🕷️ Haystack Web Collector  [Dashboard][Engines][Items][Status][Config][Database Admin] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────────────────────────────────┐   │
│  │ Database    │  │                                         │   │
│  │ Tables      │  │  Select a table or engine               │   │
│  │             │  │                                         │   │
│  │ • Engines   │  │  ← Click table names to browse records │   │
│  │ • Items     │  │                                         │   │
│  │ • ItemData  │  │  ← Click engine names to configure     │   │
│  │ • Actions   │  │                                         │   │
│  │ • Config    │  │                                         │   │
│  │             │  │                                         │   │
│  │ Engine      │  │                                         │   │
│  │ Forms       │  │                                         │   │
│  │             │  │                                         │   │
│  │ • craigslist│  │                                         │   │
│  │ • webScraper│  │                                         │   │
│  └─────────────┘  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 **KEY POINTS:**

1. **The Database Admin tab is in the TOP navigation bar**
2. **It's the RIGHTMOST tab with a database icon**
3. **Click table names on the left to browse/edit records**
4. **Use the edit/delete buttons on each record row**
5. **The interface works like a visual database browser**

The Database Admin interface should be **clearly visible** once you know where to look!