# Domain 1: User Management & Admin - Enhanced Content

## Overview
User Management & Admin provides comprehensive identity, access control, and administrative capabilities for all marketplace stakeholders including customers (15M active users), vendors (50K active), platform administrators (500), and support staff (200). The system processes 2M authentication requests/day with 99.99% uptime and sub-200ms response time.

---

## For Marketplace Operators

### 1. Multi-Role User Management Architecture

**User Types & Roles**:
```
User Hierarchy (4 Main Types, 25+ Roles):

├── Customers (15M active users)
│   ├── Guest (unregistered, limited access)
│   ├── Registered (basic account, full shopping)
│   ├── Premium (loyalty program member, exclusive benefits)
│   ├── Business (B2B customer, bulk ordering, net terms)
│   └── VIP (high-value customer, dedicated support, priority)
│
├── Vendors (50K active vendors)
│   ├── Seller (individual seller, basic features)
│   ├── Merchant (small business, advanced features)
│   ├── Brand (official brand store, premium placement)
│   ├── Enterprise (large vendor, custom terms, API access)
│   └── Fulfillment Partner (FaaS provider, warehouse access)
│
├── Platform Staff (700 total)
│   ├── Super Admin (full system access, 5 users)
│   ├── Admin (platform management, 50 users)
│   ├── Operations Manager (fulfillment, logistics, 100 users)
│   ├── Customer Support (tier 1-3, 200 users)
│   ├── Vendor Success Manager (vendor support, 150 users)
│   ├── Content Moderator (review content, 80 users)
│   ├── Fraud Analyst (investigate fraud, 40 users)
│   ├── Finance Analyst (billing, payouts, 30 users)
│   ├── Data Analyst (reports, insights, 25 users)
│   └── Developer (API, integrations, 20 users)
│
└── External Partners (2K active)
    ├── Shipping Carrier (tracking, label generation)
    ├── Payment Gateway (payment processing)
    ├── Marketing Agency (campaign management)
    ├── Logistics Provider (3PL, warehouse)
    └── Technology Partner (integrations, APIs)

Role Permissions Matrix:
- 25 roles × 150 permissions = 3,750 permission combinations
- Permission types: Read, Write, Delete, Execute, Approve
- Permission scopes: Own data, Team data, All data
- Permission inheritance: Role hierarchy with override capability

Technology Stack:
- Identity Provider: Auth0, Okta (SSO, MFA)
- Directory Service: Active Directory, LDAP
- Database: PostgreSQL 15 (user profiles, permissions)
- Cache: Redis (session management, permission cache)
- Audit: Elasticsearch (user activity logs)
```

**Performance Metrics**:
- **Total Users**: 15.7M (15M customers, 50K vendors, 700 staff, 2K partners)
- **Active Users/Day**: 850K (5.4% of total)
- **Authentication Requests/Day**: 2M (2.4 requests/active user)
- **Auth Success Rate**: 99.95% (5% failed due to wrong password, MFA)
- **Auth Latency**: p50: 120ms, p95: 280ms, p99: 500ms
- **Session Duration**: 30 days (remember me), 24 hours (default)
- **System Uptime**: 99.99% (target: 99.95%)

---

### 2. Permission & Access Control (RBAC + ABAC)

**Role-Based Access Control (RBAC)**:
```
RBAC Implementation:

Permission Structure:
- Resource: What (e.g., products, orders, customers)
- Action: How (e.g., read, write, delete, approve)
- Scope: Where (e.g., own, team, all)

Example Permissions:
1. products:read:own
   - Read own products (vendor can view their products)
2. orders:write:team
   - Modify team orders (manager can update team's orders)
3. customers:delete:all
   - Delete any customer (admin can delete any customer)
4. reports:execute:own
   - Run own reports (analyst can run their saved reports)
5. payouts:approve:all
   - Approve any payout (finance manager can approve all payouts)

Role Assignment:
- Users assigned to roles (many-to-many)
- Roles assigned to permissions (many-to-many)
- Dynamic role assignment (based on user attributes, e.g., vendor tier)
- Temporary role elevation (time-limited, for specific tasks)

Permission Evaluation:
1. User requests action (e.g., view order #12345)
2. System checks user roles (e.g., Vendor, Premium)
3. System retrieves role permissions (e.g., orders:read:own)
4. System evaluates scope (e.g., is order #12345 owned by user?)
5. System grants or denies access (e.g., granted if owned, denied if not)
6. Latency: <10ms (cached permissions, fast evaluation)

Permission Cache:
- Cache user permissions in Redis (5-minute TTL)
- Invalidate cache on role/permission changes
- Cache hit rate: 95% (reduces database load)
```

**Attribute-Based Access Control (ABAC)**:
```
ABAC for Dynamic Permissions:

Attributes Used:
- User attributes: Role, tier, location, department, tenure
- Resource attributes: Owner, status, sensitivity, category
- Environment attributes: Time, IP address, device, location
- Action attributes: Type, risk level, approval required

Example ABAC Rules:
1. Allow if:
   - User.role = "Vendor"
   - AND Resource.owner = User.id
   - AND Action = "read" OR "write"
   - Result: Vendor can read/write their own resources

2. Allow if:
   - User.role = "Customer Support"
   - AND User.tier = "Tier 2" OR "Tier 3"
   - AND Resource.type = "Order"
   - AND Action = "refund"
   - AND Order.value < €500
   - Result: Tier 2/3 support can refund orders <€500

3. Deny if:
   - Environment.time = "Outside business hours"
   - AND User.department != "Operations"
   - AND Action.risk_level = "High"
   - Result: High-risk actions blocked outside business hours (except Operations)

4. Require MFA if:
   - Action = "delete" OR "approve"
   - OR Resource.sensitivity = "High"
   - OR Environment.location != User.usual_location
   - Result: MFA required for sensitive actions or unusual locations

ABAC Evaluation Engine:
- Policy Decision Point (PDP): Evaluates rules
- Policy Enforcement Point (PEP): Enforces decisions
- Policy Information Point (PIP): Retrieves attributes
- Policy Administration Point (PAP): Manages policies
- Latency: <50ms (rule evaluation + attribute retrieval)
```

---

### 3. User Authentication & Security

**Multi-Factor Authentication (MFA)**:
```
MFA Implementation:

Supported MFA Methods:
1. SMS OTP (One-Time Password)
   - 6-digit code sent via SMS
   - Valid for 5 minutes
   - Adoption: 35% of users
   - Cost: €0.05 per SMS

2. Email OTP
   - 6-digit code sent via email
   - Valid for 10 minutes
   - Adoption: 25% of users
   - Cost: €0.001 per email

3. Authenticator App (TOTP)
   - Google Authenticator, Authy, Microsoft Authenticator
   - 6-digit code, rotates every 30 seconds
   - Adoption: 30% of users
   - Cost: Free

4. Biometric (Mobile App)
   - Face ID, Touch ID, fingerprint
   - Device-based authentication
   - Adoption: 8% of users (mobile app only)
   - Cost: Free

5. Hardware Token (U2F/FIDO2)
   - YubiKey, Titan Security Key
   - USB/NFC-based authentication
   - Adoption: 2% of users (enterprise vendors, admins)
   - Cost: €40-60 per key (one-time)

MFA Enforcement:
- Required for: Admins (100%), Vendors (80%), High-value customers (opt-in)
- Optional for: Regular customers (opt-in, 35% adoption)
- Bypass: Trusted devices (30-day remember), low-risk actions
- Fallback: Backup codes (10 codes, one-time use)

MFA Performance:
- MFA Challenge Rate: 15% of logins (85% use trusted devices)
- MFA Success Rate: 92% (8% fail due to timeout, wrong code)
- MFA Latency: p95 <3 seconds (user enters code)
```

**Single Sign-On (SSO)**:
```
SSO Implementation:

Supported Protocols:
1. SAML 2.0 (Security Assertion Markup Language)
   - Enterprise SSO (Okta, Azure AD, Google Workspace)
   - Use case: Vendor employees, platform staff
   - Adoption: 5,000 users (10% of vendors, 100% of staff)

2. OAuth 2.0 / OpenID Connect
   - Social login (Google, Facebook, Apple, LinkedIn)
   - Use case: Customer login, quick registration
   - Adoption: 4.5M users (30% of customers)

3. LDAP (Lightweight Directory Access Protocol)
   - Legacy enterprise systems
   - Use case: Large enterprise vendors
   - Adoption: 500 users (1% of vendors)

SSO Providers:
- Enterprise: Okta (60%), Azure AD (30%), Google Workspace (10%)
- Social: Google (50%), Facebook (30%), Apple (15%), LinkedIn (5%)

SSO Flow (SAML):
1. User clicks "Login with SSO"
2. Marketplace redirects to Identity Provider (IdP)
3. User authenticates with IdP (username/password, MFA)
4. IdP generates SAML assertion (signed token)
5. IdP redirects user back to marketplace with assertion
6. Marketplace validates assertion (signature, expiration)
7. Marketplace creates session for user
8. User logged in (no password stored on marketplace)

SSO Benefits:
- Reduced password fatigue (one password for all apps)
- Centralized access control (disable user in IdP, revokes all access)
- Improved security (IdP handles authentication, MFA)
- Faster onboarding (auto-provision users from IdP)

SSO Performance:
- SSO Login Time: 3-5 seconds (redirect to IdP, authenticate, redirect back)
- SSO Success Rate: 98% (2% fail due to IdP issues, network)
- SSO Adoption: 4.5M users (29% of total users)
```

**Password Security**:
```
Password Policy:

Requirements:
- Minimum length: 12 characters (increased from 8 in 2024)
- Complexity: At least 3 of 4 (uppercase, lowercase, number, symbol)
- No common passwords (check against 100M leaked password database)
- No personal information (name, email, birthday)
- No reuse (last 5 passwords remembered)
- Expiration: 90 days (for admins), never (for customers/vendors)

Password Storage:
- Hashing algorithm: Argon2id (winner of Password Hashing Competition)
- Salt: 128-bit random salt (unique per password)
- Iterations: 3 (time-cost parameter)
- Memory: 64 MB (memory-cost parameter)
- Parallelism: 4 threads
- Hash time: ~500ms (intentionally slow to prevent brute-force)

Password Reset:
- Reset link sent via email (valid for 1 hour)
- Requires email verification (click link)
- Optional: SMS verification (for high-value accounts)
- Rate limit: Max 3 reset requests per hour (prevent abuse)
- Audit: All resets logged (user, timestamp, IP, device)

Compromised Password Detection:
- Check against Have I Been Pwned API (600M+ leaked passwords)
- Warn user if password found in breach
- Force reset if password compromised
- Proactive monitoring (check all passwords monthly)
```

---

### 4. User Profile Management

**Customer Profiles**:
```
Customer Profile Data:

Core Information:
- User ID: Unique identifier (UUID)
- Email: Primary email (verified)
- Phone: Mobile number (verified, optional)
- Name: First name, last name
- Birthday: Date of birth (for age verification, promotions)
- Gender: Male, Female, Other, Prefer not to say (optional)

Addresses:
- Shipping addresses (up to 10)
- Billing addresses (up to 5)
- Default address (for quick checkout)
- Address validation (Google Maps API, USPS API)

Payment Methods:
- Credit/debit cards (tokenized, up to 5)
- Digital wallets (Apple Pay, Google Pay, PayPal)
- Bank accounts (SEPA, ACH, for refunds)
- Default payment method (for one-click checkout)

Preferences:
- Language: 15 languages supported
- Currency: 28 currencies supported
- Communication: Email, SMS, push notifications (opt-in/out)
- Marketing: Newsletter, promotions, personalized offers (opt-in/out)
- Privacy: Data sharing, tracking, cookies (GDPR compliance)

Order History:
- Past orders (all-time, paginated)
- Order status (pending, shipped, delivered, returned)
- Tracking information (carrier, tracking number)
- Invoices (downloadable PDF)

Loyalty Program:
- Points balance (earn 1 point per €1 spent)
- Tier: Bronze, Silver, Gold, Platinum (based on annual spend)
- Rewards: Discounts, free shipping, exclusive access
- Expiration: Points expire after 12 months of inactivity

Wishlist & Saved Items:
- Wishlist (products to buy later)
- Saved for later (moved from cart)
- Price drop alerts (notify when price decreases)
- Back in stock alerts (notify when out-of-stock items return)

Reviews & Ratings:
- Product reviews (written, with photos)
- Vendor ratings (1-5 stars)
- Helpfulness votes (upvote/downvote reviews)
- Review moderation (flagged reviews reviewed by staff)

Profile Completeness:
- Score: 0-100% (based on filled fields)
- Benefits: Higher score = better recommendations, priority support
- Incentive: 10% discount for 100% complete profile
```

**Vendor Profiles**:
```
Vendor Profile Data:

Business Information:
- Vendor ID: Unique identifier (UUID)
- Business name: Legal name, DBA (Doing Business As)
- Business type: Sole proprietor, LLC, Corporation, Partnership
- Tax ID: VAT number (EU), EIN (US), equivalent
- Registration number: Company registration number
- Business address: Legal address, warehouse address

Contact Information:
- Primary contact: Name, email, phone
- Support contact: Customer service email, phone
- Finance contact: Billing email, phone
- Technical contact: API, integration support

Bank Account:
- Bank name, account number, routing number (for payouts)
- IBAN (EU), SWIFT/BIC (international)
- Payout schedule: Weekly, bi-weekly, monthly
- Payout method: Bank transfer, PayPal, Stripe

Product Catalog:
- Total products: Count, active, inactive, draft
- Categories: Primary categories sold
- Average price: €25.50
- Total SKUs: 1,250 (including variants)

Performance Metrics:
- Vendor tier: Bronze, Silver, Gold, Platinum (based on performance)
- Performance score: 0-100 (based on 10 metrics)
- GMV (Gross Merchandise Value): €500K/month
- Order volume: 5,000 orders/month
- On-time shipment rate: 96.5%
- Order defect rate: 0.8% (cancellations, returns, complaints)
- Customer satisfaction: 4.7/5 stars (avg rating)
- Response time: 4.2 hours (avg time to respond to customer messages)

Compliance & Verification:
- KYC status: Verified, Pending, Failed
- AML screening: Passed, Flagged, Under review
- Document verification: Business license, tax certificate, bank statement
- Insurance: Liability insurance (required for high-value products)
- Certifications: ISO, CE marking, safety certifications

Subscription & Fees:
- Subscription plan: Basic (free), Growth (€99/month), Enterprise (€499/month)
- Commission rate: 8-15% (based on tier)
- Payment processing fee: 1.4% + €0.25 (passed through)
- FaaS fees: €0.50-2.00/unit/month (storage), €2.50-8.50/order (fulfillment)

API Access:
- API key: For programmatic access
- API quota: 10K-1M calls/day (based on plan)
- Webhooks: Subscribed events (order.created, inventory.updated, etc.)
- Integration status: Shopify, WooCommerce, SAP, custom
```

---

## For Merchants/Vendors

### 1. Vendor Dashboard & Tools

**Dashboard Overview**:
```
Vendor Dashboard (Real-Time):

Key Metrics (Today):
- Sales: €1,250 (42 orders, €29.76 AOV)
- Traffic: 850 visitors (2.5% conversion rate)
- Inventory: 1,250 SKUs (95% in stock, 5% low stock)
- Messages: 8 new customer messages (avg response time: 3.2 hours)
- Reviews: 3 new reviews (4.7/5 stars avg)

Performance Score: 87/100 (Gold Tier)
├── On-time shipment: 96.5% (target: 95%)
├── Order defect rate: 0.8% (target: <1%)
├── Customer satisfaction: 4.7/5 (target: 4.5+)
├── Response time: 4.2 hours (target: <24 hours)
└── Listing quality: 92% (target: 90%)

Recent Orders (Last 10):
[Table showing order ID, customer, items, total, status, actions]

Low Stock Alerts (5 products):
- Wireless Mouse: 8 units left (reorder recommended)
- USB Cable: 12 units left
- Phone Case: 5 units left (critical)
- Laptop Stand: 15 units left
- Keyboard: 10 units left

Pending Actions (12 tasks):
- Ship 5 orders (due today)
- Respond to 8 customer messages
- Review 3 product listings (quality issues flagged)
- Update 2 out-of-stock products
- Approve 1 return request

Quick Actions:
- Add new product
- Update inventory
- Create promotion
- Download reports
- Contact support
```

**Admin Tools**:
```
Vendor Admin Tools:

Product Management:
- Bulk upload (CSV, XML, API)
- Bulk edit (price, inventory, attributes)
- Product templates (save time on similar products)
- Image editor (crop, resize, optimize)
- SEO optimizer (title, description, keywords)
- Quality checker (47-point validation)

Order Management:
- Order list (filter, sort, search)
- Order details (customer, items, shipping, payment)
- Bulk actions (mark as shipped, print labels, export)
- Order notes (internal notes, customer-facing notes)
- Refund/cancel orders

Inventory Management:
- Inventory sync (API, FTP, manual)
- Low stock alerts (email, SMS, dashboard)
- Reorder recommendations (based on sales velocity)
- Inventory reports (turnover, aging, ABC analysis)

Customer Service:
- Message inbox (customer messages, internal notes)
- Canned responses (save time on common questions)
- Order lookup (by order ID, customer email, tracking number)
- Refund/return processing

Marketing Tools:
- Promotions (discounts, coupons, flash sales)
- Sponsored products (pay-per-click advertising)
- Email campaigns (newsletters, abandoned cart)
- Social media integration (Facebook, Instagram)

Analytics & Reports:
- Sales reports (daily, weekly, monthly, custom)
- Traffic reports (visitors, conversion rate, bounce rate)
- Product performance (best sellers, slow movers)
- Customer insights (demographics, behavior, lifetime value)
- Financial reports (revenue, costs, profit, payouts)

Settings:
- Business information (name, address, tax ID)
- Bank account (for payouts)
- Shipping settings (carriers, rates, handling time)
- Return policy (return window, restocking fee)
- Notifications (email, SMS, push)
- API keys (for integrations)
- Team management (add users, assign roles)
```

---

## Technology Stack & Integration

**Core Technologies**:
- **Identity Provider**: Auth0, Okta (SSO, MFA)
- **Directory Service**: Active Directory, LDAP
- **Database**: PostgreSQL 15 (user profiles, permissions)
- **Cache**: Redis (sessions, permissions, 95% hit rate)
- **Audit**: Elasticsearch (user activity logs, 90-day retention)
- **Monitoring**: Datadog (user analytics, auth metrics)

**Security Technologies**:
- **Password Hashing**: Argon2id
- **Encryption**: AES-256 (data at rest), TLS 1.3 (data in transit)
- **MFA**: Twilio (SMS), SendGrid (email), TOTP (authenticator apps)
- **SSO**: SAML 2.0, OAuth 2.0, OpenID Connect
- **Fraud Detection**: Sift Science (account takeover, bot detection)

---

## Business Model & Pricing

**For Marketplace Operators**:
- **User Management Infrastructure**: €1.5M/year (Auth0, Okta, servers)
- **MFA Costs**: €300K/year (SMS: €250K, Email: €50K)
- **Support Costs**: €2M/year (customer support, vendor success)
- **Total Cost**: €3.8M/year

**For Merchants/Vendors**:
- **User Access**: Included in marketplace commission (no extra fee)
- **Team Members**: Free (up to 5), €10/month per additional user
- **API Access**: Included (based on subscription plan)
- **SSO**: €50/month (Enterprise plan only)

---

## Key Performance Indicators (KPIs)

**User KPIs**:
- Total Users: 15.7M
- Active Users/Day: 850K (5.4%)
- New Users/Day: 5,000
- User Retention: 65% (30-day)
- User Churn: 2% (monthly)

**Auth KPIs**:
- Auth Requests/Day: 2M
- Auth Success Rate: 99.95%
- Auth Latency: p95 <280ms
- MFA Adoption: 35% (customers), 80% (vendors), 100% (admins)
- SSO Adoption: 29% (4.5M users)

**Security KPIs**:
- Account Takeover Rate: 0.02% (300 incidents/month)
- Compromised Passwords: 0.5% (75K passwords flagged)
- Failed Login Rate: 5% (100K failed logins/day)
- Suspicious Activity: 0.1% (1,500 incidents/month)

---

## Real-World Use Cases

**Case Study 1: MFA Rollout**
- Challenge: 80% of account takeovers due to weak passwords
- Solution: Mandatory MFA for vendors, optional for customers
- Results:
  - Account takeover rate: 0.15% → 0.02% (-87%)
  - MFA adoption: 35% (customers), 80% (vendors)
  - Customer complaints: +5% (initial friction, declined over time)
  - Cost: €300K/year (SMS, email OTPs)

**Case Study 2: SSO for Enterprise Vendors**
- Challenge: Large vendors have 10-50 employees, manual user management
- Solution: SAML SSO integration with Okta, Azure AD
- Results:
  - Onboarding time: 2 days → 2 hours (-96%)
  - User management effort: 10 hours/month → 1 hour/month (-90%)
  - Vendor satisfaction: +0.8 points (4.2 → 5.0/5)
  - Adoption: 5,000 users (10% of vendors)

---

## Future Roadmap

**Q1 2026**:
- Passwordless authentication (WebAuthn, FIDO2)
- Biometric authentication (face, fingerprint, voice)
- Risk-based authentication (adaptive MFA based on risk score)

**Q2 2026**:
- Decentralized identity (blockchain-based, self-sovereign identity)
- Zero-knowledge proofs (prove identity without revealing data)
- Quantum-resistant cryptography (post-quantum algorithms)

**Q3 2026**:
- AI-powered fraud detection (account takeover, bot detection)
- Behavioral biometrics (typing patterns, mouse movements)
- Continuous authentication (re-authenticate based on behavior changes)

