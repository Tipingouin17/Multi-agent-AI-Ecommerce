#!/usr/bin/env python3
"""
Kafka Connectivity Verification Script

This script verifies Kafka connectivity and configuration based on the .env file.
It checks:
1. Environment variable loading
2. Kafka broker connectivity
3. Topic listing
4. Producer/Consumer basic operations
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaConnectionError, KafkaError
import socket

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

class KafkaVerifier:
    def __init__(self):
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.results = {
            'env_loaded': False,
            'network_reachable': False,
            'kafka_connected': False,
            'topics_listed': False,
            'producer_works': False,
            'consumer_works': False,
            'errors': []
        }
    
    def print_header(self, text):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80)
    
    def print_result(self, test_name, success, details=""):
        """Print test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
    
    def verify_env_variables(self):
        """Verify environment variables are loaded"""
        self.print_header("1. Environment Variables Check")
        
        env_vars = {
            'KAFKA_BOOTSTRAP_SERVERS': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
            'POSTGRES_PORT': os.getenv('POSTGRES_PORT'),
            'POSTGRES_NAME': os.getenv('POSTGRES_NAME'),
            'POSTGRES_USER': os.getenv('POSTGRES_USER'),
            'REDIS_HOST': os.getenv('REDIS_HOST'),
            'REDIS_PORT': os.getenv('REDIS_PORT'),
        }
        
        print("\nLoaded Environment Variables:")
        for key, value in env_vars.items():
            if value:
                # Mask passwords
                if 'PASSWORD' in key:
                    display_value = '*' * len(value) if value else 'Not set'
                else:
                    display_value = value
                print(f"  ✅ {key}: {display_value}")
            else:
                print(f"  ❌ {key}: Not set")
        
        kafka_servers = env_vars['KAFKA_BOOTSTRAP_SERVERS']
        if kafka_servers:
            self.results['env_loaded'] = True
            self.print_result("Environment variables loaded", True, f"Kafka: {kafka_servers}")
        else:
            self.results['errors'].append("KAFKA_BOOTSTRAP_SERVERS not set in .env")
            self.print_result("Environment variables loaded", False, "KAFKA_BOOTSTRAP_SERVERS not found")
        
        return kafka_servers
    
    def verify_network_connectivity(self):
        """Verify network connectivity to Kafka broker"""
        self.print_header("2. Network Connectivity Check")
        
        # Parse host and port
        try:
            if ':' in self.kafka_servers:
                host, port = self.kafka_servers.split(':')
                port = int(port)
            else:
                host = self.kafka_servers
                port = 9092
            
            print(f"\nTesting connection to {host}:{port}...")
            
            # Try to connect to the socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                self.results['network_reachable'] = True
                self.print_result("Network connectivity", True, f"{host}:{port} is reachable")
            else:
                self.results['errors'].append(f"Cannot reach {host}:{port}")
                self.print_result("Network connectivity", False, f"{host}:{port} is not reachable")
                print(f"   Error code: {result}")
                print(f"   Make sure Kafka is running at {host}:{port}")
        
        except Exception as e:
            self.results['errors'].append(f"Network check failed: {str(e)}")
            self.print_result("Network connectivity", False, str(e))
    
    async def verify_kafka_connection(self):
        """Verify Kafka broker connection"""
        self.print_header("3. Kafka Broker Connection Check")
        
        try:
            print(f"\nConnecting to Kafka at {self.kafka_servers}...")
            
            # Try to create admin client
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.kafka_servers,
                request_timeout_ms=10000
            )
            
            await admin_client.start()
            
            self.results['kafka_connected'] = True
            self.print_result("Kafka connection", True, f"Connected to {self.kafka_servers}")
            
            # List topics
            try:
                topics = await admin_client.list_topics()
                self.results['topics_listed'] = True
                self.print_result("List topics", True, f"Found {len(topics)} topics")
                
                if topics:
                    print("\n   Available topics:")
                    for topic in sorted(topics)[:10]:  # Show first 10 topics
                        print(f"     - {topic}")
                    if len(topics) > 10:
                        print(f"     ... and {len(topics) - 10} more")
                else:
                    print("   No topics found (this is normal for a fresh Kafka installation)")
            
            except Exception as e:
                self.results['errors'].append(f"Failed to list topics: {str(e)}")
                self.print_result("List topics", False, str(e))
            
            await admin_client.close()
        
        except KafkaConnectionError as e:
            self.results['errors'].append(f"Kafka connection failed: {str(e)}")
            self.print_result("Kafka connection", False, "Connection refused")
            print(f"   Error: {str(e)}")
            print(f"   Make sure Kafka is running at {self.kafka_servers}")
        
        except Exception as e:
            self.results['errors'].append(f"Kafka connection error: {str(e)}")
            self.print_result("Kafka connection", False, str(e))
    
    async def verify_producer(self):
        """Verify Kafka producer works"""
        self.print_header("4. Kafka Producer Check")
        
        if not self.results['kafka_connected']:
            self.print_result("Producer test", False, "Skipped (Kafka not connected)")
            return
        
        try:
            print(f"\nCreating producer for {self.kafka_servers}...")
            
            producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_servers,
                request_timeout_ms=10000
            )
            
            await producer.start()
            
            # Send a test message
            test_topic = "test_connectivity"
            test_message = b"Kafka connectivity test"
            
            print(f"Sending test message to topic '{test_topic}'...")
            await producer.send_and_wait(test_topic, test_message)
            
            self.results['producer_works'] = True
            self.print_result("Producer test", True, f"Successfully sent message to '{test_topic}'")
            
            await producer.stop()
        
        except Exception as e:
            self.results['errors'].append(f"Producer test failed: {str(e)}")
            self.print_result("Producer test", False, str(e))
    
    async def verify_consumer(self):
        """Verify Kafka consumer works"""
        self.print_header("5. Kafka Consumer Check")
        
        if not self.results['kafka_connected']:
            self.print_result("Consumer test", False, "Skipped (Kafka not connected)")
            return
        
        try:
            print(f"\nCreating consumer for {self.kafka_servers}...")
            
            consumer = AIOKafkaConsumer(
                'test_connectivity',
                bootstrap_servers=self.kafka_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                consumer_timeout_ms=5000,
                request_timeout_ms=10000
            )
            
            await consumer.start()
            
            self.results['consumer_works'] = True
            self.print_result("Consumer test", True, "Successfully created consumer")
            
            await consumer.stop()
        
        except Exception as e:
            self.results['errors'].append(f"Consumer test failed: {str(e)}")
            self.print_result("Consumer test", False, str(e))
    
    def print_summary(self):
        """Print verification summary"""
        self.print_header("VERIFICATION SUMMARY")
        
        total_tests = 6
        passed_tests = sum([
            self.results['env_loaded'],
            self.results['network_reachable'],
            self.results['kafka_connected'],
            self.results['topics_listed'],
            self.results['producer_works'],
            self.results['consumer_works']
        ])
        
        print(f"\nTests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {100 * passed_tests / total_tests:.1f}%")
        
        if passed_tests == total_tests:
            print("\n✅ ✅ ✅  ALL TESTS PASSED! KAFKA IS FULLY OPERATIONAL  ✅ ✅ ✅")
            print("\nYour agents will be able to connect to Kafka successfully.")
        elif self.results['kafka_connected']:
            print("\n⚠️  KAFKA IS CONNECTED BUT SOME TESTS FAILED")
            print("\nKafka is reachable, but some features may not work properly.")
        else:
            print("\n❌ KAFKA CONNECTION FAILED")
            print("\nKafka is not accessible. Please check:")
            print("  1. Kafka is running")
            print(f"  2. Kafka is listening on {self.kafka_servers}")
            print("  3. No firewall blocking the connection")
            print("  4. .env file has correct KAFKA_BOOTSTRAP_SERVERS value")
        
        if self.results['errors']:
            print("\nErrors encountered:")
            for i, error in enumerate(self.results['errors'], 1):
                print(f"  {i}. {error}")
        
        print("\n" + "=" * 80)
    
    async def run_verification(self):
        """Run all verification tests"""
        print("\n" + "🔍" * 30)
        print("KAFKA CONNECTIVITY VERIFICATION")
        print("🔍" * 30)
        
        # 1. Check environment variables
        kafka_servers = self.verify_env_variables()
        
        if not kafka_servers:
            print("\n❌ Cannot proceed without KAFKA_BOOTSTRAP_SERVERS")
            return
        
        # 2. Check network connectivity
        self.verify_network_connectivity()
        
        # 3. Check Kafka connection
        await self.verify_kafka_connection()
        
        # 4. Test producer
        await self.verify_producer()
        
        # 5. Test consumer
        await self.verify_consumer()
        
        # Print summary
        self.print_summary()


async def main():
    """Main entry point"""
    verifier = KafkaVerifier()
    await verifier.run_verification()


if __name__ == "__main__":
    asyncio.run(main())

