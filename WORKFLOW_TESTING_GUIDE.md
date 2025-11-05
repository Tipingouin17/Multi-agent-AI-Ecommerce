# 🎯 Complete Workflow Testing Guide

**Purpose:** Step-by-step guide to complete all remaining workflow testing  
**Status:** Code complete, browser verification pending  
**Estimated Time:** 3-5 hours  

---

## Prerequisites

### 1. Start Development Server
```bash
cd /home/ubuntu/Multi-agent-AI-Ecommerce/multi-agent-dashboard
npm run dev
```
**Expected:** Server running on http://localhost:5173

### 2. Start Backend Agents (Optional - for full functionality)
```bash
cd /home/ubuntu/Multi-agent-AI-Ecommerce/agents
python3 product_agent_v3.py &          # Port 8003
python3 marketplace_connector_v3.py &  # Port 8007
```

### 3. Open Browser
Navigate to http://localhost:5173

---

## Phase 1: Verify Inventory Fix (15 minutes) ⭐ CRITICAL

### Test Case: Add Product with Inventory

**Objective:** Verify the inventory fields are visible and functional

**Steps:**
1. Navigate to http://localhost:5173/products
2. Click "Add Product" button
3. **VERIFY:** Modal opens with the following sections:
   - Product Name (text input)
   - SKU (text input)
   - Price (number input with $)
   - Cost (number input with $)
   - Category (dropdown)
   - Description (textarea)
   - **Inventory Section** (NEW - this is what we fixed!)
     - Initial Quantity (number input)
     - Warehouse Location (text input)
     - Reorder Level (number input)
     - Enable low stock alerts (checkbox)
   - Images (upload area)

4. Fill in the form:
   ```
   Product Name: Test Wireless Mouse
   SKU: TWM-001
   Price: 29.99
   Cost: 15.00
   Category: Electronics
   Description: High-quality wireless mouse with ergonomic design
   
   Inventory:
   - Initial Quantity: 100
   - Warehouse Location: Main Warehouse
   - Reorder Level: 20
   - Low Stock Alerts: ✓ (checked)
   ```

5. Click "Add Product"

6. **VERIFY:** 
   - No errors displayed
   - Modal closes
   - Product appears in product list
   - Success message shown

**Expected Result:** ✅ PASS - Inventory fields visible and functional

**If FAIL:** Check browser console for errors, review ProductManagement.jsx code

---

## Phase 2: Merchant Workflows (1-2 hours)

### Workflow 2.2: Process Order (30 minutes)

**Persona:** Marc Dubois (Merchant)  
**Objective:** Process a customer order from pending to fulfilled

**Steps:**
1. Navigate to http://localhost:5173/orders
2. **VERIFY:** Orders page loads with order list
3. Click on an order (or create a test order if none exist)
4. **VERIFY:** Order details page loads with:
   - Order number and date
   - Customer information
   - Order items list
   - Order total
   - Current status
   - Action buttons

5. Update order status:
   - Click "Mark as Processing" (if available)
   - **VERIFY:** Status updates to "Processing"

6. Add tracking information:
   - Enter tracking number: "TRACK123456"
   - Select carrier: "UPS"
   - Click "Save Tracking"
   - **VERIFY:** Tracking info saved

7. Mark as fulfilled:
   - Click "Mark as Fulfilled"
   - **VERIFY:** Status updates to "Fulfilled"
   - **VERIFY:** Customer notification sent (if implemented)

8. Verify order timeline:
   - **VERIFY:** Timeline shows all status changes with timestamps

**Expected Result:** ✅ PASS - Order processing workflow complete

**Success Criteria:**
- ✅ Can view order details
- ✅ Can update order status
- ✅ Can add tracking information
- ✅ Timeline updates correctly

---

### Workflow 2.3: Manage Inventory (30 minutes)

**Persona:** Marc Dubois (Merchant)  
**Objective:** Monitor and update inventory levels

**Steps:**
1. Navigate to http://localhost:5173/inventory
2. **VERIFY:** Inventory page loads with product list showing:
   - Product name
   - SKU
   - Current quantity
   - Warehouse location
   - Status (In Stock / Low Stock / Out of Stock)

3. Filter by low stock:
   - Select "Low Stock" from status filter
   - **VERIFY:** Only low stock items shown

4. Update stock quantity:
   - Click on a product
   - Update quantity (e.g., from 5 to 50)
   - Click "Save"
   - **VERIFY:** Quantity updates
   - **VERIFY:** Status changes from "Low Stock" to "In Stock"

5. Check inventory alerts:
   - Navigate to http://localhost:5173/inventory/alerts
   - **VERIFY:** Alerts page loads
   - **VERIFY:** Low stock alerts visible (if any)
   - **VERIFY:** Can acknowledge/dismiss alerts

6. View inventory analytics:
   - Check inventory turnover metrics
   - **VERIFY:** Data displays correctly

**Expected Result:** ✅ PASS - Inventory management workflow complete

**Success Criteria:**
- ✅ Can view inventory levels
- ✅ Can update stock quantities
- ✅ Can filter by status
- ✅ Alerts system works
- ✅ Status updates automatically

---

### Workflow 2.4: View Analytics (30 minutes)

**Persona:** Marc Dubois (Merchant)  
**Objective:** Review sales and performance metrics

**Steps:**
1. Navigate to http://localhost:5173/analytics
2. **VERIFY:** Analytics dashboard loads with:
   - Time period selector (7 Days, 30 Days, 90 Days, etc.)
   - Key metrics cards (Sales, Orders, AOV, Conversion Rate)
   - Charts and graphs

3. Change time period:
   - Select "Last 30 Days"
   - **VERIFY:** Data updates for new period
   - **VERIFY:** Charts refresh

4. View product analytics:
   - Navigate to http://localhost:5173/products/analytics
   - **VERIFY:** Product performance data loads
   - **VERIFY:** Top products list visible
   - **VERIFY:** Revenue by product chart displays

5. View order analytics:
   - Navigate to http://localhost:5173/orders/analytics
   - **VERIFY:** Order metrics load
   - **VERIFY:** Order volume chart displays
   - **VERIFY:** Average order value trend shows

6. Export data:
   - Click "Export" button
   - Select format (CSV or PDF)
   - **VERIFY:** File downloads

**Expected Result:** ✅ PASS - Analytics viewing workflow complete

**Success Criteria:**
- ✅ Can view sales metrics
- ✅ Can change time periods
- ✅ Charts display correctly
- ✅ Can export data
- ✅ Product and order analytics accessible

---

## Phase 3: Customer Workflows (1-2 hours)

### Workflow 3.1: Browse and Search Products (20 minutes)

**Persona:** Claire Martin (Customer)  
**Objective:** Find products using browse and search

**Steps:**
1. Switch to customer interface:
   - Click "Switch Interface" at bottom of page
   - Select "Access Customer Experience"

2. Browse product catalog:
   - Navigate to http://localhost:5173/products
   - **VERIFY:** Product catalog loads with grid view
   - **VERIFY:** Products display with images, names, prices

3. Use category filter:
   - Click "Electronics" category
   - **VERIFY:** Only electronics products shown
   - **VERIFY:** Product count updates

4. Use search:
   - Enter "wireless" in search bar
   - Press Enter
   - **VERIFY:** Search results page loads
   - **VERIFY:** Only matching products shown
   - **VERIFY:** Search term highlighted

5. Sort products:
   - Select "Price: Low to High" from sort dropdown
   - **VERIFY:** Products reorder by price ascending

6. View product details:
   - Click on a product
   - **VERIFY:** Product details page loads with:
     - Product images
     - Description
     - Price
     - Stock status
     - Add to Cart button
     - Reviews (if any)

**Expected Result:** ✅ PASS - Browse and search workflow complete

**Success Criteria:**
- ✅ Can browse product catalog
- ✅ Can filter by category
- ✅ Can search products
- ✅ Can sort results
- ✅ Can view product details

---

### Workflow 3.2: Purchase Product (40 minutes) ⭐ CRITICAL

**Persona:** Claire Martin (Customer)  
**Objective:** Complete full purchase flow from cart to order confirmation

**Steps:**

#### Part 1: Add to Cart
1. From product details page:
   - Select quantity: 2
   - Click "Add to Cart"
   - **VERIFY:** Success message shown
   - **VERIFY:** Cart badge updates (shows "2")

2. View cart:
   - Click cart icon in navigation
   - **VERIFY:** Cart page loads
   - **VERIFY:** Product shown with correct quantity and price
   - **VERIFY:** Subtotal calculated correctly

3. Update cart:
   - Change quantity to 3
   - **VERIFY:** Total updates
   - Click "Remove" on an item
   - **VERIFY:** Item removed from cart

#### Part 2: Checkout
4. Proceed to checkout:
   - Click "Proceed to Checkout"
   - **VERIFY:** Checkout page loads

5. Enter shipping address:
   ```
   Full Name: Claire Martin
   Email: claire.martin@email.com
   Phone: +33 6 12 34 56 78
   Address: 123 Rue de la Paix
   City: Paris
   Postal Code: 75001
   Country: France
   ```
   - Click "Continue to Delivery"
   - **VERIFY:** Moves to delivery step

6. Select delivery method:
   - Select "Standard Delivery (3-5 days)"
   - **VERIFY:** Shipping cost added to total
   - Click "Continue to Payment"
   - **VERIFY:** Moves to payment step

7. Enter payment information:
   - Select payment method: "Credit Card"
   - Enter card details (test data):
     ```
     Card Number: 4242 4242 4242 4242
     Expiry: 12/25
     CVV: 123
     ```
   - Click "Place Order"
   - **VERIFY:** Processing indicator shows

#### Part 3: Order Confirmation
8. View order confirmation:
   - **VERIFY:** Order confirmation page loads
   - **VERIFY:** Order number displayed
   - **VERIFY:** Order summary shown
   - **VERIFY:** Estimated delivery date shown
   - **VERIFY:** "Track Order" button available

9. Check email (if email system implemented):
   - **VERIFY:** Order confirmation email received

**Expected Result:** ✅ PASS - Complete purchase workflow successful

**Success Criteria:**
- ✅ Can add products to cart
- ✅ Can update cart quantities
- ✅ Can proceed to checkout
- ✅ Can enter shipping address
- ✅ Can select delivery method
- ✅ Can enter payment information
- ✅ Can place order
- ✅ Order confirmation displayed
- ✅ Order number generated

---

### Workflow 3.3: Track Order (20 minutes)

**Persona:** Claire Martin (Customer)  
**Objective:** Track order status and delivery

**Steps:**
1. Navigate to orders:
   - Click "Orders" in navigation
   - **VERIFY:** Orders page loads
   - **VERIFY:** Recent order appears in list

2. View order details:
   - Click on the order
   - **VERIFY:** Order details page loads with:
     - Order number and date
     - Order status
     - Items ordered
     - Shipping address
     - Payment method
     - Order total

3. Check order status:
   - **VERIFY:** Current status displayed (e.g., "Processing")
   - **VERIFY:** Status timeline visible showing:
     - Order Placed (✓)
     - Processing (current)
     - Shipped (pending)
     - Delivered (pending)

4. View tracking information:
   - **VERIFY:** Tracking number displayed (if shipped)
   - **VERIFY:** Carrier information shown
   - **VERIFY:** "Track Package" link available

5. Download invoice:
   - Click "Download Invoice"
   - **VERIFY:** PDF invoice downloads

6. Contact support (if needed):
   - Click "Contact Support"
   - **VERIFY:** Support form or contact info displayed

**Expected Result:** ✅ PASS - Order tracking workflow complete

**Success Criteria:**
- ✅ Can view order history
- ✅ Can view order details
- ✅ Status timeline displays correctly
- ✅ Tracking information accessible
- ✅ Can download invoice
- ✅ Support contact available

---

### Workflow 3.4: Manage Account (20 minutes)

**Persona:** Claire Martin (Customer)  
**Objective:** Update account information and preferences

**Steps:**

#### Part 1: Profile Settings
1. Navigate to account:
   - Click "Account" in navigation
   - **VERIFY:** Account page loads

2. Update profile:
   - Click "Settings" tab
   - Update information:
     ```
     First Name: Claire
     Last Name: Martin-Dubois
     Email: claire.martin.new@email.com
     Phone: +33 6 98 76 54 32
     ```
   - Click "Save Changes"
   - **VERIFY:** Success message shown
   - **VERIFY:** Changes persist after page refresh

#### Part 2: Address Management
3. Manage addresses:
   - Click "Addresses" tab
   - Click "Add New Address"
   - Enter address:
     ```
     Label: Work Address
     Address: 456 Avenue des Champs-Élysées
     City: Paris
     Postal Code: 75008
     Country: France
     ```
   - Check "Set as default shipping address"
   - Click "Save Address"
   - **VERIFY:** Address added to list
   - **VERIFY:** Marked as default

4. Edit address:
   - Click "Edit" on an address
   - Change postal code to 75009
   - Click "Save"
   - **VERIFY:** Address updated

5. Delete address:
   - Click "Delete" on an address
   - Confirm deletion
   - **VERIFY:** Address removed from list

#### Part 3: Preferences
6. Update preferences:
   - Click "Preferences" tab (if available)
   - Update email notifications:
     - ✓ Order updates
     - ✓ Promotions
     - ✗ Newsletter
   - Select language: English
   - Select currency: EUR
   - Click "Save Preferences"
   - **VERIFY:** Preferences saved

#### Part 4: Security
7. Change password:
   - Click "Security" tab
   - Enter current password
   - Enter new password
   - Confirm new password
   - Click "Update Password"
   - **VERIFY:** Password updated
   - **VERIFY:** Can login with new password

**Expected Result:** ✅ PASS - Account management workflow complete

**Success Criteria:**
- ✅ Can update profile information
- ✅ Can add/edit/delete addresses
- ✅ Can set default address
- ✅ Can update preferences
- ✅ Can change password
- ✅ Changes persist correctly

---

## Testing Checklist

### Phase 1: Inventory Fix Verification
- [ ] Inventory section visible in Add Product modal
- [ ] All 4 inventory fields present and functional
- [ ] Form submission works with inventory data
- [ ] Data persists to database

### Phase 2: Merchant Workflows
- [ ] Workflow 2.2: Process Order - COMPLETE
- [ ] Workflow 2.3: Manage Inventory - COMPLETE
- [ ] Workflow 2.4: View Analytics - COMPLETE

### Phase 3: Customer Workflows
- [ ] Workflow 3.1: Browse and Search - COMPLETE
- [ ] Workflow 3.2: Purchase Product - COMPLETE
- [ ] Workflow 3.3: Track Order - COMPLETE
- [ ] Workflow 3.4: Manage Account - COMPLETE

---

## Issue Reporting Template

If you encounter issues during testing, document them using this template:

```markdown
### Issue #X: [Brief Description]

**Workflow:** [Workflow number and name]
**Step:** [Step number where issue occurred]
**Severity:** [Critical / High / Medium / Low]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Screenshots/Errors:**
[Attach screenshots or paste error messages]

**Browser Console Errors:**
[Paste any JavaScript errors from browser console]

**Suggested Fix:**
[If known, suggest how to fix]
```

---

## Success Criteria

### Overall Success
- ✅ All 8 workflows complete without critical errors
- ✅ Inventory fix verified working
- ✅ All user journeys functional end-to-end
- ✅ No blank screens or crashes
- ✅ Error messages clear and helpful

### Production Readiness
After completing all workflows:
- **100% route coverage** ✅ (Already achieved)
- **100% workflow coverage** ⏳ (Pending completion)
- **Production deployment ready** ✅ (After workflow testing)

---

## Next Steps After Testing

1. **Document Results**
   - Fill in the testing checklist
   - Document any issues found
   - Create summary report

2. **Fix Any Issues**
   - Prioritize by severity
   - Fix critical issues immediately
   - Schedule medium/low issues for future sprints

3. **Deploy to Staging**
   - Deploy to staging environment
   - Run smoke tests
   - Get QA team sign-off

4. **Production Deployment**
   - Deploy to production
   - Monitor for errors
   - Celebrate! 🎉

---

## Support

If you need help during testing:
- Check browser console for errors
- Review code in ProductManagement.jsx
- Check backend agent logs
- Refer to COMPREHENSIVE_HANDOFF_REPORT.md for technical details

---

**Good luck with testing! You're almost at 100% production readiness! 🚀**
