#!/usr/bin/env python3
"""
End-to-End Workflow Tests for Multi-Agent E-Commerce System

Tests the 10 critical workflows using mock environment
"""
import asyncio
import sys
import os
from typing import Dict, Any

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_test_environment import create_mock_agent_environment, test_agent_lifecycle


# Import critical agents
CRITICAL_AGENTS = {
    "OrderAgent": ("agents.order_agent_production", "OrderAgent"),
    "InventoryAgent": ("agents.inventory_agent", "InventoryAgent"),
    "ProductAgent": ("agents.product_agent_production", "ProductAgent"),
    "WarehouseAgent": ("agents.warehouse_agent_production", "WarehouseAgent"),
    "TransportAgent": ("agents.transport_agent_production", "TransportAgentProduction"),
    "MarketplaceConnector": ("agents.marketplace_connector_agent_production", "MarketplaceConnectorAgentProduction"),
    "AfterSalesAgent": ("agents.after_sales_agent", "AfterSalesAgent"),
    "QualityControlAgent": ("agents.quality_control_agent", "QualityControlAgent"),
    "BackofficeAgent": ("agents.backoffice_agent", "BackofficeAgent"),
    "PaymentAgent": ("agents.payment_agent_enhanced", "PaymentAgent"),
}


async def test_workflow_1_order_creation():
    """
    Workflow 1: Order Creation and Processing
    OrderAgent -> InventoryAgent -> WarehouseAgent -> PaymentAgent
    """
    print("\n" + "="*80)
    print("WORKFLOW 1: Order Creation and Processing")
    print("="*80)
    
    results = {}
    env = create_mock_agent_environment()
    
    # Test OrderAgent
    try:
        from agents.order_agent_production import OrderAgent
        agent = OrderAgent()
        agent.db_manager = env["db_manager"]
        
        # Initialize
        await agent.initialize()
        
        # Process order creation
        result = await agent.process_business_logic({
            "operation": "create_order",
            "order_data": {
                "customer_id": "test_customer",
                "items": [{"product_id": "P001", "quantity": 2}],
                "total": 100.00
            }
        })
        
        results["OrderAgent"] = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
        
        await agent.cleanup()
        
    except Exception as e:
        results["OrderAgent"] = f"❌ ERROR: {str(e)}"
    
    # Test InventoryAgent
    try:
        from agents.inventory_agent import InventoryAgent
        agent = InventoryAgent()
        agent.db_manager = env["db_manager"]
        
        await agent.initialize()
        
        result = await agent.process_business_logic({
            "operation": "check_stock",
            "product_id": "P001",
            "warehouse_id": "W001",
            "quantity": 2
        })
        
        results["InventoryAgent"] = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
        
        await agent.cleanup()
        
    except Exception as e:
        results["InventoryAgent"] = f"❌ ERROR: {str(e)}"
    
    # Print results
    for agent_name, status in results.items():
        print(f"  {agent_name}: {status}")
    
    return results


async def test_workflow_2_product_management():
    """
    Workflow 2: Product Management
    ProductAgent -> InventoryAgent -> MarketplaceConnector
    """
    print("\n" + "="*80)
    print("WORKFLOW 2: Product Management")
    print("="*80)
    
    results = {}
    env = create_mock_agent_environment()
    
    # Test ProductAgent
    try:
        from agents.product_agent_production import ProductAgent
        agent = ProductAgent()
        agent.db_manager = env["db_manager"]
        
        await agent.initialize()
        
        result = await agent.process_business_logic({
            "operation": "create_product",
            "product_data": {
                "name": "Test Product",
                "sku": "TEST-001",
                "price": 50.00
            }
        })
        
        results["ProductAgent"] = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
        
        await agent.cleanup()
        
    except Exception as e:
        results["ProductAgent"] = f"❌ ERROR: {str(e)}"
    
    # Print results
    for agent_name, status in results.items():
        print(f"  {agent_name}: {status}")
    
    return results


async def test_workflow_3_warehouse_operations():
    """
    Workflow 3: Warehouse Operations
    WarehouseAgent -> InventoryAgent -> QualityControlAgent
    """
    print("\n" + "="*80)
    print("WORKFLOW 3: Warehouse Operations")
    print("="*80)
    
    results = {}
    env = create_mock_agent_environment()
    
    # Test WarehouseAgent
    try:
        from agents.warehouse_agent_production import WarehouseAgent
        agent = WarehouseAgent()
        agent.db_manager = env["db_manager"]
        
        await agent.initialize()
        
        result = await agent.process_business_logic({
            "operation": "process_inbound",
            "warehouse_id": "W001",
            "items": [{"product_id": "P001", "quantity": 100}]
        })
        
        results["WarehouseAgent"] = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
        
        await agent.cleanup()
        
    except Exception as e:
        results["WarehouseAgent"] = f"❌ ERROR: {str(e)}"
    
    # Test QualityControlAgent
    try:
        from agents.quality_control_agent import QualityControlAgent
        agent = QualityControlAgent()
        agent.db_manager = env["db_manager"]
        
        await agent.initialize()
        
        result = await agent.process_business_logic({
            "operation": "inspect",
            "product_id": "P001",
            "quantity": 100
        })
        
        results["QualityControlAgent"] = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
        
        await agent.cleanup()
        
    except Exception as e:
        results["QualityControlAgent"] = f"❌ ERROR: {str(e)}"
    
    # Print results
    for agent_name, status in results.items():
        print(f"  {agent_name}: {status}")
    
    return results


async def test_workflow_4_shipping_fulfillment():
    """
    Workflow 4: Shipping and Fulfillment
    OrderAgent -> WarehouseAgent -> TransportAgent
    """
    print("\n" + "="*80)
    print("WORKFLOW 4: Shipping and Fulfillment")
    print("="*80)
    
    results = {}
    env = create_mock_agent_environment()
    
    # Test TransportAgent
    try:
        from agents.transport_agent_production import TransportAgentProduction
        agent = TransportAgentProduction()
        agent.db_manager = env["db_manager"]
        
        await agent.initialize()
        
        result = await agent.process_business_logic({
            "operation": "create_shipment",
            "order_id": "O001",
            "warehouse_id": "W001",
            "destination": "Customer Address"
        })
        
        results["TransportAgent"] = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
        
        await agent.cleanup()
        
    except Exception as e:
        results["TransportAgent"] = f"❌ ERROR: {str(e)}"
    
    # Print results
    for agent_name, status in results.items():
        print(f"  {agent_name}: {status}")
    
    return results


async def test_workflow_5_returns_after_sales():
    """
    Workflow 5: Returns and After-Sales
    AfterSalesAgent -> WarehouseAgent -> InventoryAgent -> PaymentAgent
    """
    print("\n" + "="*80)
    print("WORKFLOW 5: Returns and After-Sales")
    print("="*80)
    
    results = {}
    env = create_mock_agent_environment()
    
    # Test AfterSalesAgent
    try:
        from agents.after_sales_agent import AfterSalesAgent
        agent = AfterSalesAgent()
        agent.db_manager = env["db_manager"]
        
        await agent.initialize()
        
        result = await agent.process_business_logic({
            "operation": "create_return",
            "order_id": "O001",
            "reason": "defective",
            "items": [{"product_id": "P001", "quantity": 1}]
        })
        
        results["AfterSalesAgent"] = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
        
        await agent.cleanup()
        
    except Exception as e:
        results["AfterSalesAgent"] = f"❌ ERROR: {str(e)}"
    
    # Print results
    for agent_name, status in results.items():
        print(f"  {agent_name}: {status}")
    
    return results


async def test_workflow_6_marketplace_integration():
    """
    Workflow 6: Marketplace Integration
    MarketplaceConnector -> ProductAgent -> InventoryAgent -> OrderAgent
    """
    print("\n" + "="*80)
    print("WORKFLOW 6: Marketplace Integration")
    print("="*80)
    
    results = {}
    env = create_mock_agent_environment()
    
    # Test MarketplaceConnector
    try:
        from agents.marketplace_connector_agent_production import MarketplaceConnectorAgentProduction
        agent = MarketplaceConnectorAgentProduction()
        agent.db_manager = env["db_manager"]
        
        await agent.initialize()
        
        result = await agent.process_business_logic({
            "operation": "sync_orders",
            "marketplace": "amazon",
            "since": "2024-01-01"
        })
        
        results["MarketplaceConnector"] = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
        
        await agent.cleanup()
        
    except Exception as e:
        results["MarketplaceConnector"] = f"❌ ERROR: {str(e)}"
    
    # Print results
    for agent_name, status in results.items():
        print(f"  {agent_name}: {status}")
    
    return results


async def test_workflow_7_payment_processing():
    """
    Workflow 7: Payment Processing
    OrderAgent -> PaymentAgent -> BackofficeAgent
    """
    print("\n" + "="*80)
    print("WORKFLOW 7: Payment Processing")
    print("="*80)
    
    results = {}
    env = create_mock_agent_environment()
    
    # Test PaymentAgent
    try:
        from agents.payment_agent_enhanced import PaymentAgent
        agent = PaymentAgent()
        agent.db_manager = env["db_manager"]
        
        await agent.initialize()
        
        result = await agent.process_business_logic({
            "operation": "process_payment",
            "order_id": "O001",
            "amount": 100.00,
            "payment_method": "credit_card"
        })
        
        results["PaymentAgent"] = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
        
        await agent.cleanup()
        
    except Exception as e:
        results["PaymentAgent"] = f"❌ ERROR: {str(e)}"
    
    # Test BackofficeAgent
    try:
        from agents.backoffice_agent import BackofficeAgent
        agent = BackofficeAgent()
        agent.db_manager = env["db_manager"]
        
        await agent.initialize()
        
        result = await agent.process_business_logic({
            "operation": "onboard_merchant",
            "merchant_data": {
                "name": "Test Merchant",
                "email": "test@merchant.com"
            }
        })
        
        results["BackofficeAgent"] = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
        
        await agent.cleanup()
        
    except Exception as e:
        results["BackofficeAgent"] = f"❌ ERROR: {str(e)}"
    
    # Print results
    for agent_name, status in results.items():
        print(f"  {agent_name}: {status}")
    
    return results


async def run_all_workflows():
    """Run all workflow tests"""
    print("\n" + "="*80)
    print("MULTI-AGENT E-COMMERCE SYSTEM - END-TO-END WORKFLOW TESTS")
    print("="*80)
    
    all_results = {}
    
    # Run each workflow
    workflows = [
        ("Workflow 1: Order Creation", test_workflow_1_order_creation),
        ("Workflow 2: Product Management", test_workflow_2_product_management),
        ("Workflow 3: Warehouse Operations", test_workflow_3_warehouse_operations),
        ("Workflow 4: Shipping Fulfillment", test_workflow_4_shipping_fulfillment),
        ("Workflow 5: Returns After-Sales", test_workflow_5_returns_after_sales),
        ("Workflow 6: Marketplace Integration", test_workflow_6_marketplace_integration),
        ("Workflow 7: Payment Processing", test_workflow_7_payment_processing),
    ]
    
    for workflow_name, workflow_func in workflows:
        try:
            results = await workflow_func()
            all_results[workflow_name] = results
        except Exception as e:
            print(f"\n❌ {workflow_name} FAILED: {str(e)}")
            all_results[workflow_name] = {"error": str(e)}
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for workflow_name, results in all_results.items():
        print(f"\n{workflow_name}:")
        for agent_name, status in results.items():
            total_tests += 1
            if "✅ PASS" in status:
                passed_tests += 1
            else:
                failed_tests += 1
            print(f"  {agent_name}: {status}")
    
    print(f"\n{'='*80}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ({100*passed_tests//total_tests if total_tests > 0 else 0}%)")
    print(f"Failed: {failed_tests} ({100*failed_tests//total_tests if total_tests > 0 else 0}%)")
    print(f"{'='*80}\n")
    
    return all_results


if __name__ == "__main__":
    asyncio.run(run_all_workflows())

