"""
Saga Workflows - Multi-Agent E-commerce System

Predefined saga workflows for common e-commerce operations.
These workflows demonstrate the Saga pattern in action.
"""

from typing import Dict, Any
from agents.saga_orchestrator import SagaDefinition, SagaStep


# ===========================
# ORDER CREATION SAGA
# ===========================

def create_order_saga(order_data: Dict[str, Any]) -> SagaDefinition:
    """
    Saga for creating an order with inventory reservation, payment, and fulfillment.
    
    Steps:
    1. Validate customer
    2. Reserve inventory
    3. Process payment
    4. Create order
    5. Send confirmation
    
    If any step fails, all previous steps are compensated in reverse order.
    """
    return SagaDefinition(
        saga_name="create_order",
        description="Complete order creation workflow with automatic rollback",
        steps=[
            SagaStep(
                step_id="validate_customer",
                step_name="Validate Customer",
                agent="customer_agent",
                action="validate_customer",
                compensation_action=None,  # No compensation needed for validation
                params={"customer_id": order_data.get("customer_id")},
                timeout=10,
                max_retries=2
            ),
            SagaStep(
                step_id="reserve_inventory",
                step_name="Reserve Inventory",
                agent="inventory_agent",
                action="reserve_inventory",
                compensation_action="release_inventory",
                params={
                    "items": order_data.get("items", []),
                    "warehouse_id": order_data.get("warehouse_id")
                },
                timeout=30,
                max_retries=3
            ),
            SagaStep(
                step_id="process_payment",
                step_name="Process Payment",
                agent="payment_agent",
                action="charge_customer",
                compensation_action="refund_customer",
                params={
                    "customer_id": order_data.get("customer_id"),
                    "amount": order_data.get("total_amount"),
                    "payment_method": order_data.get("payment_method")
                },
                timeout=45,
                max_retries=2
            ),
            SagaStep(
                step_id="create_order",
                step_name="Create Order",
                agent="order_agent",
                action="create_order",
                compensation_action="cancel_order",
                params={
                    "customer_id": order_data.get("customer_id"),
                    "items": order_data.get("items", []),
                    "shipping_address": order_data.get("shipping_address"),
                    "billing_address": order_data.get("billing_address")
                },
                timeout=20,
                max_retries=3
            ),
            SagaStep(
                step_id="send_confirmation",
                step_name="Send Order Confirmation",
                agent="notification_agent",
                action="send_order_confirmation",
                compensation_action=None,  # No compensation for notification
                params={
                    "customer_id": order_data.get("customer_id"),
                    "order_id": "${create_order_result.order_id}"
                },
                timeout=15,
                max_retries=2
            )
        ],
        metadata=order_data
    )


# ===========================
# ORDER CANCELLATION SAGA
# ===========================

def cancel_order_saga(order_id: str, reason: str) -> SagaDefinition:
    """
    Saga for canceling an order with refund and inventory restoration.
    
    Steps:
    1. Validate order can be cancelled
    2. Process refund
    3. Restore inventory
    4. Update order status
    5. Send cancellation notification
    """
    return SagaDefinition(
        saga_name="cancel_order",
        description="Order cancellation with refund and inventory restoration",
        steps=[
            SagaStep(
                step_id="validate_cancellation",
                step_name="Validate Order Cancellation",
                agent="order_agent",
                action="validate_cancellation",
                compensation_action=None,
                params={"order_id": order_id},
                timeout=10,
                max_retries=2
            ),
            SagaStep(
                step_id="process_refund",
                step_name="Process Refund",
                agent="payment_agent",
                action="refund_order",
                compensation_action="reverse_refund",
                params={
                    "order_id": order_id,
                    "reason": reason
                },
                timeout=45,
                max_retries=3
            ),
            SagaStep(
                step_id="restore_inventory",
                step_name="Restore Inventory",
                agent="inventory_agent",
                action="restore_inventory",
                compensation_action="re_reserve_inventory",
                params={"order_id": order_id},
                timeout=30,
                max_retries=3
            ),
            SagaStep(
                step_id="update_order_status",
                step_name="Update Order Status",
                agent="order_agent",
                action="mark_cancelled",
                compensation_action="revert_cancellation",
                params={
                    "order_id": order_id,
                    "reason": reason
                },
                timeout=20,
                max_retries=3
            ),
            SagaStep(
                step_id="send_notification",
                step_name="Send Cancellation Notification",
                agent="notification_agent",
                action="send_cancellation_notification",
                compensation_action=None,
                params={
                    "order_id": order_id,
                    "reason": reason
                },
                timeout=15,
                max_retries=2
            )
        ],
        metadata={"order_id": order_id, "reason": reason}
    )


# ===========================
# PRODUCT IMPORT SAGA
# ===========================

def import_products_saga(import_data: Dict[str, Any]) -> SagaDefinition:
    """
    Saga for importing products from external source.
    
    Steps:
    1. Validate import data
    2. Create products
    3. Set up inventory
    4. Generate SEO metadata
    5. Publish to channels
    """
    return SagaDefinition(
        saga_name="import_products",
        description="Bulk product import with validation and channel publishing",
        steps=[
            SagaStep(
                step_id="validate_import",
                step_name="Validate Import Data",
                agent="product_agent",
                action="validate_import_data",
                compensation_action=None,
                params={
                    "products": import_data.get("products", []),
                    "source": import_data.get("source")
                },
                timeout=60,
                max_retries=2
            ),
            SagaStep(
                step_id="create_products",
                step_name="Create Products",
                agent="product_agent",
                action="bulk_create_products",
                compensation_action="delete_products",
                params={
                    "products": import_data.get("products", [])
                },
                timeout=120,
                max_retries=3
            ),
            SagaStep(
                step_id="setup_inventory",
                step_name="Setup Inventory",
                agent="inventory_agent",
                action="initialize_inventory",
                compensation_action="remove_inventory",
                params={
                    "product_ids": "${create_products_result.product_ids}",
                    "warehouse_id": import_data.get("warehouse_id")
                },
                timeout=60,
                max_retries=3
            ),
            SagaStep(
                step_id="generate_seo",
                step_name="Generate SEO Metadata",
                agent="product_agent",
                action="generate_seo_bulk",
                compensation_action="remove_seo",
                params={
                    "product_ids": "${create_products_result.product_ids}"
                },
                timeout=90,
                max_retries=2
            ),
            SagaStep(
                step_id="publish_channels",
                step_name="Publish to Sales Channels",
                agent="channel_agent",
                action="publish_products",
                compensation_action="unpublish_products",
                params={
                    "product_ids": "${create_products_result.product_ids}",
                    "channels": import_data.get("channels", ["website"])
                },
                timeout=120,
                max_retries=3
            )
        ],
        metadata=import_data
    )


# ===========================
# RETURN PROCESSING SAGA
# ===========================

def process_return_saga(return_data: Dict[str, Any]) -> SagaDefinition:
    """
    Saga for processing a product return.
    
    Steps:
    1. Validate return request
    2. Generate return label
    3. Update order status
    4. Process refund (when item received)
    5. Restock inventory
    """
    return SagaDefinition(
        saga_name="process_return",
        description="Product return processing with refund and restocking",
        steps=[
            SagaStep(
                step_id="validate_return",
                step_name="Validate Return Request",
                agent="order_agent",
                action="validate_return",
                compensation_action=None,
                params={
                    "order_id": return_data.get("order_id"),
                    "items": return_data.get("items", []),
                    "reason": return_data.get("reason")
                },
                timeout=20,
                max_retries=2
            ),
            SagaStep(
                step_id="generate_label",
                step_name="Generate Return Label",
                agent="shipping_agent",
                action="generate_return_label",
                compensation_action="cancel_return_label",
                params={
                    "order_id": return_data.get("order_id"),
                    "customer_address": return_data.get("customer_address")
                },
                timeout=30,
                max_retries=3
            ),
            SagaStep(
                step_id="update_order",
                step_name="Update Order Status",
                agent="order_agent",
                action="mark_return_initiated",
                compensation_action="revert_return_status",
                params={
                    "order_id": return_data.get("order_id"),
                    "return_id": "${generate_label_result.return_id}"
                },
                timeout=20,
                max_retries=3
            ),
            SagaStep(
                step_id="send_instructions",
                step_name="Send Return Instructions",
                agent="notification_agent",
                action="send_return_instructions",
                compensation_action=None,
                params={
                    "order_id": return_data.get("order_id"),
                    "customer_id": return_data.get("customer_id"),
                    "return_label_url": "${generate_label_result.label_url}"
                },
                timeout=15,
                max_retries=2
            )
        ],
        metadata=return_data
    )


# ===========================
# INVENTORY TRANSFER SAGA
# ===========================

def transfer_inventory_saga(transfer_data: Dict[str, Any]) -> SagaDefinition:
    """
    Saga for transferring inventory between warehouses.
    
    Steps:
    1. Validate source inventory
    2. Reserve at source
    3. Create transfer order
    4. Deduct from source
    5. Add to destination
    """
    return SagaDefinition(
        saga_name="transfer_inventory",
        description="Inter-warehouse inventory transfer",
        steps=[
            SagaStep(
                step_id="validate_source",
                step_name="Validate Source Inventory",
                agent="inventory_agent",
                action="validate_transfer_source",
                compensation_action=None,
                params={
                    "warehouse_id": transfer_data.get("source_warehouse"),
                    "product_id": transfer_data.get("product_id"),
                    "quantity": transfer_data.get("quantity")
                },
                timeout=15,
                max_retries=2
            ),
            SagaStep(
                step_id="reserve_source",
                step_name="Reserve at Source",
                agent="inventory_agent",
                action="reserve_for_transfer",
                compensation_action="release_reservation",
                params={
                    "warehouse_id": transfer_data.get("source_warehouse"),
                    "product_id": transfer_data.get("product_id"),
                    "quantity": transfer_data.get("quantity")
                },
                timeout=30,
                max_retries=3
            ),
            SagaStep(
                step_id="create_transfer",
                step_name="Create Transfer Order",
                agent="inventory_agent",
                action="create_transfer_order",
                compensation_action="cancel_transfer_order",
                params={
                    "source_warehouse": transfer_data.get("source_warehouse"),
                    "destination_warehouse": transfer_data.get("destination_warehouse"),
                    "product_id": transfer_data.get("product_id"),
                    "quantity": transfer_data.get("quantity")
                },
                timeout=20,
                max_retries=3
            ),
            SagaStep(
                step_id="deduct_source",
                step_name="Deduct from Source",
                agent="inventory_agent",
                action="deduct_inventory",
                compensation_action="restore_inventory",
                params={
                    "warehouse_id": transfer_data.get("source_warehouse"),
                    "product_id": transfer_data.get("product_id"),
                    "quantity": transfer_data.get("quantity"),
                    "transfer_id": "${create_transfer_result.transfer_id}"
                },
                timeout=30,
                max_retries=3
            ),
            SagaStep(
                step_id="add_destination",
                step_name="Add to Destination",
                agent="inventory_agent",
                action="add_inventory",
                compensation_action="remove_inventory",
                params={
                    "warehouse_id": transfer_data.get("destination_warehouse"),
                    "product_id": transfer_data.get("product_id"),
                    "quantity": transfer_data.get("quantity"),
                    "transfer_id": "${create_transfer_result.transfer_id}"
                },
                timeout=30,
                max_retries=3
            )
        ],
        metadata=transfer_data
    )


# ===========================
# SAGA REGISTRY
# ===========================

SAGA_REGISTRY = {
    "create_order": create_order_saga,
    "cancel_order": cancel_order_saga,
    "import_products": import_products_saga,
    "process_return": process_return_saga,
    "transfer_inventory": transfer_inventory_saga
}


def get_saga_workflow(workflow_name: str, params: Dict[str, Any]) -> SagaDefinition:
    """Get a predefined saga workflow by name."""
    workflow_factory = SAGA_REGISTRY.get(workflow_name)
    
    if not workflow_factory:
        raise ValueError(f"Unknown saga workflow: {workflow_name}")
    
    return workflow_factory(params)

