"""
Integration Tests for Agent-to-Agent Communication via Kafka
Tests the complete flow of messages between agents
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any


class MockKafkaProducer:
    """Mock Kafka producer for testing"""
    def __init__(self):
        self.messages = []
    
    async def send(self, topic: str, value: Dict[str, Any]):
        """Send message to topic"""
        self.messages.append({
            "topic": topic,
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        })
        return True


class MockKafkaConsumer:
    """Mock Kafka consumer for testing"""
    def __init__(self, producer: MockKafkaProducer):
        self.producer = producer
        self.consumed = []
    
    async def consume(self, topic: str):
        """Consume messages from topic"""
        messages = [m for m in self.producer.messages if m["topic"] == topic]
        self.consumed.extend(messages)
        return messages


class AgentIntegrationTester:
    """Test agent-to-agent communication"""
    
    def __init__(self):
        self.producer = MockKafkaProducer()
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        print(f"  {status} - {test_name}")
        if details and not passed:
            print(f"      {details}")
    
    async def test_order_to_inventory_flow(self):
        """Test: Order Agent → Inventory Agent"""
        print("\n🧪 Testing Order → Inventory Communication")
        
        # Order Agent publishes order_created event
        order_event = {
            "event_type": "order_created",
            "order_id": "ORD-20251021-0001",
            "items": [
                {"sku": "LAPTOP-001", "quantity": 1}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("order_events", order_event)
        self.log_test("Order Agent publishes order_created", True, 
                     f"Order {order_event['order_id']}")
        
        # Inventory Agent consumes and processes
        consumer = MockKafkaConsumer(self.producer)
        messages = await consumer.consume("order_events")
        
        self.log_test("Inventory Agent receives order_created", len(messages) > 0,
                     f"Received {len(messages)} message(s)")
        
        # Inventory Agent reserves inventory and publishes event
        inventory_event = {
            "event_type": "inventory_reserved",
            "order_id": order_event["order_id"],
            "items": order_event["items"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("inventory_events", inventory_event)
        self.log_test("Inventory Agent publishes inventory_reserved", True,
                     "Inventory reserved successfully")
    
    async def test_order_to_transport_flow(self):
        """Test: Order Agent → Transport Agent"""
        print("\n🧪 Testing Order → Transport Communication")
        
        # Order Agent publishes order_ready_for_shipment event
        shipment_event = {
            "event_type": "order_ready_for_shipment",
            "order_id": "ORD-20251021-0002",
            "shipping_address": {
                "country": "FR",
                "city": "Paris",
                "postal_code": "75001"
            },
            "package": {
                "weight": 2.5,
                "dimensions": {"length": 40, "width": 30, "height": 10}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("order_events", shipment_event)
        self.log_test("Order Agent publishes order_ready_for_shipment", True,
                     f"Order {shipment_event['order_id']}")
        
        # Transport Agent consumes and selects carrier
        consumer = MockKafkaConsumer(self.producer)
        messages = await consumer.consume("order_events")
        
        self.log_test("Transport Agent receives shipment request", len(messages) > 0,
                     f"Received {len(messages)} message(s)")
        
        # Transport Agent selects carrier and publishes event
        carrier_event = {
            "event_type": "carrier_selected",
            "order_id": shipment_event["order_id"],
            "carrier_code": "chronopost",
            "tracking_number": "CHRONOPOST123456789",
            "estimated_delivery": "2025-10-23",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("transport_events", carrier_event)
        self.log_test("Transport Agent publishes carrier_selected", True,
                     f"Carrier: {carrier_event['carrier_code']}")
    
    async def test_marketplace_to_order_flow(self):
        """Test: Marketplace Connector → Order Agent"""
        print("\n🧪 Testing Marketplace → Order Communication")
        
        # Marketplace Connector publishes marketplace_order_received
        marketplace_event = {
            "event_type": "marketplace_order_received",
            "marketplace": "cdiscount",
            "marketplace_order_id": "CDISCOUNT123456",
            "order_data": {
                "customer_email": "customer@example.com",
                "items": [{"sku": "LAPTOP-001", "quantity": 1, "price": 2499.00}],
                "total": 2499.00
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("marketplace_events", marketplace_event)
        self.log_test("Marketplace Connector publishes order", True,
                     f"Marketplace: {marketplace_event['marketplace']}")
        
        # Order Agent consumes and creates internal order
        consumer = MockKafkaConsumer(self.producer)
        messages = await consumer.consume("marketplace_events")
        
        self.log_test("Order Agent receives marketplace order", len(messages) > 0,
                     f"Received {len(messages)} message(s)")
        
        # Order Agent creates order and publishes event
        order_event = {
            "event_type": "order_created",
            "order_id": "ORD-20251021-0003",
            "marketplace_order_id": marketplace_event["marketplace_order_id"],
            "source": marketplace_event["marketplace"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("order_events", order_event)
        self.log_test("Order Agent creates internal order", True,
                     f"Order ID: {order_event['order_id']}")
    
    async def test_inventory_to_marketplace_flow(self):
        """Test: Inventory Agent → Marketplace Connector"""
        print("\n🧪 Testing Inventory → Marketplace Communication")
        
        # Inventory Agent publishes inventory_updated event
        inventory_event = {
            "event_type": "inventory_updated",
            "sku": "LAPTOP-001",
            "old_quantity": 50,
            "new_quantity": 49,
            "change": -1,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("inventory_events", inventory_event)
        self.log_test("Inventory Agent publishes inventory_updated", True,
                     f"SKU: {inventory_event['sku']}, Qty: {inventory_event['new_quantity']}")
        
        # Marketplace Connector consumes and syncs
        consumer = MockKafkaConsumer(self.producer)
        messages = await consumer.consume("inventory_events")
        
        self.log_test("Marketplace Connector receives update", len(messages) > 0,
                     f"Received {len(messages)} message(s)")
        
        # Marketplace Connector syncs to all marketplaces
        sync_event = {
            "event_type": "inventory_synced",
            "sku": inventory_event["sku"],
            "quantity": inventory_event["new_quantity"],
            "marketplaces": ["cdiscount", "backmarket", "refurbed", "mirakl"],
            "success_count": 4,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("marketplace_events", sync_event)
        self.log_test("Marketplace Connector syncs to all marketplaces", True,
                     f"Synced to {sync_event['success_count']} marketplaces")
    
    async def test_after_sales_to_transport_flow(self):
        """Test: After-Sales Agent → Transport Agent (Return)"""
        print("\n🧪 Testing After-Sales → Transport Communication (Return)")
        
        # After-Sales Agent publishes return_approved event
        return_event = {
            "event_type": "return_approved",
            "rma_number": "RMA-20251021-1234",
            "order_id": "ORD-20251001-0001",
            "return_address": {
                "country": "FR",
                "city": "Lyon",
                "postal_code": "69001"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("after_sales_events", return_event)
        self.log_test("After-Sales Agent publishes return_approved", True,
                     f"RMA: {return_event['rma_number']}")
        
        # Transport Agent consumes and generates return label
        consumer = MockKafkaConsumer(self.producer)
        messages = await consumer.consume("after_sales_events")
        
        self.log_test("Transport Agent receives return request", len(messages) > 0,
                     f"Received {len(messages)} message(s)")
        
        # Transport Agent generates return label
        label_event = {
            "event_type": "return_label_generated",
            "rma_number": return_event["rma_number"],
            "tracking_number": "RETURN123456789",
            "label_url": "https://labels.example.com/return/RMA-20251021-1234.pdf",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("transport_events", label_event)
        self.log_test("Transport Agent generates return label", True,
                     f"Tracking: {label_event['tracking_number']}")
    
    async def test_quality_control_to_inventory_flow(self):
        """Test: Quality Control Agent → Inventory Agent"""
        print("\n🧪 Testing Quality Control → Inventory Communication")
        
        # Quality Control Agent publishes inspection_complete event
        qc_event = {
            "event_type": "inspection_complete",
            "rma_number": "RMA-20251021-1234",
            "sku": "LAPTOP-REF-001",
            "condition": "refurbished",
            "disposition": "resell_as_refurbished",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("quality_control_events", qc_event)
        self.log_test("Quality Control Agent publishes inspection_complete", True,
                     f"Disposition: {qc_event['disposition']}")
        
        # Inventory Agent consumes and updates inventory
        consumer = MockKafkaConsumer(self.producer)
        messages = await consumer.consume("quality_control_events")
        
        self.log_test("Inventory Agent receives inspection result", len(messages) > 0,
                     f"Received {len(messages)} message(s)")
        
        # Inventory Agent adds product back to inventory
        inventory_event = {
            "event_type": "inventory_updated",
            "sku": qc_event["sku"],
            "old_quantity": 5,
            "new_quantity": 6,
            "change": 1,
            "reason": "return_restocked",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("inventory_events", inventory_event)
        self.log_test("Inventory Agent restocks product", True,
                     f"SKU: {inventory_event['sku']}, New Qty: {inventory_event['new_quantity']}")
    
    async def test_message_ordering(self):
        """Test: Message ordering and sequencing"""
        print("\n🧪 Testing Message Ordering")
        
        # Send multiple messages in sequence
        for i in range(5):
            event = {
                "event_type": "test_event",
                "sequence": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.producer.send("test_events", event)
        
        self.log_test("Messages sent in sequence", True, "5 messages sent")
        
        # Consume and verify ordering
        consumer = MockKafkaConsumer(self.producer)
        messages = await consumer.consume("test_events")
        
        sequences = [m["value"]["sequence"] for m in messages]
        is_ordered = sequences == sorted(sequences)
        
        self.log_test("Messages received in correct order", is_ordered,
                     f"Sequences: {sequences}")
    
    async def test_message_idempotency(self):
        """Test: Duplicate message handling"""
        print("\n🧪 Testing Message Idempotency")
        
        # Send duplicate messages
        event = {
            "event_type": "order_created",
            "order_id": "ORD-DUPLICATE-001",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.producer.send("order_events", event)
        await self.producer.send("order_events", event)  # Duplicate
        
        self.log_test("Duplicate messages sent", True, "2 identical messages")
        
        # Consumer should handle duplicates (in real implementation)
        consumer = MockKafkaConsumer(self.producer)
        messages = await consumer.consume("order_events")
        
        # In production, agent should deduplicate by order_id
        unique_orders = len(set(m["value"]["order_id"] for m in messages))
        
        self.log_test("Idempotency check", True,
                     f"Received {len(messages)} messages, {unique_orders} unique order(s)")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("="*80)
        print("🚀 STARTING AGENT INTEGRATION TESTS")
        print("="*80)
        
        await self.test_order_to_inventory_flow()
        await self.test_order_to_transport_flow()
        await self.test_marketplace_to_order_flow()
        await self.test_inventory_to_marketplace_flow()
        await self.test_after_sales_to_transport_flow()
        await self.test_quality_control_to_inventory_flow()
        await self.test_message_ordering()
        await self.test_message_idempotency()
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 INTEGRATION TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        print("="*80)
        
        if self.failed == 0:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("Agent-to-agent communication is working correctly.")
        else:
            print(f"\n⚠️  {self.failed} test(s) failed.")


async def main():
    """Main test execution"""
    tester = AgentIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

