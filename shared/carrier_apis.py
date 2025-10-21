"""
Carrier API Integrations
Provides unified interface for multiple carrier APIs
"""

import os
import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal
from abc import ABC, abstractmethod
import aiohttp
import json

logger = structlog.get_logger(__name__)


class ServiceLevel(str, Enum):
    """Shipping service levels"""
    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"
    ECONOMY = "economy"


class ShipmentStatus(str, Enum):
    """Shipment tracking status"""
    CREATED = "created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED_DELIVERY = "failed_delivery"
    RETURNED = "returned"
    EXCEPTION = "exception"


class Address(BaseModel):
    """Shipping address model"""
    name: str
    company: Optional[str] = None
    street1: str
    street2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str  # ISO 2-letter code
    phone: Optional[str] = None
    email: Optional[str] = None


class Package(BaseModel):
    """Package dimensions and weight"""
    weight: Decimal  # in kg
    length: Decimal  # in cm
    width: Decimal  # in cm
    height: Decimal  # in cm
    description: Optional[str] = None
    value: Optional[Decimal] = None  # declared value for insurance


class RateQuote(BaseModel):
    """Shipping rate quote"""
    carrier_code: str
    carrier_name: str
    service_level: ServiceLevel
    price: Decimal
    currency: str = "EUR"
    transit_days: int
    estimated_delivery: datetime
    on_time_rate: Optional[float] = None  # Historical performance


class ShipmentLabel(BaseModel):
    """Shipping label details"""
    tracking_number: str
    label_url: str
    label_format: str = "PDF"
    carrier_code: str
    service_level: ServiceLevel
    cost: Decimal


class TrackingEvent(BaseModel):
    """Tracking event"""
    timestamp: datetime
    status: ShipmentStatus
    location: Optional[str] = None
    description: str
    carrier_code: str


class BaseCarrierAPI(ABC):
    """Base class for carrier API integrations"""
    
    def __init__(self, carrier_code: str, carrier_name: str):
        self.carrier_code = carrier_code
        self.carrier_name = carrier_name
        self.api_key = os.getenv(f"{carrier_code.upper()}_API_KEY", "")
        self.api_url = ""
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    @abstractmethod
    async def get_rates(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: Optional[ServiceLevel] = None
    ) -> List[RateQuote]:
        """Get shipping rates"""
        pass
    
    @abstractmethod
    async def create_shipment(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: ServiceLevel
    ) -> ShipmentLabel:
        """Create shipment and generate label"""
        pass
    
    @abstractmethod
    async def track_shipment(
        self,
        tracking_number: str
    ) -> List[TrackingEvent]:
        """Track shipment"""
        pass
    
    @abstractmethod
    async def cancel_shipment(
        self,
        tracking_number: str
    ) -> bool:
        """Cancel shipment"""
        pass


class ColissimoAPI(BaseCarrierAPI):
    """Colissimo (La Poste) API Integration"""
    
    def __init__(self):
        super().__init__("colissimo", "Colissimo")
        self.api_url = "https://ws.colissimo.fr/sls-ws"
        # In production, use real API credentials
        self.contract_number = os.getenv("COLISSIMO_CONTRACT_NUMBER", "")
    
    async def get_rates(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: Optional[ServiceLevel] = None
    ) -> List[RateQuote]:
        """Get Colissimo shipping rates"""
        try:
            # Determine service based on destination
            is_domestic = destination.country == "FR"
            is_eu = destination.country in ["DE", "BE", "IT", "ES", "NL", "PT", "AT", "LU"]
            
            rates = []
            
            if is_domestic:
                # Domestic France rates
                if package.weight <= 1:
                    price = Decimal("5.50")
                    transit_days = 1
                elif package.weight <= 5:
                    price = Decimal("7.90")
                    transit_days = 2
                elif package.weight <= 10:
                    price = Decimal("12.50")
                    transit_days = 2
                else:
                    price = Decimal("18.00")
                    transit_days = 3
                
                rates.append(RateQuote(
                    carrier_code=self.carrier_code,
                    carrier_name=self.carrier_name,
                    service_level=ServiceLevel.STANDARD,
                    price=price,
                    transit_days=transit_days,
                    estimated_delivery=datetime.utcnow() + timedelta(days=transit_days),
                    on_time_rate=0.95
                ))
            
            elif is_eu:
                # EU rates
                if package.weight <= 2:
                    price = Decimal("15.00")
                    transit_days = 3
                elif package.weight <= 5:
                    price = Decimal("22.00")
                    transit_days = 4
                else:
                    price = Decimal("35.00")
                    transit_days = 5
                
                rates.append(RateQuote(
                    carrier_code=self.carrier_code,
                    carrier_name=self.carrier_name,
                    service_level=ServiceLevel.STANDARD,
                    price=price,
                    transit_days=transit_days,
                    estimated_delivery=datetime.utcnow() + timedelta(days=transit_days),
                    on_time_rate=0.90
                ))
            
            else:
                # International rates
                if package.weight <= 2:
                    price = Decimal("25.00")
                    transit_days = 7
                else:
                    price = Decimal("45.00")
                    transit_days = 10
                
                rates.append(RateQuote(
                    carrier_code=self.carrier_code,
                    carrier_name=self.carrier_name,
                    service_level=ServiceLevel.STANDARD,
                    price=price,
                    transit_days=transit_days,
                    estimated_delivery=datetime.utcnow() + timedelta(days=transit_days),
                    on_time_rate=0.85
                ))
            
            logger.info("Colissimo rates retrieved",
                       origin=origin.country,
                       destination=destination.country,
                       rates_count=len(rates))
            
            return rates
            
        except Exception as e:
            logger.error("Failed to get Colissimo rates", error=str(e))
            return []
    
    async def create_shipment(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: ServiceLevel
    ) -> ShipmentLabel:
        """Create Colissimo shipment"""
        try:
            # Generate tracking number
            tracking_number = f"COL{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # In production, call actual Colissimo API
            # For simulation, generate mock label
            label_url = f"https://api.colissimo.fr/labels/{tracking_number}.pdf"
            
            # Get rate for cost
            rates = await self.get_rates(origin, destination, package, service_level)
            cost = rates[0].price if rates else Decimal("5.50")
            
            label = ShipmentLabel(
                tracking_number=tracking_number,
                label_url=label_url,
                carrier_code=self.carrier_code,
                service_level=service_level,
                cost=cost
            )
            
            logger.info("Colissimo shipment created",
                       tracking_number=tracking_number)
            
            return label
            
        except Exception as e:
            logger.error("Failed to create Colissimo shipment", error=str(e))
            raise
    
    async def track_shipment(
        self,
        tracking_number: str
    ) -> List[TrackingEvent]:
        """Track Colissimo shipment"""
        try:
            # In production, call actual Colissimo tracking API
            # For simulation, generate mock tracking events
            events = [
                TrackingEvent(
                    timestamp=datetime.utcnow() - timedelta(hours=24),
                    status=ShipmentStatus.CREATED,
                    location="Paris, France",
                    description="Shipment created",
                    carrier_code=self.carrier_code
                ),
                TrackingEvent(
                    timestamp=datetime.utcnow() - timedelta(hours=20),
                    status=ShipmentStatus.PICKED_UP,
                    location="Paris, France",
                    description="Package picked up",
                    carrier_code=self.carrier_code
                ),
                TrackingEvent(
                    timestamp=datetime.utcnow() - timedelta(hours=12),
                    status=ShipmentStatus.IN_TRANSIT,
                    location="Lyon Sorting Center",
                    description="In transit to destination",
                    carrier_code=self.carrier_code
                )
            ]
            
            return events
            
        except Exception as e:
            logger.error("Failed to track Colissimo shipment", error=str(e))
            return []
    
    async def cancel_shipment(
        self,
        tracking_number: str
    ) -> bool:
        """Cancel Colissimo shipment"""
        try:
            # In production, call actual Colissimo API
            logger.info("Colissimo shipment cancelled",
                       tracking_number=tracking_number)
            return True
        except Exception as e:
            logger.error("Failed to cancel Colissimo shipment", error=str(e))
            return False


class ChronopostAPI(BaseCarrierAPI):
    """Chronopost (Express Delivery) API Integration"""
    
    def __init__(self):
        super().__init__("chronopost", "Chronopost")
        self.api_url = "https://ws.chronopost.fr/shipping-cxf"
    
    async def get_rates(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: Optional[ServiceLevel] = None
    ) -> List[RateQuote]:
        """Get Chronopost rates (express delivery)"""
        try:
            is_domestic = destination.country == "FR"
            
            rates = []
            
            # Express service (next day)
            if is_domestic:
                if package.weight <= 5:
                    price = Decimal("12.90")
                elif package.weight <= 10:
                    price = Decimal("18.50")
                else:
                    price = Decimal("25.00")
                
                transit_days = 1
                on_time_rate = 0.98
            else:
                # International express
                if package.weight <= 5:
                    price = Decimal("35.00")
                elif package.weight <= 10:
                    price = Decimal("50.00")
                else:
                    price = Decimal("75.00")
                
                transit_days = 2
                on_time_rate = 0.95
            
            rates.append(RateQuote(
                carrier_code=self.carrier_code,
                carrier_name=self.carrier_name,
                service_level=ServiceLevel.EXPRESS,
                price=price,
                transit_days=transit_days,
                estimated_delivery=datetime.utcnow() + timedelta(days=transit_days),
                on_time_rate=on_time_rate
            ))
            
            return rates
            
        except Exception as e:
            logger.error("Failed to get Chronopost rates", error=str(e))
            return []
    
    async def create_shipment(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: ServiceLevel
    ) -> ShipmentLabel:
        """Create Chronopost shipment"""
        tracking_number = f"CHR{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        label_url = f"https://api.chronopost.fr/labels/{tracking_number}.pdf"
        
        rates = await self.get_rates(origin, destination, package, service_level)
        cost = rates[0].price if rates else Decimal("12.90")
        
        return ShipmentLabel(
            tracking_number=tracking_number,
            label_url=label_url,
            carrier_code=self.carrier_code,
            service_level=service_level,
            cost=cost
        )
    
    async def track_shipment(self, tracking_number: str) -> List[TrackingEvent]:
        """Track Chronopost shipment"""
        return [
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(hours=12),
                status=ShipmentStatus.IN_TRANSIT,
                location="Paris Hub",
                description="Express delivery in progress",
                carrier_code=self.carrier_code
            )
        ]
    
    async def cancel_shipment(self, tracking_number: str) -> bool:
        """Cancel Chronopost shipment"""
        return True


class DPDAPI(BaseCarrierAPI):
    """DPD API Integration"""
    
    def __init__(self):
        super().__init__("dpd", "DPD")
        self.api_url = "https://api.dpd.com"
    
    async def get_rates(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: Optional[ServiceLevel] = None
    ) -> List[RateQuote]:
        """Get DPD rates"""
        is_domestic = destination.country == origin.country
        
        if is_domestic:
            price = Decimal("6.10") if package.weight <= 5 else Decimal("10.50")
            transit_days = 1
            on_time_rate = 0.93
        else:
            price = Decimal("18.00") if package.weight <= 5 else Decimal("30.00")
            transit_days = 3
            on_time_rate = 0.88
        
        return [RateQuote(
            carrier_code=self.carrier_code,
            carrier_name=self.carrier_name,
            service_level=ServiceLevel.STANDARD,
            price=price,
            transit_days=transit_days,
            estimated_delivery=datetime.utcnow() + timedelta(days=transit_days),
            on_time_rate=on_time_rate
        )]
    
    async def create_shipment(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: ServiceLevel
    ) -> ShipmentLabel:
        """Create DPD shipment"""
        tracking_number = f"DPD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        rates = await self.get_rates(origin, destination, package, service_level)
        
        return ShipmentLabel(
            tracking_number=tracking_number,
            label_url=f"https://api.dpd.com/labels/{tracking_number}.pdf",
            carrier_code=self.carrier_code,
            service_level=service_level,
            cost=rates[0].price if rates else Decimal("6.10")
        )
    
    async def track_shipment(self, tracking_number: str) -> List[TrackingEvent]:
        """Track DPD shipment"""
        return [
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(hours=8),
                status=ShipmentStatus.IN_TRANSIT,
                location="Distribution Center",
                description="Package in transit",
                carrier_code=self.carrier_code
            )
        ]
    
    async def cancel_shipment(self, tracking_number: str) -> bool:
        """Cancel DPD shipment"""
        return True


class ColisPriveAPI(BaseCarrierAPI):
    """Colis Privé API Integration"""
    
    def __init__(self):
        super().__init__("colis_prive", "Colis Privé")
        self.api_url = "https://api.colisprive.com"
    
    async def get_rates(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: Optional[ServiceLevel] = None
    ) -> List[RateQuote]:
        """Get Colis Privé rates (economy option)"""
        # Colis Privé is typically cheaper but slower
        if package.weight <= 5:
            price = Decimal("4.20")
        elif package.weight <= 10:
            price = Decimal("7.50")
        else:
            price = Decimal("12.00")
        
        return [RateQuote(
            carrier_code=self.carrier_code,
            carrier_name=self.carrier_name,
            service_level=ServiceLevel.ECONOMY,
            price=price,
            transit_days=2,
            estimated_delivery=datetime.utcnow() + timedelta(days=2),
            on_time_rate=0.88
        )]
    
    async def create_shipment(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: ServiceLevel
    ) -> ShipmentLabel:
        """Create Colis Privé shipment"""
        tracking_number = f"CP{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        rates = await self.get_rates(origin, destination, package, service_level)
        
        return ShipmentLabel(
            tracking_number=tracking_number,
            label_url=f"https://api.colisprive.com/labels/{tracking_number}.pdf",
            carrier_code=self.carrier_code,
            service_level=service_level,
            cost=rates[0].price if rates else Decimal("4.20")
        )
    
    async def track_shipment(self, tracking_number: str) -> List[TrackingEvent]:
        """Track Colis Privé shipment"""
        return [
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(hours=6),
                status=ShipmentStatus.IN_TRANSIT,
                location="Regional Hub",
                description="Package in transit",
                carrier_code=self.carrier_code
            )
        ]
    
    async def cancel_shipment(self, tracking_number: str) -> bool:
        """Cancel Colis Privé shipment"""
        return True


class UPSAPI(BaseCarrierAPI):
    """UPS API Integration"""
    
    def __init__(self):
        super().__init__("ups", "UPS")
        self.api_url = "https://onlinetools.ups.com/api"
    
    async def get_rates(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: Optional[ServiceLevel] = None
    ) -> List[RateQuote]:
        """Get UPS rates"""
        rates = []
        
        # UPS Standard
        if package.weight <= 5:
            price = Decimal("15.00")
        else:
            price = Decimal("25.00")
        
        rates.append(RateQuote(
            carrier_code=self.carrier_code,
            carrier_name=f"{self.carrier_name} Standard",
            service_level=ServiceLevel.STANDARD,
            price=price,
            transit_days=3,
            estimated_delivery=datetime.utcnow() + timedelta(days=3),
            on_time_rate=0.92
        ))
        
        # UPS Express
        express_price = price * Decimal("1.5")
        rates.append(RateQuote(
            carrier_code=self.carrier_code,
            carrier_name=f"{self.carrier_name} Express",
            service_level=ServiceLevel.EXPRESS,
            price=express_price,
            transit_days=1,
            estimated_delivery=datetime.utcnow() + timedelta(days=1),
            on_time_rate=0.96
        ))
        
        return rates
    
    async def create_shipment(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: ServiceLevel
    ) -> ShipmentLabel:
        """Create UPS shipment"""
        tracking_number = f"1Z{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        rates = await self.get_rates(origin, destination, package, service_level)
        
        matching_rate = next((r for r in rates if r.service_level == service_level), rates[0])
        
        return ShipmentLabel(
            tracking_number=tracking_number,
            label_url=f"https://api.ups.com/labels/{tracking_number}.pdf",
            carrier_code=self.carrier_code,
            service_level=service_level,
            cost=matching_rate.price
        )
    
    async def track_shipment(self, tracking_number: str) -> List[TrackingEvent]:
        """Track UPS shipment"""
        return [
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(hours=10),
                status=ShipmentStatus.IN_TRANSIT,
                location="UPS Facility",
                description="Package in transit",
                carrier_code=self.carrier_code
            )
        ]
    
    async def cancel_shipment(self, tracking_number: str) -> bool:
        """Cancel UPS shipment"""
        return True


class FedExAPI(BaseCarrierAPI):
    """FedEx API Integration"""
    
    def __init__(self):
        super().__init__("fedex", "FedEx")
        self.api_url = "https://apis.fedex.com"
    
    async def get_rates(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: Optional[ServiceLevel] = None
    ) -> List[RateQuote]:
        """Get FedEx rates"""
        rates = []
        
        # FedEx Ground
        if package.weight <= 5:
            price = Decimal("14.00")
        else:
            price = Decimal("24.00")
        
        rates.append(RateQuote(
            carrier_code=self.carrier_code,
            carrier_name=f"{self.carrier_name} Ground",
            service_level=ServiceLevel.STANDARD,
            price=price,
            transit_days=3,
            estimated_delivery=datetime.utcnow() + timedelta(days=3),
            on_time_rate=0.91
        ))
        
        # FedEx Express
        express_price = price * Decimal("1.6")
        rates.append(RateQuote(
            carrier_code=self.carrier_code,
            carrier_name=f"{self.carrier_name} Express",
            service_level=ServiceLevel.EXPRESS,
            price=express_price,
            transit_days=1,
            estimated_delivery=datetime.utcnow() + timedelta(days=1),
            on_time_rate=0.95
        ))
        
        # FedEx Overnight
        overnight_price = price * Decimal("2.0")
        rates.append(RateQuote(
            carrier_code=self.carrier_code,
            carrier_name=f"{self.carrier_name} Overnight",
            service_level=ServiceLevel.OVERNIGHT,
            price=overnight_price,
            transit_days=1,
            estimated_delivery=datetime.utcnow() + timedelta(days=1),
            on_time_rate=0.97
        ))
        
        return rates
    
    async def create_shipment(
        self,
        origin: Address,
        destination: Address,
        package: Package,
        service_level: ServiceLevel
    ) -> ShipmentLabel:
        """Create FedEx shipment"""
        tracking_number = f"FDX{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        rates = await self.get_rates(origin, destination, package, service_level)
        
        matching_rate = next((r for r in rates if r.service_level == service_level), rates[0])
        
        return ShipmentLabel(
            tracking_number=tracking_number,
            label_url=f"https://api.fedex.com/labels/{tracking_number}.pdf",
            carrier_code=self.carrier_code,
            service_level=service_level,
            cost=matching_rate.price
        )
    
    async def track_shipment(self, tracking_number: str) -> List[TrackingEvent]:
        """Track FedEx shipment"""
        return [
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(hours=8),
                status=ShipmentStatus.IN_TRANSIT,
                location="FedEx Hub",
                description="Package in transit",
                carrier_code=self.carrier_code
            )
        ]
    
    async def cancel_shipment(self, tracking_number: str) -> bool:
        """Cancel FedEx shipment"""
        return True


class CarrierManager:
    """
    Unified carrier management
    Provides single interface to all carrier APIs
    """
    
    def __init__(self):
        self.carriers: Dict[str, BaseCarrierAPI] = {
            "colissimo": ColissimoAPI(),
            "chronopost": ChronopostAPI(),
            "dpd": DPDAPI(),
            "colis_prive": ColisPriveAPI(),
            "ups": UPSAPI(),
            "fedex": FedExAPI()
        }
    
    async def get_all_rates(
        self,
        origin: Address,
        destination: Address,
        package: Package
    ) -> List[RateQuote]:
        """Get rates from all carriers"""
        all_rates = []
        
        tasks = [
            carrier.get_rates(origin, destination, package)
            for carrier in self.carriers.values()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_rates.extend(result)
        
        # Sort by price
        all_rates.sort(key=lambda r: r.price)
        
        return all_rates
    
    def get_carrier(self, carrier_code: str) -> Optional[BaseCarrierAPI]:
        """Get specific carrier API"""
        return self.carriers.get(carrier_code)
    
    async def close_all(self):
        """Close all carrier API sessions"""
        for carrier in self.carriers.values():
            await carrier.close()


# Singleton instance
_carrier_manager: Optional[CarrierManager] = None


def get_carrier_manager() -> CarrierManager:
    """Get singleton carrier manager instance"""
    global _carrier_manager
    if _carrier_manager is None:
        _carrier_manager = CarrierManager()
    return _carrier_manager

