"""
Enhanced Transport Management Agent

This agent manages all aspects of shipping and transportation with integrated support for:
- European carrier API integrations (DPD, GLS, Hermes, Colissimo, Chronopost, etc.)
- Real-time label generation
- Route optimization
- Shipment tracking
- Carrier selection based on cost, speed, and reliability
- Contract-based pricing
- Performance monitoring

European Carriers Supported:
- DPD (Dynamic Parcel Distribution)
- GLS (General Logistics Systems)
- Hermes/Evri
- Colissimo (La Poste)
- Chronopost
- TNT/FedEx Europe
- DHL Express Europe
- UPS Europe
- Colis Privé

Technologies:
- Carrier-specific APIs for label generation and tracking
- OpenAI for intelligent carrier selection
- Kafka for inter-agent communication
- PostgreSQL for data storage
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from shared.db_helpers import DatabaseHelper
import requests
from decimal import Decimal
import structlog
import sys
from contextlib import asynccontextmanager

# AI
from openai import OpenAI

# Database
import psycopg2
from psycopg2.extras import RealDictCursor

# Kafka
from kafka import KafkaProducer, KafkaConsumer

# FastAPI
from fastapi import FastAPI, HTTPException, Depends, Body, Path
from fastapi.middleware.cors import CORSMiddleware

# Configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'multi_agent_ecommerce'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

KAFKA_CONFIG = {
    'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    'transport_topic': 'transport_management_requests',
    'response_topic': 'transport_management_responses'
}

# Carrier API configurations (from environment)
CARRIER_CONFIGS = {
    'dpd': {
        'api_url': os.getenv('DPD_API_URL', 'https://api.dpd.com/v1'),
        'api_key': os.getenv('DPD_API_KEY'),
        'customer_number': os.getenv('DPD_CUSTOMER_NUMBER')
    },
    'gls': {
        'api_url': os.getenv('GLS_API_URL', 'https://api.gls-group.eu/v1'),
        'api_key': os.getenv('GLS_API_KEY'),
        'customer_id': os.getenv('GLS_CUSTOMER_ID')
    },
    'hermes': {
        'api_url': os.getenv('HERMES_API_URL', 'https://api.hermesworld.com/v1'),
        'api_key': os.getenv('HERMES_API_KEY'),
        'client_id': os.getenv('HERMES_CLIENT_ID')
    },
    'colissimo': {
        'api_url': os.getenv('COLISSIMO_API_URL', 'https://ws.colissimo.fr/sls-ws'),
        'contract_number': os.getenv('COLISSIMO_CONTRACT_NUMBER'),
        'password': os.getenv('COLISSIMO_PASSWORD')
    },
    'chronopost': {
        'api_url': os.getenv('CHRONOPOST_API_URL', 'https://ws.chronopost.fr/shipping-cxf'),
        'account_number': os.getenv('CHRONOPOST_ACCOUNT_NUMBER'),
        'password': os.getenv('CHRONOPOST_PASSWORD')
    },
    'dhl': {
        'api_url': os.getenv('DHL_API_URL', 'https://api-eu.dhl.com/parcel/de/shipping/v2'),
        'api_key': os.getenv('DHL_API_KEY'),
        'api_secret': os.getenv('DHL_API_SECRET')
    },
    'ups': {
        'api_url': os.getenv('UPS_API_URL', 'https://onlinetools.ups.com/api'),
        'access_key': os.getenv('UPS_ACCESS_KEY'),
        'username': os.getenv('UPS_USERNAME'),
        'password': os.getenv('UPS_PASSWORD')
    },
    'colis_prive': {
        'api_url': os.getenv('COLIS_PRIVE_API_URL', 'https://api.colisprive.com/v1'),
        'api_key': os.getenv('COLIS_PRIVE_API_KEY'),
        'customer_code': os.getenv('COLIS_PRIVE_CUSTOMER_CODE')
    }
}

# Initialize structured logger
logger = structlog.get_logger(__name__)

# --- FastAPI Setup ---
# Module-level app instance for Uvicorn
app = FastAPI(title="Transport Management Agent API",
              description="Enhanced agent for managing shipping and transportation.")

# Agent instance (will be initialized later)
transport_agent: Optional['TransportManagementAgent'] = None

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TransportManagementAgent:
    """Enhanced agent for managing shipping and transportation"""
    
    def __init__(self):
        self.db_conn = None
        self.kafka_producer = None
        self.kafka_consumer = None
        self.openai_client = None
        self.carrier_integrations = {}
        self.is_initialized = False
        
        # Add project root to Python path for shared modules
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        project_root = os.path.dirname(current_dir)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        self.setup_routes()
    
    @asynccontextmanager
    async def lifespan_context(self, app: FastAPI):
        """
        FastAPI Lifespan Context Manager for agent startup and shutdown.
        """
        # Startup
        logger.info("FastAPI Lifespan Startup: Transport Management Agent")
        await self.initialize()
        
        yield
        
        # Shutdown
        logger.info("FastAPI Lifespan Shutdown: Transport Management Agent")
        await self.cleanup()
        logger.info("Transport Management Agent API shutdown complete")
        
    async def initialize(self):
        """Initialize connections and carrier integrations"""
        if self.is_initialized:
            return
            
        try:
            # Database connection
            self.db_conn = psycopg2.connect(**DATABASE_CONFIG)
            logger.info("Connected to database")
            
            # Kafka producer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("Kafka producer initialized")
            
            # Kafka consumer
            self.kafka_consumer = KafkaConsumer(
                KAFKA_CONFIG['transport_topic'],
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='transport_management_agent',
                auto_offset_reset='latest'
            )
            logger.info("Kafka consumer initialized")
            
            # OpenAI client
            self.openai_client = OpenAI()
            logger.info("OpenAI client initialized")
            
            # Initialize carrier integrations
            self.initialize_carrier_integrations()
            
            self.is_initialized = True
            logger.info("Transport Management Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            raise
    
    def initialize_carrier_integrations(self):
        """Initialize carrier API integrations"""
        self.carrier_integrations = {
            'dpd': DPDIntegration(CARRIER_CONFIGS['dpd']),
            'gls': GLSIntegration(CARRIER_CONFIGS['gls']),
            'hermes': HermesIntegration(CARRIER_CONFIGS['hermes']),
            'colissimo': ColissimoIntegration(CARRIER_CONFIGS['colissimo']),
            'chronopost': ChronopostIntegration(CARRIER_CONFIGS['chronopost']),
            'dhl': DHLIntegration(CARRIER_CONFIGS['dhl']),
            'ups': UPSIntegration(CARRIER_CONFIGS['ups']),
            'colis_prive': ColisPriveIntegration(CARRIER_CONFIGS['colis_prive'])
        }
        logger.info(f"Initialized {len(self.carrier_integrations)} carrier integrations")
    
    def select_carrier(self, shipment_details: Dict) -> Dict[str, Any]:
        """
        Select the best carrier for a shipment using AI and historical data
        
        Args:
            shipment_details: Dictionary with shipment information
                - origin: Origin address
                - destination: Destination address
                - weight: Package weight in kg
                - dimensions: Package dimensions (length, width, height in cm)
                - service_level: Desired service level (standard, express, overnight)
                - delivery_date: Expected delivery date
                - special_handling: Any special requirements
        
        Returns:
            Dictionary with selected carrier and pricing
        """
        try:
            logger.info("Selecting carrier for shipment")
            
            # Get available carriers and their quotes
            carrier_quotes = self.get_carrier_quotes(shipment_details)
            
            # Get historical performance data
            performance_data = self.get_carrier_performance(
                origin_country=shipment_details['origin']['country'],
                destination_country=shipment_details['destination']['country']
            )
            
            # Use AI to select the best carrier
            selected_carrier = self.ai_select_carrier(
                shipment_details=shipment_details,
                carrier_quotes=carrier_quotes,
                performance_data=performance_data
            )
            
            logger.info(f"Selected carrier: {selected_carrier['carrier_code']}")
            
            return {
                'success': True,
                'selected_carrier': selected_carrier,
                'all_quotes': carrier_quotes
            }
            
        except Exception as e:
            logger.error(f"Error selecting carrier: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_carrier_quotes(self, shipment_details: Dict) -> List[Dict]:
        """Get quotes from all available carriers"""
        quotes = []
        
        for carrier_code, integration in self.carrier_integrations.items():
            try:
                # Check if carrier services this route
                if not integration.services_route(
                    shipment_details['origin']['country'],
                    shipment_details['destination']['country']
                ):
                    continue
                
                # Get quote from carrier
                quote = integration.get_quote(shipment_details)
                
                if quote:
                    quotes.append({
                        'carrier_code': carrier_code,
                        'carrier_name': integration.carrier_name,
                        'service_level': quote['service_level'],
                        'price': quote['price'],
                        'currency': quote['currency'],
                        'estimated_delivery': quote['estimated_delivery'],
                        'transit_days': quote['transit_days']
                    })
            except Exception as e:
                logger.warning(f"Error getting quote from {carrier_code}: {str(e)}")
                continue
        
        return quotes
    
    def get_carrier_performance(self, origin_country: str, destination_country: str) -> Dict:
        """Get historical performance data for carriers on this route"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        carrier_code,
                        COUNT(*) as total_shipments,
                        AVG(CASE WHEN delivered_on_time THEN 1 ELSE 0 END) as on_time_rate,
                        AVG(actual_transit_days) as avg_transit_days,
                        AVG(customer_rating) as avg_rating
                    FROM shipment_history
                    WHERE origin_country = %s 
                    AND destination_country = %s
                    AND created_at >= NOW() - INTERVAL '90 days'
                    GROUP BY carrier_code
                """, (origin_country, destination_country))
                
                performance = {}
                for row in cursor.fetchall():
                    performance[row['carrier_code']] = dict(row)
                
                return performance
        except Exception as e:
            logger.error(f"Error fetching carrier performance: {str(e)}")
            return {}
    
    def ai_select_carrier(self, shipment_details: Dict, carrier_quotes: List[Dict], 
                         performance_data: Dict) -> Dict:
        """
        Use AI to select the best carrier based on multiple factors
        
        Factors considered:
        - Price
        - Delivery speed
        - Historical on-time performance
        - Customer ratings
        - Service level requirements
        - Special handling capabilities
        """
        try:
            # Prepare context for AI
            context = f"""
You are an AI assistant specialized in carrier selection for e-commerce shipping.

Shipment Details:
- Origin: {shipment_details['origin']['country']}
- Destination: {shipment_details['destination']['country']}
- Weight: {shipment_details['weight']} kg
- Dimensions: {shipment_details['dimensions']}
- Required Service Level: {shipment_details.get('service_level', 'standard')}
- Expected Delivery Date: {shipment_details.get('delivery_date', 'ASAP')}
- Special Handling: {shipment_details.get('special_handling', 'None')}

Available Carrier Quotes:
{json.dumps(carrier_quotes, indent=2)}

Historical Performance Data (last 90 days):
{json.dumps(performance_data, indent=2)}

Selection Criteria (in order of priority):
1. On-time delivery (must meet expected delivery date)
2. Historical on-time performance rate
3. Price (optimize for cost)
4. Customer ratings
5. Transit time

Select the best carrier and explain your reasoning. Respond in JSON format:
{{
    "carrier_code": "selected_carrier_code",
    "reasoning": "explanation of selection",
    "confidence": 0.95,
    "risk_factors": ["any potential risks"]
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a specialized AI for carrier selection in e-commerce logistics. Always respond with valid JSON."},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse AI response
            response_text = response.choices[0].message.content.strip()
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
            
            ai_selection = json.loads(response_text)
            
            # Find the selected carrier's quote
            selected_quote = next(
                (q for q in carrier_quotes if q['carrier_code'] == ai_selection['carrier_code']),
                None
            )
            
            if not selected_quote:
                # Fallback to cheapest carrier
                selected_quote = min(carrier_quotes, key=lambda x: x['price'])
                ai_selection['carrier_code'] = selected_quote['carrier_code']
                ai_selection['reasoning'] = "Fallback to lowest price carrier"
            
            return {
                **selected_quote,
                'ai_reasoning': ai_selection['reasoning'],
                'confidence': ai_selection.get('confidence', 0.8),
                'risk_factors': ai_selection.get('risk_factors', [])
            }
            
        except Exception as e:
            logger.error(f"Error in AI carrier selection: {str(e)}")
            # Fallback to cheapest carrier
            if carrier_quotes:
                return min(carrier_quotes, key=lambda x: x['price'])
            raise
    
    def generate_shipping_label(self, shipment_id: int, carrier_code: str) -> Dict[str, Any]:
        """
        Generate shipping label using carrier API
        
        Args:
            shipment_id: ID of the shipment
            carrier_code: Code of the carrier to use
        
        Returns:
            Dictionary with label URL and tracking number
        """
        try:
            logger.info(f"Generating label for shipment {shipment_id} with {carrier_code}")
            
            # Get shipment details
            shipment = self.get_shipment_details(shipment_id)
            
            if not shipment:
                raise ValueError(f"Shipment {shipment_id} not found")
            
            # Get carrier integration
            integration = self.carrier_integrations.get(carrier_code)
            
            if not integration:
                raise ValueError(f"Carrier {carrier_code} not supported")
            
            # Generate label via carrier API
            label_result = integration.generate_label(shipment)
            
            # Save label information
            self.save_label_info(shipment_id, label_result)
            
            # Send document generation request for PDF label
            self.request_label_document(shipment_id, label_result)
            
            logger.info(f"Label generated: {label_result['tracking_number']}")
            
            return {
                'success': True,
                'tracking_number': label_result['tracking_number'],
                'label_url': label_result['label_url'],
                'label_format': label_result['format']
            }
            
        except Exception as e:
            logger.error(f"Error generating shipping label: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def track_shipment(self, tracking_number: str, carrier_code: str) -> Dict[str, Any]:
        """
        Track a shipment using carrier API
        
        Args:
            tracking_number: Tracking number
            carrier_code: Carrier code
        
        Returns:
            Dictionary with tracking events and current status
        """
        try:
            logger.info(f"Tracking shipment: {tracking_number} ({carrier_code})")
            
            # Get carrier integration
            integration = self.carrier_integrations.get(carrier_code)
            
            if not integration:
                raise ValueError(f"Carrier {carrier_code} not supported")
            
            # Get tracking information from carrier API
            tracking_info = integration.track_shipment(tracking_number)
            
            # Update shipment status in database
            self.update_shipment_status(tracking_number, tracking_info)
            
            return {
                'success': True,
                'tracking_number': tracking_number,
                'status': tracking_info['status'],
                'events': tracking_info['events'],
                'estimated_delivery': tracking_info.get('estimated_delivery'),
                'current_location': tracking_info.get('current_location')
            }
            
        except Exception as e:
            logger.error(f"Error tracking shipment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def optimize_route(self, shipment_details: Dict) -> Dict[str, Any]:
        """
        Request route optimization from carrier
        
        Args:
            shipment_details: Shipment information
        
        Returns:
            Optimized route information
        """
        try:
            carrier_code = shipment_details.get('carrier_code')
            integration = self.carrier_integrations.get(carrier_code)
            
            if not integration or not hasattr(integration, 'optimize_route'):
                return {
                    'success': False,
                    'error': 'Route optimization not supported by this carrier'
                }
            
            route = integration.optimize_route(shipment_details)
            
            return {
                'success': True,
                'route': route
            }
            
        except Exception as e:
            logger.error(f"Error optimizing route: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_shipment_details(self, shipment_id: int) -> Optional[Dict]:
        """Get shipment details from database"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM shipments WHERE id = %s
                """, (shipment_id,))
                shipment = cursor.fetchone()
                return dict(shipment) if shipment else None
        except Exception as e:
            logger.error(f"Error fetching shipment details: {str(e)}")
            return None
    
    def save_label_info(self, shipment_id: int, label_result: Dict):
        """Save label information to database"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE shipments
                    SET tracking_number = %s,
                        label_url = %s,
                        label_format = %s,
                        label_generated_at = %s,
                        status = 'label_generated'
                    WHERE id = %s
                """, (
                    label_result['tracking_number'],
                    label_result['label_url'],
                    label_result['format'],
                    datetime.now(),
                    shipment_id
                ))
                self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error saving label info: {str(e)}")
            self.db_conn.rollback()
    
    def request_label_document(self, shipment_id: int, label_result: Dict):
        """Request document generation for shipping label"""
        try:
            message = {
                'type': 'generate_shipping_label',
                'request_id': f"label_{shipment_id}_{datetime.now().timestamp()}",
                'shipment_id': shipment_id,
                'format': 'PDF',
                'label_data': label_result
            }
            self.kafka_producer.send('document_generation_requests', message)
        except Exception as e:
            logger.error(f"Error requesting label document: {str(e)}")
    
    def update_shipment_status(self, tracking_number: str, tracking_info: Dict):
        """Update shipment status in database"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE shipments
                    SET status = %s,
                        current_location = %s,
                        estimated_delivery = %s,
                        last_tracking_update = %s,
                        tracking_events = %s
                    WHERE tracking_number = %s
                """, (
                    tracking_info['status'],
                    tracking_info.get('current_location'),
                    tracking_info.get('estimated_delivery'),
                    datetime.now(),
                    json.dumps(tracking_info['events']),
                    tracking_number
                ))
                self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error updating shipment status: {str(e)}")
            self.db_conn.rollback()
    
    def process_kafka_message(self, message: Dict):
        """Process incoming Kafka message"""
        try:
            request_type = message.get('type')
            request_id = message.get('request_id')
            
            logger.info(f"Processing request {request_id}: {request_type}")
            
            result = None
            
            if request_type == 'select_carrier':
                result = self.select_carrier(message.get('shipment_details'))
            elif request_type == 'generate_label':
                result = self.generate_shipping_label(
                    message.get('shipment_id'),
                    message.get('carrier_code')
                )
            elif request_type == 'track_shipment':
                result = self.track_shipment(
                    message.get('tracking_number'),
                    message.get('carrier_code')
                )
            elif request_type == 'optimize_route':
                result = self.optimize_route(message.get('shipment_details'))
            else:
                result = {'success': False, 'error': f'Unknown request type: {request_type}'}
            
            # Send response
            response = {
                'request_id': request_id,
                'type': request_type,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            self.kafka_producer.send(KAFKA_CONFIG['response_topic'], response)
            logger.info(f"Sent response for request {request_id}")
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    # --- FastAPI Routes ---
    def setup_routes(self):
        """Sets up FastAPI routes for the agent."""
        
        @app.get("/health", summary="Health Check", tags=["Monitoring"])
        async def health_check():
            """Endpoint to check the health of the agent and its connections."""
            if not transport_agent.is_initialized:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            return {"status": "healthy", "db_connected": transport_agent.db_conn is not None}

        @app.post("/select_carrier", summary="Select the best carrier for a shipment", tags=["Transportation"])
        async def select_carrier_endpoint(shipment_details: Dict = Body(..., description="Shipment details")):
            """Endpoint to select the best carrier using AI."""
            if not transport_agent.is_initialized:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            return transport_agent.select_carrier(shipment_details)

        @app.post("/generate_label", summary="Generate shipping label", tags=["Transportation"])
        async def generate_label_endpoint(shipment_id: int = Body(..., embed=True), carrier_code: str = Body(..., embed=True)):
            """Endpoint to generate a shipping label."""
            if not transport_agent.is_initialized:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            return transport_agent.generate_shipping_label(shipment_id, carrier_code)

        @app.get("/track_shipment", summary="Track a shipment", tags=["Transportation"])
        async def track_shipment_endpoint(tracking_number: str, carrier_code: str):
            """Endpoint to track a shipment."""
            if not transport_agent.is_initialized:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            return transport_agent.track_shipment(tracking_number, carrier_code)

        @app.post("/optimize_route", summary="Optimize a delivery route", tags=["Transportation"])
        async def optimize_route_endpoint(shipment_details: Dict = Body(..., description="Shipment details")):
            """Endpoint to optimize a delivery route."""
            if not transport_agent.is_initialized:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            return transport_agent.optimize_route(shipment_details)

    # --- Kafka Processing (Can be run in a separate thread/process) ---
    async def run_kafka_consumer(self):
        """Main agent loop for Kafka consumption"""
        logger.info("Transport Management Agent Kafka consumer started")
        
        try:
            # Note: KafkaConsumer is blocking, so this should be run in a separate thread/process
            # For simplicity in this refactor, we'll just log the intention.
            # In a real FastAPI app, this would be handled in a background task.
            logger.warning("Kafka consumer is blocking and should be run in a background task.")
            # for message in self.kafka_consumer:
            #     self.process_kafka_message(message.value)
        except Exception as e:
            logger.error(f"Error in Kafka consumer loop: {str(e)}")
        finally:
            logger.info("Kafka consumer loop finished")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.db_conn:
            self.db_conn.close()
        if self.kafka_producer:
            self.kafka_producer.close()
        if self.kafka_consumer:
            self.kafka_consumer.close()
        logger.info("Transport Management Agent stopped")


# Carrier Integration Classes
# Each carrier has its own integration class implementing the carrier's specific API

class CarrierIntegration:
    """Base class for carrier integrations"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.carrier_name = "Generic Carrier"
        self.carrier_code = "generic"
    
    def services_route(self, origin_country: str, destination_country: str) -> bool:
        """Check if carrier services this route"""
        return True
    
    def get_quote(self, shipment_details: Dict) -> Optional[Dict]:
        """Get shipping quote"""
        # Implement basic quote logic
        return {
            "carrier": self.name,
            "service": "standard",
            "price": 15.99,
            "currency": "EUR",
            "estimated_days": 3
        }
    
    def generate_label(self, shipment: Dict) -> Dict:
        """Generate shipping label"""
        # Implement basic label generation
        return {
            "label_url": f"https://api.{self.name.lower()}.com/labels/{shipment.get('id', 'unknown')}.pdf",
            "tracking_number": f"{self.name[:3].upper()}{shipment.get('id', '000000')}",
            "format": "PDF"
        }
    
    def track_shipment(self, tracking_number: str) -> Dict:
        """Track shipment"""
        # Implement basic tracking
        return {
            "tracking_number": tracking_number,
            "status": "in_transit",
            "location": "Distribution Center",
            "estimated_delivery": "2025-10-24"
        }


class DPDIntegration(CarrierIntegration):
    """DPD (Dynamic Parcel Distribution) integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.carrier_name = "DPD"
        self.carrier_code = "dpd"
    
    def get_quote(self, shipment_details: Dict) -> Optional[Dict]:
        """Get DPD quote"""
        try:
            # Call DPD API for quote
            response = requests.post(
                f"{self.config['api_url']}/quote",
                headers={'Authorization': f"Bearer {self.config['api_key']}"},
                json={
                    'origin': shipment_details['origin'],
                    'destination': shipment_details['destination'],
                    'weight': shipment_details['weight'],
                    'dimensions': shipment_details['dimensions']
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'service_level': data.get('service', 'standard'),
                    'price': float(data.get('price', 0)),
                    'currency': data.get('currency', 'EUR'),
                    'estimated_delivery': data.get('estimated_delivery'),
                    'transit_days': data.get('transit_days', 3)
                }
        except Exception as e:
            logger.error(f"Error getting DPD quote: {str(e)}")
        return None
    
    def generate_label(self, shipment: Dict) -> Dict:
        """Generate DPD label"""
        # Implementation would call DPD label generation API
        # This is a simplified example
        return {
            'tracking_number': f"DPD{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'label_url': 'https://api.dpd.com/labels/...',
            'format': 'PDF'
        }
    
    def track_shipment(self, tracking_number: str) -> Dict:
        """Track DPD shipment"""
        # Implementation would call DPD tracking API
        return {
            'status': 'in_transit',
            'events': [],
            'current_location': 'Paris, France',
            'estimated_delivery': (datetime.now() + timedelta(days=2)).isoformat()
        }


class GLSIntegration(CarrierIntegration):
    """GLS (General Logistics Systems) integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.carrier_name = "GLS"
        self.carrier_code = "gls"
    
    def get_quote(self, shipment_details: Dict) -> Optional[Dict]:
        """Get GLS quote"""
        # Similar implementation to DPD
        return None
    
    def generate_label(self, shipment: Dict) -> Dict:
        """Generate GLS label"""
        return {
            'tracking_number': f"GLS{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'label_url': 'https://api.gls-group.eu/labels/...',
            'format': 'PDF'
        }
    
    def track_shipment(self, tracking_number: str) -> Dict:
        """Track GLS shipment"""
        return {
            'status': 'in_transit',
            'events': [],
            'current_location': 'Unknown',
            'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat()
        }


class HermesIntegration(CarrierIntegration):
    """Hermes/Evri integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.carrier_name = "Hermes"
        self.carrier_code = "hermes"
    
    def get_quote(self, shipment_details: Dict) -> Optional[Dict]:
        """Get Hermes quote"""
        return None
    
    def generate_label(self, shipment: Dict) -> Dict:
        """Generate Hermes label"""
        return {
            'tracking_number': f"HER{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'label_url': 'https://api.hermesworld.com/labels/...',
            'format': 'PDF'
        }
    
    def track_shipment(self, tracking_number: str) -> Dict:
        """Track Hermes shipment"""
        return {
            'status': 'in_transit',
            'events': [],
            'current_location': 'Unknown',
            'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat()
        }


class ColissimoIntegration(CarrierIntegration):
    """Colissimo (La Poste) integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.carrier_name = "Colissimo"
        self.carrier_code = "colissimo"
    
    def get_quote(self, shipment_details: Dict) -> Optional[Dict]:
        """Get Colissimo quote"""
        return None
    
    def generate_label(self, shipment: Dict) -> Dict:
        """Generate Colissimo label"""
        return {
            'tracking_number': f"COL{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'label_url': 'https://ws.colissimo.fr/labels/...',
            'format': 'PDF'
        }
    
    def track_shipment(self, tracking_number: str) -> Dict:
        """Track Colissimo shipment"""
        return {
            'status': 'in_transit',
            'events': [],
            'current_location': 'Unknown',
            'estimated_delivery': (datetime.now() + timedelta(days=2)).isoformat()
        }


class ChronopostIntegration(CarrierIntegration):
    """Chronopost integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.carrier_name = "Chronopost"
        self.carrier_code = "chronopost"
    
    def get_quote(self, shipment_details: Dict) -> Optional[Dict]:
        """Get Chronopost quote"""
        return None
    
    def generate_label(self, shipment: Dict) -> Dict:
        """Generate Chronopost label"""
        return {
            'tracking_number': f"CHR{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'label_url': 'https://ws.chronopost.fr/labels/...',
            'format': 'PDF'
        }
    
    def track_shipment(self, tracking_number: str) -> Dict:
        """Track Chronopost shipment"""
        return {
            'status': 'in_transit',
            'events': [],
            'current_location': 'Unknown',
            'estimated_delivery': (datetime.now() + timedelta(days=1)).isoformat()
        }


class DHLIntegration(CarrierIntegration):
    """DHL Express Europe integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.carrier_name = "DHL Express"
        self.carrier_code = "dhl"
    
    def get_quote(self, shipment_details: Dict) -> Optional[Dict]:
        """Get DHL quote"""
        return None
    
    def generate_label(self, shipment: Dict) -> Dict:
        """Generate DHL label"""
        return {
            'tracking_number': f"DHL{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'label_url': 'https://api-eu.dhl.com/labels/...',
            'format': 'PDF'
        }
    
    def track_shipment(self, tracking_number: str) -> Dict:
        """Track DHL shipment"""
        return {
            'status': 'in_transit',
            'events': [],
            'current_location': 'Unknown',
            'estimated_delivery': (datetime.now() + timedelta(days=1)).isoformat()
        }


class UPSIntegration(CarrierIntegration):
    """UPS Europe integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.carrier_name = "UPS"
        self.carrier_code = "ups"
    
    def get_quote(self, shipment_details: Dict) -> Optional[Dict]:
        """Get UPS quote"""
        return None
    
    def generate_label(self, shipment: Dict) -> Dict:
        """Generate UPS label"""
        return {
            'tracking_number': f"1Z{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'label_url': 'https://onlinetools.ups.com/labels/...',
            'format': 'PDF'
        }
    
    def track_shipment(self, tracking_number: str) -> Dict:
        """Track UPS shipment"""
        return {
            'status': 'in_transit',
            'events': [],
            'current_location': 'Unknown',
            'estimated_delivery': (datetime.now() + timedelta(days=2)).isoformat()
        }


class ColisPriveIntegration(CarrierIntegration):
    """Colis Privé integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.carrier_name = "Colis Privé"
        self.carrier_code = "colis_prive"
    
    def get_quote(self, shipment_details: Dict) -> Optional[Dict]:
        """Get Colis Privé quote"""
        return None
    
    def generate_label(self, shipment: Dict) -> Dict:
        """Generate Colis Privé label"""
        return {
            'tracking_number': f"CP{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'label_url': 'https://api.colisprive.com/labels/...',
            'format': 'PDF'
        }
    
    def track_shipment(self, tracking_number: str) -> Dict:
        """Track Colis Privé shipment"""
        return {
            'status': 'in_transit',
            'events': [],
            'current_location': 'Unknown',
            'estimated_delivery': (datetime.now() + timedelta(days=3)).isoformat()
        }


if __name__ == '__main__':
    import uvicorn
    
    # Setup logging
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    
    # Initialize agent instance for the main block

    transport_agent = TransportManagementAgent()
    
    # Get port from environment variables
    port = int(os.getenv("PORT", "8014"))

    logger.info("Starting Transport Management Agent FastAPI server", port=port)

    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", lifespan="on")

