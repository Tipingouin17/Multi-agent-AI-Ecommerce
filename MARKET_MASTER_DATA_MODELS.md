# MARKET MASTER TOOL - COMPLETE DATA MODELS

**Date:** November 20, 2025  
**Purpose:** Document complete data structures, fields, and workflows for all entities in Market Master Tool

---

## PRODUCT DATA MODEL

### Product Creation Workflow

**8-Step Wizard with Progress Tracking:**
- Step 1: Basic Information (13% complete)
- Step 2: Specifications
- Step 3: Visual Assets  
- Step 4: Pricing & Costs
- Step 5: Inventory & Logistics
- Step 6: Bundle & Kit Config
- Step 7: Marketplace & Compliance
- Step 8: Review & Activation

### Step 1: Basic Information

**Section: Product Identity**

| Field Name | Type | Required | Features | Notes |
|------------|------|----------|----------|-------|
| **Product Name** | Text | Yes (*) | - | Main product name |
| **Display Name** | Text | No | Optional | Alternative display name for marketplaces |
| **SKU** | Text | Yes (*) | "Generate" button | Unique product identifier with auto-generation |
| **Category** | Dropdown | Yes (*) | Select from categories | Product categorization |
| **Product Type** | Dropdown | No | Default: "Simple Product" | Product type (Simple/Variable/Bundle/etc.) |
| **Brand** | Text | No | - | Product brand/manufacturer |
| **Model Number** | Text | No | - | Manufacturer model number |

**Section: Product Description**

| Field Name | Type | Required | Features | Notes |
|------------|------|----------|----------|-------|
| **Description** | Rich Text | Yes (*) | - | Full product description |
| **Key Features** | List/Array | No | - | Bullet points of key features |

**Actions Available:**
- **Save Draft** - Save incomplete product
- **Previous** - Go to previous step (disabled on step 1)
- **Next** - Proceed to next step
- **Close** - Cancel and close form

---

### Step 2: Specifications

*[To be documented after navigation]*

---

### Step 3: Visual Assets

*[To be documented after navigation]*

---

### Step 4: Pricing & Costs

*[To be documented after navigation]*

---

### Step 5: Inventory & Logistics

*[To be documented after navigation]*

---

### Step 6: Bundle & Kit Config

*[To be documented after navigation]*

---

### Step 7: Marketplace & Compliance

*[To be documented after navigation]*

---

### Step 8: Review & Activation

*[To be documented after navigation]*

---

## WAREHOUSE DATA MODEL

*[To be documented]*

---

## SUPPLIER DATA MODEL

*[To be documented]*

---

## OFFER DATA MODEL - Detailed Analysis

### Offer Creation Wizard

**8-Step Wizard Structure:**
1. **Product & Marketplace Selection** (Required)
2. **Pricing Strategy Configuration** (Required)
3. **Inventory & Logistics Setup** (Required)
4. **Marketplace Compliance** (Required)
5. **Promotional & Marketing** (Optional)
6. **Performance & Analytics** (Optional)
7. **Testing & Validation** (Required)
8. **Review & Activation** (Required)

**Estimated Time:** 3 minutes

### Step 1: Product & Marketplace Selection

#### Creation Mode Options
| Mode | Description |
|------|-------------|
| **Single Offer** | Create one offer at a time |
| **Bulk Creation** | Create multiple offers efficiently |
| **From Template** | Use pre-configured template |

#### Product Selection Fields
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| **Product Selection** | Multi-select | Yes | Shows product cards with: Name, SKU, Category, Price, Stock level |

**Sample Products Displayed:**
- Wireless Bluetooth Headphones (SKU: WBH-001, Electronics, $89.99, 150 in stock)
- Organic Cotton T-Shirt (SKU: OCT-002, Clothing, $24.99, 300 in stock)
- Smart Water Bottle (SKU: SWB-003, Lifestyle, $45, 75 in stock)

#### Marketplace Selection Fields
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| **Target Marketplaces** | Multi-select | Yes | Shows marketplace cards with: Name, Connection status, Type, Compatibility percentage |

**Sample Marketplaces Displayed:**
- **Amazon** (connected, marketplace, 95% compatibility)
- **eBay** (connected, marketplace, 88% compatibility)
- **Shopify Store** (connected, ecommerce_platform, 92% compatibility)
- **Walmart Marketplace** (disconnected, with "Connect" button)

**Key Features:**
- **Multi-marketplace support** - Can create offers for multiple marketplaces simultaneously
- **Compatibility scoring** - Shows compatibility percentage for each marketplace
- **Connection management** - Shows connection status and allows connecting new marketplaces
- **Bulk creation mode** - Supports creating multiple offers efficiently
- **Template support** - Can use pre-configured templates for faster creation
- **Validation** - Real-time validation with error messages

**Validation Rules:**
- At least one product must be selected
- At least one marketplace must be selected

---

## ORDER DATA MODEL - Detailed Analysis

### Order Creation Wizard

**8-Step Wizard Structure:**
1. **Customer Information** (Required)
2. **Order Details** (Required)
3. **Product Selection** (Required)
4. **Pricing & Totals** (Required)
5. **Shipping & Fulfillment** (Required)
6. **Payment & Financial** (Required)
7. **Compliance & Documentation** (Optional)
8. **Review & Activation** (Required)

**Estimated Time:** 3 minutes

### Step 1: Customer Information

#### Customer Selection
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| **Search Existing Customers** | Search input | Conditional | Search by name or email |
| **Create New Customer** | Button | Conditional | Opens new customer creation form |

**Validation:** Either existing customer must be selected OR new customer email must be provided

#### Billing Address
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| **Address Line 1** | Text | Yes | Primary address |
| **Address Line 2** | Text | No | Secondary address (apartment, suite, etc.) |
| **City** | Text | Yes | City name |
| **State/Region** | Text | Yes | State or region |
| **Postal Code** | Text | Yes | ZIP/Postal code |
| **Country** | Dropdown | Yes | Country selection |

#### Customer Notes
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| **Additional Notes** | Textarea | No | Free-form customer notes |

**Key Features:**
- **Dual customer selection mode** - Search existing or create new
- **Complete billing address capture** - All standard address fields
- **Customer notes** - Additional information tracking
- **Validation** - Real-time validation with error messages

### Steps 2-8: Order Details, Product Selection, etc.
*(To be documented - wizard has 8 total steps)*

**Order List Features:**
- Order Number (auto-generated, format: ORD-XXXXXX)
- Customer (name and email)
- Marketplace (e.g., Walmart)
- Status (pending, processing, shipped, delivered)
- Risk Level (low, medium, high)
- Total (with currency)
- Items count
- Date

**Dashboard Metrics:**
- Total Orders (count)
- Pending Orders (needs attention)
- Shipped Orders (fulfillment percentage)
- Total Revenue (this month)

---

## CUSTOMER DATA MODEL

*[To be documented]*

---

## ADVERTISING CAMPAIGN DATA MODEL - Detailed Analysis

### Campaign Creation Form

**Simple Form Structure (Single-step)**

| Field Name | Type | Required | Options/Notes |
|------------|------|----------|---------------|
| **Name** | Text | Yes | Example: "Summer Promo" |
| **Platform** | Dropdown | Yes | 5 options: Google Ads, Meta Ads, Amazon Ads, TikTok Ads, FnacDarty |
| **Budget** | Number | Yes | Campaign budget amount |
| **Start Date** | Date picker | Yes | Format: mm/dd/yyyy |
| **End Date** | Date picker | Yes | Format: mm/dd/yyyy |
| **Status** | Dropdown | Yes | 3 options: Active, Paused, Draft |

**Key Features:**
- **Multi-platform support** - Google Ads, Meta Ads, Amazon Ads, TikTok Ads, FnacDarty
- **Platform connection management** - Shows connection status for each platform
- **Budget tracking** - Total budget and spent tracking
- **Performance metrics** - CTR, Conversion Rate, ROI, Average CPA
- **Campaign management** - Filter by platform and status
- **Import/Export** - Bulk campaign management
- **A/B Testing** - Dedicated tab for A/B testing
- **Budget Optimization** - Dedicated tab for budget optimization

**Dashboard Metrics:**
- Total Campaigns
- Active Campaigns (running now)
- Total Budget
- Total Spent
- CTR (Click-through rate)
- Conv Rate (Conversions / Clicks)
- ROI (Weighted by spend)
- Avg CPA (Cost per acquisition)

**Ad Platforms Supported:**
1. Google Ads (Connected)
2. Meta Ads (Connected)
3. Amazon Ads (Connected)
4. TikTok Ads (Not connected)
5. FnacDarty (Not connected)

---

## PRICING RULE DATA MODEL (Reprisal Intelligence)

*[To be documented]*

---

**Status:** In Progress  
**Next Steps:** Navigate through all 8 product creation steps, then document other entity data models



## WAREHOUSE DATA MODEL - Detailed Analysis

### Warehouse Creation Workflow

**7-Step Wizard with Progress Tracking:**
- Step 1: Basic Information (14% complete)
- Step 2: Facility Specifications
- Step 3: Operational Capabilities
- Step 4: Security & Safety
- Step 5: Customs & Compliance
- Step 6: Technology & Integration
- Step 7: Review & Finalization

### Step 1: Basic Information

**Section 1: Warehouse Identity**

| Field Name | Type | Required | Options/Notes |
|------------|------|----------|---------------|
| **Warehouse Name** | Text | Yes | e.g., Lyon Distribution Center |
| **Display Name** | Text | No | e.g., Lyon DC |
| **Warehouse Code** | Text | Yes | e.g., LYN-01 |
| **Facility Type** | Dropdown | Yes | 5 options: Distribution Center, Fulfillment Center, Warehouse, Cross-Dock, Cold Storage |

**Section 2: Location Details**

| Field Name | Type | Required |
|------------|------|----------|
| **Street Address** | Text | Yes |
| **City** | Text | Yes |
| **State/Region** | Text | Yes |
| **Postal Code** | Text | Yes |
| **Country** | Text/Dropdown | Yes |

**Section 3: Contact Information**

| Field Name | Type | Required |
|------------|------|----------|
| **Warehouse Manager** | Text | Yes |
| **Phone Number** | Text | Yes |
| **Email Address** | Email | Yes |

### Remaining Steps (To be explored):
- Step 2: Facility Specifications
- Step 3: Operational Capabilities  
- Step 4: Security & Safety
- Step 5: Customs & Compliance
- Step 6: Technology & Integration
- Step 7: Review & Finalization

---



## SUPPLIER DATA MODEL - Detailed Analysis

### Supplier Creation Form

**3-Tab Form Structure:**
- Tab 1: Basic Info
- Tab 2: Contact
- Tab 3: Integration

### Tab 1: Basic Info (Documented)

| Field Name | Type | Required | Options/Notes |
|------------|------|----------|---------------|
| **Supplier Name** | Text | Yes | Enter supplier name |
| **Supplier Type** | Dropdown | Yes | 3 options: Dropshipping, Wholesale, Manufacturer |
| **Status** | Dropdown | Yes | 3 options: Active, Inactive, Suspended |
| **Terms and Conditions** | Textarea | No | Free-form text for supplier terms |

**Key Features:**
- **Dropshipping support** - First-class feature with dedicated supplier type
- **Supplier status management** - Active/Inactive/Suspended states
- **Terms tracking** - Built-in terms and conditions field

### Tabs 2 & 3: Contact and Integration
*(Tabs appear to be non-functional or empty in current implementation)*

---

