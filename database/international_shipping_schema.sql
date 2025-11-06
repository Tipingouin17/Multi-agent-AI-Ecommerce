-- International Shipping Support Schema
-- Comprehensive international shipping with customs and compliance

-- International Shipments (international order shipments)
CREATE TABLE IF NOT EXISTS international_shipments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    tracking_number VARCHAR(100),
    origin_country VARCHAR(2) NOT NULL, -- ISO 3166-1 alpha-2
    destination_country VARCHAR(2) NOT NULL,
    shipper_name VARCHAR(255),
    shipper_address TEXT,
    shipper_tax_id VARCHAR(50),
    consignee_name VARCHAR(255),
    consignee_address TEXT,
    consignee_tax_id VARCHAR(50),
    total_value DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'USD',
    weight_kg DECIMAL(10,2),
    dimensions_cm VARCHAR(50), -- LxWxH
    incoterms VARCHAR(10) DEFAULT 'DDP', -- DDP, DDU, EXW, etc.
    carrier VARCHAR(50),
    service_level VARCHAR(50),
    shipping_cost DECIMAL(15,2),
    insurance_cost DECIMAL(15,2),
    customs_status VARCHAR(50), -- pending, cleared, held, returned
    created_at TIMESTAMP DEFAULT NOW(),
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP
);

-- Customs Documents (generated customs documentation)
CREATE TABLE IF NOT EXISTS customs_documents (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER REFERENCES international_shipments(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL, -- commercial_invoice, customs_declaration, certificate_origin, packing_list
    document_number VARCHAR(100),
    document_format VARCHAR(10) DEFAULT 'pdf',
    file_path TEXT,
    filing_status VARCHAR(50), -- draft, filed, accepted, rejected
    filed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HS Codes (Harmonized System product classification)
CREATE TABLE IF NOT EXISTS hs_codes (
    id SERIAL PRIMARY KEY,
    hs_code VARCHAR(10) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    parent_code VARCHAR(10),
    level INTEGER, -- 2, 4, 6, 8, 10 digit levels
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Duty Rates (import duty rates by country and HS code)
CREATE TABLE IF NOT EXISTS duty_rates (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(2) NOT NULL,
    hs_code VARCHAR(10) NOT NULL,
    duty_rate DECIMAL(10,4), -- Percentage
    duty_type VARCHAR(50), -- ad_valorem, specific, compound
    vat_rate DECIMAL(10,4), -- VAT/GST percentage
    effective_date DATE NOT NULL,
    expiry_date DATE,
    notes TEXT,
    UNIQUE(country_code, hs_code, effective_date)
);

-- Exchange Rates (currency exchange rates)
CREATE TABLE IF NOT EXISTS exchange_rates (
    id SERIAL PRIMARY KEY,
    base_currency VARCHAR(3) DEFAULT 'USD',
    target_currency VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(15,6) NOT NULL,
    rate_source VARCHAR(50), -- API source
    rate_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(base_currency, target_currency, rate_date)
);

-- Country Regulations (country-specific shipping rules)
CREATE TABLE IF NOT EXISTS country_regulations (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(2) NOT NULL UNIQUE,
    country_name VARCHAR(100) NOT NULL,
    de_minimis_threshold DECIMAL(15,2), -- Duty-free threshold
    de_minimis_currency VARCHAR(3),
    vat_threshold DECIMAL(15,2), -- VAT exemption threshold
    requires_tax_id BOOLEAN DEFAULT false,
    requires_eori BOOLEAN DEFAULT false, -- Economic Operators Registration and Identification
    restricted_items JSONB, -- Array of restricted item categories
    prohibited_items JSONB, -- Array of prohibited items
    documentation_requirements JSONB,
    special_notes TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Landed Costs (calculated landed costs)
CREATE TABLE IF NOT EXISTS landed_costs (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER REFERENCES international_shipments(id) ON DELETE CASCADE,
    product_cost DECIMAL(15,2) NOT NULL,
    shipping_cost DECIMAL(15,2) NOT NULL,
    insurance_cost DECIMAL(15,2),
    duty_amount DECIMAL(15,2),
    vat_amount DECIMAL(15,2),
    handling_fee DECIMAL(15,2),
    total_landed_cost DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    calculation_date TIMESTAMP DEFAULT NOW()
);

-- Product HS Codes (product to HS code mapping)
CREATE TABLE IF NOT EXISTS product_hs_codes (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    hs_code VARCHAR(10) NOT NULL,
    country_of_origin VARCHAR(2),
    classification_confidence DECIMAL(5,2), -- 0-100
    classified_by VARCHAR(100), -- user, system, ai
    verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, hs_code)
);

-- Compliance Checks (sanctions and restrictions screening)
CREATE TABLE IF NOT EXISTS compliance_checks (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER REFERENCES international_shipments(id) ON DELETE CASCADE,
    check_type VARCHAR(50) NOT NULL, -- sanctions, export_control, restricted_party
    check_status VARCHAR(50) NOT NULL, -- pass, fail, review
    check_result JSONB, -- Detailed results
    checked_at TIMESTAMP DEFAULT NOW()
);

-- Trade Agreements (preferential trade agreements)
CREATE TABLE IF NOT EXISTS trade_agreements (
    id SERIAL PRIMARY KEY,
    agreement_name VARCHAR(100) NOT NULL,
    agreement_code VARCHAR(20),
    origin_country VARCHAR(2) NOT NULL,
    destination_country VARCHAR(2) NOT NULL,
    hs_codes JSONB, -- Array of eligible HS codes
    preferential_rate DECIMAL(10,4), -- Reduced duty rate
    requirements JSONB, -- Certificate requirements
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT true
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_international_shipments_order ON international_shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_international_shipments_tracking ON international_shipments(tracking_number);
CREATE INDEX IF NOT EXISTS idx_international_shipments_destination ON international_shipments(destination_country);
CREATE INDEX IF NOT EXISTS idx_international_shipments_status ON international_shipments(customs_status);

CREATE INDEX IF NOT EXISTS idx_customs_documents_shipment ON customs_documents(shipment_id);
CREATE INDEX IF NOT EXISTS idx_customs_documents_type ON customs_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_customs_documents_status ON customs_documents(filing_status);

CREATE INDEX IF NOT EXISTS idx_hs_codes_code ON hs_codes(hs_code);
CREATE INDEX IF NOT EXISTS idx_hs_codes_parent ON hs_codes(parent_code);

CREATE INDEX IF NOT EXISTS idx_duty_rates_country ON duty_rates(country_code);
CREATE INDEX IF NOT EXISTS idx_duty_rates_hs_code ON duty_rates(hs_code);
CREATE INDEX IF NOT EXISTS idx_duty_rates_effective ON duty_rates(effective_date);

CREATE INDEX IF NOT EXISTS idx_exchange_rates_currencies ON exchange_rates(base_currency, target_currency);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_date ON exchange_rates(rate_date);

CREATE INDEX IF NOT EXISTS idx_country_regulations_code ON country_regulations(country_code);

CREATE INDEX IF NOT EXISTS idx_landed_costs_shipment ON landed_costs(shipment_id);

CREATE INDEX IF NOT EXISTS idx_product_hs_codes_product ON product_hs_codes(product_id);
CREATE INDEX IF NOT EXISTS idx_product_hs_codes_hs_code ON product_hs_codes(hs_code);

CREATE INDEX IF NOT EXISTS idx_compliance_checks_shipment ON compliance_checks(shipment_id);
CREATE INDEX IF NOT EXISTS idx_compliance_checks_status ON compliance_checks(check_status);

CREATE INDEX IF NOT EXISTS idx_trade_agreements_countries ON trade_agreements(origin_country, destination_country);
CREATE INDEX IF NOT EXISTS idx_trade_agreements_active ON trade_agreements(is_active);
