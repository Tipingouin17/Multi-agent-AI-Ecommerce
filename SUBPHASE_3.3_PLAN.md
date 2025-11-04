# Sub-phase 3.3 Plan: Store Settings & Configuration

**Priority:** High  
**Estimated Pages:** 8-10  
**Estimated Duration:** 2-3 weeks  
**Dependencies:** Sub-phases 3.1 and 3.2 complete

---

## Overview

Sub-phase 3.3 focuses on building the essential store configuration and settings pages that enable merchants to set up and manage their e-commerce operations. These pages provide the foundational configuration required for a store to function properly, including general settings, payment processing, shipping zones, tax rules, and integrations.

---

## Objectives

The primary objective of Sub-phase 3.3 is to deliver a comprehensive store configuration system that allows merchants to customize their store operations according to their business needs. This includes setting up payment gateways, defining shipping zones and rates, configuring tax rules, managing email templates, and integrating with third-party services.

---

## Planned Pages

### 1. Store Settings (General)

**Route:** `/settings/general`  
**Priority:** Critical  
**Complexity:** Medium

This page serves as the central hub for basic store configuration. Merchants can set their store name, logo, contact information, business address, currency, timezone, and language preferences. The page also includes options for store status (active/maintenance mode) and basic SEO settings like meta description and social media links.

**Key Features:**
- Store identity configuration (name, logo, tagline)
- Contact information (email, phone, address)
- Regional settings (currency, timezone, language)
- Store status toggle (active/maintenance)
- Basic SEO settings
- Social media links

**API Endpoints:**
- `GET /api/settings/general` - Retrieve general settings
- `PUT /api/settings/general` - Update general settings
- `POST /api/settings/logo` - Upload store logo

---

### 2. Payment Settings

**Route:** `/settings/payments`  
**Priority:** Critical  
**Complexity:** High

The payment settings page allows merchants to configure and manage their payment gateways. This includes integration with popular payment processors like Stripe, PayPal, Square, and others. Merchants can enable multiple payment methods, configure API credentials, set up payment processing rules, and manage payout schedules.

**Key Features:**
- Payment gateway integration (Stripe, PayPal, Square, etc.)
- Multiple payment method support
- API credential management
- Payment processing rules
- Payout schedule configuration
- Test mode toggle
- Payment method ordering
- Currency conversion settings

**API Endpoints:**
- `GET /api/settings/payments` - List payment configurations
- `POST /api/settings/payments` - Add payment gateway
- `PUT /api/settings/payments/{id}` - Update payment gateway
- `DELETE /api/settings/payments/{id}` - Remove payment gateway
- `POST /api/settings/payments/{id}/test` - Test payment gateway

---

### 3. Shipping Zones & Rates

**Route:** `/settings/shipping`  
**Priority:** Critical  
**Complexity:** Very High

This page enables merchants to define geographic shipping zones and configure shipping rates for each zone. Merchants can create zones based on countries, states, or postal codes, then assign shipping methods with rates based on weight, price, or flat rate. The page supports multiple carriers and custom shipping rules.

**Key Features:**
- Geographic zone creation (country, state, postal code)
- Multiple shipping methods per zone
- Rate calculation options (weight-based, price-based, flat rate)
- Carrier integration (USPS, FedEx, UPS, DHL)
- Free shipping thresholds
- Handling fees
- Delivery time estimates
- Zone priority and fallback rules

**API Endpoints:**
- `GET /api/settings/shipping/zones` - List shipping zones
- `POST /api/settings/shipping/zones` - Create shipping zone
- `PUT /api/settings/shipping/zones/{id}` - Update shipping zone
- `DELETE /api/settings/shipping/zones/{id}` - Delete shipping zone
- `GET /api/settings/shipping/methods` - List shipping methods
- `POST /api/settings/shipping/methods` - Create shipping method

---

### 4. Tax Configuration

**Route:** `/settings/taxes`  
**Priority:** High  
**Complexity:** Very High

The tax configuration page allows merchants to set up tax rules based on jurisdiction. This includes sales tax, VAT, GST, and other tax types. Merchants can define tax rates by country, state, or postal code, configure tax-inclusive or tax-exclusive pricing, and set up automatic tax calculation rules.

**Key Features:**
- Tax rate configuration by jurisdiction
- Multiple tax types (sales tax, VAT, GST)
- Tax-inclusive vs tax-exclusive pricing
- Automatic tax calculation
- Tax exemption rules
- Digital goods tax handling
- Tax reporting configuration
- Integration with tax calculation services (TaxJar, Avalara)

**API Endpoints:**
- `GET /api/settings/taxes` - List tax configurations
- `POST /api/settings/taxes` - Create tax rule
- `PUT /api/settings/taxes/{id}` - Update tax rule
- `DELETE /api/settings/taxes/{id}` - Delete tax rule
- `POST /api/settings/taxes/calculate` - Test tax calculation

---

### 5. Email Templates

**Route:** `/settings/emails`  
**Priority:** High  
**Complexity:** High

This page provides a template editor for transactional emails sent by the system. Merchants can customize email templates for order confirmation, shipping notification, password reset, welcome emails, and more. The editor supports HTML with variable substitution and preview functionality.

**Key Features:**
- Template library (order, shipping, account, marketing)
- HTML email editor with variables
- Template preview with sample data
- Default template restoration
- Email sender configuration
- SMTP settings
- Email testing functionality
- Template versioning

**API Endpoints:**
- `GET /api/settings/emails/templates` - List email templates
- `GET /api/settings/emails/templates/{id}` - Get template
- `PUT /api/settings/emails/templates/{id}` - Update template
- `POST /api/settings/emails/templates/{id}/preview` - Preview template
- `POST /api/settings/emails/templates/{id}/test` - Send test email
- `POST /api/settings/emails/templates/{id}/reset` - Reset to default

---

### 6. Notification Settings

**Route:** `/settings/notifications`  
**Priority:** Medium  
**Complexity:** Medium

The notification settings page allows merchants to configure which notifications they receive and through which channels (email, SMS, push). Merchants can set up alerts for new orders, low inventory, customer inquiries, payment issues, and system events.

**Key Features:**
- Notification channel configuration (email, SMS, push)
- Event-based notification rules
- Notification frequency settings
- Quiet hours configuration
- Notification recipients management
- Custom notification rules
- Notification history
- Test notification functionality

**API Endpoints:**
- `GET /api/settings/notifications` - Get notification settings
- `PUT /api/settings/notifications` - Update notification settings
- `POST /api/settings/notifications/test` - Send test notification
- `GET /api/settings/notifications/history` - Notification history

---

### 7. Domain & SSL

**Route:** `/settings/domain`  
**Priority:** Medium  
**Complexity:** High

This page enables merchants to configure custom domains for their store and manage SSL certificates. Merchants can add custom domains, verify ownership, configure DNS settings, and enable HTTPS. The page also provides SSL certificate status and renewal information.

**Key Features:**
- Custom domain configuration
- Domain verification process
- DNS configuration guidance
- SSL certificate management
- Auto-renewal settings
- HTTPS enforcement
- Domain redirect rules
- Subdomain configuration

**API Endpoints:**
- `GET /api/settings/domains` - List configured domains
- `POST /api/settings/domains` - Add custom domain
- `PUT /api/settings/domains/{id}` - Update domain settings
- `DELETE /api/settings/domains/{id}` - Remove domain
- `POST /api/settings/domains/{id}/verify` - Verify domain ownership
- `GET /api/settings/domains/{id}/ssl` - Get SSL certificate status

---

### 8. API Keys & Webhooks

**Route:** `/settings/api`  
**Priority:** Medium  
**Complexity:** High

This developer-focused page provides API key management and webhook configuration. Merchants can generate API keys for integrations, configure webhook endpoints for real-time event notifications, and view API usage statistics. The page includes security features like key rotation and IP whitelisting.

**Key Features:**
- API key generation and management
- Key permissions and scopes
- Webhook endpoint configuration
- Event subscription management
- Webhook retry settings
- API usage statistics
- Request logs and debugging
- IP whitelisting
- Key rotation functionality

**API Endpoints:**
- `GET /api/settings/api-keys` - List API keys
- `POST /api/settings/api-keys` - Generate API key
- `DELETE /api/settings/api-keys/{id}` - Revoke API key
- `GET /api/settings/webhooks` - List webhooks
- `POST /api/settings/webhooks` - Create webhook
- `PUT /api/settings/webhooks/{id}` - Update webhook
- `DELETE /api/settings/webhooks/{id}` - Delete webhook
- `POST /api/settings/webhooks/{id}/test` - Test webhook

---

## Technical Considerations

### UI Components Required

Several specialized UI components will be needed for Sub-phase 3.3 that were not required in previous sub-phases. These include a zone builder for shipping configuration with map visualization, a tax rate calculator with jurisdiction lookup, an HTML email editor with variable insertion, a domain verification wizard with DNS guidance, and an API key generator with security features.

### Third-party Integrations

Sub-phase 3.3 will require integration with several third-party services including payment gateways (Stripe, PayPal, Square), shipping carriers (USPS, FedEx, UPS, DHL), tax calculation services (TaxJar, Avalara), email delivery services (SendGrid, Mailgun), and domain registrars for DNS configuration.

### Security Considerations

Configuration pages handle sensitive information including payment gateway credentials, API keys, and SMTP passwords. All sensitive data must be encrypted at rest and in transit. API keys should support scoping and permissions to limit access. Webhook endpoints should include signature verification to prevent unauthorized requests.

### Data Validation

Configuration data must be thoroughly validated to prevent errors. Payment gateway credentials should be tested before saving. Shipping zones must have valid geographic data. Tax rates must be numeric and within reasonable ranges. Email templates must be valid HTML. Domain names must follow DNS standards.

---

## Implementation Strategy

### Phase 1: Core Settings (Week 1)

The first week will focus on implementing the core settings pages including Store Settings (General), Payment Settings, and Shipping Zones & Rates. These are the most critical pages that merchants need to get their store operational.

### Phase 2: Configuration & Compliance (Week 2)

The second week will implement Tax Configuration, Email Templates, and Notification Settings. These pages are important for compliance and customer communication but are not blocking for basic store operations.

### Phase 3: Advanced Features (Week 3)

The third week will implement Domain & SSL and API Keys & Webhooks. These are more advanced features that technical merchants will need for custom integrations and professional store setup.

---

## Testing Requirements

### Functional Testing

Each configuration page must be tested to ensure that settings are saved correctly and applied to the store. Payment gateway integration must be tested with test transactions. Shipping rate calculations must be verified with sample orders. Tax calculations must be validated against known tax rates.

### Integration Testing

Configuration changes must be tested to ensure they propagate correctly to other parts of the system. For example, changing payment settings should update the checkout page. Modifying shipping zones should affect shipping rate calculations at checkout. Email template changes should be reflected in transactional emails.

### Security Testing

API key generation and management must be tested for security vulnerabilities. Webhook signature verification must be validated. Payment gateway credential storage must be encrypted. Access controls must prevent unauthorized configuration changes.

---

## Success Criteria

Sub-phase 3.3 will be considered successful when all planned pages are implemented with full functionality, all API endpoints are integrated and tested, configuration changes are properly persisted and applied, third-party integrations are functional, and comprehensive documentation is provided.

---

## Risks & Mitigation

### Integration Complexity

Risk: Third-party integrations may be more complex than anticipated. Mitigation: Start with the most common payment gateways and shipping carriers. Provide clear documentation for merchants to complete integration setup.

### Data Migration

Risk: Existing stores may have configuration data that needs to be migrated. Mitigation: Provide import/export functionality for configuration data. Include validation to ensure data integrity during migration.

### Performance

Risk: Complex configuration queries may impact performance. Mitigation: Implement caching for frequently accessed configuration data. Optimize database queries with proper indexing.

---

## Conclusion

Sub-phase 3.3 represents a critical milestone in the merchant portal development. These configuration pages are essential for merchants to set up and operate their stores effectively. The implementation will require careful attention to security, data validation, and third-party integrations. Upon completion, merchants will have a comprehensive configuration system that rivals industry-leading platforms.

---

**Plan Created:** November 4, 2025  
**Target Completion:** 2-3 weeks  
**Dependencies:** Sub-phases 3.1 and 3.2 complete  
**Next Sub-phase:** 3.4 (Financial Reports & Analytics)
