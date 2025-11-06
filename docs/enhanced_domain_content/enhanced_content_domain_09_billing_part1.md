# Domain 9: Billing & Payments - Enhanced Content (Part 1)

## Overview
Billing & Payments manages all financial transactions across the marketplace, including customer payments, vendor payouts, commission calculations, refunds, and financial reporting. The system processes €2.8B in annual GMV, handling 15M transactions/year with 99.98% payment success rate and PCI DSS Level 1 compliance.

---

## For Marketplace Operators

### 1. Payment Processing Architecture

**System Design**: Multi-Payment Gateway Architecture
```
Payment Processing Layers:

├── Payment Gateway Orchestration Layer
│   ├── Primary Gateway: Stripe (70% of transactions)
│   │   - Coverage: 28 European countries, 135+ currencies
│   │   - Payment Methods: Credit/debit cards, digital wallets, BNPL
│   │   - Success Rate: 99.5% (authorization success)
│   │   - Processing Fee: 1.4% + €0.25 per transaction (EU cards)
│   │   - Settlement: T+2 days (2 days after transaction)
│   │
│   ├── Secondary Gateway: Adyen (25% of transactions)
│   │   - Coverage: Global (200+ countries)
│   │   - Payment Methods: Local payment methods (iDEAL, Bancontact, Sofort)
│   │   - Success Rate: 99.3%
│   │   - Processing Fee: 1.5% + €0.10 per transaction
│   │   - Settlement: T+1 days
│   │
│   └── Backup Gateway: PayPal (5% of transactions)
│       - Coverage: Global
│       - Payment Methods: PayPal balance, linked cards/banks
│       - Success Rate: 98.8%
│       - Processing Fee: 2.9% + €0.35 per transaction
│       - Settlement: Instant (for PayPal balance)
│
├── Smart Routing Layer
│   ├── AI-Powered Gateway Selection
│   │   - ML Model: XGBoost (98.5% accuracy)
│   │   - Input Features: Payment method, amount, country, customer history, gateway performance
│   │   - Optimization Goal: Maximize success rate (60%), minimize cost (40%)
│   │   - Latency: <20ms (real-time routing decision)
│   │
│   ├── Failover & Retry Logic
│   │   - Auto-retry on decline (up to 3 attempts with different gateways)
│   │   - Cascade routing (Stripe → Adyen → PayPal if declined)
│   │   - Success rate improvement: +2.5% (97.3% → 99.8% with retries)
│   │
│   └── Load Balancing
│       - Distribute traffic across gateways (prevent overload)
│       - Real-time capacity monitoring
│       - Dynamic routing (shift traffic if gateway issues)
│
├── Payment Method Support Layer
│   ├── Credit/Debit Cards (60% of transactions)
│   │   - Visa, Mastercard, American Express, Discover
│   │   - 3D Secure 2.0 (Strong Customer Authentication, SCA)
│   │   - Tokenization (store card tokens, not raw card numbers)
│   │   - Success Rate: 99.5%
│   │
│   ├── Digital Wallets (25% of transactions)
│   │   - Apple Pay, Google Pay, PayPal, Amazon Pay
│   │   - One-click checkout (stored payment methods)
│   │   - Biometric authentication (Face ID, Touch ID)
│   │   - Success Rate: 99.8% (higher than cards)
│   │
│   ├── Buy Now Pay Later (BNPL) (10% of transactions)
│   │   - Klarna, Affirm, Afterpay, Clearpay
│   │   - Split payments (4 installments, 0% interest)
│   │   - Credit check (soft inquiry, instant approval)
│   │   - Success Rate: 95% (lower due to credit checks)
│   │
│   ├── Bank Transfers (3% of transactions)
│   │   - SEPA Direct Debit (Europe), ACH (US)
│   │   - iDEAL (Netherlands), Bancontact (Belgium), Sofort (Germany)
│   │   - Lower fees (0.5-1%) but slower (1-3 days)
│   │   - Success Rate: 98%
│   │
│   └── Alternative Payment Methods (2% of transactions)
│       - Cryptocurrency (Bitcoin, Ethereum via Coinbase Commerce)
│       - Mobile payments (Swish, MobilePay, Vipps)
│       - Cash on delivery (COD, emerging markets)
│       - Success Rate: 92-98% (varies by method)
│
├── Fraud Detection & Prevention Layer
│   ├── Real-Time Fraud Scoring
│   │   - ML Model: Random Forest + Neural Network ensemble
│   │   - Input Features: 200+ features (device, location, behavior, transaction history)
│   │   - Fraud Score: 0-100 (0=safe, 100=fraudulent)
│   │   - Thresholds: <20=auto-approve, 20-60=manual review, >60=auto-decline
│   │   - Accuracy: 98.5% (fraud detection), 0.5% false positive rate
│   │
│   ├── 3D Secure 2.0 (SCA Compliance)
│   │   - Strong Customer Authentication (EU PSD2 requirement)
│   │   - Frictionless flow (90% of transactions, no challenge)
│   │   - Challenge flow (10% of transactions, SMS/app authentication)
│   │   - Fraud reduction: 70% (vs. non-SCA transactions)
│   │
│   ├── Velocity Checks
│   │   - Limit transactions per card/customer/IP (prevent card testing)
│   │   - Example: Max 5 transactions per card per hour
│   │   - Block suspicious patterns (multiple failed attempts, rapid-fire transactions)
│   │
│   ├── Device Fingerprinting
│   │   - Identify devices (browser, OS, screen resolution, timezone)
│   │   - Detect emulators, VPNs, proxies (high-risk indicators)
│   │   - Link transactions to devices (detect account takeover)
│   │
│   └── Address Verification Service (AVS)
│       - Verify billing address matches card issuer records
│       - Reduce fraud (mismatched addresses flagged for review)
│       - Compliance (required for some high-risk transactions)
│
├── Compliance & Security Layer
│   ├── PCI DSS Level 1 Compliance
│   │   - Highest level of PCI compliance (>6M transactions/year)
│   │   - Annual audit (Qualified Security Assessor, QSA)
│   │   - Requirements: Network security, access control, encryption, monitoring
│   │   - Tokenization (never store raw card numbers)
│   │
│   ├── GDPR Compliance
│   │   - Data minimization (collect only necessary data)
│   │   - Right to erasure (delete customer data on request)
│   │   - Data portability (export customer data)
│   │   - Consent management (explicit opt-in for marketing)
│   │
│   ├── PSD2 Compliance (EU)
│   │   - Strong Customer Authentication (SCA, 3D Secure 2.0)
│   │   - Open Banking (account-to-account payments)
│   │   - Exemptions (low-value transactions <€30, trusted beneficiaries)
│   │
│   └── AML/KYC Compliance
│       - Anti-Money Laundering (AML) checks
│       - Know Your Customer (KYC) verification (for high-value transactions)
│       - Transaction monitoring (detect suspicious patterns)
│       - Reporting (suspicious activity reports to authorities)
│
└── Reconciliation & Settlement Layer
    ├── Automated Reconciliation
    │   - Match gateway settlements with internal records (daily)
    │   - Identify discrepancies (missing transactions, incorrect amounts)
    │   - Dispute resolution (chargebacks, refunds, adjustments)
    │   - Accuracy: 99.95% (auto-reconciled), 0.05% manual review
    │
    ├── Multi-Currency Settlement
    │   - Support 28 currencies (EUR, GBP, USD, etc.)
    │   - Real-time FX rates (updated every 5 minutes)
    │   - Currency conversion fees (0.5-1% markup)
    │   - Hedge FX risk (forward contracts for large transactions)
    │
    └── Vendor Payout Processing
        - Calculate vendor payouts (GMV - commission - fees)
        - Payout schedule (weekly, bi-weekly, monthly)
        - Payout methods (bank transfer, PayPal, Stripe Connect)
        - Payout latency: T+7 days (7 days after order delivery)

Technology Stack:
- Payment Gateways: Stripe, Adyen, PayPal
- Fraud Detection: Sift Science, Ravelin
- PCI Compliance: Tokenization (Stripe, Adyen), PCI DSS Level 1 certified infrastructure
- Database: PostgreSQL 15 (transactions), MongoDB (fraud logs)
- Message Queue: Apache Kafka (payment events)
- Analytics: Tableau, Looker (payment analytics)
```

**Performance Metrics**:
- **Transaction Volume**: 15M transactions/year (41K/day avg, 120K/day peak)
- **GMV Processed**: €2.8B/year (€7.7M/day avg, €23M/day peak)
- **Payment Success Rate**: 99.8% (with smart routing and retries)
- **Authorization Latency**: p50: 450ms, p95: 1.2s, p99: 2.5s
- **Fraud Rate**: 0.15% (€4.2M fraud prevented/year)
- **Chargeback Rate**: 0.08% (target: <0.1%)
- **System Uptime**: 99.99% (target: 99.95%)

---

### 2. Commission & Fee Management

**Commission Structure**:
```
Marketplace Commission Model (Tiered by Vendor Performance):

Tier 1: Platinum Vendors (Top 5%, Performance Score 90-100)
├── Commission Rate: 8% of GMV
├── Eligibility: GMV >€500K/month, 95%+ on-time, 4.7+ rating
├── Benefits: Lowest commission, priority support, featured placement
└── Example: €1M GMV → €80K commission

Tier 2: Gold Vendors (Top 20%, Performance Score 75-89)
├── Commission Rate: 10% of GMV
├── Eligibility: GMV >€100K/month, 93%+ on-time, 4.5+ rating
├── Benefits: Competitive commission, dedicated account manager
└── Example: €500K GMV → €50K commission

Tier 3: Silver Vendors (Top 50%, Performance Score 60-74)
├── Commission Rate: 12% of GMV
├── Eligibility: GMV >€10K/month, 90%+ on-time, 4.3+ rating
├── Benefits: Standard commission, email support
└── Example: €100K GMV → €12K commission

Tier 4: Bronze Vendors (Bottom 50%, Performance Score 0-59)
├── Commission Rate: 15% of GMV
├── Eligibility: All other vendors
├── Benefits: Standard marketplace access
└── Example: €50K GMV → €7.5K commission

Commission Calculation:
Commission = (Product Price × Quantity × Commission Rate) - Discounts - Refunds

Example Transaction:
- Product: Wireless Mouse, €25
- Quantity: 1
- Commission Rate: 10% (Gold vendor)
- Commission: €25 × 1 × 10% = €2.50
- Vendor Payout: €25 - €2.50 = €22.50 (before shipping, fees)
```

**Additional Fees**:
```
Marketplace Fees (Beyond Commission):

1. Payment Processing Fees:
   - Credit/Debit Cards: 1.4% + €0.25 per transaction (passed through from Stripe)
   - Digital Wallets: 1.5% + €0.20 per transaction
   - BNPL: 3.5% + €0.30 per transaction (higher due to credit risk)
   - Bank Transfers: 0.5% + €0.10 per transaction (lowest cost)
   - Who Pays: Marketplace absorbs (included in commission)

2. Fulfillment Fees (FaaS Vendors):
   - Storage: €0.50-2.00/unit/month
   - Fulfillment: €2.50-8.50/order
   - Returns: €2.00-3.00/return
   - Who Pays: Vendor (deducted from payout)

3. Shipping Fees:
   - Cost: €4.50-12.50/shipment (depends on carrier, destination)
   - Who Pays: Marketplace (70%), Vendor (20%), Customer (10%)

4. Advertising Fees (Optional):
   - Sponsored Products: €0.30-2.00 per click (CPC model)
   - Display Ads: €5-20 per 1,000 impressions (CPM model)
   - Who Pays: Vendor (optional, for increased visibility)

5. Subscription Fees (Optional):
   - Basic Plan: Free (standard commission rates)
   - Growth Plan: €99/month (1% commission discount, priority support)
   - Enterprise Plan: €499/month (2% commission discount, dedicated manager, custom terms)
   - Who Pays: Vendor (optional, for lower commission rates)

6. Chargeback Fees:
   - Fee: €15 per chargeback (administrative cost)
   - Who Pays: Vendor (if vendor at fault), Marketplace (if marketplace at fault)
   - Prevention: Fraud detection, clear return policies, good customer service

Total Effective Fee (Example):
- Product: €100, Commission: 10% (€10)
- Payment Processing: 1.4% + €0.25 (€1.65)
- Fulfillment: €3.50 (FaaS)
- Shipping: €8.50 (vendor pays)
- Total Fees: €23.65 (23.65% of GMV)
- Vendor Payout: €76.35 (76.35% of GMV)
```

---

### 3. Vendor Payout Management

**Payout Process**:
```
Vendor Payout Workflow:

Step 1: Order Delivery (Day 0)
- Customer receives order, confirms delivery
- Payment captured from customer (held in escrow)
- Payout clock starts (T+7 days)

Step 2: Return Window (Days 1-7)
- Customer has 7 days to initiate return (standard policy)
- If return initiated, payout delayed until return processed
- If no return, proceed to payout

Step 3: Payout Calculation (Day 7)
- Calculate vendor payout:
  - GMV: €100 (product price)
  - Commission: €10 (10%)
  - Payment Processing: €1.65 (1.4% + €0.25)
  - Fulfillment: €3.50 (FaaS)
  - Shipping: €8.50 (vendor pays)
  - Refunds: €0 (no returns)
  - Chargebacks: €0 (no chargebacks)
  - Adjustments: €0 (no adjustments)
  - Net Payout: €100 - €10 - €1.65 - €3.50 - €8.50 = €76.35

Step 4: Payout Initiation (Day 7)
- Generate payout batch (all orders delivered 7 days ago)
- Send payout to vendor's bank account (SEPA transfer)
- Payout notification (email, vendor portal)

Step 5: Payout Settlement (Day 8-9)
- Bank transfer processing (1-2 business days)
- Vendor receives funds in bank account
- Payout confirmation (email, vendor portal)

Payout Schedule Options:
- Weekly: Every Monday (for orders delivered previous Monday-Sunday)
- Bi-Weekly: Every other Monday (for orders delivered previous 2 weeks)
- Monthly: 1st of month (for orders delivered previous month)
- On-Demand: Instant payout (for Platinum vendors, 1% fee)

Payout Methods:
- Bank Transfer (SEPA, ACH): 95% of payouts (standard, free)
- PayPal: 3% of payouts (faster, 1% fee)
- Stripe Connect: 2% of payouts (instant, 1.5% fee)
```

**Payout Dashboard (Vendor View)**:
```
Vendor Payout Dashboard:

Current Balance: €12,450
├── Pending (Not Yet Delivered): €3,200 (120 orders)
├── In Return Window (Delivered <7 days): €5,800 (210 orders)
├── Ready for Payout (Delivered >7 days): €3,450 (125 orders)
└── On Hold (Disputes, Investigations): €0 (0 orders)

Next Payout: Monday, Oct 21, 2025
├── Amount: €3,450
├── Orders: 125 orders (delivered Oct 7-13)
├── Payout Method: Bank Transfer (SEPA)
└── Estimated Arrival: Oct 22-23, 2025

Payout History (Last 3 Months):
- Oct 2025: €28,500 (4 payouts, avg €7,125/payout)
- Sep 2025: €26,200 (4 payouts, avg €6,550/payout)
- Aug 2025: €24,800 (4 payouts, avg €6,200/payout)
- Total: €79,500 (12 payouts)

Payout Breakdown (This Month):
- GMV: €32,000 (1,200 orders, €26.67 AOV)
- Commission: €3,200 (10%)
- Payment Processing: €550 (1.7%)
- Fulfillment: €4,200 (FaaS)
- Shipping: €10,200 (vendor pays)
- Refunds: €800 (2.5% return rate)
- Chargebacks: €50 (0.15%)
- Net Payout: €13,000 (40.6% of GMV)

Payout Settings:
- Payout Schedule: Weekly (every Monday)
- Payout Method: Bank Transfer (SEPA)
- Bank Account: DE89 3704 0044 0532 0130 00 (verified)
- Tax Information: VAT ID DE123456789 (verified)
```

---

### 4. Refund & Chargeback Management

**Refund Processing**:
```
Refund Workflow:

Scenario 1: Customer-Initiated Return (80% of refunds)
1. Customer initiates return (within 7-day return window)
2. Return approved (automatic for most items)
3. Customer ships item back to fulfillment center
4. Item received and inspected (quality check)
5. Refund issued to customer (original payment method)
6. Vendor charged for refund (deducted from next payout)

Refund Timeline:
- Return Initiated: Day 0
- Item Shipped Back: Day 1-3
- Item Received: Day 4-6
- Inspection: Day 6-7
- Refund Issued: Day 7 (instant to customer)
- Vendor Charged: Next payout (Day 14)

Refund Amount:
- Full Refund: Product price + shipping (if marketplace paid)
- Partial Refund: Product price only (if customer paid shipping)
- Restocking Fee: 15% (if item damaged by customer, not as described)

Scenario 2: Vendor-Initiated Refund (15% of refunds)
1. Vendor cancels order (out of stock, pricing error, etc.)
2. Refund issued to customer (instant)
3. Vendor charged for refund (deducted from next payout)
4. No return required (order not shipped)

Scenario 3: Marketplace-Initiated Refund (5% of refunds)
1. Marketplace cancels order (fraud, policy violation, etc.)
2. Refund issued to customer (instant)
3. Marketplace absorbs refund cost (vendor not charged)
4. No return required (order not shipped)

Refund Performance (This Month):
- Total Refunds: 1,200 refunds (€96,000)
- Refund Rate: 2.5% (1,200 / 48,000 orders)
- Refund Reasons:
  - Changed Mind: 35% (420 refunds)
  - Defective/Damaged: 25% (300 refunds)
  - Wrong Item: 15% (180 refunds)
  - Not as Described: 15% (180 refunds)
  - Late Delivery: 10% (120 refunds)
```

**Chargeback Management**:
```
Chargeback Workflow:

What is a Chargeback?
- Customer disputes transaction with bank/card issuer
- Bank reverses transaction (customer gets money back)
- Merchant (marketplace) loses revenue + chargeback fee (€15-25)
- Vendor may be charged (if vendor at fault)

Common Chargeback Reasons:
1. Fraud (40%): Unauthorized transaction, stolen card
2. Product Not Received (30%): Customer claims non-delivery
3. Product Not as Described (20%): Quality issues, wrong item
4. Duplicate Charge (5%): Customer charged twice
5. Other (5%): Subscription cancellation, processing errors

Chargeback Process:
1. Customer files dispute with bank (Day 0)
2. Bank notifies marketplace (Day 1-3)
3. Marketplace investigates (Day 3-7)
   - Review order details, tracking, delivery confirmation
   - Contact vendor for evidence (photos, receipts, communications)
4. Marketplace responds to bank (Day 7)
   - Provide evidence (tracking, delivery proof, customer signature)
   - Argue case (legitimate transaction, customer received product)
5. Bank makes final decision (Day 30-90)
   - Merchant Wins: Chargeback reversed, merchant keeps revenue
   - Customer Wins: Chargeback upheld, merchant loses revenue + fee

Chargeback Prevention:
- Clear product descriptions (reduce "not as described" disputes)
- Proof of delivery (signature, photo, GPS)
- Fraud detection (prevent unauthorized transactions)
- Good customer service (resolve issues before chargeback)

Chargeback Performance (This Month):
- Total Chargebacks: 38 chargebacks (€3,040 + €570 fees)
- Chargeback Rate: 0.08% (38 / 48,000 orders)
- Chargeback Reasons:
  - Fraud: 15 chargebacks (40%)
  - Product Not Received: 11 chargebacks (30%)
  - Not as Described: 8 chargebacks (20%)
  - Other: 4 chargebacks (10%)
- Win Rate: 65% (25 chargebacks won, 13 lost)
- Cost: €1,975 (13 lost chargebacks × €152 avg) + €570 (38 × €15 fee) = €2,545
```


