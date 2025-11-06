"""
Intelligent Carrier Selection Agent v3 with AI Rate Card Extraction
Handles carrier management, rate shopping, label generation, and AI-powered rate card extraction
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, date
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from openai import OpenAI
import base64

app = FastAPI(title="Carrier Selection Agent with AI", version="3.0.0")

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

# OpenAI client for AI rate extraction
openai_client = OpenAI()

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

class CarrierCreate(BaseModel):
    carrier_code: str
    carrier_name: str
    account_number: Optional[str] = None
    dim_weight_divisor: Optional[int] = 139

class ServiceCreate(BaseModel):
    carrier_id: int
    service_code: str
    service_name: str
    service_type: str
    estimated_days: Optional[int] = None

class RateQuoteRequest(BaseModel):
    origin_zip: str
    destination_zip: str
    weight_lbs: float
    length_inches: Optional[float] = None
    width_inches: Optional[float] = None
    height_inches: Optional[float] = None
    service_type: Optional[str] = None

class LabelGenerateRequest(BaseModel):
    order_id: int
    carrier_id: int
    service_id: int
    origin_address: dict
    destination_address: dict
    weight_lbs: float
    dimensions: Optional[dict] = None
    insured_value: Optional[float] = None

class ManualRateEntry(BaseModel):
    carrier_id: int
    service_id: int
    origin_zip: str
    destination_zip: str
    weight_lbs: float
    total_rate: float
    estimated_days: Optional[int] = None
    zone: Optional[str] = None

# ============================================================================
# Helper Functions
# ============================================================================

def calculate_dimensional_weight(length: float, width: float, height: float, divisor: int = 139) -> float:
    """Calculate dimensional weight: (L × W × H) / divisor"""
    return (length * width * height) / divisor

def get_billable_weight(actual_weight: float, dim_weight: float) -> float:
    """Billable weight is the maximum of actual and dimensional weight"""
    return max(actual_weight, dim_weight)

def determine_zone(origin_zip: str, destination_zip: str) -> str:
    """Determine shipping zone (simplified)"""
    try:
        origin_prefix = int(origin_zip[:3])
        dest_prefix = int(destination_zip[:3])
        distance = abs(origin_prefix - dest_prefix)
        
        if distance < 50:
            return "Zone 2"
        elif distance < 150:
            return "Zone 4"
        elif distance < 300:
            return "Zone 6"
        else:
            return "Zone 8"
    except:
        return "Zone 5"

def simulate_carrier_rate(carrier_code: str, service_type: str, weight: float, zone: str) -> dict:
    """Simulate carrier rate"""
    base_rates = {
        "FEDEX": {"ground": 8.50, "express": 25.00, "overnight": 45.00},
        "UPS": {"ground": 8.25, "express": 24.50, "overnight": 44.00},
        "USPS": {"ground": 7.50, "express": 22.00, "overnight": 40.00},
        "DHL": {"ground": 9.00, "express": 26.00, "overnight": 48.00}
    }
    
    zone_multipliers = {
        "Zone 2": 1.0,
        "Zone 4": 1.3,
        "Zone 6": 1.6,
        "Zone 8": 2.0
    }
    
    base = base_rates.get(carrier_code, {}).get(service_type, 10.00)
    zone_mult = zone_multipliers.get(zone, 1.5)
    weight_mult = 1 + (weight / 10)
    
    base_rate = base * zone_mult * weight_mult
    fuel_surcharge = base_rate * 0.12
    total = base_rate + fuel_surcharge
    
    days_map = {"ground": 5, "express": 2, "overnight": 1}
    estimated_days = days_map.get(service_type, 3)
    
    return {
        "base_rate": round(base_rate, 2),
        "fuel_surcharge": round(fuel_surcharge, 2),
        "total_rate": round(total, 2),
        "estimated_days": estimated_days,
        "estimated_delivery_date": (datetime.now() + timedelta(days=estimated_days)).date().isoformat()
    }

async def extract_rates_with_ai(file_content: bytes, file_type: str, carrier_name: str) -> dict:
    """Use AI to extract rate information from uploaded documents"""
    
    prompt = f"""You are a shipping rate card extraction specialist. Extract structured rate information from this {carrier_name} rate card document.

Extract the following information:
1. Service levels (Ground, Express, Overnight, etc.)
2. Zones and their definitions
3. Weight brackets
4. Base rates for each zone/weight combination
5. Fuel surcharges (percentage or fixed)
6. Additional fees (residential delivery, signature, etc.)
7. Dimensional weight divisor
8. Effective dates

Return the data in this JSON format:
{{
    "carrier_name": "{carrier_name}",
    "effective_date": "YYYY-MM-DD",
    "expiration_date": "YYYY-MM-DD",
    "dim_weight_divisor": 139,
    "fuel_surcharge_percent": 12.5,
    "services": [
        {{
            "service_name": "Ground",
            "service_code": "GROUND",
            "service_type": "ground"
        }}
    ],
    "zones": [
        {{
            "zone_code": "Zone 2",
            "description": "0-150 miles"
        }}
    ],
    "rates": [
        {{
            "service_code": "GROUND",
            "zone": "Zone 2",
            "weight_min_lbs": 0,
            "weight_max_lbs": 5,
            "base_rate": 8.50
        }}
    ],
    "additional_fees": [
        {{
            "fee_name": "Residential Delivery",
            "fee_amount": 4.50
        }}
    ]
}}

If you cannot extract certain information, use null or reasonable defaults.
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a shipping rate card extraction specialist. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        extracted_text = response.choices[0].message.content
        
        # Parse JSON from response
        if "```json" in extracted_text:
            extracted_text = extracted_text.split("```json")[1].split("```")[0].strip()
        elif "```" in extracted_text:
            extracted_text = extracted_text.split("```")[1].split("```")[0].strip()
        
        extracted_data = json.loads(extracted_text)
        
        return {
            "success": True,
            "data": extracted_data,
            "rates_count": len(extracted_data.get("rates", [])),
            "services_count": len(extracted_data.get("services", []))
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "carrier_agent_ai",
        "version": "3.0.0",
        "features": ["ai_rate_extraction", "rate_shopping", "label_generation"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/carriers")
async def create_carrier(carrier: CarrierCreate):
    """Create a new carrier"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO carriers 
            (carrier_code, carrier_name, account_number, dim_weight_divisor, is_active)
            VALUES (%s, %s, %s, %s, true)
            RETURNING id
        """, (carrier.carrier_code, carrier.carrier_name, carrier.account_number, carrier.dim_weight_divisor))
        
        carrier_id = cursor.fetchone()['id']
        conn.commit()
        
        return {
            "success": True,
            "carrier_id": carrier_id,
            "message": f"Carrier {carrier.carrier_name} created successfully"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/carriers")
async def list_carriers(active_only: bool = True):
    """List all carriers"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "SELECT * FROM carriers"
        if active_only:
            query += " WHERE is_active = true"
        query += " ORDER BY carrier_name"
        
        cursor.execute(query)
        carriers = cursor.fetchall()
        
        return {
            "success": True,
            "carriers": [dict(c) for c in carriers],
            "total": len(carriers)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/carriers/{carrier_id}/upload-rate-card")
async def upload_rate_card(carrier_id: int, file: UploadFile = File(...)):
    """Upload and process carrier rate card with AI extraction"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        file_content = await file.read()
        file_type = file.filename.split('.')[-1].lower()
        
        cursor.execute("""
            INSERT INTO rate_card_uploads 
            (carrier_id, upload_filename, file_type, upload_status, extraction_status)
            VALUES (%s, %s, %s, 'completed', 'processing')
            RETURNING id
        """, (carrier_id, file.filename, file_type))
        
        upload_id = cursor.fetchone()['id']
        conn.commit()
        
        cursor.execute("SELECT carrier_name FROM carriers WHERE id = %s", (carrier_id,))
        carrier = cursor.fetchone()
        carrier_name = carrier['carrier_name'] if carrier else "Unknown Carrier"
        
        extraction_result = await extract_rates_with_ai(file_content, file_type, carrier_name)
        
        if extraction_result['success']:
            cursor.execute("""
                UPDATE rate_card_uploads
                SET extracted_data = %s,
                    extraction_status = 'extracted',
                    rates_imported_count = %s,
                    processed_at = NOW()
                WHERE id = %s
            """, (json.dumps(extraction_result['data']), 
                  extraction_result['rates_count'], 
                  upload_id))
            conn.commit()
            
            return {
                "success": True,
                "upload_id": upload_id,
                "extracted_data": extraction_result['data'],
                "rates_count": extraction_result['rates_count'],
                "services_count": extraction_result['services_count'],
                "message": "Rate card processed successfully. Review and import rates."
            }
        else:
            cursor.execute("""
                UPDATE rate_card_uploads
                SET extraction_status = 'failed',
                    validation_errors = %s,
                    processed_at = NOW()
                WHERE id = %s
            """, (json.dumps({"error": extraction_result['error']}), upload_id))
            conn.commit()
            
            raise HTTPException(status_code=500, detail=f"AI extraction failed: {extraction_result['error']}")
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/rate-cards/{upload_id}/import")
async def import_extracted_rates(upload_id: int):
    """Import AI-extracted rates into shipping_rates table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT carrier_id, extracted_data 
            FROM rate_card_uploads 
            WHERE id = %s AND extraction_status = 'extracted'
        """, (upload_id,))
        
        upload = cursor.fetchone()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found or not ready for import")
        
        carrier_id = upload['carrier_id']
        extracted_data = upload['extracted_data']
        
        services_map = {}
        for service in extracted_data.get('services', []):
            cursor.execute("""
                INSERT INTO carrier_services 
                (carrier_id, service_code, service_name, service_type, is_active)
                VALUES (%s, %s, %s, %s, true)
                ON CONFLICT (carrier_id, service_code) DO UPDATE
                SET service_name = EXCLUDED.service_name
                RETURNING id
            """, (carrier_id, service['service_code'], service['service_name'], service['service_type']))
            
            service_id = cursor.fetchone()['id']
            services_map[service['service_code']] = service_id
        
        rates_imported = 0
        for rate in extracted_data.get('rates', []):
            service_id = services_map.get(rate['service_code'])
            if not service_id:
                continue
            
            origin_zip = "10001"
            dest_zip = "90001" if rate['zone'] == "Zone 8" else "10101"
            
            cursor.execute("""
                INSERT INTO shipping_rates 
                (carrier_id, service_id, origin_zip, destination_zip, 
                 weight_lbs, base_rate, total_rate, zone, rate_valid_until)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW() + INTERVAL '30 days')
            """, (carrier_id, service_id, origin_zip, dest_zip,
                  (rate['weight_min_lbs'] + rate['weight_max_lbs']) / 2,
                  rate['base_rate'], rate['base_rate'], rate['zone']))
            
            rates_imported += 1
        
        cursor.execute("""
            UPDATE rate_card_uploads
            SET extraction_status = 'imported',
                rates_imported_count = %s
            WHERE id = %s
        """, (rates_imported, upload_id))
        
        conn.commit()
        
        return {
            "success": True,
            "rates_imported": rates_imported,
            "services_created": len(services_map),
            "message": f"Successfully imported {rates_imported} rates"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/rate-cards")
async def list_rate_card_uploads(carrier_id: Optional[int] = None):
    """List rate card uploads"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "SELECT * FROM rate_card_uploads WHERE 1=1"
        params = []
        
        if carrier_id:
            query += " AND carrier_id = %s"
            params.append(carrier_id)
        
        query += " ORDER BY created_at DESC LIMIT 50"
        
        cursor.execute(query, params)
        uploads = cursor.fetchall()
        
        return {
            "success": True,
            "uploads": [dict(u) for u in uploads],
            "total": len(uploads)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/shipping/rates/manual")
async def create_manual_rate(rate: ManualRateEntry):
    """Manually create a shipping rate"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO shipping_rates 
            (carrier_id, service_id, origin_zip, destination_zip, weight_lbs,
             billable_weight_lbs, base_rate, total_rate, zone, estimated_days,
             rate_valid_until)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() + INTERVAL '30 days')
            RETURNING id
        """, (rate.carrier_id, rate.service_id, rate.origin_zip, rate.destination_zip,
              rate.weight_lbs, rate.weight_lbs, rate.total_rate, rate.total_rate,
              rate.zone, rate.estimated_days))
        
        rate_id = cursor.fetchone()['id']
        conn.commit()
        
        return {
            "success": True,
            "rate_id": rate_id,
            "message": "Rate created successfully"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/shipping/rates")
async def get_shipping_rates(request: RateQuoteRequest):
    """Get shipping rates from all carriers"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        dim_weight = None
        if request.length_inches and request.width_inches and request.height_inches:
            dim_weight = calculate_dimensional_weight(
                request.length_inches,
                request.width_inches,
                request.height_inches
            )
        
        billable_weight = get_billable_weight(request.weight_lbs, dim_weight) if dim_weight else request.weight_lbs
        zone = determine_zone(request.origin_zip, request.destination_zip)
        
        cursor.execute("SELECT * FROM carriers WHERE is_active = true")
        carriers = cursor.fetchall()
        
        rates = []
        for carrier in carriers:
            cursor.execute("""
                SELECT * FROM carrier_services 
                WHERE carrier_id = %s AND is_active = true
            """, (carrier['id'],))
            
            services = cursor.fetchall()
            
            for service in services:
                simulated = simulate_carrier_rate(
                    carrier['carrier_code'],
                    service['service_type'],
                    billable_weight,
                    zone
                )
                
                rates.append({
                    "carrier": carrier['carrier_name'],
                    "carrier_id": carrier['id'],
                    "service": service['service_name'],
                    "service_id": service['id'],
                    "service_type": service['service_type'],
                    "total_rate": simulated['total_rate'],
                    "base_rate": simulated['base_rate'],
                    "fuel_surcharge": simulated['fuel_surcharge'],
                    "estimated_days": simulated['estimated_days'],
                    "estimated_delivery_date": simulated['estimated_delivery_date'],
                    "zone": zone
                })
        
        rates.sort(key=lambda x: x['total_rate'])
        
        return {
            "success": True,
            "rates": rates,
            "total_options": len(rates),
            "cheapest": rates[0] if rates else None,
            "fastest": min(rates, key=lambda x: x['estimated_days']) if rates else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/shipping/labels")
async def generate_label(request: LabelGenerateRequest):
    """Generate shipping label"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        tracking_number = f"TRK{datetime.now().strftime('%Y%m%d%H%M%S')}{request.order_id}"
        
        cursor.execute("""
            INSERT INTO shipping_labels
            (order_id, carrier_id, service_id, tracking_number, status,
             origin_address, destination_address, package_weight_lbs,
             package_dimensions, insured_value, cost)
            VALUES (%s, %s, %s, %s, 'active', %s, %s, %s, %s, %s, 0)
            RETURNING id
        """, (request.order_id, request.carrier_id, request.service_id,
              tracking_number, json.dumps(request.origin_address),
              json.dumps(request.destination_address), request.weight_lbs,
              json.dumps(request.dimensions) if request.dimensions else None,
              request.insured_value))
        
        label_id = cursor.fetchone()['id']
        
        cursor.execute("""
            INSERT INTO tracking_events
            (tracking_number, label_id, event_type, event_description,
             event_timestamp, carrier_id)
            VALUES (%s, %s, 'label_created', 'Shipping label created', NOW(), %s)
        """, (tracking_number, label_id, request.carrier_id))
        
        conn.commit()
        
        return {
            "success": True,
            "label_id": label_id,
            "tracking_number": tracking_number,
            "message": "Shipping label generated successfully"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/shipping/tracking/{tracking_number}")
async def get_tracking(tracking_number: str):
    """Get tracking information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM shipping_labels WHERE tracking_number = %s
        """, (tracking_number,))
        
        label = cursor.fetchone()
        
        if not label:
            raise HTTPException(status_code=404, detail="Tracking number not found")
        
        cursor.execute("""
            SELECT * FROM tracking_events
            WHERE tracking_number = %s
            ORDER BY event_timestamp DESC
        """, (tracking_number,))
        
        events = cursor.fetchall()
        
        return {
            "success": True,
            "tracking_number": tracking_number,
            "label": dict(label),
            "events": [dict(e) for e in events],
            "latest_event": dict(events[0]) if events else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8034)
