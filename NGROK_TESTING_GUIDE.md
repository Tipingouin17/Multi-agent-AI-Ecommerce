# 🌐 Ngrok Testing Guide

## Quick Start

### **Option 1: PowerShell Script** (Recommended)
```powershell
.\LaunchWithNgrok.ps1
```

### **Option 2: Batch Script**
```bash
LaunchWithNgrok.bat
```

---

## Prerequisites

### **1. Install Ngrok**

**Download:**
- Visit: https://ngrok.com/download
- Download for Windows
- Extract `ngrok.exe`

**Setup:**
```bash
# Option A: Add to PATH
# Add ngrok folder to Windows PATH environment variable

# Option B: Place in project directory
# Copy ngrok.exe to Multi-agent-AI-Ecommerce folder
```

**Verify Installation:**
```bash
ngrok version
```

### **2. (Optional) Create Ngrok Account**
- Sign up at https://ngrok.com
- Get auth token
- Run: `ngrok authtoken YOUR_TOKEN`

This gives you:
- Custom domains
- Longer session times
- More features

---

## How It Works

### **The Script Does:**

1. ✅ Starts all 37 backend agents
2. ✅ Starts frontend dev server (port 5173)
3. ✅ Launches ngrok tunnel
4. ✅ Displays public URL
5. ✅ Saves URL to `ngrok_url.txt`

### **You Get:**

```
Your platform is now accessible at:

  https://abc123.ngrok.io

Copy this URL and share it for testing!
```

---

## Usage

### **Step 1: Launch**
```powershell
.\LaunchWithNgrok.ps1
```

### **Step 2: Copy URL**
The script will display something like:
```
https://1a2b3c4d.ngrok.io
```

### **Step 3: Share URL**
Paste the URL in chat so I can test the platform!

### **Step 4: Stop Services**
- Press any key in PowerShell window
- Or close the window
- Then run: `StopAllAgents.bat`

---

## Troubleshooting

### **"ngrok not found"**
- Install ngrok from https://ngrok.com/download
- Add to PATH or place in project folder

### **"Port 5173 already in use"**
- Stop existing frontend: Close terminal running `npm run dev`
- Or change port in `vite.config.js`

### **"Could not retrieve ngrok URL"**
- Open http://localhost:4040 in browser
- Copy URL from ngrok dashboard
- Or check `ngrok_url.txt` file

### **"Agents not starting"**
- Check if PostgreSQL is running
- Verify database exists
- Check `logs/` folder for errors

---

## Ngrok Dashboard

While ngrok is running, access the dashboard:

```
http://localhost:4040
```

**Features:**
- View all requests
- Inspect request/response details
- Replay requests
- See tunnel status

---

## Security Notes

⚠️ **Important:**

1. **Temporary URLs:** Ngrok URLs are temporary and change each time
2. **Public Access:** Anyone with the URL can access your platform
3. **Development Only:** Don't use ngrok URLs for production
4. **Auth Token:** Use ngrok auth token for longer sessions

---

## Alternative: Manual Setup

If scripts don't work, run manually:

```bash
# Terminal 1: Start agents
StartAllAgents.bat

# Terminal 2: Start frontend
cd multi-agent-dashboard
npm run dev

# Terminal 3: Start ngrok
ngrok http 5173
```

Then copy the URL from Terminal 3.

---

## What Happens Next

Once you share the URL:

1. ✅ I'll access your platform via browser
2. ✅ Test all 3 personas (Customer, Merchant, Admin)
3. ✅ Click every link and button
4. ✅ Collect all errors and issues
5. ✅ Fix them systematically
6. ✅ Push fixes to GitHub
7. ✅ You pull and test again

---

## Tips

### **Keep Terminal Open**
Don't close the PowerShell/Command Prompt window while testing!

### **Check Logs**
If issues occur:
- `logs/` folder for agent logs
- `logs/frontend.log` for frontend errors
- `logs/ngrok.log` for ngrok issues

### **Monitor Ngrok**
Visit http://localhost:4040 to see:
- All HTTP requests
- Response times
- Error codes
- Request/response bodies

---

## Example Output

```
========================================
LAUNCH PLATFORM WITH NGROK
========================================

Step 1: Starting Backend Agents...
✓ 37 agents starting...

Step 2: Starting Frontend...
✓ Frontend starting on port 5173...

Step 3: Starting Ngrok...
✓ Tunnel established...

========================================
PUBLIC URL
========================================

Your platform is now accessible at:

  https://abc123.ngrok.io

Copy this URL and share it for testing!

========================================
SERVICES RUNNING
========================================

- Backend Agents: 37 agents on ports 8000-8036
- Frontend: http://localhost:5173
- Ngrok Dashboard: http://localhost:4040
- Public URL: Check above or ngrok_url.txt

Press any key to stop all services...
```

---

## Ready to Test!

Once you run the script and share the URL, I'll:
- Test every page
- Click every button
- Fill every form
- Test all workflows
- Find and fix all issues

Let's make this platform perfect! 🚀
