# Testing and Validation Guide

## Multi-Agent AI E-commerce Platform

This guide provides comprehensive instructions for testing all features of the multi-agent e-commerce platform, including the newly implemented services.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start Testing](#quick-start-testing)
3. [Testing New Features](#testing-new-features)
4. [Integration Testing](#integration-testing)
5. [Performance Testing](#performance-testing)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 14+
- Apache Kafka 3.4+
- Redis 7+
- Node.js 22+ (for dashboard)

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce.git
cd Multi-agent-AI-Ecommerce

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

---

## Quick Start Testing

### 1. Start Infrastructure

```bash
# Using the launch script (recommended)
./launch.sh --dev

# Or manually with Docker Compose
cd infrastructure
docker-compose up -d
```

### 2. Initialize Database

```bash
# Run database migrations
python3 database/init_database.py

# Verify tables were created
psql -h localhost -U multi_agent_user -d multi_agent_ecommerce -c "\dt"
```

### 3. Create Kafka Topics

```bash
# Initialize Kafka topics
python3 infrastructure/init_kafka_topics.py

# Verify topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

### 4. Run Feature Tests

```bash
# Test all new features
python3 test_new_features.py

# Expected output: All tests should pass ✅
```

---

## Testing New Features

### Product Agent Features

#### Test Product Variants
```python
from agents.product_variants_service import ProductVariantsService, CreateVariantRequest
from shared.database_manager import DatabaseManager

db_manager = DatabaseManager()
service = ProductVariantsService(db_manager)

# Create a variant
variant_request = CreateVariantRequest(
    product_id="prod-001",
    variant_sku="TSHIRT-RED-L",
    attributes={
        "color": "red",
        "size": "L"
    },
    price_adjustment=5.00,
    stock_quantity=100
)

variant = await service.create_variant(variant_request)
print(f"Created variant: {variant.variant_id}")
```

#### Test Product Categories
```python
from agents.product_categories_service import ProductCategoriesService, CreateCategoryRequest

service = ProductCategoriesService(db_manager)

# Create a category
category_request = CreateCategoryRequest(
    category_code="electronics",
    category_name="Electronics",
    parent_id=None,
    description="Electronic devices and accessories"
)

category = await service.create_category(category_request)
print(f"Created category: {category.category_id}")
```

#### Test Product SEO
```python
from agents.product_seo_service import ProductSEOService

service = ProductSEOService(db_manager)

# Generate SEO for a product
seo = await service.generate_product_seo(
    product_id="prod-001",
    product_name="Premium Wireless Headphones",
    product_description="High-quality wireless headphones with noise cancellation",
    category="Electronics",
    brand="TechBrand",
    price=199.99
)

print(f"Generated SEO - Title: {seo.meta_title}")
print(f"URL Slug: {seo.url_slug}")
```

#### Test Product Bundles
```python
from agents.product_bundles_service import ProductBundlesService, CreateBundleRequest, BundleType

service = ProductBundlesService(db_manager)

# Create a product bundle
bundle_request = CreateBundleRequest(
    bundle_name="Starter Pack",
    bundle_sku="BUNDLE-STARTER-001",
    bundle_type=BundleType.FIXED,
    bundle_price=149.99,
    components=[
        {"product_id": "prod-001", "quantity": 1, "is_optional": False},
        {"product_id": "prod-002", "quantity": 2, "is_optional": False}
    ]
)

bundle = await service.create_bundle(bundle_request)
print(f"Created bundle: {bundle.bundle_id}")
```

#### Test Product Attributes
```python
from agents.product_attributes_service import ProductAttributesService, CreateAttributeRequest, AttributeType

service = ProductAttributesService(db_manager)

# Create an attribute
attr_request = CreateAttributeRequest(
    attribute_code="color",
    attribute_name="Color",
    attribute_type=AttributeType.SELECT,
    is_filterable=True,
    options=[
        {"option_value": "red", "option_label": "Red"},
        {"option_value": "blue", "option_label": "Blue"},
        {"option_value": "green", "option_label": "Green"}
    ]
)

attribute = await service.create_attribute(attr_request)
print(f"Created attribute: {attribute.attribute_id}")
```

### Order Agent Features

#### Test Order Cancellation
```python
from agents.order_cancellation_service import OrderCancellationService, CreateCancellationRequest, CancellationReason

service = OrderCancellationService(db_manager)

# Request order cancellation
cancel_request = CreateCancellationRequest(
    order_id="order-12345",
    reason=CancellationReason.CUSTOMER_REQUEST,
    reason_details="Customer changed mind",
    requested_by="customer-789"
)

cancellation = await service.create_cancellation_request(cancel_request)
print(f"Cancellation request created: {cancellation.request_id}")
print(f"Status: {cancellation.status}")
```

#### Test Partial Shipments
```python
from agents.partial_shipments_service import PartialShipmentsService, CreateShipmentRequest

service = PartialShipmentsService(db_manager)

# Create a partial shipment
shipment_request = CreateShipmentRequest(
    order_id="order-12345",
    items=[
        {"order_item_id": "item-001", "quantity": 2},
        {"order_item_id": "item-002", "quantity": 1}
    ],
    carrier="UPS",
    tracking_number="1Z999AA10123456784"
)

shipment = await service.create_shipment(shipment_request)
print(f"Shipment created: {shipment.shipment_id}")
print(f"Tracking: {shipment.tracking_number}")
```

### Workflow Orchestration

#### Test Saga Pattern
```python
from agents.saga_orchestrator import SagaOrchestrator, CreateSagaRequest

orchestrator = SagaOrchestrator(db_manager)

# Create a saga for order placement
saga_request = CreateSagaRequest(
    saga_name="place_order",
    description="Complete order placement workflow",
    steps=[
        {
            "step_id": "validate-inventory",
            "step_name": "Validate Inventory",
            "agent": "inventory_agent",
            "action": "reserve_inventory",
            "compensation_action": "release_inventory",
            "params": {"order_id": "order-12345"}
        },
        {
            "step_id": "process-payment",
            "step_name": "Process Payment",
            "agent": "payment_agent",
            "action": "charge_payment",
            "compensation_action": "refund_payment",
            "params": {"order_id": "order-12345", "amount": 199.99}
        },
        {
            "step_id": "create-shipment",
            "step_name": "Create Shipment",
            "agent": "shipping_agent",
            "action": "create_shipment",
            "compensation_action": "cancel_shipment",
            "params": {"order_id": "order-12345"}
        }
    ]
)

saga = await orchestrator.create_saga(saga_request)
execution = await orchestrator.execute_saga(saga.saga_id, {"order_id": "order-12345"})
print(f"Saga execution: {execution.execution_id}")
print(f"Status: {execution.status}")
```

### Warehouse Capacity Management

#### Test Warehouse Capacity
```python
from agents.warehouse_capacity_service import WarehouseCapacityService

service = WarehouseCapacityService(db_manager)

# Get current capacity
capacity = await service.get_current_capacity("warehouse-001")
print(f"Warehouse: {capacity.warehouse_id}")
print(f"Space utilization: {capacity.utilization_rate}%")
print(f"Orders/hour capacity: {capacity.orders_per_hour_capacity}")
print(f"Current orders/hour: {capacity.current_orders_per_hour}")
print(f"Active employees: {capacity.active_employees}")
print(f"Available equipment: {capacity.available_equipment}")
```

#### Test Throughput Metrics
```python
from datetime import datetime, timedelta

# Calculate throughput for the last 24 hours
period_end = datetime.utcnow()
period_start = period_end - timedelta(days=1)

throughput = await service.calculate_throughput_metrics(
    "warehouse-001",
    period_start,
    period_end
)

print(f"Orders processed: {throughput.total_orders_processed}")
print(f"Orders per hour: {throughput.orders_per_hour}")
print(f"Units per hour: {throughput.units_per_hour}")
print(f"Accuracy rate: {throughput.accuracy_rate}%")
```

#### Test Capacity Forecasting
```python
from datetime import datetime, timedelta

# Forecast capacity needs for next week
forecast_date = datetime.utcnow() + timedelta(days=7)

forecast = await service.forecast_capacity_needs(
    warehouse_id="warehouse-001",
    forecast_date=forecast_date,
    expected_orders=5000,
    expected_units=50000
)

print(f"Required employees: {forecast.required_employees}")
print(f"Employee gap: {forecast.employee_gap}")
print(f"Required equipment: {forecast.required_equipment}")
print(f"Equipment gap: {forecast.equipment_gap}")
print(f"Required space: {forecast.required_space_sqft} sqft")
print("\nRecommendations:")
for rec in forecast.recommendations:
    print(f"  - {rec}")
```

#### Test Performance KPIs
```python
from datetime import datetime, timedelta

# Get performance KPIs for the last month
period_end = datetime.utcnow()
period_start = period_end - timedelta(days=30)

kpis = await service.get_performance_kpis(
    "warehouse-001",
    period_start,
    period_end
)

print(f"Order fill rate: {kpis.order_fill_rate}%")
print(f"On-time delivery: {kpis.on_time_delivery_rate}%")
print(f"Order accuracy: {kpis.order_accuracy}%")
print(f"Picks per labor hour: {kpis.picks_per_labor_hour}")
print(f"Cost per order: ${kpis.cost_per_order}")
print(f"Storage utilization: {kpis.storage_utilization}%")
print(f"Incident rate: {kpis.incident_rate}")
```

---

## Integration Testing

### End-to-End Order Flow

```bash
# Run the complete order flow test
python3 tests/test_complete_order_flow.py
```

This test will:
1. Create a product with variants
2. Add product to cart
3. Place an order
4. Process payment
5. Reserve inventory
6. Create shipment
7. Track delivery
8. Handle returns (if needed)

### Multi-Agent Communication Test

```bash
# Test inter-agent communication via Kafka
python3 tests/test_agent_communication.py
```

---

## Performance Testing

### Load Testing

```bash
# Test with 100 concurrent orders
python3 tests/load_test.py --orders 100 --concurrent 10

# Test warehouse throughput
python3 tests/test_warehouse_throughput.py --duration 3600  # 1 hour
```

### Stress Testing

```bash
# Stress test the system
python3 tests/stress_test.py --max-load 1000
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart PostgreSQL
docker restart postgres

# Check connection
psql -h localhost -U multi_agent_user -d multi_agent_ecommerce -c "SELECT 1;"
```

#### Kafka Not Available
```bash
# Check Kafka status
docker ps | grep kafka

# Restart Kafka and Zookeeper
docker-compose restart zookeeper kafka

# Wait 30 seconds for Kafka to fully start
sleep 30

# Verify topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

#### Agent Not Starting
```bash
# Check logs
docker logs <agent-container-name>

# Check if all dependencies are running
./launch.sh --status

# Restart specific agent
docker-compose restart <agent-name>
```

#### Import Errors
```bash
# Reinstall the package
pip install -e .

# Verify installation
python3 -c "import agents; print('Success')"
```

### Debugging Tips

1. **Enable Debug Logging**
   ```python
   import structlog
   structlog.configure(
       wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG)
   )
   ```

2. **Check Agent Health**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Monitor Kafka Messages**
   ```bash
   docker exec -it kafka kafka-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic order_events \
     --from-beginning
   ```

4. **Query Database Directly**
   ```bash
   psql -h localhost -U multi_agent_user -d multi_agent_ecommerce
   ```

---

## Automated Testing

### Run All Tests
```bash
# Run complete test suite
pytest tests/ -v --cov=agents --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Continuous Integration
The repository includes GitHub Actions workflows for automated testing on every push.

---

## Test Data

### Sample Test Data
The database migrations include sample data for testing:
- 2 warehouses
- 4 employees
- 4 equipment items
- Sample capacity metrics

### Generate More Test Data
```bash
# Generate realistic test data
python3 scripts/generate_test_data.py --orders 1000 --products 500
```

---

## Validation Checklist

Use this checklist to validate all features:

- [ ] All services import successfully
- [ ] Database migrations run without errors
- [ ] Kafka topics are created
- [ ] Product variants can be created and retrieved
- [ ] Product categories work with hierarchy
- [ ] SEO generation works correctly
- [ ] Product bundles calculate prices correctly
- [ ] Product attributes enable filtering
- [ ] Order cancellations process correctly
- [ ] Partial shipments track properly
- [ ] Saga orchestration handles failures
- [ ] Warehouse capacity metrics are accurate
- [ ] Throughput calculations are correct
- [ ] Capacity forecasts provide recommendations
- [ ] Performance KPIs calculate properly
- [ ] All agents communicate via Kafka
- [ ] Dashboard displays data correctly
- [ ] API endpoints respond correctly
- [ ] Error handling works as expected
- [ ] Logging captures important events

---

## Next Steps

After completing testing:

1. Review the [CODE_REVIEW_REPORT.md](CODE_REVIEW_REPORT.md) for code quality insights
2. Check [IMPROVEMENT_RECOMMENDATIONS.md](IMPROVEMENT_RECOMMENDATIONS.md) for enhancement suggestions
3. Read [FEATURES_IMPLEMENTED_README.md](FEATURES_IMPLEMENTED_README.md) for feature documentation
4. Consult [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production deployment

---

## Support

For issues or questions:
- Check the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide
- Review [GitHub Issues](https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce/issues)
- Consult the [COMPLETE_STARTUP_GUIDE.md](COMPLETE_STARTUP_GUIDE.md)

---

**Last Updated:** October 2025  
**Version:** 2.0

