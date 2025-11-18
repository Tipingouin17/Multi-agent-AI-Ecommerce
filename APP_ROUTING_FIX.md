# App.jsx Routing Fix

## Problem
Multiple `<Routes>` blocks cause React Router conflicts and infinite loops.

## Solution
Consolidate into a single `<Routes>` block with conditional route rendering.

## Implementation

Replace lines 336-447 with:

```jsx
{/* Single Routes block for all routing */}
<Routes>
  {/* Public routes - always available */}
  <Route path="/login" element={<Login />} />
  <Route path="/register" element={<Register />} />
  
  {/* Admin routes */}
  {selectedInterface === 'admin' && (
    <>
      <Route path="/" element={<ProtectedRoute allowedRoles={['admin']}><AdminLayout onInterfaceReset={handleInterfaceReset} /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<ErrorBoundary><AdminDashboard /></ErrorBoundary>} />
        {/* ... all other admin routes ... */}
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </>
  )}
  
  {/* Merchant routes */}
  {selectedInterface === 'merchant' && (
    <>
      <Route path="/" element={<ProtectedRoute allowedRoles={['merchant']}><MerchantLayout onInterfaceReset={handleInterfaceReset} /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<ErrorBoundary><MerchantDashboard /></ErrorBoundary>} />
        {/* ... all other merchant routes ... */}
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </>
  )}
  
  {/* Customer routes */}
  {selectedInterface === 'customer' && (
    <>
      <Route path="/" element={<ProtectedRoute allowedRoles={['customer']}><CustomerLayout onInterfaceReset={handleInterfaceReset} /></ProtectedRoute>}>
        <Route index element={<Home />} />
        {/* ... all other customer routes ... */}
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </>
  )}
  
  {/* Default: redirect to login if no interface selected */}
  {!selectedInterface && (
    <Route path="*" element={<Navigate to="/login" replace />} />
  )}
</Routes>
```

## Key Changes
1. Single `<Routes>` block instead of 4 separate ones
2. Conditional rendering inside Routes using fragments (`<>`)
3. Catch-all routes only active when their interface is selected
4. Default catch-all redirects to login when no interface selected
