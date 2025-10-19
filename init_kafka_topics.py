#!/usr/bin/env python3
"""
Kafka Topics Initialization Script for Multi-Agent E-commerce System

This script creates all necessary Kafka topics for inter-agent communication.
Run this once after starting Kafka.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import TopicAlreadyExistsError
except ImportError:
    print("ERROR: kafka-python not installed")
    print("Install with: pip install kafka-python")
    sys.exit(1)


def create_kafka_topics():
    """Create all Kafka topics needed by the agents."""
    
    print("="*70)
    print("Multi-Agent E-commerce System - Kafka Topics Initialization")
    print("="*70)
    print()
    
    # Get Kafka configuration from environment
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    print(f"Kafka Configuration:")
    print(f"  Bootstrap Servers: {kafka_bootstrap_servers}")
    print()
    
    # Define all topics needed by agents
    topics = [
        # Agent-specific topics
        "order_agent_topic",
        "product_agent_topic",
        "inventory_agent_topic",
        "warehouse_selection_agent_topic",
        "carrier_selection_agent_topic",
        "demand_forecasting_agent_topic",
        "dynamic_pricing_agent_topic",
        "customer_communication_agent_topic",
        "reverse_logistics_agent_topic",
        "risk_anomaly_detection_agent_topic",
        "standard_marketplace_agent_topic",
        "refurbished_marketplace_agent_topic",
        "d2c_ecommerce_agent_topic",
        "ai_monitoring_agent_topic",
        
        # System topics
        "monitoring_agent_topic",
        "system_events",
        "agent_status",
        "alerts",
    ]
    
    try:
        print("Connecting to Kafka...")
        admin_client = KafkaAdminClient(
            bootstrap_servers=kafka_bootstrap_servers,
            client_id='topic_initializer'
        )
        print("SUCCESS: Connected to Kafka")
        print()
        
        # Create NewTopic objects
        new_topics = [
            NewTopic(
                name=topic,
                num_partitions=3,
                replication_factor=1
            )
            for topic in topics
        ]
        
        print(f"Creating {len(topics)} topics...")
        print()
        
        # Create topics
        created_count = 0
        exists_count = 0
        
        for topic_obj in new_topics:
            try:
                admin_client.create_topics([topic_obj], validate_only=False)
                print(f"  SUCCESS: Created topic '{topic_obj.name}'")
                created_count += 1
            except TopicAlreadyExistsError:
                print(f"  INFO: Topic '{topic_obj.name}' already exists")
                exists_count += 1
            except Exception as e:
                print(f"  ERROR: Failed to create topic '{topic_obj.name}': {e}")
        
        print()
        print("="*70)
        print(f"Topic initialization complete!")
        print(f"  Created: {created_count} topics")
        print(f"  Already existed: {exists_count} topics")
        print(f"  Total: {len(topics)} topics")
        print("="*70)
        print()
        print("You can now start the agents with: .\\start-system.ps1")
        print()
        
        admin_client.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to connect to Kafka: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Ensure Kafka is running:")
        print("     docker ps | findstr kafka")
        print("  2. Check Kafka logs:")
        print("     docker logs multi-agent-kafka")
        print("  3. Verify Kafka is accessible:")
        print(f"     telnet {kafka_bootstrap_servers.split(':')[0]} {kafka_bootstrap_servers.split(':')[1]}")
        print()
        return False


if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed, using environment variables only")
    
    # Run initialization
    success = create_kafka_topics()
    sys.exit(0 if success else 1)

