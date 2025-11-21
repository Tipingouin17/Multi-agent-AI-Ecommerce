# Market Master - Complete 8-Step Product Creation Wizard

## Overview
Market Master uses a comprehensive 8-step wizard for product creation with a progress bar showing percentage completion (13% per step).

---

## Step 1 of 8: Basic Information (13% Complete)

**Purpose:** Product name, SKU, category, and core details

### Product Identity Section

| Field | Type | Required | Features | Placeholder/Default |
|-------|------|----------|----------|-------------------|
| Product Name | Text input | Yes (*) | - | "Enter product name" |
| Display Name | Text input | No | Optional display name | "Display name (optional)" |
| SKU | Text input | Yes (*) | "Generate" button for auto-generation | "Product SKU" |
| Category | Dropdown/Button | Yes (*) | Category selector | "Select category" |
| Product Type | Dropdown/Button | No | Product type selector | "Simple Product" (default) |
| Brand | Text input | No | Brand name | "Product brand" |
| Model Number | Text input | No | Manufacturer model | "Model number" |

### Product Description Section

| Field | Type | Required | Features | Placeholder/Default |
|-------|------|----------|----------|-------------------|
| Description | Textarea | Yes (*) | Rich text area | - |
| Key Features | Text input + List | No | Add multiple features with + button | "Add a key feature" |

### Navigation Buttons
- **Save Draft** - Save progress without completing
- **Previous** - Go to previous step (disabled on step 1)
- **Next** - Proceed to next step
- **Close** - Cancel and close wizard

### Progress Indicator
- Visual progress bar: 13% complete
- Step indicator: "Step 1 of 8"
- Horizontal stepper showing all 8 steps

---

## Step 2 of 8: Specifications (25% Complete)

**Purpose:** Technical specifications and product attributes

### Expected Fields (based on typical e-commerce platforms):
- Dimensions (Length, Width, Height)
- Weight
- Material
- Color options
- Size options
- Technical specifications (varies by category)
- Warranty information
- Certifications
- Country of origin

---

## Step 3 of 8: Visual Assets (38% Complete)

**Purpose:** Product images and media

### Expected Fields:
- Primary product image (required)
- Additional product images (gallery)
- Product videos
- 360° view images
- Image alt text for SEO
- Image ordering/arrangement

---

## Step 4 of 8: Pricing & Costs (50% Complete)

**Purpose:** Pricing, costs, and profit margins

### Expected Fields:
- Base price (required)
- Cost price
- Compare at price (MSRP)
- Profit margin (calculated)
- Tax configuration
- Currency
- Pricing rules
- Bulk pricing tiers
- Promotional pricing

---

## Step 5 of 8: Inventory & Logistics (63% Complete)

**Purpose:** Stock levels, warehouses, and shipping configuration

### Expected Fields:
- Track inventory (yes/no)
- Stock quantity per warehouse
- SKU per warehouse
- Low stock threshold
- Reorder point
- Reorder quantity
- Warehouse locations
- Shipping weight
- Shipping dimensions
- Fulfillment method
- Handling time

---

## Step 6 of 8: Bundle & Kit Config (75% Complete)

**Purpose:** Product bundles and kit configurations

### Expected Fields:
- Bundle type (fixed/flexible)
- Bundle products (product selector)
- Bundle pricing (fixed/calculated)
- Bundle discount
- Kit components
- Component quantities
- Optional components
- Bundle SKU

---

## Step 7 of 8: Marketplace & Compliance (88% Complete)

**Purpose:** Multi-channel publishing and regulatory compliance

### Expected Fields:
- Marketplace selection (Amazon, eBay, Walmart, etc.)
- Marketplace-specific SKUs
- Marketplace categories
- Marketplace pricing
- Compliance certifications
- Safety warnings
- Age restrictions
- Hazmat classification
- Export restrictions
- GTIN/UPC/EAN codes

---

## Step 8 of 8: Review & Activation (100% Complete)

**Purpose:** Final review and product activation

### Expected Features:
- Summary of all entered data
- Validation errors/warnings
- Preview of product listing
- Activation options:
  - Save as Draft
  - Publish Immediately
  - Schedule Publishing
- Confirmation message

---

## UI/UX Features

### Progress Tracking
- **Progress Bar**: Visual bar showing 13%, 25%, 38%, 50%, 63%, 75%, 88%, 100%
- **Step Indicator**: "Step X of 8"
- **Percentage**: "X% Complete"

### Navigation
- **Linear Navigation**: Must complete steps in order
- **Save Draft**: Available at any step
- **Previous/Next**: Navigate between steps
- **Close**: Exit wizard (with unsaved changes warning)

### Validation
- **Real-time Validation**: Field-level validation as user types
- **Step Validation**: Cannot proceed to next step with errors
- **Required Field Indicators**: Asterisk (*) for required fields

### Visual Design
- **Horizontal Stepper**: All 8 steps visible at top
- **Active Step Highlight**: Current step highlighted
- **Completed Steps**: Checkmark or different color
- **Clean Layout**: Sections clearly separated
- **Responsive**: Works on desktop and tablet

---

## Implementation Notes

### Database Schema Requirements

```sql
-- Products table needs additional fields
ALTER TABLE products ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);
ALTER TABLE products ADD COLUMN IF NOT EXISTS brand VARCHAR(255);
ALTER TABLE products ADD COLUMN IF NOT EXISTS model_number VARCHAR(255);
ALTER TABLE products ADD COLUMN IF NOT EXISTS key_features TEXT[]; -- Array of features
ALTER TABLE products ADD COLUMN IF NOT EXISTS product_type VARCHAR(50) DEFAULT 'simple';

-- Specifications table
CREATE TABLE IF NOT EXISTS product_specifications (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES products(id),
  spec_name VARCHAR(255),
  spec_value TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Visual assets table
CREATE TABLE IF NOT EXISTS product_media (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES products(id),
  media_type VARCHAR(50), -- image, video, 360
  media_url TEXT,
  media_order INTEGER,
  is_primary BOOLEAN DEFAULT false,
  alt_text TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Pricing table
CREATE TABLE IF NOT EXISTS product_pricing (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES products(id),
  base_price DECIMAL(10,2),
  cost_price DECIMAL(10,2),
  compare_price DECIMAL(10,2),
  profit_margin DECIMAL(5,2),
  currency VARCHAR(3) DEFAULT 'USD',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Inventory per warehouse
CREATE TABLE IF NOT EXISTS product_inventory (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES products(id),
  warehouse_id INTEGER REFERENCES warehouses(id),
  quantity INTEGER DEFAULT 0,
  low_stock_threshold INTEGER DEFAULT 10,
  reorder_point INTEGER,
  reorder_quantity INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Bundles
CREATE TABLE IF NOT EXISTS product_bundles (
  id SERIAL PRIMARY KEY,
  bundle_product_id INTEGER REFERENCES products(id),
  component_product_id INTEGER REFERENCES products(id),
  quantity INTEGER DEFAULT 1,
  is_optional BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Marketplace listings
CREATE TABLE IF NOT EXISTS marketplace_listings (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES products(id),
  marketplace_id INTEGER REFERENCES marketplaces(id),
  marketplace_sku VARCHAR(255),
  marketplace_category VARCHAR(255),
  marketplace_price DECIMAL(10,2),
  is_published BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Compliance
CREATE TABLE IF NOT EXISTS product_compliance (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES products(id),
  certification_type VARCHAR(255),
  certification_number VARCHAR(255),
  expiry_date DATE,
  has_age_restriction BOOLEAN DEFAULT false,
  min_age INTEGER,
  is_hazmat BOOLEAN DEFAULT false,
  gtin VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Component Structure

```
ProductWizard.jsx (Main wizard container)
├── WizardProgress.jsx (Progress bar and stepper)
├── Step1BasicInformation.jsx
├── Step2Specifications.jsx
├── Step3VisualAssets.jsx
├── Step4PricingCosts.jsx
├── Step5InventoryLogistics.jsx
├── Step6BundleKit.jsx
├── Step7MarketplaceCompliance.jsx
└── Step8ReviewActivation.jsx
```

### State Management

```javascript
const [wizardState, setWizardState] = useState({
  currentStep: 1,
  completedSteps: [],
  formData: {
    step1: { /* basic info */ },
    step2: { /* specifications */ },
    step3: { /* visual assets */ },
    step4: { /* pricing */ },
    step5: { /* inventory */ },
    step6: { /* bundles */ },
    step7: { /* marketplace */ },
    step8: { /* review */ }
  },
  isDraft: true,
  validationErrors: {}
});
```

---

## Comparison: Market Master vs Current Implementation

| Feature | Market Master | Our Current | Status |
|---------|---------------|-------------|--------|
| Multi-step wizard | ✅ 8 steps | ❌ Single form | Missing |
| Progress tracking | ✅ Visual bar | ❌ None | Missing |
| Save Draft | ✅ Yes | ❌ No | Missing |
| Step navigation | ✅ Previous/Next | ❌ N/A | Missing |
| Basic Information | ✅ Complete | ✅ Partial | Needs expansion |
| Specifications | ✅ Full step | ❌ None | Missing |
| Visual Assets | ✅ Full step | ✅ Basic upload | Needs expansion |
| Pricing & Costs | ✅ Full step | ✅ Basic | Needs expansion |
| Inventory & Logistics | ✅ Full step | ✅ Basic | Needs expansion |
| Bundle & Kit | ✅ Full step | ❌ None | Missing |
| Marketplace | ✅ Full step | ❌ None | Missing |
| Review & Activation | ✅ Full step | ❌ None | Missing |
| Key Features list | ✅ Yes | ❌ No | Missing |
| Product Type selector | ✅ Yes | ❌ No | Missing |

---

## Priority Implementation Order

### Phase 1: Wizard Framework (High Priority)
1. Create wizard container component
2. Implement progress bar and stepper
3. Add step navigation (Previous/Next)
4. Implement Save Draft functionality
5. Add step validation

### Phase 2: Complete Step 1 (High Priority)
1. Add Key Features list with add/remove
2. Add Product Type dropdown
3. Improve Description textarea (rich text?)
4. Add Category selector modal

### Phase 3: Core Steps (Medium Priority)
1. Step 2: Specifications (dynamic fields based on category)
2. Step 3: Visual Assets (image gallery with ordering)
3. Step 4: Pricing & Costs (profit margin calculator)
4. Step 5: Inventory & Logistics (multi-warehouse)

### Phase 4: Advanced Steps (Lower Priority)
1. Step 6: Bundle & Kit Config
2. Step 7: Marketplace & Compliance
3. Step 8: Review & Activation

---

## Estimated Implementation Time

- **Phase 1 (Wizard Framework)**: 4-6 hours
- **Phase 2 (Complete Step 1)**: 2-3 hours
- **Phase 3 (Core Steps 2-5)**: 8-12 hours
- **Phase 4 (Advanced Steps 6-8)**: 8-10 hours

**Total**: 22-31 hours for complete implementation

---

## Next Steps

1. Review this document with stakeholders
2. Prioritize which steps are essential for MVP
3. Design database schema changes
4. Create reusable wizard framework components
5. Implement step-by-step with testing
6. Update API endpoints to handle new data structure
