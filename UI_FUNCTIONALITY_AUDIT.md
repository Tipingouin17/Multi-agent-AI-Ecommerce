# UI Functionality Audit Report

## Summary

- **UI Components analyzed:** 23
- **Agents with APIs:** 29
- **Matched API calls:** 77
- **Unmatched API calls:** 2

**API Coverage:** 97.5%

## ⚠️ Unmatched API Calls (Potential Missing Endpoints)

These UI components are calling APIs that don't exist in any agent:

- **Component:** `components/DatabaseTest.jsx`
  - **API Call:** `${API_BASE_URL}:${agent.port}${agent.endpoint}`

- **Component:** `components/DatabaseTest.jsx`
  - **API Call:** `:${agent.port`

## Agent API Endpoints

### after_sales_agent

- `GET /health`
- `GET /`

### analytics_agent_complete

- `GET /api/v1/analytics/dashboard`
- `GET /api/v1/analytics/sales`
- `GET /api/v1/analytics/customers`
- `GET /health`

### backoffice_agent

- `GET /health`
- `GET /`

### carrier_selection_agent

- `GET /health`

### chatbot_agent

- `POST /api/v1/chatbot/conversations`
- `POST /api/v1/chatbot/messages`
- `GET /api/v1/chatbot/conversations/{conversation_id}/messages`
- `POST /api/v1/chatbot/conversations/{conversation_id}/end`
- `POST /api/v1/chatbot/conversations/{conversation_id}/escalate`
- `POST /api/v1/chatbot/feedback`
- `GET /health`

### compliance_agent

- `GET /`
- `GET /health`
- `POST /api/v1/compliance/consent`
- `POST /api/v1/compliance/data-access-request`
- `POST /api/v1/compliance/audit-log`
- `GET /api/v1/compliance/audit-logs`
- `GET /api/v1/compliance/reports/consent-summary`

### customer_agent_enhanced

- `GET /`
- `GET /health`
- `GET /customers`
- `GET /customers/{customer_id}`
- `POST /customers`
- `PUT /customers/{customer_id}`
- `DELETE /customers/{customer_id}`
- `POST /customers/{customer_id}/addresses`
- `GET /customers/{customer_id}/addresses`
- `GET /customers/{customer_id}/loyalty`
- `POST /customers/{customer_id}/interactions`

### customer_communication_agent

- `GET /health`

### d2c_ecommerce_agent

- `GET /health`

### document_generation_agent

- `GET /health`
- `GET /`
- `POST /generate/invoice`
- `POST /generate/shipping_label`
- `POST /generate/packing_slip`

### dynamic_pricing_agent

- `GET /health`

### inventory_agent_enhanced

- `POST /api/v1/stock-levels`
- `GET /api/v1/stock-levels/{product_id}`
- `POST /api/v1/stock-levels/adjust`
- `GET /api/v1/stock-levels/low-stock`
- `GET /api/v1/stock-levels/{product_id}/availability`
- `GET /health`

### knowledge_management_agent

- `GET /health`
- `GET /`
- `POST /api/v1/knowledge/articles`
- `GET /api/v1/knowledge/articles/{article_id}`
- `PUT /api/v1/knowledge/articles/{article_id}`
- `DELETE /api/v1/knowledge/articles/{article_id}`
- `POST /api/v1/knowledge/search`
- `POST /api/v1/knowledge/articles/{article_id}/helpful`

### marketplace_connector_agent

- `GET /health`
- `GET /`
- `POST /api/v1/marketplaces/connections`
- `GET /api/v1/marketplaces/connections`
- `GET /api/v1/marketplaces/connections/{connection_id}`
- `PUT /api/v1/marketplaces/connections/{connection_id}`
- `DELETE /api/v1/marketplaces/connections/{connection_id}`
- `POST /api/v1/marketplaces/{connection_id}/sync-orders`
- `GET /api/v1/marketplaces/{connection_id}/orders`
- `POST /api/v1/marketplaces/sync-inventory`
- `POST /api/v1/marketplaces/messages`
- `GET /api/v1/marketplaces/{connection_id}/messages/unread`
- `POST /api/v1/marketplaces/offers`
- `GET /api/v1/marketplaces/{connection_id}/offers`

### marketplace_connector_agent_production

- `GET /health`
- `GET /`
- `POST /orders/sync`
- `POST /inventory/sync`
- `POST /price/sync`
- `POST /listing/create`

### notification_agent

- `POST /api/v1/notifications/send`
- `GET /api/v1/notifications/{notification_id}`
- `GET /api/v1/notifications/customer/{customer_id}`
- `GET /api/v1/notifications/preferences/{customer_id}`
- `PUT /api/v1/notifications/preferences`
- `GET /health`

### payment_agent_enhanced

- `GET /api/v1/payment/gateways`
- `POST /api/v1/payment/methods`
- `GET /api/v1/payment/methods/{customer_id}`
- `POST /api/v1/payment/process`
- `GET /api/v1/payment/transactions/{transaction_id}`
- `POST /api/v1/payment/refund`
- `POST /api/v1/payment/authorize`
- `GET /`
- `GET /health`

### product_agent

- `GET /health`

### product_agent_api

- `POST /api/v1/products/{product_id}/variants`
- `GET /api/v1/products/{product_id}/variants`
- `PUT /api/v1/variants/{variant_id}`
- `POST /api/v1/variants/{variant_id}/set-master`
- `POST /api/v1/variant-attributes`
- `POST /api/v1/bundles`
- `GET /api/v1/bundles/{bundle_id}`
- `GET /api/v1/bundles/{bundle_id}/price`
- `POST /api/v1/bundles/{bundle_id}/activate`
- `POST /api/v1/products/{product_id}/images`
- `GET /api/v1/products/{product_id}/images`
- `POST /api/v1/images/{image_id}/set-primary`
- `POST /api/v1/products/{product_id}/media`
- `GET /api/v1/products/{product_id}/media`
- `POST /api/v1/categories`
- `GET /api/v1/categories`
- `GET /api/v1/categories/{category_id}`
- `GET /api/v1/categories/{category_id}/breadcrumb`
- `POST /api/v1/products/{product_id}/categories`
- `POST /api/v1/attribute-groups`
- `POST /api/v1/attributes`
- `POST /api/v1/products/{product_id}/attributes`
- `GET /api/v1/products/{product_id}/attributes`
- `GET /health`
- `POST /api/v1/pricing-rules`
- `GET /api/v1/products/{product_id}/price`
- `POST /api/v1/products/{product_id}/price`
- `POST /api/v1/pricing/bulk-update`
- `POST /api/v1/competitor-prices`
- `POST /api/v1/products/{product_id}/reviews`
- `GET /api/v1/products/{product_id}/reviews`
- `GET /api/v1/products/{product_id}/reviews/summary`
- `POST /api/v1/reviews/{review_id}/approve`
- `POST /api/v1/reviews/{review_id}/vote`
- `POST /api/v1/reviews/{review_id}/response`
- `POST /api/v1/inventory`
- `GET /api/v1/products/{product_id}/inventory`
- `POST /api/v1/inventory/adjust`
- `POST /api/v1/inventory/reserve`
- `GET /api/v1/products/{product_id}/availability`
- `GET /api/v1/inventory/low-stock`
- `POST /api/v1/product-relationships`
- `GET /api/v1/products/{product_id}/related`
- `POST /api/v1/products/{product_id}/recommendations`
- `POST /api/v1/product-recommendations`
- `POST /api/v1/products/{product_id}/lifecycle`
- `POST /api/v1/products/{product_id}/status`
- `POST /api/v1/products/{product_id}/versions`
- `POST /api/v1/products/{product_id}/changes`
- `POST /api/v1/products/{product_id}/approvals`
- `POST /api/v1/approvals/{approval_id}/review`

### promotion_agent

- `POST /api/v1/promotions`
- `GET /api/v1/promotions/active`
- `POST /api/v1/promotions/validate`
- `POST /api/v1/promotions/{promotion_id}/use`
- `GET /health`

### recommendation_agent

- `POST /api/v1/recommendations/interaction`
- `POST /api/v1/recommendations/generate`
- `GET /api/v1/recommendations/trending`
- `GET /api/v1/recommendations/similar/{product_id}`
- `GET /health`

### returns_agent

- `GET /health`
- `GET /`
- `GET /api/v1/returns/reasons`
- `POST /api/v1/returns`
- `GET /api/v1/returns/{return_id}`
- `POST /api/v1/returns/{return_id}/approve`
- `POST /api/v1/returns/{return_id}/refund`
- `GET /api/v1/returns/customer/{customer_id}`

### shipping_agent_ai

- `GET /api/v1/shipping/carriers`
- `POST /api/v1/shipping/select-carrier`
- `POST /api/v1/shipping/shipments`
- `GET /api/v1/shipping/shipments/{shipment_id}`
- `GET /api/v1/shipping/track/{tracking_number}`
- `GET /health`

### supplier_agent

- `GET /health`
- `GET /`
- `GET /suppliers`
- `GET /suppliers/{supplier_id}`
- `GET /suppliers/{supplier_id}/products`
- `POST /purchase-orders`
- `GET /purchase-orders/{po_id}`
- `PATCH /purchase-orders/{po_id}/status`
- `POST /po-receipts`
- `GET /suppliers/{supplier_id}/performance`

### support_agent

- `POST /api/v1/support/tickets`
- `GET /api/v1/support/tickets/{ticket_id}`
- `PATCH /api/v1/support/tickets/{ticket_id}`
- `POST /api/v1/support/tickets/{ticket_id}/messages`
- `GET /api/v1/support/tickets/{ticket_id}/messages`
- `POST /api/v1/support/tickets/escalate`
- `GET /api/v1/support/tickets/{ticket_id}/sla`
- `GET /health`

### tax_agent

- `POST /api/v1/tax/calculate`
- `POST /api/v1/tax/exemptions`
- `POST /api/v1/tax/reports`
- `GET /health`

### transport_agent_production

- `GET /health`
- `GET /`
- `POST /carriers/{carrier_code}/config`
- `GET /carriers/{carrier_code}/config`
- `GET /carriers/config`
- `DELETE /carriers/{carrier_code}/config`

### warehouse_agent

- `GET /api/v1/warehouses`
- `GET /api/v1/warehouses/{warehouse_id}/inventory`
- `POST /api/v1/warehouses/allocate`
- `POST /api/v1/warehouses/pick-lists`
- `POST /api/v1/warehouses/pick-lists/{pick_list_id}/start`
- `POST /api/v1/warehouses/pick-lists/{pick_list_id}/complete`
- `GET /api/v1/warehouses/{warehouse_id}/pick-lists/pending`
- `GET /health`

### workflow_orchestration_agent

- `POST /api/v1/workflows/execute`
- `GET /api/v1/workflows/{execution_id}/status`
- `GET /health`

## ✅ Successfully Matched API Calls

- **Component:** `App.jsx`
  - **UI Call:** `http://localhost:${agent.port}/health`
  - **Agent:** `analytics_agent_complete`
  - **Endpoint:** `/health`

- **Component:** `components/DatabaseTest.jsx`
  - **UI Call:** `${API_BASE_URL}:8014/system/overview`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `components/DatabaseTest.jsx`
  - **UI Call:** `${API_BASE_URL}:8002/products`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `components/DatabaseTest.jsx`
  - **UI Call:** `${API_BASE_URL}:8001/orders`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `components/DatabaseTest.jsx`
  - **UI Call:** `:8014/system/overview`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `components/DatabaseTest.jsx`
  - **UI Call:** `:8002/products`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `components/DatabaseTest.jsx`
  - **UI Call:** `:8001/orders`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `components/agent-visualizations/AIMonitoringView.jsx`
  - **UI Call:** `http://localhost:8014/system/overview`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `components/agent-visualizations/CarrierSelectionView.jsx`
  - **UI Call:** `http://localhost:8006/api/shipments/${shipmentId}`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `components/agent-visualizations/CarrierSelectionView.jsx`
  - **UI Call:** `http://localhost:8006/api/carriers`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `pages/admin/AIModelConfiguration.jsx`
  - **UI Call:** `/api/ai-models`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `pages/admin/AIModelConfiguration.jsx`
  - **UI Call:** `/api/ai-models/${modelId}`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `pages/admin/AIModelConfiguration.jsx`
  - **UI Call:** `/api/ai-models/${modelId}/${action}`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `pages/admin/BusinessRulesConfiguration.jsx`
  - **UI Call:** `http://localhost:8011/api/rules`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `pages/admin/BusinessRulesConfiguration.jsx`
  - **UI Call:** `http://localhost:8000/api/business-rules/${ruleId}`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `pages/admin/BusinessRulesConfiguration.jsx`
  - **UI Call:** `http://localhost:8000/api/business-rules/${testingRule.rule_id}/test`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `pages/admin/BusinessRulesConfiguration.jsx`
  - **UI Call:** `http://localhost:8000/api/business-rules/${rule.rule_id}`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `pages/admin/CarrierConfiguration.jsx`
  - **UI Call:** `http://localhost:8006/api/carriers/config`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `pages/admin/CarrierConfiguration.jsx`
  - **UI Call:** `http://localhost:8000/api/carriers/${carrierId}`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`

- **Component:** `pages/admin/CarrierConfiguration.jsx`
  - **UI Call:** `http://localhost:8000/api/carriers/upload-pricelist`
  - **Agent:** `compliance_agent`
  - **Endpoint:** `/`
