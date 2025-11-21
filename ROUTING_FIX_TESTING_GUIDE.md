# Routing Fix - Testing Guide

## Quick Start

1. **Pull the latest changes:**
   ```bash
   git pull origin main
   ```

2. **Restart your dev server:**
   ```bash
   npm run dev
   ```

3. **Open browser console** (F12) to monitor for errors

4. **Follow the test scenarios below**

---

## Test Scenarios

### ✅ Scenario 1: Initial Load

**Steps:**
1. Open http://localhost:5173
2. Should see interface selector page
3. Check console - should have NO errors

**Expected:**
- ✅ Interface selector loads
- ✅ No "No routes matched location '/'" error
- ✅ No infinite loop warnings
- ✅ Database status shows (connected/disconnected)

**If it fails:**
- Check if App.jsx was replaced correctly
- Verify no syntax errors in console
- Clear browser cache and try again

---

### ✅ Scenario 2: Admin Interface Navigation

**Steps:**
1. Click "Access System Administrator"
2. Should navigate to `/admin/dashboard`
3. Click through sidebar menu items
4. Wait 30 seconds (health check interval)
5. Navigate again

**Expected:**
- ✅ Smooth navigation to admin dashboard
- ✅ All admin routes work
- ✅ No remounting of entire app
- ✅ Health check doesn't disrupt navigation
- ✅ No "Maximum update depth" errors

**Routes to test:**
- `/admin/dashboard`
- `/admin/agents`
- `/admin/monitoring`
- `/admin/alerts`
- `/admin/analytics`
- `/admin/configuration`

---

### ✅ Scenario 3: Merchant Interface Navigation

**Steps:**
1. Return to interface selector (if available)
2. Or refresh and select "Merchant Portal"
3. Should navigate to `/merchant/dashboard`
4. Click through all menu sections
5. Test product wizard (Add Product button)

**Expected:**
- ✅ Smooth navigation to merchant dashboard
- ✅ All merchant routes work
- ✅ Product wizard opens without errors
- ✅ No route conflicts with admin
- ✅ No WebSocket disconnections

**Routes to test:**
- `/merchant/dashboard`
- `/merchant/products`
- `/merchant/orders`
- `/merchant/inventory`
- `/merchant/analytics`
- `/merchant/settings/general`

---

### ✅ Scenario 4: Customer Interface Navigation

**Steps:**
1. Select "Customer Experience"
2. Should navigate to `/customer`
3. Browse products
4. Add to cart
5. Navigate to account

**Expected:**
- ✅ Customer home page loads
- ✅ Product catalog works
- ✅ Shopping cart functions
- ✅ No route conflicts
- ✅ Smooth navigation

**Routes to test:**
- `/customer` (home)
- `/customer/products`
- `/customer/cart`
- `/customer/orders`
- `/customer/account`

---

### ✅ Scenario 5: Database Test Interface

**Steps:**
1. Select "Database Integration Test"
2. Should navigate to `/database-test`
3. Check database connection status
4. Run test queries

**Expected:**
- ✅ Database test page loads
- ✅ Connection status displays
- ✅ No routing errors
- ✅ Can return to interface selector

---

### ✅ Scenario 6: Direct URL Navigation

**Steps:**
1. Manually type URLs in address bar:
   - `http://localhost:5173/admin/dashboard`
   - `http://localhost:5173/merchant/products`
   - `http://localhost:5173/customer/cart`
   - `http://localhost:5173/invalid-route`

**Expected:**
- ✅ Valid routes load correctly
- ✅ Invalid routes redirect to appropriate page
- ✅ No "No routes matched" errors
- ✅ No infinite redirect loops

---

### ✅ Scenario 7: Browser Back/Forward

**Steps:**
1. Navigate through multiple pages
2. Click browser back button
3. Click browser forward button
4. Repeat several times

**Expected:**
- ✅ Back/forward work correctly
- ✅ No route stack overflow
- ✅ No duplicate history entries
- ✅ State preserved correctly

---

### ✅ Scenario 8: Health Check During Navigation

**Steps:**
1. Start navigating between pages
2. Wait for 30-second health check to trigger
3. Continue navigating immediately after
4. Check console for errors

**Expected:**
- ✅ Health check runs in background
- ✅ No navigation disruption
- ✅ No "Cannot update during render" warnings
- ✅ WebSocket stays connected

---

### ✅ Scenario 9: WebSocket Stability

**Steps:**
1. Open browser console
2. Navigate to admin dashboard
3. Watch WebSocket connection status
4. Wait 2-3 minutes
5. Navigate to different pages

**Expected:**
- ✅ WebSocket connects once
- ✅ No repeated 1006 errors
- ✅ Connection stays stable
- ✅ No reconnection loops

---

### ✅ Scenario 10: Page Refresh

**Steps:**
1. Navigate to any page (e.g., `/merchant/products`)
2. Press F5 to refresh
3. Check if page loads correctly
4. Check if interface selection is preserved

**Expected:**
- ✅ Page reloads correctly
- ✅ Interface selection preserved (localStorage)
- ✅ No redirect to login/selector
- ✅ State restored correctly

---

## Console Monitoring

### ✅ What You Should SEE

```
✅ [React Router] Route matched: /admin/dashboard
✅ [WebSocket] Connected
✅ [Health Check] Database: Connected (3/5 agents healthy)
```

### ❌ What You Should NOT See

```
❌ Warning: Maximum update depth exceeded
❌ Error: Too many calls to Location or History APIs
❌ Error: No routes matched location "/"
❌ Warning: Cannot update during an existing state transition
❌ WebSocket error: 1006 (Abnormal Closure)
❌ CORS error on health check
```

---

## Performance Checks

### Before Fix
- Routes remount on every interface change
- Health checks disrupt navigation
- Multiple re-renders per navigation
- WebSocket reconnects frequently

### After Fix
- Routes never remount (single stable tree)
- Health checks run in idle time
- Minimal re-renders
- WebSocket stays connected

**How to verify:**
1. Open React DevTools
2. Enable "Highlight updates"
3. Navigate between pages
4. Should see minimal flashing (only content changes, not entire app)

---

## Troubleshooting

### Issue: "No routes matched location '/'"

**Cause:** Old App.jsx still in use

**Fix:**
```bash
cd multi-agent-dashboard/src
cp App_FIXED.jsx App.jsx
npm run dev
```

---

### Issue: Still seeing infinite loops

**Cause:** Browser cache or old build

**Fix:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+F5)
3. Restart dev server
4. Try incognito mode

---

### Issue: WebSocket still disconnecting

**Cause:** Backend not running or CORS issue

**Fix:**
1. Check if backend is running on port 8015
2. Verify CORS settings in backend
3. Check network tab for failed requests

---

### Issue: Routes redirect to wrong place

**Cause:** localStorage has old interface selection

**Fix:**
```javascript
// In browser console:
localStorage.clear()
location.reload()
```

---

## Automated Testing (Optional)

If you want to add automated tests:

```javascript
// Example test with React Testing Library
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

test('root route resolves without errors', () => {
  render(
    <MemoryRouter initialEntries={['/']}>
      <App />
    </MemoryRouter>
  );
  
  // Should not throw "No routes matched" error
  expect(screen.getByText(/Multi-Agent E-commerce Platform/i)).toBeInTheDocument();
});

test('admin routes are always defined', () => {
  render(
    <MemoryRouter initialEntries={['/admin/dashboard']}>
      <App />
    </MemoryRouter>
  );
  
  // Should load admin dashboard
  expect(screen.getByText(/Admin Dashboard/i)).toBeInTheDocument();
});
```

---

## Success Criteria

Your routing fix is successful if:

- ✅ No console errors during navigation
- ✅ All routes load correctly
- ✅ No infinite loops or remounting
- ✅ WebSocket stays connected
- ✅ Health checks don't disrupt navigation
- ✅ Back/forward buttons work
- ✅ Direct URLs work
- ✅ Page refresh preserves state
- ✅ Performance is smooth

---

## Rollback Plan

If the fix causes issues:

1. **Restore backup:**
   ```bash
   cd multi-agent-dashboard/src
   cp App.jsx.backup_* App.jsx
   npm run dev
   ```

2. **Report issues:**
   - What route were you on?
   - What action triggered the error?
   - What error message appeared?
   - Screenshot of console

3. **Temporary workaround:**
   - Use only one interface at a time
   - Avoid rapid navigation
   - Refresh page if stuck

---

## Next Steps After Testing

Once all tests pass:

1. **Delete backup files:**
   ```bash
   rm multi-agent-dashboard/src/App.jsx.backup_*
   rm multi-agent-dashboard/src/App_FIXED.jsx
   ```

2. **Update documentation:**
   - Note any edge cases found
   - Document any workarounds needed

3. **Deploy to production:**
   - Test in staging first
   - Monitor error logs
   - Have rollback plan ready

---

**Document Version:** 1.0  
**Created:** Nov 21, 2025  
**Author:** Manus AI Agent  
**Status:** Ready for Testing
