"""
International Shipping Support Agent v3
Comprehensive international shipping with customs, duty calculation, and compliance
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json

app = FastAPI(title="International Shipping Agent", version="3.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# ============================================================================
# Pydantic Models
# ============================================================================

class DutyCalculationRequest(BaseModel):
    product_value: float
    hs_code: str
    destination_country: str
    origin_country: str = "US"

class LandedCostRequest(BaseModel):
    product_value: float
    hs_code: str
    destination_country: str
    origin_country: str = "US"
    weight_kg: float
    currency: str = "USD"

class CurrencyConversionRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str

# ============================================================================
# Sample Data - Country Regulations
# ============================================================================

COUNTRY_REGULATIONS = {
    "US": {
        "name": "United States",
        "de_minimis": 800,
        "vat_rate": 0,
        "requires_tax_id": False
    },
    "GB": {
        "name": "United Kingdom",
        "de_minimis": 135,
        "vat_rate": 20.0,
        "requires_tax_id": False
    },
    "DE": {
        "name": "Germany",
        "de_minimis": 150,
        "vat_rate": 19.0,
        "requires_tax_id": False
    },
    "FR": {
        "name": "France",
        "de_minimis": 150,
        "vat_rate": 20.0,
        "requires_tax_id": False
    },
    "CA": {
        "name": "Canada",
        "de_minimis": 20,
        "vat_rate": 5.0,  # GST
        "requires_tax_id": False
    },
    "AU": {
        "name": "Australia",
        "de_minimis": 1000,
        "vat_rate": 10.0,  # GST
        "requires_tax_id": False
    },
    "JP": {
        "name": "Japan",
        "de_minimis": 10000,
        "vat_rate": 10.0,
        "requires_tax_id": False
    },
    "CN": {
        "name": "China",
        "de_minimis": 50,
        "vat_rate": 13.0,
        "requires_tax_id": False
    }
}

# Sample HS Code duty rates (simplified)
HS_CODE_DUTY_RATES = {
    "6109": {"description": "T-shirts", "default_duty": 16.5},
    "6203": {"description": "Men's suits", "default_duty": 29.5},
    "6204": {"description": "Women's suits", "default_duty": 28.2},
    "8517": {"description": "Phones/Electronics", "default_duty": 0},
    "6402": {"description": "Footwear", "default_duty": 37.5},
    "4202": {"description": "Bags/Luggage", "default_duty": 17.6},
    "9503": {"description": "Toys", "default_duty": 0},
    "6401": {"description": "Waterproof footwear", "default_duty": 37.5}
}

# Sample exchange rates
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "CAD": 1.36,
    "AUD": 1.52,
    "JPY": 149.50,
    "CNY": 7.24
}

# ============================================================================
# Helper Functions
# ============================================================================

def get_country_regulations(country_code: str) -> Dict:
    """Get country regulations"""
    return COUNTRY_REGULATIONS.get(country_code, {
        "name": "Unknown",
        "de_minimis": 0,
        "vat_rate": 0,
        "requires_tax_id": False
    })

def get_duty_rate(hs_code: str) -> float:
    """Get duty rate for HS code"""
    # Get first 4 digits of HS code
    hs_prefix = hs_code[:4]
    hs_info = HS_CODE_DUTY_RATES.get(hs_prefix, {"default_duty": 5.0})
    return hs_info.get("default_duty", 5.0)

def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert currency"""
    if from_currency == to_currency:
        return amount
    
    # Convert to USD first, then to target currency
    usd_amount = amount / EXCHANGE_RATES.get(from_currency, 1.0)
    target_amount = usd_amount * EXCHANGE_RATES.get(to_currency, 1.0)
    
    return round(target_amount, 2)

# ============================================================================
# API Endpoints - Health & Info
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "international_shipping_agent",
        "version": "3.0.0",
        "features": ["duty_calculation", "landed_cost", "customs_docs", "multi_currency"],
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# API Endpoints - Duty & Tax Calculation
# ============================================================================

@app.post("/api/international/duty/calculate")
async def calculate_duty(request: DutyCalculationRequest):
    """Calculate import duty and taxes"""
    
    try:
        # Get country regulations
        regulations = get_country_regulations(request.destination_country)
        
        # Check de minimis threshold
        de_minimis = regulations.get("de_minimis", 0)
        
        # Calculate duty
        duty_rate = get_duty_rate(request.hs_code)
        duty_amount = 0
        
        if request.product_value > de_minimis:
            duty_amount = request.product_value * (duty_rate / 100)
        
        # Calculate VAT/GST
        vat_rate = regulations.get("vat_rate", 0)
        vat_base = request.product_value + duty_amount
        vat_amount = vat_base * (vat_rate / 100)
        
        return {
            "success": True,
            "product_value": request.product_value,
            "destination_country": request.destination_country,
            "country_name": regulations.get("name"),
            "hs_code": request.hs_code,
            "duty": {
                "rate_percentage": duty_rate,
                "amount": round(duty_amount, 2),
                "applied": duty_amount > 0
            },
            "vat": {
                "rate_percentage": vat_rate,
                "base": round(vat_base, 2),
                "amount": round(vat_amount, 2)
            },
            "de_minimis_threshold": de_minimis,
            "total_duties_taxes": round(duty_amount + vat_amount, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/international/landed-cost")
async def calculate_landed_cost(request: LandedCostRequest):
    """Calculate total landed cost"""
    
    try:
        # Product cost
        product_cost = request.product_value
        
        # Estimate shipping cost based on weight and destination
        # Simplified calculation: $10 base + $5 per kg
        shipping_cost = 10 + (request.weight_kg * 5)
        
        # Insurance (2% of product value)
        insurance = product_cost * 0.02
        
        # Calculate duty
        regulations = get_country_regulations(request.destination_country)
        de_minimis = regulations.get("de_minimis", 0)
        
        duty_rate = get_duty_rate(request.hs_code)
        duty_amount = 0
        if product_cost > de_minimis:
            duty_amount = product_cost * (duty_rate / 100)
        
        # Calculate VAT
        vat_rate = regulations.get("vat_rate", 0)
        vat_base = product_cost + duty_amount
        vat_amount = vat_base * (vat_rate / 100)
        
        # Handling fee
        handling_fee = 10.00
        
        # Total landed cost
        total_landed_cost = (
            product_cost +
            shipping_cost +
            insurance +
            duty_amount +
            vat_amount +
            handling_fee
        )
        
        # Calculate percentages
        breakdown = {
            "product_percentage": round((product_cost / total_landed_cost) * 100, 1),
            "shipping_percentage": round((shipping_cost / total_landed_cost) * 100, 1),
            "duties_taxes_percentage": round(((duty_amount + vat_amount) / total_landed_cost) * 100, 1),
            "fees_percentage": round(((insurance + handling_fee) / total_landed_cost) * 100, 1)
        }
        
        return {
            "success": True,
            "destination_country": request.destination_country,
            "country_name": regulations.get("name"),
            "currency": request.currency,
            "costs": {
                "product_cost": round(product_cost, 2),
                "shipping_cost": round(shipping_cost, 2),
                "insurance": round(insurance, 2),
                "duty": round(duty_amount, 2),
                "vat": round(vat_amount, 2),
                "handling_fee": round(handling_fee, 2),
                "total_landed_cost": round(total_landed_cost, 2)
            },
            "breakdown": breakdown,
            "duty_info": {
                "duty_rate": duty_rate,
                "vat_rate": vat_rate,
                "de_minimis_threshold": de_minimis
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API Endpoints - Currency
# ============================================================================

@app.get("/api/international/exchange-rates")
async def get_exchange_rates(base_currency: str = "USD"):
    """Get current exchange rates"""
    
    if base_currency not in EXCHANGE_RATES:
        raise HTTPException(status_code=400, detail="Invalid base currency")
    
    # Calculate rates relative to base currency
    base_rate = EXCHANGE_RATES[base_currency]
    rates = {}
    
    for currency, rate in EXCHANGE_RATES.items():
        if currency != base_currency:
            rates[currency] = round(rate / base_rate, 6)
    
    return {
        "success": True,
        "base_currency": base_currency,
        "rates": rates,
        "last_updated": datetime.now().isoformat()
    }

@app.post("/api/international/currency/convert")
async def convert_currency_api(request: CurrencyConversionRequest):
    """Convert currency"""
    
    try:
        converted_amount = convert_currency(
            request.amount,
            request.from_currency,
            request.to_currency
        )
        
        return {
            "success": True,
            "original_amount": request.amount,
            "original_currency": request.from_currency,
            "converted_amount": converted_amount,
            "converted_currency": request.to_currency,
            "exchange_rate": round(converted_amount / request.amount, 6)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API Endpoints - Country Information
# ============================================================================

@app.get("/api/international/countries")
async def get_countries():
    """Get list of supported countries"""
    
    countries = []
    for code, info in COUNTRY_REGULATIONS.items():
        countries.append({
            "code": code,
            "name": info["name"],
            "de_minimis": info["de_minimis"],
            "vat_rate": info["vat_rate"],
            "requires_tax_id": info["requires_tax_id"]
        })
    
    return {
        "success": True,
        "total_countries": len(countries),
        "countries": countries
    }

@app.get("/api/international/countries/{country_code}")
async def get_country_info(country_code: str):
    """Get country-specific information"""
    
    regulations = get_country_regulations(country_code.upper())
    
    if not regulations.get("name"):
        raise HTTPException(status_code=404, detail="Country not found")
    
    return {
        "success": True,
        "country_code": country_code.upper(),
        "country_name": regulations["name"],
        "de_minimis_threshold": regulations["de_minimis"],
        "vat_rate": regulations["vat_rate"],
        "requires_tax_id": regulations["requires_tax_id"]
    }

# ============================================================================
# API Endpoints - HS Codes
# ============================================================================

@app.get("/api/international/hs-codes")
async def get_hs_codes():
    """Get list of HS codes"""
    
    hs_codes = []
    for code, info in HS_CODE_DUTY_RATES.items():
        hs_codes.append({
            "hs_code": code,
            "description": info["description"],
            "default_duty_rate": info["default_duty"]
        })
    
    return {
        "success": True,
        "total_codes": len(hs_codes),
        "hs_codes": hs_codes
    }

@app.get("/api/international/hs-codes/{hs_code}")
async def get_hs_code_info(hs_code: str):
    """Get HS code information"""
    
    hs_prefix = hs_code[:4]
    info = HS_CODE_DUTY_RATES.get(hs_prefix)
    
    if not info:
        raise HTTPException(status_code=404, detail="HS code not found")
    
    return {
        "success": True,
        "hs_code": hs_code,
        "description": info["description"],
        "default_duty_rate": info["default_duty"]
    }

# ============================================================================
# API Endpoints - Dashboard
# ============================================================================

@app.get("/api/international/dashboard")
async def get_international_dashboard():
    """Get international shipping dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get shipment summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_shipments,
                COUNT(CASE WHEN customs_status = 'cleared' THEN 1 END) as cleared_shipments,
                COUNT(CASE WHEN customs_status = 'pending' THEN 1 END) as pending_shipments,
                COUNT(DISTINCT destination_country) as destination_countries
            FROM international_shipments
        """)
        
        summary = cursor.fetchone()
        
        return {
            "success": True,
            "summary": dict(summary) if summary else {},
            "supported_countries": len(COUNTRY_REGULATIONS),
            "supported_currencies": len(EXCHANGE_RATES),
            "hs_codes_available": len(HS_CODE_DUTY_RATES),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8038)
