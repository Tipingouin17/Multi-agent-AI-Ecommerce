"""
Dynamic Pricing Agent - Multi-Agent E-commerce System

This agent uses AI to optimize product pricing in real-time based on:
- Market conditions and competitor pricing
- Demand forecasting and inventory levels
- Customer behavior and price sensitivity
- Seasonal trends and promotional strategies
- Profit margin optimization
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import openai
import sys
import os

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)

# Get the directory containing the current file
current_dir = os.path.dirname(current_file_path)

# Get the parent directory (project root)
project_root = os.path.dirname(current_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")

# Now try the import
try:
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    print("Successfully imported shared.base_agent")
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current sys.path: {sys.path}")
    
    # List files in the shared directory to verify it exists
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        print(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            print(f"  - {item}")
    else:
        print(f"Directory not found: {shared_dir}")

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.models import APIResponse
from shared.database import DatabaseManager, get_database_manager


logger = structlog.get_logger(__name__)


class PricingStrategy(BaseModel):
    """Model for pricing strategy configuration."""
    strategy_id: str
    name: str
    description: str
    min_margin_percent: float
    max_discount_percent: float
    demand_sensitivity: float  # How much to adjust price based on demand
    competitor_sensitivity: float  # How much to consider competitor prices
    inventory_sensitivity: float  # How much to adjust based on inventory levels
    active: bool = True


class PriceOptimizationRequest(BaseModel):
    """Request model for price optimization."""
    product_id: str
    channel: Optional[str] = None  # marketplace, website, etc.
    current_price: float
    cost_price: float
    target_margin_percent: Optional[float] = None
    consider_competitors: bool = True
    consider_demand: bool = True
    consider_inventory: bool = True


class CompetitorPrice(BaseModel):
    """Model for competitor pricing data."""
    competitor_name: str
    price: float
    availability: bool
    last_updated: datetime
    source: str  # "api", "scraping", "manual"


class PriceRecommendation(BaseModel):
    """Model for price recommendation."""
    product_id: str
    channel: Optional[str]
    current_price: float
    recommended_price: float
    price_change_percent: float
    expected_margin_percent: float
    confidence_score: float
    reasoning: List[str]
    factors_considered: Dict[str, Any]
    valid_until: datetime
    generated_at: datetime


class PriceChangeEvent(BaseModel):
    """Model for price change tracking."""
    product_id: str
    channel: Optional[str]
    old_price: float
    new_price: float
    change_reason: str
    change_type: str  # "automatic", "manual", "promotional"
    effective_date: datetime
    created_by: str  # agent_id or user_id


class DynamicPricingAgent(BaseAgent):
    """
    Dynamic Pricing Agent provides AI-powered pricing optimization including:
    - Real-time price optimization based on multiple factors
    - Competitor price monitoring and analysis
    - Demand-based pricing adjustments
    - Inventory-driven pricing strategies
    - Promotional pricing recommendations
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="dynamic_pricing_agent", **kwargs)
        self.app = FastAPI(title="Dynamic Pricing Agent API", version="1.0.0")
        self.setup_routes()
        
        # Initialize OpenAI client
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # Pricing data and strategies
        self.pricing_strategies: Dict[str, PricingStrategy] = {}
        self.competitor_prices: Dict[str, List[CompetitorPrice]] = {}
        self.price_history: Dict[str, List[PriceChangeEvent]] = {}
        
        # Register message handlers
        self.register_handler(MessageType.DEMAND_FORECAST, self._handle_demand_forecast)
        self.register_handler(MessageType.INVENTORY_UPDATE, self._handle_inventory_update)
        self.register_handler(MessageType.COMPETITOR_PRICE_UPDATE, self._handle_competitor_price_update)
    
    async def initialize(self):
        """Initialize the Dynamic Pricing Agent."""
        self.logger.info("Initializing Dynamic Pricing Agent")
        
        # Initialize pricing strategies
        await self._initialize_pricing_strategies()
        
        # Load competitor pricing data
        await self._load_competitor_prices()
        
        # Start background tasks
        asyncio.create_task(self._monitor_competitor_prices())
        asyncio.create_task(self._optimize_prices_periodically())
        asyncio.create_task(self._analyze_pricing_performance())
        
        self.logger.info("Dynamic Pricing Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Dynamic Pricing Agent")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process dynamic pricing business logic."""
        action = data.get("action")
        
        if action == "optimize_price":
            return await self._optimize_price(data["request"])
        elif action == "get_price_recommendation":
            return await self._get_price_recommendation(data["request"])
        elif action == "update_competitor_prices":
            return await self._update_competitor_prices(data["product_id"], data["prices"])
        elif action == "get_pricing_analytics":
            return await self._get_pricing_analytics(data.get("product_id"))
        elif action == "apply_promotional_pricing":
            return await self._apply_promotional_pricing(data["promotion_config"])
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Dynamic Pricing Agent."""
        
        @self.app.post("/optimize-price", response_model=APIResponse)
        async def optimize_price(request: PriceOptimizationRequest):
            """Optimize price for a product."""
            try:
                result = await self._optimize_price(request.dict())
                
                return APIResponse(
                    success=True,
                    message="Price optimized successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to optimize price", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/price-recommendation", response_model=APIResponse)
        async def get_price_recommendation(request: PriceOptimizationRequest):
            """Get price recommendation without applying changes."""
            try:
                result = await self._get_price_recommendation(request.dict())
                
                return APIResponse(
                    success=True,
                    message="Price recommendation generated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get price recommendation", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/competitor-prices/{product_id}", response_model=APIResponse)
        async def update_competitor_prices(product_id: str, prices: List[CompetitorPrice]):
            """Update competitor prices for a product."""
            try:
                result = await self._update_competitor_prices(product_id, [p.dict() for p in prices])
                
                return APIResponse(
                    success=True,
                    message="Competitor prices updated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to update competitor prices", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/analytics", response_model=APIResponse)
        async def get_pricing_analytics(product_id: Optional[str] = None):
            """Get pricing analytics and performance metrics."""
            try:
                result = await self._get_pricing_analytics(product_id)
                
                return APIResponse(
                    success=True,
                    message="Pricing analytics retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get pricing analytics", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/competitor-prices/{product_id}", response_model=APIResponse)
        async def get_competitor_prices(product_id: str):
            """Get competitor prices for a product."""
            try:
                prices = self.competitor_prices.get(product_id, [])
                
                return APIResponse(
                    success=True,
                    message="Competitor prices retrieved successfully",
                    data={"product_id": product_id, "competitor_prices": [p.dict() for p in prices]}
                )
            
            except Exception as e:
                self.logger.error("Failed to get competitor prices", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/strategies", response_model=APIResponse)
        async def list_pricing_strategies():
            """List all pricing strategies."""
            try:
                strategies = [strategy.dict() for strategy in self.pricing_strategies.values()]
                
                return APIResponse(
                    success=True,
                    message="Pricing strategies retrieved successfully",
                    data={"strategies": strategies}
                )
            
            except Exception as e:
                self.logger.error("Failed to list pricing strategies", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _optimize_price(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize price for a product and apply the changes."""
        try:
            # Get price recommendation
            recommendation_result = await self._get_price_recommendation(request_data)
            recommendation = PriceRecommendation(**recommendation_result)
            
            # Apply the price change if confidence is high enough
            if recommendation.confidence_score >= 0.7:  # 70% confidence threshold
                await self._apply_price_change(recommendation)
                
                # Send price update notification
                await self.send_message(
                    recipient_agent="product_agent",
                    message_type=MessageType.PRICE_UPDATE,
                    payload={
                        "product_id": recommendation.product_id,
                        "channel": recommendation.channel,
                        "old_price": recommendation.current_price,
                        "new_price": recommendation.recommended_price,
                        "change_reason": "automatic_optimization",
                        "confidence_score": recommendation.confidence_score
                    }
                )
                
                self.logger.info("Price optimized and applied", 
                               product_id=recommendation.product_id, 
                               old_price=recommendation.current_price,
                               new_price=recommendation.recommended_price,
                               confidence=recommendation.confidence_score)
                
                return {
                    "price_applied": True,
                    "recommendation": recommendation.dict()
                }
            else:
                self.logger.info("Price optimization confidence too low, recommendation only", 
                               product_id=recommendation.product_id,
                               confidence=recommendation.confidence_score)
                
                return {
                    "price_applied": False,
                    "reason": "Low confidence score",
                    "recommendation": recommendation.dict()
                }
        
        except Exception as e:
            self.logger.error("Failed to optimize price", error=str(e))
            raise
    
    async def _get_price_recommendation(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate price recommendation without applying changes."""
        try:
            product_id = request_data["product_id"]
            channel = request_data.get("channel")
            current_price = request_data["current_price"]
            cost_price = request_data["cost_price"]
            target_margin_percent = request_data.get("target_margin_percent", 30.0)
            
            # Collect pricing factors
            factors = await self._collect_pricing_factors(
                product_id, 
                channel,
                request_data.get("consider_competitors", True),
                request_data.get("consider_demand", True),
                request_data.get("consider_inventory", True)
            )
            
            # Use AI to generate price recommendation
            ai_recommendation = await self._ai_price_recommendation(
                product_id, current_price, cost_price, target_margin_percent, factors
            )
            
            if ai_recommendation:
                recommended_price = ai_recommendation["recommended_price"]
                reasoning = ai_recommendation["reasoning"]
                confidence = ai_recommendation["confidence"]
            else:
                # Fallback to rule-based pricing
                recommended_price, reasoning, confidence = await self._rule_based_pricing(
                    current_price, cost_price, target_margin_percent, factors
                )
            
            # Calculate metrics
            price_change_percent = ((recommended_price - current_price) / current_price) * 100
            expected_margin_percent = ((recommended_price - cost_price) / recommended_price) * 100
            
            # Create recommendation
            recommendation = PriceRecommendation(
                product_id=product_id,
                channel=channel,
                current_price=current_price,
                recommended_price=round(recommended_price, 2),
                price_change_percent=round(price_change_percent, 2),
                expected_margin_percent=round(expected_margin_percent, 2),
                confidence_score=confidence,
                reasoning=reasoning,
                factors_considered=factors,
                valid_until=datetime.utcnow() + timedelta(hours=6),  # Valid for 6 hours
                generated_at=datetime.utcnow()
            )
            
            return recommendation.dict()
        
        except Exception as e:
            self.logger.error("Failed to get price recommendation", error=str(e))
            raise
    
    async def _collect_pricing_factors(
        self, 
        product_id: str, 
        channel: Optional[str],
        consider_competitors: bool,
        consider_demand: bool,
        consider_inventory: bool
    ) -> Dict[str, Any]:
        """Collect all factors that influence pricing decisions."""
        try:
            factors = {}
            
            # Competitor pricing data
            if consider_competitors:
                competitor_data = await self._get_competitor_pricing_data(product_id)
                factors["competitors"] = competitor_data
            
            # Demand forecast data
            if consider_demand:
                demand_data = await self._get_demand_data(product_id)
                factors["demand"] = demand_data
            
            # Inventory data
            if consider_inventory:
                inventory_data = await self._get_inventory_data(product_id)
                factors["inventory"] = inventory_data
            
            # Market conditions
            market_data = await self._get_market_conditions()
            factors["market"] = market_data
            
            # Historical pricing performance
            performance_data = await self._get_pricing_performance(product_id)
            factors["performance"] = performance_data
            
            # Seasonal factors
            seasonal_data = await self._get_seasonal_factors(product_id)
            factors["seasonality"] = seasonal_data
            
            return factors
        
        except Exception as e:
            self.logger.error("Failed to collect pricing factors", error=str(e))
            return {}
    
    async def _ai_price_recommendation(
        self, 
        product_id: str, 
        current_price: float, 
        cost_price: float, 
        target_margin: float, 
        factors: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Use AI to generate price recommendation."""
        try:
            if not openai.api_key:
                self.logger.warning("OpenAI API key not configured, using rule-based pricing")
                return None
            
            # Prepare AI prompt
            prompt = f"""
            You are an expert pricing strategist for an e-commerce platform. Analyze the following data and recommend an optimal price for the product.

            Product Information:
            - Product ID: {product_id}
            - Current Price: €{current_price}
            - Cost Price: €{cost_price}
            - Target Margin: {target_margin}%
            - Current Margin: {((current_price - cost_price) / current_price * 100):.1f}%

            Market Factors:
            {json.dumps(factors, indent=2, default=str)}

            Consider the following in your recommendation:
            1. Maintain profitability while staying competitive
            2. Balance demand optimization with margin protection
            3. Account for inventory levels and turnover
            4. Consider seasonal and market trends
            5. Ensure price changes are reasonable (avoid extreme swings)

            Provide your recommendation in JSON format:
            {{
                "recommended_price": 25.99,
                "reasoning": [
                    "Competitor prices are 10% higher, allowing for price increase",
                    "High demand forecast supports premium pricing",
                    "Low inventory suggests price increase to manage demand"
                ],
                "confidence": 0.85,
                "risk_factors": ["Market volatility", "Seasonal demand uncertainty"]
            }}
            """
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert pricing strategist with deep knowledge of e-commerce pricing optimization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                ai_result = json.loads(content)
                
                # Validate the recommendation
                recommended_price = ai_result.get("recommended_price", current_price)
                
                # Apply safety constraints
                min_price = cost_price * 1.1  # Minimum 10% margin
                max_price = current_price * 1.5  # Maximum 50% increase
                
                recommended_price = max(min_price, min(max_price, recommended_price))
                
                return {
                    "recommended_price": recommended_price,
                    "reasoning": ai_result.get("reasoning", ["AI-generated recommendation"]),
                    "confidence": min(0.95, ai_result.get("confidence", 0.7))
                }
            
            except json.JSONDecodeError:
                self.logger.error("Failed to parse AI response as JSON", response=content)
                return None
        
        except Exception as e:
            self.logger.error("AI price recommendation failed", error=str(e))
            return None
    
    async def _rule_based_pricing(
        self, 
        current_price: float, 
        cost_price: float, 
        target_margin: float, 
        factors: Dict[str, Any]
    ) -> Tuple[float, List[str], float]:
        """Fallback rule-based pricing algorithm."""
        try:
            reasoning = []
            price_adjustments = []
            
            # Base price with target margin
            base_price = cost_price / (1 - target_margin / 100)
            
            # Competitor-based adjustment
            competitor_data = factors.get("competitors", {})
            if competitor_data.get("average_price"):
                competitor_avg = competitor_data["average_price"]
                if competitor_avg > current_price * 1.1:
                    price_adjustments.append(0.05)  # 5% increase
                    reasoning.append("Competitors pricing 10% higher, opportunity for increase")
                elif competitor_avg < current_price * 0.9:
                    price_adjustments.append(-0.03)  # 3% decrease
                    reasoning.append("Competitors pricing 10% lower, need to stay competitive")
            
            # Demand-based adjustment
            demand_data = factors.get("demand", {})
            if demand_data.get("trend") == "increasing":
                price_adjustments.append(0.03)  # 3% increase
                reasoning.append("Increasing demand trend supports price increase")
            elif demand_data.get("trend") == "decreasing":
                price_adjustments.append(-0.02)  # 2% decrease
                reasoning.append("Decreasing demand suggests price reduction")
            
            # Inventory-based adjustment
            inventory_data = factors.get("inventory", {})
            if inventory_data.get("level") == "low":
                price_adjustments.append(0.04)  # 4% increase
                reasoning.append("Low inventory levels support higher pricing")
            elif inventory_data.get("level") == "high":
                price_adjustments.append(-0.02)  # 2% decrease
                reasoning.append("High inventory levels suggest price reduction to move stock")
            
            # Apply adjustments
            total_adjustment = sum(price_adjustments)
            adjusted_price = current_price * (1 + total_adjustment)
            
            # Ensure minimum margin
            min_price = cost_price * 1.1  # 10% minimum margin
            final_price = max(min_price, adjusted_price)
            
            # Calculate confidence based on number of factors
            confidence = 0.6 + (len(reasoning) * 0.1)  # Higher confidence with more factors
            confidence = min(0.9, confidence)
            
            if not reasoning:
                reasoning.append("No significant market factors detected, maintaining current price")
                final_price = current_price
            
            return final_price, reasoning, confidence
        
        except Exception as e:
            self.logger.error("Rule-based pricing failed", error=str(e))
            return current_price, ["Error in pricing calculation, maintaining current price"], 0.5
    
    async def _get_competitor_pricing_data(self, product_id: str) -> Dict[str, Any]:
        """Get competitor pricing data for a product."""
        try:
            competitor_prices = self.competitor_prices.get(product_id, [])
            
            if not competitor_prices:
                return {"available": False}
            
            # Calculate statistics
            prices = [cp.price for cp in competitor_prices if cp.availability]
            
            if not prices:
                return {"available": False}
            
            return {
                "available": True,
                "count": len(prices),
                "average_price": sum(prices) / len(prices),
                "min_price": min(prices),
                "max_price": max(prices),
                "last_updated": max(cp.last_updated for cp in competitor_prices).isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to get competitor pricing data", error=str(e))
            return {"available": False}
    
    async def _get_demand_data(self, product_id: str) -> Dict[str, Any]:
        """Get demand forecast data for a product."""
        try:
            # In production, this would query the demand forecasting agent
            # For now, return simulated data
            
            import random
            
            trends = ["increasing", "stable", "decreasing"]
            trend = random.choice(trends)
            
            return {
                "available": True,
                "trend": trend,
                "forecast_30_days": random.uniform(50, 200),
                "confidence": random.uniform(0.6, 0.9),
                "last_updated": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to get demand data", error=str(e))
            return {"available": False}
    
    async def _get_inventory_data(self, product_id: str) -> Dict[str, Any]:
        """Get inventory data for a product."""
        try:
            # In production, this would query the inventory agent
            # For now, return simulated data
            
            import random
            
            current_stock = random.randint(0, 100)
            
            if current_stock < 10:
                level = "low"
            elif current_stock > 50:
                level = "high"
            else:
                level = "normal"
            
            return {
                "available": True,
                "current_stock": current_stock,
                "level": level,
                "days_of_supply": random.uniform(5, 30),
                "last_updated": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to get inventory data", error=str(e))
            return {"available": False}
    
    async def _get_market_conditions(self) -> Dict[str, Any]:
        """Get general market conditions."""
        try:
            # In production, this would integrate with market data APIs
            # For now, return simulated data
            
            import random
            
            conditions = ["bullish", "neutral", "bearish"]
            condition = random.choice(conditions)
            
            return {
                "condition": condition,
                "volatility": random.uniform(0.1, 0.5),
                "consumer_confidence": random.uniform(0.6, 0.9),
                "last_updated": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to get market conditions", error=str(e))
            return {"condition": "neutral", "volatility": 0.2}
    
    async def _get_pricing_performance(self, product_id: str) -> Dict[str, Any]:
        """Get historical pricing performance for a product."""
        try:
            price_history = self.price_history.get(product_id, [])
            
            if not price_history:
                return {"available": False}
            
            # Calculate performance metrics
            recent_changes = [event for event in price_history if event.effective_date > datetime.utcnow() - timedelta(days=30)]
            
            return {
                "available": True,
                "total_changes": len(price_history),
                "recent_changes": len(recent_changes),
                "last_change": price_history[-1].effective_date.isoformat() if price_history else None,
                "average_change_percent": 2.5  # Simulated average
            }
        
        except Exception as e:
            self.logger.error("Failed to get pricing performance", error=str(e))
            return {"available": False}
    
    async def _get_seasonal_factors(self, product_id: str) -> Dict[str, Any]:
        """Get seasonal factors affecting pricing."""
        try:
            # Simple seasonal analysis based on current date
            now = datetime.utcnow()
            month = now.month
            
            # Define seasonal patterns (simplified)
            if month in [11, 12]:  # Holiday season
                seasonal_factor = 1.1  # 10% premium
                season = "holiday"
            elif month in [6, 7, 8]:  # Summer
                seasonal_factor = 1.05  # 5% premium
                season = "summer"
            elif month in [1, 2]:  # Post-holiday
                seasonal_factor = 0.95  # 5% discount
                season = "post_holiday"
            else:
                seasonal_factor = 1.0
                season = "normal"
            
            return {
                "season": season,
                "factor": seasonal_factor,
                "month": month,
                "description": f"Seasonal adjustment for {season} period"
            }
        
        except Exception as e:
            self.logger.error("Failed to get seasonal factors", error=str(e))
            return {"season": "normal", "factor": 1.0}
    
    async def _apply_price_change(self, recommendation: PriceRecommendation):
        """Apply a price change based on recommendation."""
        try:
            # Create price change event
            price_change = PriceChangeEvent(
                product_id=recommendation.product_id,
                channel=recommendation.channel,
                old_price=recommendation.current_price,
                new_price=recommendation.recommended_price,
                change_reason="automatic_optimization",
                change_type="automatic",
                effective_date=datetime.utcnow(),
                created_by=self.agent_id
            )
            
            # Store price change history
            if recommendation.product_id not in self.price_history:
                self.price_history[recommendation.product_id] = []
            
            self.price_history[recommendation.product_id].append(price_change)
            
            # In production, this would update the product database
            self.logger.info("Price change applied", 
                           product_id=recommendation.product_id,
                           old_price=recommendation.current_price,
                           new_price=recommendation.recommended_price)
        
        except Exception as e:
            self.logger.error("Failed to apply price change", error=str(e))
            raise
    
    async def _update_competitor_prices(self, product_id: str, prices_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update competitor prices for a product."""
        try:
            competitor_prices = []
            
            for price_data in prices_data:
                competitor_price = CompetitorPrice(
                    competitor_name=price_data["competitor_name"],
                    price=price_data["price"],
                    availability=price_data.get("availability", True),
                    last_updated=datetime.utcnow(),
                    source=price_data.get("source", "api")
                )
                competitor_prices.append(competitor_price)
            
            # Store competitor prices
            self.competitor_prices[product_id] = competitor_prices
            
            # Trigger price optimization if significant changes detected
            await self._check_for_price_optimization_trigger(product_id)
            
            return {
                "product_id": product_id,
                "updated_prices": len(competitor_prices),
                "last_updated": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to update competitor prices", error=str(e))
            raise
    
    async def _get_pricing_analytics(self, product_id: Optional[str] = None) -> Dict[str, Any]:
        """Get pricing analytics and performance metrics."""
        try:
            if product_id:
                # Analytics for specific product
                price_history = self.price_history.get(product_id, [])
                competitor_prices = self.competitor_prices.get(product_id, [])
                
                return {
                    "product_id": product_id,
                    "price_changes": len(price_history),
                    "last_price_change": price_history[-1].effective_date.isoformat() if price_history else None,
                    "competitor_count": len(competitor_prices),
                    "price_position": await self._calculate_price_position(product_id),
                    "optimization_opportunities": await self._identify_optimization_opportunities(product_id)
                }
            else:
                # Overall analytics
                total_products = len(self.price_history)
                total_changes = sum(len(history) for history in self.price_history.values())
                
                return {
                    "total_products_tracked": total_products,
                    "total_price_changes": total_changes,
                    "average_changes_per_product": total_changes / total_products if total_products > 0 else 0,
                    "active_strategies": len([s for s in self.pricing_strategies.values() if s.active]),
                    "last_optimization_run": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            self.logger.error("Failed to get pricing analytics", error=str(e))
            raise
    
    async def _apply_promotional_pricing(self, promotion_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply promotional pricing strategy."""
        try:
            product_ids = promotion_config.get("product_ids", [])
            discount_percent = promotion_config.get("discount_percent", 10.0)
            start_date = datetime.fromisoformat(promotion_config.get("start_date", datetime.utcnow().isoformat()))
            end_date = datetime.fromisoformat(promotion_config.get("end_date", (datetime.utcnow() + timedelta(days=7)).isoformat()))
            
            applied_promotions = []
            
            for product_id in product_ids:
                # Get current price (simulated)
                current_price = 25.99  # In production, get from product database
                
                # Calculate promotional price
                promotional_price = current_price * (1 - discount_percent / 100)
                
                # Create price change event
                price_change = PriceChangeEvent(
                    product_id=product_id,
                    channel=None,
                    old_price=current_price,
                    new_price=promotional_price,
                    change_reason=f"promotional_discount_{discount_percent}%",
                    change_type="promotional",
                    effective_date=start_date,
                    created_by=self.agent_id
                )
                
                # Store price change
                if product_id not in self.price_history:
                    self.price_history[product_id] = []
                
                self.price_history[product_id].append(price_change)
                
                applied_promotions.append({
                    "product_id": product_id,
                    "original_price": current_price,
                    "promotional_price": promotional_price,
                    "discount_percent": discount_percent,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                })
                
                # Send promotion notification
                await self.send_message(
                    recipient_agent="product_agent",
                    message_type=MessageType.PRICE_UPDATE,
                    payload={
                        "product_id": product_id,
                        "old_price": current_price,
                        "new_price": promotional_price,
                        "change_reason": "promotional_pricing",
                        "promotion_end_date": end_date.isoformat()
                    }
                )
            
            return {
                "promotion_id": str(uuid4()),
                "applied_products": len(applied_promotions),
                "promotions": applied_promotions,
                "created_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to apply promotional pricing", error=str(e))
            raise
    
    async def _calculate_price_position(self, product_id: str) -> Dict[str, Any]:
        """Calculate price position relative to competitors."""
        try:
            competitor_prices = self.competitor_prices.get(product_id, [])
            
            if not competitor_prices:
                return {"position": "unknown", "reason": "No competitor data"}
            
            # Get current price (simulated)
            current_price = 25.99  # In production, get from product database
            
            available_prices = [cp.price for cp in competitor_prices if cp.availability]
            
            if not available_prices:
                return {"position": "unknown", "reason": "No available competitor prices"}
            
            avg_competitor_price = sum(available_prices) / len(available_prices)
            min_competitor_price = min(available_prices)
            max_competitor_price = max(available_prices)
            
            # Determine position
            if current_price < min_competitor_price:
                position = "lowest"
            elif current_price > max_competitor_price:
                position = "highest"
            elif current_price < avg_competitor_price:
                position = "below_average"
            elif current_price > avg_competitor_price:
                position = "above_average"
            else:
                position = "average"
            
            return {
                "position": position,
                "current_price": current_price,
                "competitor_average": round(avg_competitor_price, 2),
                "competitor_min": min_competitor_price,
                "competitor_max": max_competitor_price,
                "price_difference_percent": round(((current_price - avg_competitor_price) / avg_competitor_price) * 100, 2)
            }
        
        except Exception as e:
            self.logger.error("Failed to calculate price position", error=str(e))
            return {"position": "unknown", "reason": "Calculation error"}
    
    async def _identify_optimization_opportunities(self, product_id: str) -> List[Dict[str, Any]]:
        """Identify pricing optimization opportunities."""
        try:
            opportunities = []
            
            # Check competitor pricing opportunity
            price_position = await self._calculate_price_position(product_id)
            if price_position["position"] == "below_average":
                opportunities.append({
                    "type": "competitor_pricing",
                    "description": "Price is below competitor average, consider increase",
                    "potential_impact": "positive",
                    "confidence": 0.7
                })
            
            # Check inventory-based opportunity
            inventory_data = await self._get_inventory_data(product_id)
            if inventory_data.get("level") == "low":
                opportunities.append({
                    "type": "inventory_optimization",
                    "description": "Low inventory allows for premium pricing",
                    "potential_impact": "positive",
                    "confidence": 0.8
                })
            
            # Check demand-based opportunity
            demand_data = await self._get_demand_data(product_id)
            if demand_data.get("trend") == "increasing":
                opportunities.append({
                    "type": "demand_optimization",
                    "description": "Increasing demand supports price increase",
                    "potential_impact": "positive",
                    "confidence": 0.75
                })
            
            return opportunities
        
        except Exception as e:
            self.logger.error("Failed to identify optimization opportunities", error=str(e))
            return []
    
    async def _initialize_pricing_strategies(self):
        """Initialize default pricing strategies."""
        try:
            # Define default pricing strategies
            strategies = [
                PricingStrategy(
                    strategy_id="competitive",
                    name="Competitive Pricing",
                    description="Price based on competitor analysis",
                    min_margin_percent=15.0,
                    max_discount_percent=20.0,
                    demand_sensitivity=0.3,
                    competitor_sensitivity=0.7,
                    inventory_sensitivity=0.2
                ),
                PricingStrategy(
                    strategy_id="demand_based",
                    name="Demand-Based Pricing",
                    description="Price based on demand forecasting",
                    min_margin_percent=20.0,
                    max_discount_percent=15.0,
                    demand_sensitivity=0.8,
                    competitor_sensitivity=0.2,
                    inventory_sensitivity=0.4
                ),
                PricingStrategy(
                    strategy_id="inventory_driven",
                    name="Inventory-Driven Pricing",
                    description="Price based on inventory levels",
                    min_margin_percent=10.0,
                    max_discount_percent=30.0,
                    demand_sensitivity=0.2,
                    competitor_sensitivity=0.3,
                    inventory_sensitivity=0.8
                )
            ]
            
            for strategy in strategies:
                self.pricing_strategies[strategy.strategy_id] = strategy
            
            self.logger.info("Pricing strategies initialized", count=len(strategies))
        
        except Exception as e:
            self.logger.error("Failed to initialize pricing strategies", error=str(e))
    
    async def _load_competitor_prices(self):
        """Load initial competitor pricing data."""
        try:
            # In production, this would load from database or external APIs
            # For now, create sample data
            
            sample_products = ["product_1", "product_2", "product_3"]
            
            for product_id in sample_products:
                competitor_prices = [
                    CompetitorPrice(
                        competitor_name="Competitor A",
                        price=24.99,
                        availability=True,
                        last_updated=datetime.utcnow(),
                        source="api"
                    ),
                    CompetitorPrice(
                        competitor_name="Competitor B",
                        price=26.50,
                        availability=True,
                        last_updated=datetime.utcnow(),
                        source="scraping"
                    ),
                    CompetitorPrice(
                        competitor_name="Competitor C",
                        price=23.75,
                        availability=False,
                        last_updated=datetime.utcnow() - timedelta(hours=2),
                        source="api"
                    )
                ]
                
                self.competitor_prices[product_id] = competitor_prices
            
            self.logger.info("Competitor prices loaded", products=len(sample_products))
        
        except Exception as e:
            self.logger.error("Failed to load competitor prices", error=str(e))
    
    async def _check_for_price_optimization_trigger(self, product_id: str):
        """Check if price optimization should be triggered."""
        try:
            # Get current competitor data
            competitor_data = await self._get_competitor_pricing_data(product_id)
            
            if competitor_data.get("available"):
                # Check if significant price changes detected
                # This is a simplified trigger - in production, more sophisticated logic would be used
                
                # Trigger optimization if we have competitor data
                optimization_request = {
                    "product_id": product_id,
                    "current_price": 25.99,  # In production, get from database
                    "cost_price": 18.00,     # In production, get from database
                    "consider_competitors": True,
                    "consider_demand": True,
                    "consider_inventory": True
                }
                
                await self._get_price_recommendation(optimization_request)
        
        except Exception as e:
            self.logger.error("Failed to check price optimization trigger", error=str(e))
    
    async def _handle_demand_forecast(self, message: AgentMessage):
        """Handle demand forecast updates for pricing optimization."""
        payload = message.payload
        product_id = payload.get("product_id")
        predicted_demand = payload.get("predicted_demand")
        confidence_score = payload.get("confidence_score")
        
        if product_id and predicted_demand is not None:
            try:
                # Trigger price optimization based on demand changes
                optimization_request = {
                    "product_id": product_id,
                    "current_price": 25.99,  # In production, get from database
                    "cost_price": 18.00,     # In production, get from database
                    "consider_demand": True,
                    "consider_competitors": True,
                    "consider_inventory": False
                }
                
                recommendation = await self._get_price_recommendation(optimization_request)
                
                # If high confidence and significant price change, send alert
                if (recommendation["confidence_score"] > 0.8 and 
                    abs(recommendation["price_change_percent"]) > 5):
                    
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.RISK_ALERT,
                        payload={
                            "alert_type": "pricing_opportunity",
                            "product_id": product_id,
                            "current_price": recommendation["current_price"],
                            "recommended_price": recommendation["recommended_price"],
                            "confidence": recommendation["confidence_score"],
                            "severity": "info"
                        }
                    )
            
            except Exception as e:
                self.logger.error("Failed to handle demand forecast", error=str(e), product_id=product_id)
    
    async def _handle_inventory_update(self, message: AgentMessage):
        """Handle inventory updates for pricing optimization."""
        payload = message.payload
        product_id = payload.get("product_id")
        new_quantity = payload.get("new_quantity")
        
        if product_id and new_quantity is not None:
            # Trigger pricing review for low inventory items
            if new_quantity < 10:  # Low inventory threshold
                try:
                    optimization_request = {
                        "product_id": product_id,
                        "current_price": 25.99,  # In production, get from database
                        "cost_price": 18.00,     # In production, get from database
                        "consider_inventory": True,
                        "consider_demand": True,
                        "consider_competitors": False
                    }
                    
                    await self._get_price_recommendation(optimization_request)
                
                except Exception as e:
                    self.logger.error("Failed to handle inventory update", error=str(e), product_id=product_id)
    
    async def _handle_competitor_price_update(self, message: AgentMessage):
        """Handle competitor price updates."""
        payload = message.payload
        product_id = payload.get("product_id")
        competitor_prices = payload.get("competitor_prices", [])
        
        if product_id and competitor_prices:
            try:
                await self._update_competitor_prices(product_id, competitor_prices)
            
            except Exception as e:
                self.logger.error("Failed to handle competitor price update", error=str(e), product_id=product_id)
    
    async def _monitor_competitor_prices(self):
        """Background task to monitor competitor prices."""
        while not self.shutdown_event.is_set():
            try:
                # In production, this would scrape competitor websites or call APIs
                # For now, simulate price updates
                
                for product_id in self.competitor_prices.keys():
                    # Simulate price changes
                    import random
                    
                    if random.random() < 0.1:  # 10% chance of price change
                        competitor_prices = self.competitor_prices[product_id]
                        
                        for cp in competitor_prices:
                            # Simulate small price changes
                            change_percent = random.uniform(-0.05, 0.05)  # ±5%
                            cp.price = cp.price * (1 + change_percent)
                            cp.last_updated = datetime.utcnow()
                        
                        # Trigger optimization check
                        await self._check_for_price_optimization_trigger(product_id)
                
                # Sleep for 1 hour before next check
                await asyncio.sleep(3600)
            
            except Exception as e:
                self.logger.error("Error monitoring competitor prices", error=str(e))
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def _optimize_prices_periodically(self):
        """Background task to optimize prices periodically."""
        while not self.shutdown_event.is_set():
            try:
                # Run optimization every 6 hours
                await asyncio.sleep(6 * 3600)
                
                if not self.shutdown_event.is_set():
                    self.logger.info("Starting periodic price optimization")
                    
                    # Optimize prices for all tracked products
                    for product_id in self.competitor_prices.keys():
                        try:
                            optimization_request = {
                                "product_id": product_id,
                                "current_price": 25.99,  # In production, get from database
                                "cost_price": 18.00,     # In production, get from database
                                "consider_competitors": True,
                                "consider_demand": True,
                                "consider_inventory": True
                            }
                            
                            await self._optimize_price(optimization_request)
                        
                        except Exception as e:
                            self.logger.error("Failed to optimize price", error=str(e), product_id=product_id)
                    
                    self.logger.info("Periodic price optimization completed")
            
            except Exception as e:
                self.logger.error("Error in periodic price optimization", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _analyze_pricing_performance(self):
        """Background task to analyze pricing performance."""
        while not self.shutdown_event.is_set():
            try:
                # Analyze performance every 24 hours
                await asyncio.sleep(24 * 3600)
                
                if not self.shutdown_event.is_set():
                    analytics = await self._get_pricing_analytics()
                    
                    # Send performance report to monitoring agent
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.RISK_ALERT,
                        payload={
                            "alert_type": "pricing_performance_report",
                            "total_products": analytics["total_products_tracked"],
                            "total_changes": analytics["total_price_changes"],
                            "average_changes": analytics["average_changes_per_product"],
                            "severity": "info"
                        }
                    )
            
            except Exception as e:
                self.logger.error("Error analyzing pricing performance", error=str(e))
                await asyncio.sleep(12 * 3600)  # Wait 12 hours on error


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Dynamic Pricing Agent", version="1.0.0")

# Global agent instance
dynamic_pricing_agent: Optional[DynamicPricingAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Dynamic Pricing Agent on startup."""
    global dynamic_pricing_agent
    dynamic_pricing_agent = DynamicPricingAgent()
    await dynamic_pricing_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Dynamic Pricing Agent on shutdown."""
    global dynamic_pricing_agent
    if dynamic_pricing_agent:
        await dynamic_pricing_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if dynamic_pricing_agent:
        health_status = dynamic_pricing_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", dynamic_pricing_agent.app if dynamic_pricing_agent else FastAPI())


if __name__ == "__main__":
    import uvicorn
    from shared.database import initialize_database_manager, DatabaseConfig
    import os
    
    # Initialize database
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres123")
    )
    initialize_database_manager(db_config)
    
    # Run the agent
    uvicorn.run(
        "dynamic_pricing_agent:app",
        host="0.0.0.0",
        port=8007,
        reload=False,
        log_level="info"
    )
