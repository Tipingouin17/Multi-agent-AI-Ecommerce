-- Document Generation System Migration
-- Supports PDF, label, and document template management

-- Document Templates Table
CREATE TABLE IF NOT EXISTS document_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL, -- invoice, shipping_label, packing_slip, return_label, report, custom
    description TEXT,
    template_content TEXT, -- HTML/Jinja2 template
    format VARCHAR(20) DEFAULT 'PDF', -- PDF, PNG, ZPL, HTML
    page_size VARCHAR(20) DEFAULT 'LETTER', -- LETTER, A4, LABEL_4X6
    orientation VARCHAR(20) DEFAULT 'portrait', -- portrait, landscape
    variables JSONB, -- Template variables and their descriptions
    styles JSONB, -- CSS styles or formatting rules
    enabled BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Generated Documents Table
CREATE TABLE IF NOT EXISTS generated_documents (
    id SERIAL PRIMARY KEY,
    document_type VARCHAR(50) NOT NULL,
    template_id INTEGER REFERENCES document_templates(id),
    related_id INTEGER NOT NULL, -- Order ID, Shipment ID, etc.
    related_type VARCHAR(50) NOT NULL, -- order, shipment, return, customer
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255),
    format VARCHAR(20) NOT NULL,
    file_size_kb INTEGER,
    generated_by VARCHAR(100) DEFAULT 'document_generation_agent',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    download_count INTEGER DEFAULT 0,
    last_downloaded_at TIMESTAMP,
    metadata JSONB
);

-- Document Generation Queue
CREATE TABLE IF NOT EXISTS document_generation_queue (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(100) UNIQUE NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    template_id INTEGER REFERENCES document_templates(id),
    related_id INTEGER NOT NULL,
    related_type VARCHAR(50) NOT NULL,
    format VARCHAR(20) DEFAULT 'PDF',
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    parameters JSONB, -- Additional parameters for generation
    result JSONB, -- Generation result (file_path, errors, etc.)
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

-- Document Access Log
CREATE TABLE IF NOT EXISTS document_access_log (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES generated_documents(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    customer_id INTEGER REFERENCES customers(id),
    access_type VARCHAR(50) NOT NULL, -- view, download, print, email
    ip_address VARCHAR(45),
    user_agent TEXT,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document Batch Jobs
CREATE TABLE IF NOT EXISTS document_batch_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    template_id INTEGER REFERENCES document_templates(id),
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    total_count INTEGER DEFAULT 0,
    processed_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    parameters JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX idx_document_templates_type ON document_templates(type);
CREATE INDEX idx_document_templates_enabled ON document_templates(enabled);
CREATE INDEX idx_generated_documents_type ON generated_documents(document_type);
CREATE INDEX idx_generated_documents_related ON generated_documents(related_type, related_id);
CREATE INDEX idx_generated_documents_generated_at ON generated_documents(generated_at);
CREATE INDEX idx_document_generation_queue_status ON document_generation_queue(status);
CREATE INDEX idx_document_generation_queue_priority ON document_generation_queue(priority);
CREATE INDEX idx_document_access_log_document ON document_access_log(document_id);
CREATE INDEX idx_document_access_log_accessed_at ON document_access_log(accessed_at);
CREATE INDEX idx_document_batch_jobs_status ON document_batch_jobs(status);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_document_template_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER document_templates_updated_at
    BEFORE UPDATE ON document_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_document_template_timestamp();

-- Insert sample document templates
INSERT INTO document_templates (
    name, type, description, template_content, format, page_size, variables, enabled, is_default
) VALUES
(
    'Standard Invoice Template',
    'invoice',
    'Default invoice template with company branding',
    '<html><body><h1>INVOICE</h1><p>Order #: {{order_number}}</p></body></html>',
    'PDF',
    'LETTER',
    '{"order_number": "Order number", "customer_name": "Customer name", "items": "Order items array", "total": "Total amount"}'::jsonb,
    true,
    true
),
(
    'Shipping Label 4x6',
    'shipping_label',
    'Standard 4x6 inch shipping label',
    '<html><body><h2>{{carrier}}</h2><p>Tracking: {{tracking_number}}</p></body></html>',
    'PDF',
    'LABEL_4X6',
    '{"carrier": "Carrier name", "tracking_number": "Tracking number", "recipient_name": "Recipient name", "address": "Shipping address"}'::jsonb,
    true,
    true
),
(
    'Packing Slip Template',
    'packing_slip',
    'Standard packing slip for warehouse',
    '<html><body><h1>PACKING SLIP</h1><p>Order #: {{order_number}}</p></body></html>',
    'PDF',
    'LETTER',
    '{"order_number": "Order number", "items": "Items to pack", "customer_name": "Customer name"}'::jsonb,
    true,
    true
),
(
    'Return Label Template',
    'return_label',
    'Return shipping label template',
    '<html><body><h2>RETURN LABEL</h2><p>RMA #: {{rma_number}}</p></body></html>',
    'PDF',
    'LABEL_4X6',
    '{"rma_number": "RMA number", "return_address": "Return address", "customer_name": "Customer name"}'::jsonb,
    true,
    true
),
(
    'ZPL Shipping Label',
    'shipping_label',
    'ZPL format for Zebra printers',
    '^XA^FO50,50^A0N,50,50^FD{{carrier}}^FS^XZ',
    'ZPL',
    'LABEL_4X6',
    '{"carrier": "Carrier name", "tracking_number": "Tracking number", "recipient_name": "Recipient name"}'::jsonb,
    true,
    false
);

-- Comments for documentation
COMMENT ON TABLE document_templates IS 'Configurable templates for document generation';
COMMENT ON TABLE generated_documents IS 'Records of all generated documents';
COMMENT ON TABLE document_generation_queue IS 'Queue for asynchronous document generation';
COMMENT ON TABLE document_access_log IS 'Audit log of document access';
COMMENT ON TABLE document_batch_jobs IS 'Batch document generation jobs';

