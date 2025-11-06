# Feature 8: International Shipping Support

## Overview
Comprehensive international shipping system that handles customs documentation, duty and tax calculation, multi-currency support, and compliance management for cross-border e-commerce operations.

## Business Requirements

### 1. Customs Documentation
- Commercial invoice generation
- Customs declaration forms
- Certificate of origin
- Packing list
- Harmonized System (HS) code management
- Export documentation
- Regulatory compliance documents

### 2. Duty and Tax Calculation
- Import duty calculation by country
- Value Added Tax (VAT) calculation
- Goods and Services Tax (GST)
- Tariff classification
- De minimis thresholds
- Duty-free allowances
- Tax exemptions and special cases

### 3. International Carrier Integration
- DHL Express international
- FedEx International
- UPS Worldwide
- USPS International
- Regional carriers (Royal Mail, Canada Post, etc.)
- Rate comparison across carriers
- Transit time estimation

### 4. Multi-Currency Support
- Real-time exchange rates
- Currency conversion
- Multi-currency pricing
- Payment processing in local currency
- Currency hedging options
- Historical exchange rate tracking

### 5. Address Validation
- International address formats
- Postal code validation
- Country-specific requirements
- Address standardization
- Delivery restrictions by country
- PO Box and military address handling

### 6. Compliance Management
- Export control regulations
- Restricted/prohibited items by country
- Sanctions screening
- Trade compliance rules
- Country-specific regulations
- Documentation requirements

### 7. Landed Cost Calculation
- Product cost
- Shipping cost
- Insurance
- Duties and taxes
- Handling fees
- Total landed cost display

## Technical Requirements

### Database Schema

#### international_shipments
- Shipment details for international orders
- Origin and destination countries
- Customs information
- Documentation status

#### customs_documents
- Generated customs documents
- Document type and format
- Filing status
- Regulatory compliance

#### hs_codes
- Harmonized System codes
- Product classifications
- Duty rates by country
- Restrictions and regulations

#### duty_rates
- Import duty rates by country and HS code
- VAT/GST rates
- Special tariffs
- Effective dates

#### exchange_rates
- Currency exchange rates
- Historical rates
- Rate source and timestamp
- Base currency

#### country_regulations
- Country-specific shipping rules
- Restricted items
- Documentation requirements
- De minimis thresholds

#### landed_costs
- Calculated landed costs
- Cost breakdown
- Currency conversions
- Calculation timestamp

### API Endpoints

#### Customs & Documentation
1. `POST /api/international/customs/invoice` - Generate commercial invoice
2. `POST /api/international/customs/declaration` - Create customs declaration
3. `GET /api/international/customs/documents/{shipment_id}` - Get documents
4. `POST /api/international/customs/certificate-origin` - Generate certificate

#### Duty & Tax Calculation
5. `POST /api/international/duty/calculate` - Calculate duties and taxes
6. `GET /api/international/duty/rates` - Get duty rates by country/HS code
7. `POST /api/international/landed-cost` - Calculate total landed cost
8. `GET /api/international/vat-rates` - Get VAT rates by country

#### HS Codes
9. `GET /api/international/hs-codes/search` - Search HS codes
10. `GET /api/international/hs-codes/{code}` - Get HS code details
11. `POST /api/international/hs-codes/classify` - Classify product

#### Currency
12. `GET /api/international/exchange-rates` - Get current exchange rates
13. `POST /api/international/currency/convert` - Convert currency
14. `GET /api/international/exchange-rates/history` - Historical rates

#### Compliance
15. `POST /api/international/compliance/check` - Check compliance
16. `GET /api/international/restrictions/{country}` - Get country restrictions
17. `POST /api/international/sanctions/screen` - Screen for sanctions

#### Shipping
18. `POST /api/international/rates` - Get international shipping rates
19. `POST /api/international/label` - Generate international label
20. `GET /api/international/transit-time` - Estimate transit time

### Business Logic

#### Duty Calculation
```python
def calculate_duty(product_value, hs_code, destination_country, origin_country):
    # Get duty rate for HS code and country
    duty_rate = get_duty_rate(hs_code, destination_country)
    
    # Check for trade agreements (e.g., USMCA, EU)
    if has_trade_agreement(origin_country, destination_country):
        duty_rate = get_preferential_rate(hs_code, origin_country, destination_country)
    
    # Calculate duty
    duty_amount = product_value * (duty_rate / 100)
    
    # Check de minimis threshold
    de_minimis = get_de_minimis_threshold(destination_country)
    if product_value < de_minimis:
        duty_amount = 0
    
    return {
        "duty_rate": duty_rate,
        "duty_amount": duty_amount,
        "de_minimis_threshold": de_minimis,
        "duty_applied": duty_amount > 0
    }
```

#### VAT/GST Calculation
```python
def calculate_vat(product_value, duty_amount, destination_country):
    # Get VAT rate for country
    vat_rate = get_vat_rate(destination_country)
    
    # VAT base = product value + duty + shipping
    vat_base = product_value + duty_amount
    
    # Calculate VAT
    vat_amount = vat_base * (vat_rate / 100)
    
    # Check VAT exemptions
    if is_vat_exempt(destination_country, product_value):
        vat_amount = 0
    
    return {
        "vat_rate": vat_rate,
        "vat_base": vat_base,
        "vat_amount": vat_amount
    }
```

#### Landed Cost Calculation
```python
def calculate_landed_cost(order):
    # Product cost
    product_cost = order.subtotal
    
    # Shipping cost
    shipping_cost = calculate_international_shipping(
        order.origin_country,
        order.destination_country,
        order.weight,
        order.dimensions
    )
    
    # Insurance (typically 1-3% of product value)
    insurance = product_cost * 0.02
    
    # Duty
    duty = calculate_duty(
        product_cost,
        order.hs_code,
        order.destination_country,
        order.origin_country
    )
    
    # VAT/GST
    vat = calculate_vat(
        product_cost,
        duty['duty_amount'],
        order.destination_country
    )
    
    # Handling fees
    handling_fee = 10.00  # Flat fee or percentage
    
    # Total landed cost
    total_landed_cost = (
        product_cost +
        shipping_cost +
        insurance +
        duty['duty_amount'] +
        vat['vat_amount'] +
        handling_fee
    )
    
    return {
        "product_cost": product_cost,
        "shipping_cost": shipping_cost,
        "insurance": insurance,
        "duty": duty['duty_amount'],
        "vat": vat['vat_amount'],
        "handling_fee": handling_fee,
        "total_landed_cost": total_landed_cost,
        "breakdown": {
            "product_percentage": (product_cost / total_landed_cost) * 100,
            "shipping_percentage": (shipping_cost / total_landed_cost) * 100,
            "duties_taxes_percentage": ((duty['duty_amount'] + vat['vat_amount']) / total_landed_cost) * 100
        }
    }
```

#### Commercial Invoice Generation
```python
def generate_commercial_invoice(shipment_id):
    shipment = get_shipment(shipment_id)
    
    invoice_data = {
        "invoice_number": generate_invoice_number(),
        "invoice_date": datetime.now(),
        "shipper": {
            "name": shipment.shipper_name,
            "address": shipment.shipper_address,
            "country": shipment.origin_country,
            "tax_id": shipment.shipper_tax_id
        },
        "consignee": {
            "name": shipment.consignee_name,
            "address": shipment.consignee_address,
            "country": shipment.destination_country,
            "tax_id": shipment.consignee_tax_id
        },
        "items": [],
        "totals": {
            "subtotal": 0,
            "shipping": shipment.shipping_cost,
            "insurance": shipment.insurance,
            "total": 0
        },
        "terms": "DDP",  # Delivered Duty Paid
        "reason_for_export": "Sale",
        "currency": shipment.currency
    }
    
    # Add line items
    for item in shipment.items:
        invoice_data["items"].append({
            "description": item.description,
            "hs_code": item.hs_code,
            "country_of_origin": item.origin_country,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.quantity * item.unit_price,
            "weight": item.weight
        })
        invoice_data["totals"]["subtotal"] += item.quantity * item.unit_price
    
    invoice_data["totals"]["total"] = (
        invoice_data["totals"]["subtotal"] +
        invoice_data["totals"]["shipping"] +
        invoice_data["totals"]["insurance"]
    )
    
    # Generate PDF
    pdf = generate_invoice_pdf(invoice_data)
    
    # Save document
    save_customs_document(shipment_id, "commercial_invoice", pdf)
    
    return invoice_data
```

### Performance Targets

- **Duty Calculation**: < 1 second
- **Landed Cost Calculation**: < 2 seconds
- **Document Generation**: < 5 seconds
- **Rate Shopping**: < 3 seconds for 5 carriers
- **Currency Conversion**: < 500ms

### Integration Points

- **Carrier APIs**: DHL, FedEx, UPS for international shipping
- **Customs APIs**: Electronic customs filing systems
- **Exchange Rate APIs**: Real-time currency data
- **HS Code Database**: Product classification
- **Compliance Databases**: Sanctions and restrictions

## Success Metrics

### Operational KPIs
- Customs clearance success rate: > 98%
- Document generation accuracy: > 99%
- Duty calculation accuracy: > 99%
- Average customs clearance time: < 24 hours

### Business KPIs
- International order conversion rate: > 15%
- Landed cost transparency: 100% of orders
- Customs delay rate: < 2%
- International shipping cost optimization: > 10%

### User Experience KPIs
- Landed cost display accuracy: > 99%
- Checkout completion rate: > 70%
- Customer satisfaction with international shipping: > 4.0/5.0

## Implementation Priority

**Phase 1 (MVP):**
1. Basic duty and VAT calculation
2. Simple commercial invoice generation
3. Multi-currency support
4. International carrier integration
5. Landed cost calculator

**Phase 2 (Enhanced):**
6. HS code classification
7. Customs declaration automation
8. Compliance checking
9. Address validation
10. Certificate of origin

**Phase 3 (Advanced):**
11. Real-time customs tracking
12. Automated duty payment
13. Trade agreement optimization
14. Advanced compliance screening
15. Multi-language documentation

## Testing Requirements

### Unit Tests
- Duty calculation logic
- VAT calculation
- Currency conversion
- Document generation

### Integration Tests
- End-to-end international order flow
- Customs document workflow
- Carrier API integration
- Exchange rate updates

### Performance Tests
- Bulk landed cost calculations
- Concurrent document generation
- Rate shopping performance

## Dependencies

- International carrier accounts (DHL, FedEx, UPS)
- Exchange rate API (e.g., Open Exchange Rates)
- HS code database
- Country regulations database
- PDF generation library

## Risks & Mitigation

### Risk 1: Regulatory Changes
**Mitigation**: Regular database updates, compliance monitoring, legal review

### Risk 2: Duty Calculation Errors
**Mitigation**: Multiple validation sources, manual review option, error tracking

### Risk 3: Currency Fluctuations
**Mitigation**: Real-time rates, rate locking at checkout, hedging strategies

### Risk 4: Customs Delays
**Mitigation**: Proactive documentation, carrier partnerships, tracking alerts

## Future Enhancements

- Automated customs brokerage
- Duty drawback management
- Free trade zone optimization
- Blockchain for customs
- AI-powered HS code classification
- Predictive customs clearance times
- Dynamic duty optimization
- Green customs initiatives
