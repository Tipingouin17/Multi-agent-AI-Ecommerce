# Dashboard Fix Guide

## Issue Summary

The React dashboard was experiencing import resolution errors for `@/lib/api` even though the file exists and the path alias is properly configured in `vite.config.js`.

## Root Cause

The Vite development server was started before the path alias configuration was properly recognized, or there was a caching issue preventing the module resolution from working correctly.

## Solution

### Step 1: Clean Installation

```powershell
# Navigate to dashboard directory
cd multi-agent-dashboard

# Remove node_modules and package-lock.json
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item package-lock.json -ErrorAction SilentlyContinue

# Clear npm cache
npm cache clean --force

# Reinstall dependencies
npm install
```

### Step 2: Verify Configuration

The `vite.config.js` should have the following path alias configuration:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
```

### Step 3: Start Development Server

```powershell
# Start the dashboard
npm run dev
```

The dashboard should now start successfully on `http://localhost:5173`

## Additional Troubleshooting

### If Import Errors Persist

1. **Check Node.js Version**: Ensure you're using Node.js v18, v20, or v22+
   ```powershell
   node --version
   ```

2. **Clear Vite Cache**:
   ```powershell
   Remove-Item -Recurse -Force .vite -ErrorAction SilentlyContinue
   npm run dev
   ```

3. **Verify File Structure**:
   ```
   multi-agent-dashboard/
   ├── src/
   │   ├── lib/
   │   │   ├── api.js          ✓ Must exist
   │   │   └── utils.js
   │   ├── pages/
   │   ├── components/
   │   └── App.jsx
   ├── vite.config.js          ✓ Must have @ alias
   └── package.json
   ```

4. **Check Import Syntax**: Ensure all imports use the correct syntax:
   ```javascript
   import { apiService } from "@/lib/api"  // Correct
   ```

### Common Errors and Solutions

| Error | Solution |
|-------|----------|
| `Failed to resolve import "@/lib/api"` | Clean install and restart Vite server |
| `EBADENGINE Unsupported engine` | Update to Node.js v18+ or v22+ |
| `Module not found: axios` | Run `npm install` to install dependencies |
| Blank page after startup | Check browser console for errors, verify API endpoints |

## Verification Steps

After starting the dashboard:

1. **Check Console**: No import errors should appear
2. **Access Dashboard**: Navigate to `http://localhost:5173`
3. **Test API Calls**: Verify that API service is making requests to agent endpoints
4. **Check Network Tab**: Ensure requests are being sent to correct ports (8001-8014)

## Integration with Backend Agents

The dashboard connects to 14 backend agents on the following ports:

| Agent | Port |
|-------|------|
| Order Agent | 8001 |
| Product Agent | 8002 |
| Inventory Agent | 8003 |
| Warehouse Selection Agent | 8004 |
| Carrier Selection Agent | 8005 |
| Demand Forecasting Agent | 8006 |
| Dynamic Pricing Agent | 8007 |
| Customer Communication Agent | 8008 |
| Reverse Logistics Agent | 8009 |
| Risk & Anomaly Detection Agent | 8010 |
| Standard Marketplace Agent | 8011 |
| Refurbished Marketplace Agent | 8012 |
| D2C Marketplace Agent | 8013 |
| AI Monitoring Agent | 8014 |

Ensure all agents are running before testing dashboard functionality.

## Next Steps

1. Start all Docker services: `docker-compose up -d`
2. Wait for Kafka to be ready
3. Start all agents: `.\start-system.ps1`
4. Start dashboard: `cd multi-agent-dashboard && npm run dev`
5. Access dashboard at `http://localhost:5173`

