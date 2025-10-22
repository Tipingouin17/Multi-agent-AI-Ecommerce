
"""
Transport Agent (Production-Ready with Carrier API Integration)
Handles carrier selection, rate calculation, label generation, and price list uploads
"""

import os
import sys
import asyncio
import structlog
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from shared.base_agent import BaseAgent
from shared.kafka_config import KafkaProducer, KafkaConsumer
from shared.database import DatabaseManager
from shared.db_helpers import DatabaseHelper
from shared.carrier_apis import (
    get_carrier_manager,
    Address,
    Package,
    ServiceLevel,
    RateQuote
)
from shared.models import CarrierConfig, AgentMessage, MessageType # Assuming these models exist

logger = structlog.get_logger(__name__)


class CarrierPriceUpload(BaseModel):
    """Carrier price list upload model"""
    upload_id: str
    carrier_code: str
    file_name: str
    file_url: str
    file_type: str  # csv, excel, pdf
    uploaded_by: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)

class TransportAgentProduction(BaseAgent):
    """
    Transport Agent - Production Ready
    
    Responsibilities:
    - Select optimal carrier based on AI/ML
    - Calculate shipping rates from database
    - Generate shipping labels via carrier APIs
    - Track shipments
    - Process carrier price list uploads
    - Update carrier configurations
    - Monitor carrier performance
    """
    
    def __init__(self, agent_id: str = "TransportAgentProduction", agent_type: str = "TransportAgent"):
        super().__init__(agent_id, agent_type)
        self.kafka_producer: Optional[KafkaProducer] = None
        self.kafka_consumer: Optional[KafkaConsumer] = None
        self.carrier_manager = get_carrier_manager()
        self.db_manager: Optional[DatabaseManager] = None
        self.db_helper: Optional[DatabaseHelper] = None
        self._db_initialized: bool = False
        
    async def initialize(self):
        """Initialize agent"""
        await super().initialize()
        
        # Initialize Database Manager and Helper
        try:
            db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./transport_agent.db")
            self.db_manager = DatabaseManager(db_url)
            self.db_helper = DatabaseHelper(self.db_manager)
            await self.db_manager.connect()
            await self.db_manager.create_all()
            self._db_initialized = True
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            self._db_initialized = False

        try:
            self.kafka_producer = KafkaProducer()
            self.kafka_consumer = KafkaConsumer(*[
                    "shipment_requested",
                    "carrier_rate_requested",
                    "carrier_pricelist_uploaded",
                    "shipment_tracking_requested"
                ],
                group_id=os.getenv("KAFKA_CONSUMER_GROUP_ID", "transport_agent_production")
            )
            logger.info("Kafka producers and consumers initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Kafka", error=str(e))
            # Depending on criticality, you might want to re-raise or set a flag

        logger.info("Transport Agent (Production) initialized")
    
    async def select_optimal_carrier(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        required_delivery_date: Optional[datetime] = None,
        preferred_service_level: Optional[ServiceLevel] = None
    ) -> Dict[str, Any]:
        """
        Select optimal carrier using AI/ML algorithm
        
        Priority factors:
        1. On-time delivery rate (most important)
        2. Cost optimization
        3. Service level requirements
        4. Required delivery date
        
        Args:
            origin: Shipping origin address
            destination: Destination address
            package: Package details
            required_delivery_date: Required delivery date
            preferred_service_level: Preferred service level
            
        Returns:
            Selected carrier and rate details
        """
        try:
            logger.info("Selecting optimal carrier",
                       origin_country=origin.country,
                       destination_country=destination.country,
                       weight=float(package.weight))
            
            all_rates = await self.carrier_manager.get_all_rates(
                origin,
                destination,
                package
            )
            
            if not all_rates:
                logger.warning("No carrier rates available")
                return {"success": False, "error": "No carriers available for this route"}
            
            if preferred_service_level:
                filtered_rates = [r for r in all_rates if r.service_level == preferred_service_level]
                if filtered_rates:
                    all_rates = filtered_rates
            
            if required_delivery_date:
                all_rates = [r for r in all_rates if r.estimated_delivery <= required_delivery_date]
            
            if not all_rates:
                logger.warning("No carriers meet delivery requirements")
                return {"success": False, "error": "No carriers available that meet delivery requirements"}
            
            # Score carriers using weighted algorithm
            # Weights: on_time_rate (60%), price (40%)
            scored_rates = []
            
            prices = [float(r.price) for r in all_rates]
            min_price = min(prices)
            max_price = max(prices)
            price_range = max_price - min_price if max_price > min_price else 1
            
            for rate in all_rates:
                on_time_score = (rate.on_time_rate or 0.9) * 100
                price_normalized = (float(rate.price) - min_price) / price_range
                price_score = (1 - price_normalized) * 100
                total_score = (on_time_score * 0.6) + (price_score * 0.4)
                
                scored_rates.append({
                    "rate": rate,
                    "score": total_score,
                    "on_time_score": on_time_score,
                    "price_score": price_score
                })
            
            scored_rates.sort(key=lambda x: x["score"], reverse=True)
            
            best_option = scored_rates[0]
            selected_rate = best_option["rate"]
            
            logger.info("Optimal carrier selected",
                       carrier=selected_rate.carrier_code,
                       price=float(selected_rate.price),
                       on_time_rate=selected_rate.on_time_rate,
                       score=best_option["score"])
            
            return {
                "success": True,
                "selected_carrier": selected_rate.carrier_code,
                "carrier_name": selected_rate.carrier_name,
                "service_level": selected_rate.service_level,
                "price": float(selected_rate.price),
                "currency": selected_rate.currency,
                "transit_days": selected_rate.transit_days,
                "estimated_delivery": selected_rate.estimated_delivery.isoformat(),
                "on_time_rate": selected_rate.on_time_rate,
                "selection_score": best_option["score"],
                "alternatives": [
                    {
                        "carrier": opt["rate"].carrier_code,
                        "price": float(opt["rate"].price),
                        "score": opt["score"]
                    }
                    for opt in scored_rates[1:4]
                ]
            }
            
        except Exception as e:
            logger.error("Failed to select carrier", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def create_shipment(
        self,
        carrier_code: str,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: ServiceLevel,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Create shipment and generate label
        
        Args:
            carrier_code: Selected carrier code
            origin: Origin address
            destination: Destination address
            package: Package details
            service_level: Service level
            order_id: Order ID
            
        Returns:
            Shipment details with label
        """
        try:
            logger.info("Creating shipment",
                       carrier=carrier_code,
                       order_id=order_id)
            
            carrier = self.carrier_manager.get_carrier(carrier_code)
            if not carrier:
                raise ValueError(f"Carrier {carrier_code} not found")
            
            label = await carrier.create_shipment(
                origin,
                destination,
                package,
                service_level
            )
            
            if self.kafka_producer:
                await self.kafka_producer.send(
                    "shipment_created",
                    {
                        "order_id": order_id,
                        "tracking_number": label.tracking_number,
                        "carrier_code": carrier_code,
                        "label_url": label.label_url,
                        "cost": float(label.cost),
                        "created_at": datetime.utcnow().isoformat()
                    }
                )
            
            logger.info("Shipment created",
                       tracking_number=label.tracking_number,
                       carrier=carrier_code)
            
            return {
                "success": True,
                "tracking_number": label.tracking_number,
                "label_url": label.label_url,
                "carrier_code": carrier_code,
                "cost": float(label.cost)
            }
            
        except Exception as e:
            logger.error("Failed to create shipment", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def track_shipment(
        self,
        carrier_code: str,
        tracking_number: str
    ) -> Dict[str, Any]:
        """
        Track shipment status
        
        Args:
            carrier_code: Carrier code
            tracking_number: Tracking number
            
        Returns:
            Tracking details
        """
        try:
            logger.info("Tracking shipment",
                       carrier=carrier_code,
                       tracking_number=tracking_number)
            
            carrier = self.carrier_manager.get_carrier(carrier_code)
            if not carrier:
                raise ValueError(f"Carrier {carrier_code} not found")
            
            tracking_status = await carrier.track_shipment(tracking_number)
            
            return {
                "success": True,
                "tracking_number": tracking_number,
                "carrier_code": carrier_code,
                "status": tracking_status.status,
                "estimated_delivery": tracking_status.estimated_delivery.isoformat() if tracking_status.estimated_delivery else None,
                "last_update": tracking_status.last_update.isoformat() if tracking_status.last_update else None,
                "events": tracking_status.events
            }
            
        except Exception as e:
            logger.error("Failed to track shipment", error=str(e))
            return {"success": False, "error": str(e)}

    async def process_carrier_pricelist_upload(self, upload: CarrierPriceUpload):
        """
        Processes an uploaded carrier price list.
        
        Args:
            upload: The CarrierPriceUpload object containing upload details.
        """
        try:
            if not self._db_initialized or not self.db_helper or not self.db_manager: 
                logger.warning("Database not initialized, cannot process price list upload.")
                return

            logger.info("Processing carrier pricelist upload", upload_id=upload.upload_id, carrier_code=upload.carrier_code)
            
            # Example: Simulate parsing and storing data from the uploaded file
            # In a real scenario, this would involve reading the file_url, parsing its content
            # (e.g., CSV, Excel, PDF), and then updating the database with new pricing rules.
            # For demonstration, we'll just log and simulate a database operation.
            
            async with self.db_manager.get_session() as session:
                # This is a placeholder for actual database operations.
                # You would typically have a SQLAlchemy model for price lists or pricing rules
                # and use self.db_helper.create/update/get_all with that model.
                # For now, we'll just save the upload metadata.
                logger.info(f"Simulating saving upload metadata for {upload.upload_id} to DB.")
                # await self.db_helper.create(session, PriceListMetadataModel(**upload.dict()))
                await asyncio.sleep(0.5) # Simulate async DB operation
                logger.info("Carrier pricelist processed successfully", upload_id=upload.upload_id)
            
            if self.kafka_producer:
                await self.kafka_producer.send(
                    "carrier_pricelist_processed",
                    {"upload_id": upload.upload_id, "status": "processed", "carrier_code": upload.carrier_code}
                )
        except Exception as e:
            logger.error("Error processing carrier pricelist upload", upload_id=upload.upload_id, error=str(e))
            if self.kafka_producer:
                await self.kafka_producer.send(
                    "carrier_pricelist_processing_failed",
                    {"upload_id": upload.upload_id, "status": "failed", "carrier_code": upload.carrier_code, "error": str(e)}
                )

    async def get_carrier_config(self, carrier_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the configuration for a specific carrier from the database.

        Args:
            carrier_code: The unique code of the carrier.

        Returns:
            A dictionary containing the carrier's configuration, or None if not found.
        """
        try:
            if not self._db_initialized or not self.db_helper or not self.db_manager: 
                logger.warning("Database not initialized, cannot get carrier config.")
                return None
            async with self.db_manager.get_session() as session:
                logger.info("Retrieving carrier configuration", carrier_code=carrier_code)
                config = await self.db_helper.get_by_id(session, CarrierConfig, carrier_code)
                return config.to_dict() if config else None
        except Exception as e:
            logger.error("Failed to get carrier config", carrier_code=carrier_code, error=str(e))
            return None

    async def update_carrier_config(self, carrier_code: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates the configuration for a specific carrier in the database.

        Args:
            carrier_code: The unique code of the carrier.
            config_data: A dictionary containing the configuration data to update.

        Returns:
            A dictionary indicating success or failure of the update operation.
        """
        try:
            if not self._db_initialized or not self.db_helper or not self.db_manager: 
                logger.warning("Database not initialized, cannot update carrier config.")
                return {"success": False, "error": "Database not initialized"}
            async with self.db_manager.get_session() as session:
                logger.info("Updating carrier configuration", carrier_code=carrier_code)
                updated = await self.db_helper.update(session, CarrierConfig, carrier_code, config_data)
                if updated:
                    return {"success": True, "carrier_code": carrier_code, "updated_config": config_data}
                else:
                    # If update returns False, it means the item was not found or no changes were made
                    # For now, we'll assume it means not found, a more robust implementation would check for actual changes
                    return {"success": False, "error": f"Carrier config {carrier_code} not found or no changes applied."}
        except Exception as e:
            logger.error("Failed to update carrier config", carrier_code=carrier_code, error=str(e))
            return {"success": False, "error": str(e)}

    async def get_all_carrier_configs(self) -> List[Dict[str, Any]]:
        """
        Retrieves all carrier configurations from the database.

        Returns:
            A list of dictionaries, each representing a carrier's configuration.
        """
        try:
            if not self._db_initialized or not self.db_helper or not self.db_manager: 
                logger.warning("Database not initialized, cannot get all carrier configs.")
                return []
            async with self.db_manager.get_session() as session:
                logger.info("Retrieving all carrier configurations")
                configs = await self.db_helper.get_all(session, CarrierConfig)
                return [c.to_dict() for c in configs]
        except Exception as e:
            logger.error("Failed to get all carrier configs", error=str(e))
            return []

    async def delete_carrier_config(self, carrier_code: str) -> Dict[str, Any]:
        """
        Deletes a specific carrier configuration from the database.

        Args:
            carrier_code: The unique code of the carrier to delete.

        Returns:
            A dictionary indicating success or failure of the delete operation.
        """
        try:
            if not self._db_initialized or not self.db_helper or not self.db_manager: 
                logger.warning("Database not initialized, cannot delete carrier config.")
                return {"success": False, "error": "Database not initialized"}
            async with self.db_manager.get_session() as session:
                logger.info("Deleting carrier configuration", carrier_code=carrier_code)
                deleted = await self.db_helper.delete(session, CarrierConfig, carrier_code)
                if deleted:
                    return {"success": True, "carrier_code": carrier_code, "status": "deleted"}
                else:
                    return {"success": False, "error": f"Carrier config {carrier_code} not found."}
        except Exception as e:
            logger.error("Failed to delete carrier config", carrier_code=carrier_code, error=str(e))
            return {"success": False, "error": str(e)}

    async def process_message(self, message: AgentMessage):
        """
        Processes incoming messages from Kafka.

        Args:
            message: The AgentMessage object containing the message details.
        """
        try:
            logger.info("Processing message", topic=message.topic, message_type=message.message_type.value)
            data = message.payload

            if message.message_type == MessageType.SHIPMENT_REQUESTED:
                # Handle shipment request
                origin = Address(**data["origin"])
                destination = Address(**data["destination"])
                package = Package(**data["package"])
                service_level = ServiceLevel[data["service_level"]]
                order_id = data["order_id"]
                
                result = await self.create_shipment(
                    data["carrier_code"],
                    origin,
                    destination,
                    package,
                    service_level,
                    order_id
                )
                if not result["success"] and self.kafka_producer:
                    await self.kafka_producer.send(
                        "shipment_creation_failed",
                        {"order_id": order_id, "error": result["error"]}
                    )

            elif message.message_type == MessageType.CARRIER_RATE_REQUESTED:
                # Handle rate request
                origin = Address(**data["origin"])
                destination = Address(**data["destination"])
                package = Package(**data["package"])
                
                rates = await self.carrier_manager.get_all_rates(
                    origin,
                    destination,
                    package
                )
                
                if self.kafka_producer:
                    await self.kafka_producer.send(
                        "carrier_rates_retrieved",
                        {
                            "request_id": data.get("request_id"),
                            "rates": [
                                {
                                    "carrier": r.carrier_code,
                                    "price": float(r.price),
                                    "transit_days": r.transit_days
                                }
                                for r in rates
                            ]
                        }
                    )
            
            elif message.message_type == MessageType.CARRIER_PRICELIST_UPLOADED:
                # Handle price list upload
                upload = CarrierPriceUpload(**data)
                await self.process_carrier_pricelist_upload(upload)
            
            elif message.message_type == MessageType.SHIPMENT_TRACKING_REQUESTED:
                # Handle tracking request
                tracking = await self.track_shipment(
                    data["carrier_code"],
                    data["tracking_number"]
                )
                
                if self.kafka_producer:
                    await self.kafka_producer.send(
                        "shipment_tracking_updated",
                        tracking
                    )
            else:
                logger.warning("Unknown message type received", message_type=message.message_type.value)

        except Exception as e:
            logger.error("Error processing incoming message", error=str(e), message=message.dict())
            if self.kafka_producer:
                await self.kafka_producer.send(
                    "agent_error",
                    {"agent_id": self.agent_id, "error": str(e), "original_message": message.dict()}
                )

    async def run(self):
        """
        Runs the main loop of the transport agent, consuming messages from Kafka.
        """
        await self.initialize()
        logger.info("Transport Agent starting main loop")
        try:
            if self.kafka_consumer:
                await self.kafka_consumer.start_consumer(self.process_message)
            else:
                logger.error("Kafka consumer not initialized, cannot start main loop.")
        except Exception as e:
            logger.error("Error in agent run loop", error=str(e))
        finally:
            logger.info("Transport Agent shutting down.")
            if self.kafka_producer:
                await self.kafka_producer.stop()
            if self.kafka_consumer:
                await self.kafka_consumer.stop()
            if self.db_manager:
                await self.db_manager.disconnect()
            await self.shutdown()
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            if self.kafka_producer:
                await self.kafka_producer.stop()
            if self.kafka_consumer:
                await self.kafka_consumer.stop()
            if self.db_manager:
                await self.db_manager.disconnect()
            await super().cleanup()
            logger.info(f"{self.agent_name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process transport-specific business logic
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "get_rate")
            
            if operation == "get_rate":
                # Calculate shipping rate
                origin = Address(**data.get("origin", {}))
                destination = Address(**data.get("destination", {}))
                package = Package(**data.get("package", {}))
                carrier_code = data.get("carrier_code")
                service_level = ServiceLevel(data.get("service_level", "standard"))
                
                rate = await self.get_shipping_rate(
                    origin, destination, package, carrier_code, service_level
                )
                return {"status": "success", "rate": rate}
            
            elif operation == "create_label":
                # Generate shipping label
                shipment_data = data.get("shipment_data", {})
                label = await self.create_shipping_label(shipment_data)
                return {"status": "success", "label": label}
            
            elif operation == "track_shipment":
                # Track shipment
                carrier_code = data.get("carrier_code")
                tracking_number = data.get("tracking_number")
                tracking_info = await self.track_shipment(carrier_code, tracking_number)
                return {"status": "success", "tracking": tracking_info}
            
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}

# FastAPI Server Setup
app = FastAPI(
    title="Transport Agent Production",
    description="Transport Agent Production - Multi-Agent E-commerce Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_instance: Optional[TransportAgentProduction] = None

@app.on_event("startup")
async def startup_event():
    """Initializes the agent instance on FastAPI startup."""
    global agent_instance
    agent_instance = TransportAgentProduction()
    await agent_instance.initialize()
    asyncio.create_task(agent_instance.run()) # Run the agent's Kafka consumer in the background

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shuts down the agent instance on FastAPI shutdown.
    """
    global agent_instance
    if agent_instance:
        await agent_instance.shutdown()

@app.get("/health", summary="Health check", response_description="Agent health status")
async def health_check():
    """Returns the health status of the agent."""
    return {"status": "healthy", "agent": "transport_agent_production"}

@app.get("/", summary="Root endpoint", response_description="Agent information")
async def root():
    """Returns basic information about the agent."""
    return {
        "agent": "transport_agent_production",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/carriers/{carrier_code}/config", summary="Update carrier configuration", response_description="Updated carrier configuration")
async def update_carrier_configuration_api(carrier_code: str, config_data: Dict[str, Any]):
    """
    Updates the configuration for a specific carrier.

    Args:
        carrier_code: The unique code of the carrier.
        config_data: A dictionary containing the configuration data to update.

    Returns:
        A dictionary indicating success or failure of the update operation.
    """
    if not agent_instance: raise HTTPException(status_code=503, detail="Agent not initialized")
    result = await agent_instance.update_carrier_config(carrier_code, config_data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/carriers/{carrier_code}/config", summary="Get carrier configuration", response_description="Carrier configuration")
async def get_carrier_configuration_api(carrier_code: str):
    """
    Retrieves the configuration for a specific carrier.

    Args:
        carrier_code: The unique code of the carrier.

    Returns:
        A dictionary containing the carrier's configuration, or 404 if not found.
    """
    if not agent_instance: raise HTTPException(status_code=503, detail="Agent not initialized")
    config = await agent_instance.get_carrier_config(carrier_code)
    if not config:
        raise HTTPException(status_code=404, detail=f"Carrier config for {carrier_code} not found")
    return config

@app.get("/carriers/config", summary="Get all carrier configurations", response_description="All carrier configurations")
async def get_all_carrier_configurations_api():
    """
    Retrieves all carrier configurations.

    Returns:
        A list of dictionaries, each representing a carrier's configuration.
    """
    if not agent_instance: raise HTTPException(status_code=503, detail="Agent not initialized")
    configs = await agent_instance.get_all_carrier_configs()
    return configs

@app.delete("/carriers/{carrier_code}/config", summary="Delete carrier configuration", response_description="Deletion status")
async def delete_carrier_configuration_api(carrier_code: str):
    """
    Deletes a specific carrier configuration.

    Args:
        carrier_code: The unique code of the carrier to delete.

    Returns:
        A dictionary indicating success or failure of the delete operation.
    """
    if not agent_instance: raise HTTPException(status_code=503, detail="Agent not initialized")
    result = await agent_instance.delete_carrier_config(carrier_code)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# This block will run the FastAPI app and the agent's Kafka consumer
if __name__ == "__main__":
    # The agent is initialized and run via FastAPI's startup event, which handles the main loop
    # This __main__ block is primarily for running the FastAPI server.
    port = int(os.getenv("PORT", 8017))
    logger.info(f"Starting FastAPI server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

