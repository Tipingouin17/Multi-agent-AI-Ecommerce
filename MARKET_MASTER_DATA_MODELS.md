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

## OFFER DATA MODEL

*[To be documented]*

---

## ORDER DATA MODEL

*[To be documented]*

---

## CUSTOMER DATA MODEL

*[To be documented]*

---

## ADVERTISING CAMPAIGN DATA MODEL

*[To be documented]*

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

