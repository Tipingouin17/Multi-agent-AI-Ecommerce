-- Warehouse Capacity and Workforce Management Tables
-- Migration: 021_warehouse_capacity.sql

-- =====================================================
-- WAREHOUSE CAPACITY TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_capacity (
    capacity_id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    total_space_sqft DECIMAL(12, 2) NOT NULL,
    used_space_sqft DECIMAL(12, 2) NOT NULL DEFAULT 0,
    orders_per_hour_capacity DECIMAL(10, 2) DEFAULT 0,
    current_orders_per_hour DECIMAL(10, 2) DEFAULT 0,
    units_per_hour_capacity DECIMAL(10, 2) DEFAULT 0,
    current_units_per_hour DECIMAL(10, 2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(warehouse_id)
);

-- =====================================================
-- WAREHOUSE EMPLOYEES
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_employees (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    employee_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- picker, packer, receiver, shipper, etc.
    skill_level VARCHAR(50) NOT NULL, -- beginner, intermediate, advanced, expert
    hourly_rate DECIMAL(10, 2) NOT NULL,
    shift VARCHAR(50) NOT NULL, -- morning, afternoon, night, full_day
    is_active BOOLEAN DEFAULT true,
    hire_date TIMESTAMP NOT NULL,
    certifications TEXT[], -- Array of certification names
    avg_picks_per_hour DECIMAL(10, 2),
    avg_packs_per_hour DECIMAL(10, 2),
    accuracy_rate DECIMAL(5, 2), -- Percentage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_warehouse_employees_warehouse ON warehouse_employees(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_employees_role ON warehouse_employees(role);
CREATE INDEX IF NOT EXISTS idx_warehouse_employees_shift ON warehouse_employees(shift);
CREATE INDEX IF NOT EXISTS idx_warehouse_employees_active ON warehouse_employees(is_active);

-- =====================================================
-- WAREHOUSE EQUIPMENT
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_equipment (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    equipment_id VARCHAR(255) NOT NULL UNIQUE,
    equipment_type VARCHAR(50) NOT NULL, -- forklift, pallet_jack, scanner, etc.
    name VARCHAR(255) NOT NULL,
    is_available BOOLEAN DEFAULT true,
    is_operational BOOLEAN DEFAULT true,
    last_maintenance TIMESTAMP,
    next_maintenance TIMESTAMP,
    assigned_to VARCHAR(255), -- Employee ID
    utilization_rate DECIMAL(5, 2), -- Percentage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_warehouse_equipment_warehouse ON warehouse_equipment(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_equipment_type ON warehouse_equipment(equipment_type);
CREATE INDEX IF NOT EXISTS idx_warehouse_equipment_available ON warehouse_equipment(is_available, is_operational);

-- =====================================================
-- WAREHOUSE THROUGHPUT TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_throughput (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    orders_per_hour_capacity DECIMAL(10, 2) NOT NULL,
    current_orders_per_hour DECIMAL(10, 2) NOT NULL,
    units_per_hour_capacity DECIMAL(10, 2) NOT NULL,
    current_units_per_hour DECIMAL(10, 2) NOT NULL,
    active_employees INT NOT NULL,
    active_equipment INT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_warehouse_throughput_warehouse_time ON warehouse_throughput(warehouse_id, timestamp DESC);

-- =====================================================
-- ORDER PROCESSING TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_order_processing (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    order_id VARCHAR(255) NOT NULL,
    employee_id VARCHAR(255),
    started_at TIMESTAMP NOT NULL,
    picked_at TIMESTAMP,
    packed_at TIMESTAMP,
    completed_at TIMESTAMP,
    is_accurate BOOLEAN DEFAULT true,
    error_type VARCHAR(100),
    FOREIGN KEY (employee_id) REFERENCES warehouse_employees(employee_id)
);

CREATE INDEX IF NOT EXISTS idx_warehouse_order_processing_warehouse ON warehouse_order_processing(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_order_processing_employee ON warehouse_order_processing(employee_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_order_processing_completed ON warehouse_order_processing(completed_at);

-- =====================================================
-- ORDER ITEMS PROCESSING
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_order_items (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    order_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_warehouse_order_items_warehouse ON warehouse_order_items(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_order_items_processed ON warehouse_order_items(processed_at);

-- =====================================================
-- WAREHOUSE COSTS TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_costs (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    total_cost DECIMAL(12, 2) NOT NULL,
    labor_cost DECIMAL(12, 2) NOT NULL,
    equipment_cost DECIMAL(12, 2) NOT NULL,
    overhead_cost DECIMAL(12, 2) NOT NULL,
    total_hours DECIMAL(10, 2) NOT NULL,
    overtime_hours DECIMAL(10, 2) DEFAULT 0,
    UNIQUE(warehouse_id, date)
);

CREATE INDEX IF NOT EXISTS idx_warehouse_costs_warehouse_date ON warehouse_costs(warehouse_id, date DESC);

-- =====================================================
-- WAREHOUSE ORDERS TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_orders (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    order_id VARCHAR(255) NOT NULL UNIQUE,
    is_fulfilled BOOLEAN DEFAULT false,
    delivered_on_time BOOLEAN,
    is_accurate BOOLEAN DEFAULT true,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_warehouse_orders_warehouse ON warehouse_orders(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_orders_completed ON warehouse_orders(completed_at);

-- =====================================================
-- SAFETY INCIDENTS TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_safety_incidents (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    incident_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    incident_type VARCHAR(100) NOT NULL,
    is_near_miss BOOLEAN DEFAULT false,
    employee_id VARCHAR(255),
    description TEXT,
    severity VARCHAR(50), -- minor, moderate, severe, critical
    total_hours_worked DECIMAL(10, 2), -- For rate calculation
    FOREIGN KEY (employee_id) REFERENCES warehouse_employees(employee_id)
);

CREATE INDEX IF NOT EXISTS idx_warehouse_safety_warehouse ON warehouse_safety_incidents(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_safety_date ON warehouse_safety_incidents(incident_date DESC);

-- =====================================================
-- CAPACITY FORECASTS
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_capacity_forecasts (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    forecast_date DATE NOT NULL,
    expected_orders INT NOT NULL,
    expected_units INT NOT NULL,
    required_employees INT NOT NULL,
    required_equipment INT NOT NULL,
    required_space_sqft DECIMAL(12, 2) NOT NULL,
    employee_gap INT NOT NULL,
    equipment_gap INT NOT NULL,
    space_gap DECIMAL(12, 2) NOT NULL,
    recommendations TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(warehouse_id, forecast_date)
);

CREATE INDEX IF NOT EXISTS idx_warehouse_forecasts_warehouse_date ON warehouse_capacity_forecasts(warehouse_id, forecast_date DESC);

-- =====================================================
-- SHIFTS MANAGEMENT
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_shifts (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    shift_id VARCHAR(255) NOT NULL UNIQUE,
    shift_type VARCHAR(50) NOT NULL, -- morning, afternoon, night, full_day
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    capacity INT NOT NULL, -- Max employees
    current_headcount INT DEFAULT 0,
    required_roles JSONB, -- {"picker": 5, "packer": 3, ...}
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_warehouse_shifts_warehouse ON warehouse_shifts(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_shifts_type ON warehouse_shifts(shift_type);

-- =====================================================
-- PERFORMANCE KPIs TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_performance_kpis (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(255) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    order_fill_rate DECIMAL(5, 2),
    on_time_delivery_rate DECIMAL(5, 2),
    order_accuracy DECIMAL(5, 2),
    inventory_accuracy DECIMAL(5, 2),
    picks_per_labor_hour DECIMAL(10, 2),
    orders_per_labor_hour DECIMAL(10, 2),
    cost_per_order DECIMAL(10, 2),
    labor_cost_percentage DECIMAL(5, 2),
    overtime_percentage DECIMAL(5, 2),
    storage_utilization DECIMAL(5, 2),
    incident_rate DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(warehouse_id, period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_warehouse_kpis_warehouse_period ON warehouse_performance_kpis(warehouse_id, period_start DESC);

-- =====================================================
-- SAMPLE DATA FOR TESTING
-- =====================================================

-- Insert sample warehouse capacity
INSERT INTO warehouse_capacity (warehouse_id, total_space_sqft, used_space_sqft, orders_per_hour_capacity, units_per_hour_capacity)
VALUES 
    ('warehouse-001', 50000.00, 35000.00, 100.00, 1000.00),
    ('warehouse-002', 75000.00, 45000.00, 150.00, 1500.00)
ON CONFLICT (warehouse_id) DO NOTHING;

-- Insert sample employees
INSERT INTO warehouse_employees (warehouse_id, employee_id, name, role, skill_level, hourly_rate, shift, hire_date)
VALUES 
    ('warehouse-001', 'emp-001', 'John Picker', 'picker', 'advanced', 18.50, 'morning', '2023-01-15'),
    ('warehouse-001', 'emp-002', 'Jane Packer', 'packer', 'expert', 20.00, 'morning', '2022-06-10'),
    ('warehouse-001', 'emp-003', 'Bob Forklift', 'forklift_operator', 'expert', 22.00, 'afternoon', '2021-03-20'),
    ('warehouse-002', 'emp-004', 'Alice Supervisor', 'supervisor', 'expert', 28.00, 'full_day', '2020-09-01')
ON CONFLICT (employee_id) DO NOTHING;

-- Insert sample equipment
INSERT INTO warehouse_equipment (warehouse_id, equipment_id, equipment_type, name, is_available, is_operational)
VALUES 
    ('warehouse-001', 'equip-001', 'forklift', 'Forklift Alpha', true, true),
    ('warehouse-001', 'equip-002', 'forklift', 'Forklift Beta', true, true),
    ('warehouse-001', 'equip-003', 'scanner', 'Scanner 001', true, true),
    ('warehouse-002', 'equip-004', 'pallet_jack', 'Pallet Jack 001', true, true)
ON CONFLICT (equipment_id) DO NOTHING;

COMMENT ON TABLE warehouse_capacity IS 'Tracks overall warehouse capacity metrics including space, throughput, and resource utilization';
COMMENT ON TABLE warehouse_employees IS 'Manages warehouse workforce including roles, skills, shifts, and performance metrics';
COMMENT ON TABLE warehouse_equipment IS 'Tracks warehouse equipment inventory, availability, and maintenance schedules';
COMMENT ON TABLE warehouse_throughput IS 'Historical tracking of warehouse throughput metrics over time';
COMMENT ON TABLE warehouse_order_processing IS 'Tracks individual order processing times and accuracy';
COMMENT ON TABLE warehouse_costs IS 'Daily warehouse cost tracking including labor, equipment, and overhead';
COMMENT ON TABLE warehouse_safety_incidents IS 'Records safety incidents and near-misses for compliance and improvement';
COMMENT ON TABLE warehouse_capacity_forecasts IS 'Stores capacity forecasts and gap analysis for planning';
COMMENT ON TABLE warehouse_shifts IS 'Defines warehouse shift schedules and capacity';
COMMENT ON TABLE warehouse_performance_kpis IS 'Aggregated warehouse performance KPIs by period';

