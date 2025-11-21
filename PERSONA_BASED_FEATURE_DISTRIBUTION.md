# Persona-Based Feature Distribution Plan

## Executive Summary

Our platform has a **multi-persona architecture** with three distinct portals serving different user roles. Features must be implemented in the correct portal based on user permissions and responsibilities.

**Current Architecture:**
- **Admin Portal** (`/pages/admin/`) - Platform-wide configuration and management
- **Merchant Portal** (`/pages/merchant/`) - Merchant-specific operations  
- **Customer Portal** (`/pages/customer/`) - Customer-facing features

**Key Principle:** Configuration and system-wide management belongs to Admin. Day-to-day operations belong to Merchant. Shopping and orders belong to Customer.

---

## Current Implementation Analysis

### Products Management

**Current Location:** Merchant Portal (`/pages/merchant/ProductManagement.jsx`)
**Route:** `/products` (Merchant portal)
**Status:** ✅ Correctly placed - Merchants manage their own products

**Existing Files:**
- `ProductManagement.jsx` - Main product list page
- `ProductForm.jsx` - Add/edit product form
- `BulkProductUpload.jsx` - Bulk upload functionality
- `ProductAnalytics.jsx` - Product analytics

### Inventory Management

**Current Location:** Merchant Portal (`/pages/merchant/InventoryManagement.jsx`)
**Route:** `/inventory` (Merchant portal)
**Status:** ✅ Correctly placed - Merchants manage their inventory levels

**Existing Files:**
- `InventoryManagement.jsx` - Main inventory page
- `InventoryAlerts.jsx` - Low stock alerts
- `InventoryDashboard.jsx` - Inventory analytics

### Warehouse Management

**Current Location:** Admin Portal (`/pages/admin/`)
**Existing Files:**
- `WarehouseConfiguration.jsx` - Warehouse setup and configuration
- `WarehouseCapacityManagement.jsx` - Capacity planning

**Status:** ✅ Correctly placed - Admins configure warehouses that merchants use

### Marketplace Integration

**Current Location:** Both portals
- Admin: `MarketplaceIntegration.jsx` - Platform-level marketplace connections
- Merchant: `MarketplaceIntegration.jsx` - Merchant-specific marketplace listings

**Status:** ⚠️ Needs clarification on separation of concerns

---

## Persona-Based Feature Distribution

### ADMIN PORTAL - Platform Configuration

**Responsibility:** Configure system-wide settings that merchants will use

#### Warehouse Features (Admin Only)

**Page:** `/pages/admin/WarehouseConfiguration.jsx`

**Features to Implement:**
1. ✅ **Add/Edit/Delete Warehouses**
   - Create new warehouse locations
   - Configure warehouse details (name, address, contact)
   - Set warehouse capacity limits
   - Assign warehouse managers/staff
   - Enable/disable warehouses

2. ✅ **Warehouse Capacity Management**
   - Set maximum capacity per warehouse
   - Define capacity thresholds (Low: >85%, Medium: 70-85%, High: <70%)
   - Configure storage zones and bin locations
   - Set utilization targets (e.g., 70-85% optimal)

3. ✅ **Staff Management**
   - Assign staff to warehouses
   - Set staff roles and permissions
   - Track staff schedules and shifts

4. ✅ **Automation Configuration**
   - Set automation level (manual/semi-automated/automated)
   - Configure warehouse management systems (WMS)
   - Integration with robotics and automation tools

5. ✅ **Warehouse Metrics Dashboard**
   - Total warehouses in system
   - Total storage capacity across all warehouses
   - System-wide utilization metrics
   - Warehouse performance comparisons

**NOT in Admin:**
- ❌ Product stock levels (this is merchant-specific)
- ❌ Individual product inventory (merchant manages this)
- ❌ Merchant-specific warehouse allocation

#### Marketplace Configuration (Admin Only)

**Page:** `/pages/admin/MarketplaceIntegration.jsx`

**Features to Implement:**
1. ✅ **Add/Remove Marketplace Integrations**
   - Connect new marketplaces (Amazon, eBay, Walmart, etc.)
   - Configure API credentials and webhooks
   - Set up marketplace-specific settings
   - Enable/disable marketplace integrations

2. ✅ **Marketplace Fee Configuration**
   - Set commission rates per marketplace
   - Configure transaction fees
   - Define pricing rules

3. ✅ **Compliance and Regulations**
   - Configure marketplace-specific requirements
   - Set up tax and legal compliance rules
   - Manage marketplace policies

**NOT in Admin:**
- ❌ Publishing products to marketplaces (merchant does this)
- ❌ Managing marketplace listings (merchant-specific)
- ❌ Marketplace orders (merchant manages their orders)

#### Channel Configuration (Admin Only)

**Page:** `/pages/admin/ChannelConfiguration.jsx`

**Features:**
- Configure sales channels (online store, POS, mobile app)
- Set channel-specific settings
- Manage channel integrations

#### Carrier Configuration (Admin Only)

**Page:** `/pages/admin/CarrierConfiguration.jsx`

**Features:**
- Add/remove shipping carriers
- Configure carrier API integrations
- Set up shipping rate tables
- Manage carrier contracts

---

### MERCHANT PORTAL - Day-to-Day Operations

**Responsibility:** Manage products, inventory, orders, and marketplace listings

#### Products Management (Merchant)

**Page:** `/pages/merchant/ProductManagement.jsx`

**Features to Implement:**
1. ✅ **Product CRUD Operations**
   - Create new products
   - Edit existing products
   - Delete/archive products
   - Bulk product operations

2. ✅ **Product Catalog Management**
   - Product descriptions (two-line display in list)
   - Product images and media
   - Product categories and tags
   - Product variations and bundles
   - SKU management with auto-generation

3. ✅ **Product Metrics Dashboard**
   - Total Products count
   - Low Stock Items (products below threshold)
   - Active Products (% active with progress bar)
   - Marketplace Connected (% of products published)

4. ✅ **Bulk Operations**
   - Bulk select products (checkboxes)
   - Bulk activate/deactivate
   - Bulk price updates
   - Bulk marketplace publishing
   - Bulk delete/archive

5. ✅ **Enhanced Product Fields**
   - Product Name
   - Display Name (optional)
   - Description (shown in list view)
   - SKU (with auto-generate button)
   - Brand
   - Model Number
   - Category
   - Price
   - Cost
   - Stock levels

6. ✅ **Product Creation Wizard** (8 steps)
   - Step 1: Basic Information
   - Step 2: Specifications
   - Step 3: Visual Assets
   - Step 4: Pricing & Costs
   - Step 5: Inventory & Logistics
   - Step 6: Bundle & Kit Config
   - Step 7: Marketplace & Compliance
   - Step 8: Review & Activation

**NOT in Merchant:**
- ❌ Creating new warehouses (admin configures these)
- ❌ Adding new marketplaces (admin configures these)
- ❌ System-wide warehouse metrics (admin views these)

#### Inventory Management (Merchant)

**Page:** `/pages/merchant/InventoryManagement.jsx`

**Features to Implement:**
1. ✅ **Stock Level Management**
   - View stock levels per product per warehouse
   - Update stock quantities
   - Set low stock thresholds per product
   - Receive low stock alerts

2. ✅ **Multi-Warehouse Inventory**
   - View inventory across all warehouses (read-only list)
   - Allocate stock to specific warehouses
   - Transfer stock between warehouses
   - View warehouse utilization (read-only)

3. ✅ **Inventory Metrics**
   - Total inventory value
   - Low stock items count
   - Out of stock items
   - Inventory turnover rate

4. ✅ **Replenishment**
   - Automatic reorder point calculations
   - Purchase order suggestions
   - Supplier integration for restocking

**Warehouse Information (Read-Only for Merchant):**
- View warehouse names and locations
- View warehouse capacity status
- View current utilization
- **Cannot** add/edit/delete warehouses
- **Cannot** configure warehouse settings

#### Marketplace Listings (Merchant)

**Page:** `/pages/merchant/MarketplaceIntegration.jsx`

**Features to Implement:**
1. ✅ **Publish Products to Marketplaces**
   - Select products to publish
   - Choose target marketplaces (from admin-configured list)
   - Map product attributes to marketplace requirements
   - Set marketplace-specific pricing

2. ✅ **Manage Marketplace Listings**
   - View all marketplace listings
   - Update listing details
   - Sync inventory across marketplaces
   - Handle marketplace orders

3. ✅ **Marketplace Coverage Metrics**
   - % of products published to marketplaces
   - Marketplace-specific performance
   - Listing health status

**Available Marketplaces (Read-Only):**
- View marketplaces configured by admin
- **Cannot** add new marketplace integrations
- **Cannot** configure marketplace API settings

---

### CUSTOMER PORTAL - Shopping Experience

**Responsibility:** Browse products, place orders, track deliveries

#### Product Browsing (Customer)

**Page:** `/pages/customer/ProductCatalog.jsx`

**Features:**
- Browse product catalog
- Search and filter products
- View product details
- Add to cart
- View product reviews

**NOT in Customer:**
- ❌ Product management (merchant only)
- ❌ Inventory management (merchant only)
- ❌ Warehouse information (internal only)

---

## Implementation Priority by Persona

### Phase 1: Merchant Portal Enhancements (High Priority)

**Why First:** Merchants are the primary users who need these features daily

**Products Page (`/pages/merchant/ProductManagement.jsx`):**
1. Add product descriptions to list view (two-line display)
2. Add Low Stock Items metric card
3. Add Marketplace Coverage metric card
4. Add progress bars to Active Products metric
5. Implement bulk selection system (checkboxes + "More actions")
6. Add SKU auto-generation feature
7. Add Brand, Model Number, Display Name fields

**Estimated Time:** 4-6 hours
**Impact:** 80% → 90% readiness

### Phase 2: Admin Portal Enhancements (Medium Priority)

**Why Second:** Admins need these to configure the system for merchants

**Warehouse Configuration (`/pages/admin/WarehouseConfiguration.jsx`):**
1. Add warehouse metrics dashboard (4 cards)
2. Add capacity management fields
3. Add staff tracking
4. Add automation level configuration
5. Add utilization tracking
6. Implement bulk warehouse operations

**Estimated Time:** 4-6 hours
**Impact:** 90% → 95% readiness

### Phase 3: Advanced Features (Lower Priority)

**Merchant Portal:**
- 8-step product creation wizard
- Advanced product analytics
- Enhanced marketplace publishing workflow

**Admin Portal:**
- Advanced warehouse analytics
- Warehouse performance comparisons
- Predictive capacity planning

**Estimated Time:** 6-8 hours
**Impact:** 95% → 98% readiness

---

## Database Schema Considerations

### Products Table (Merchant Data)
```sql
-- Merchant-managed fields
ALTER TABLE products ADD COLUMN IF NOT EXISTS merchant_id INTEGER REFERENCES merchants(id);
ALTER TABLE products ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS brand VARCHAR(255);
ALTER TABLE products ADD COLUMN IF NOT EXISTS model_number VARCHAR(255);
ALTER TABLE products ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);
ALTER TABLE products ADD COLUMN IF NOT EXISTS low_stock_threshold INTEGER DEFAULT 10;
```

### Warehouses Table (Admin Data)
```sql
-- Admin-managed fields
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS max_capacity INTEGER;
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS current_utilization INTEGER DEFAULT 0;
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS capacity_level VARCHAR(50);
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS staff_count INTEGER DEFAULT 0;
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS automation_level VARCHAR(50) DEFAULT 'manual';
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS target_utilization_min INTEGER DEFAULT 70;
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS target_utilization_max INTEGER DEFAULT 85;
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
```

### Inventory Table (Merchant Data, References Admin Warehouses)
```sql
-- Links merchant products to admin warehouses
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS product_id INTEGER REFERENCES products(id);
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS warehouse_id INTEGER REFERENCES warehouses(id);
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 0;
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS merchant_id INTEGER REFERENCES merchants(id);
```

### Marketplace Integrations Table (Admin Data)
```sql
-- Admin-managed marketplace configurations
ALTER TABLE marketplace_integrations ADD COLUMN IF NOT EXISTS marketplace_name VARCHAR(255);
ALTER TABLE marketplace_integrations ADD COLUMN IF NOT EXISTS api_key TEXT;
ALTER TABLE marketplace_integrations ADD COLUMN IF NOT EXISTS api_secret TEXT;
ALTER TABLE marketplace_integrations ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE marketplace_integrations ADD COLUMN IF NOT EXISTS commission_rate DECIMAL(5,2);
```

### Marketplace Listings Table (Merchant Data, References Admin Marketplaces)
```sql
-- Merchant-managed listings on admin-configured marketplaces
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS product_id INTEGER REFERENCES products(id);
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS marketplace_id INTEGER REFERENCES marketplace_integrations(id);
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS merchant_id INTEGER REFERENCES merchants(id);
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS listing_status VARCHAR(50);
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS marketplace_price DECIMAL(10,2);
```

---

## API Endpoints by Persona

### Admin Endpoints (Port 8004)

**Warehouses:**
- `POST /api/admin/warehouses` - Create warehouse
- `PUT /api/admin/warehouses/:id` - Update warehouse
- `DELETE /api/admin/warehouses/:id` - Delete warehouse
- `GET /api/admin/warehouses` - List all warehouses
- `GET /api/admin/warehouses/metrics` - System-wide warehouse metrics

**Marketplaces:**
- `POST /api/admin/marketplaces` - Add marketplace integration
- `PUT /api/admin/marketplaces/:id` - Update marketplace config
- `DELETE /api/admin/marketplaces/:id` - Remove marketplace
- `GET /api/admin/marketplaces` - List all marketplace integrations

### Merchant Endpoints (Port 8003)

**Products:**
- `POST /api/merchant/products` - Create product
- `PUT /api/merchant/products/:id` - Update product
- `DELETE /api/merchant/products/:id` - Delete product
- `GET /api/merchant/products` - List merchant's products
- `GET /api/merchant/products/metrics` - Product metrics (low stock, marketplace coverage)
- `POST /api/merchant/products/bulk` - Bulk operations

**Inventory:**
- `GET /api/merchant/inventory` - View inventory across warehouses
- `PUT /api/merchant/inventory/:product_id/:warehouse_id` - Update stock level
- `POST /api/merchant/inventory/transfer` - Transfer stock between warehouses
- `GET /api/merchant/warehouses` - List available warehouses (read-only)

**Marketplace Listings:**
- `POST /api/merchant/marketplace-listings` - Publish product to marketplace
- `PUT /api/merchant/marketplace-listings/:id` - Update listing
- `DELETE /api/merchant/marketplace-listings/:id` - Remove listing
- `GET /api/merchant/marketplace-listings` - List merchant's marketplace listings
- `GET /api/merchant/marketplaces` - List available marketplaces (read-only)

---

## Summary

**Key Principle:** Admin configures, Merchant operates, Customer shops.

**Admin Portal:**
- Warehouse configuration and management
- Marketplace integration setup
- Channel and carrier configuration
- System-wide metrics and analytics

**Merchant Portal:**
- Product catalog management
- Inventory management (using admin-configured warehouses)
- Marketplace listings (using admin-configured marketplaces)
- Orders and fulfillment
- Merchant-specific analytics

**Customer Portal:**
- Product browsing and shopping
- Order tracking
- Account management

This separation ensures proper access control, data security, and logical feature organization.
