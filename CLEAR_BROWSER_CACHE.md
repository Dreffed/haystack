# 🔄 Fix Browser Cache Issue - Database Admin Tab Missing

## The Problem:
You're seeing an old version of the HTML without the "Database Admin" tab because your browser cached the old file.

## 🚀 IMMEDIATE SOLUTIONS:

### Solution 1: Hard Refresh
**Windows/Linux:** Press `Ctrl + F5` or `Ctrl + Shift + R`
**Mac:** Press `Cmd + Shift + R`

### Solution 2: Clear Browser Cache
1. Open Developer Tools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Solution 3: Private/Incognito Mode
Open a new private/incognito window and try again

### Solution 4: Different Browser
Try Chrome, Firefox, or Edge to see which works

## 🔧 RESTART SERVICES:

### If using Docker:
```bash
cd D:\users\ms\git\Dreffed\haystack
docker-compose down
docker-compose up -d --force-recreate
```

### If running manually:
1. Stop any running servers (Ctrl+C)
2. Restart the backend: `python docker/backend/main.py`
3. Restart the frontend: `cd docker/frontend && python -m http.server 80`

## ✅ WHAT YOU SHOULD SEE AFTER FIXING:

The navigation bar should show:
```
[Dashboard] [Engines] [Items] [Status] [Config] [Database Admin] ← This should appear!
```

## 🧪 TEST THE FIX:

1. Open browser to http://localhost
2. Look for "Database Admin" tab (rightmost)
3. Click it to see the admin interface
4. You should see database tables on the left panel

Try the hard refresh first - that usually fixes it!