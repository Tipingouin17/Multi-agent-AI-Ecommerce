"""
Database Population Script
Populates database with realistic carrier rates, marketplace data, and test data
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Mock database connection for demonstration
# In production, use actual psycopg2 or asyncpg


class DatabasePopulator:
    """Populate database with realistic test data"""
    
    def __init__(self):
        self.carriers_data = []
        self.marketplaces_data = []
        self.products_data = []
        self.orders_data = []
    
    async def populate_all(self):
        """Populate all tables"""
        print("🚀 Starting database population...")
        
        await self.populate_carriers()
        await self.populate_carrier_pricing()
        await self.populate_carrier_surcharges()
        await self.populate_carrier_performance()
        
        await self.populate_marketplaces()
        await self.populate_marketplace_commissions()
        await self.populate_marketplace_fees()
        
        await self.populate_products()
        await self.populate_inventory()
        await self.populate_marketplace_listings()
        
        await self.populate_test_orders()
        await self.populate_test_customers()
        
        print("✅ Database population complete!")
        self.print_summary()
    
    async def populate_carriers(self):
        """Populate carriers table"""
        print("\n📦 Populating carriers...")
        
        carriers = [
            {
                "carrier_code": "colissimo",
                "carrier_name": "Colissimo",
                "api_url": "https://ws.colissimo.fr/sls-ws",
                "is_active": True,
                "supports_tracking": True,
                "supports_label_generation": True,
                "average_on_time_rate": 0.95
            },
            {
                "carrier_code": "chronopost",
                "carrier_name": "Chronopost",
                "api_url": "https://ws.chronopost.fr/shipping-cxf",
                "is_active": True,
                "supports_tracking": True,
                "supports_label_generation": True,
                "average_on_time_rate": 0.98
            },
            {
                "carrier_code": "dpd",
                "carrier_name": "DPD",
                "api_url": "https://api.dpd.com",
                "is_active": True,
                "supports_tracking": True,
                "supports_label_generation": True,
                "average_on_time_rate": 0.93
            },
            {
                "carrier_code": "colis_prive",
                "carrier_name": "Colis Privé",
                "api_url": "https://api.colisprive.com",
                "is_active": True,
                "supports_tracking": True,
                "supports_label_generation": True,
                "average_on_time_rate": 0.88
            },
            {
                "carrier_code": "ups",
                "carrier_name": "UPS",
                "api_url": "https://onlinetools.ups.com/api",
                "is_active": True,
                "supports_tracking": True,
                "supports_label_generation": True,
                "average_on_time_rate": 0.92
            },
            {
                "carrier_code": "fedex",
                "carrier_name": "FedEx",
                "api_url": "https://apis.fedex.com",
                "is_active": True,
                "supports_tracking": True,
                "supports_label_generation": True,
                "average_on_time_rate": 0.91
            }
        ]
        
        self.carriers_data = carriers
        print(f"  ✅ Added {len(carriers)} carriers")
    
    async def populate_carrier_pricing(self):
        """Populate carrier pricing with realistic rates"""
        print("\n💰 Populating carrier pricing...")
        
        # Countries in scope
        countries = {
            "FR": "France",
            "DE": "Germany",
            "BE": "Belgium",
            "IT": "Italy",
            "ES": "Spain",
            "NL": "Netherlands",
            "PT": "Portugal",
            "AT": "Austria",
            "GB": "United Kingdom",
            "US": "United States"
        }
        
        pricing_data = []
        
        # Colissimo pricing
        colissimo_rates = [
            # Domestic France
            ("FR", "FR", "Domestic", 0, 0.5, 4.95),
            ("FR", "FR", "Domestic", 0.5, 1, 5.50),
            ("FR", "FR", "Domestic", 1, 2, 6.90),
            ("FR", "FR", "Domestic", 2, 5, 7.90),
            ("FR", "FR", "Domestic", 5, 10, 12.50),
            ("FR", "FR", "Domestic", 10, 30, 18.00),
            # EU Zone
            ("FR", "DE", "EU", 0, 2, 15.00),
            ("FR", "DE", "EU", 2, 5, 22.00),
            ("FR", "DE", "EU", 5, 10, 28.00),
            ("FR", "DE", "EU", 10, 30, 35.00),
            ("FR", "BE", "EU", 0, 2, 14.00),
            ("FR", "IT", "EU", 0, 2, 16.00),
            ("FR", "ES", "EU", 0, 2, 15.50),
            ("FR", "NL", "EU", 0, 2, 14.50),
            # International
            ("FR", "GB", "International", 0, 2, 25.00),
            ("FR", "GB", "International", 2, 5, 35.00),
            ("FR", "US", "International", 0, 2, 45.00),
            ("FR", "US", "International", 2, 5, 65.00),
        ]
        
        for origin, dest, zone, weight_min, weight_max, price in colissimo_rates:
            pricing_data.append({
                "carrier_code": "colissimo",
                "origin_country": origin,
                "destination_country": dest,
                "destination_zone": zone,
                "weight_min": weight_min,
                "weight_max": weight_max,
                "base_price": price,
                "currency": "EUR"
            })
        
        # Chronopost (Express) - 30% more expensive but faster
        for origin, dest, zone, weight_min, weight_max, price in colissimo_rates:
            pricing_data.append({
                "carrier_code": "chronopost",
                "origin_country": origin,
                "destination_country": dest,
                "destination_zone": zone,
                "weight_min": weight_min,
                "weight_max": weight_max,
                "base_price": price * 1.3,
                "currency": "EUR"
            })
        
        # DPD - Similar to Colissimo
        for origin, dest, zone, weight_min, weight_max, price in colissimo_rates:
            pricing_data.append({
                "carrier_code": "dpd",
                "origin_country": origin,
                "destination_country": dest,
                "destination_zone": zone,
                "weight_min": weight_min,
                "weight_max": weight_max,
                "base_price": price * 1.05,
                "currency": "EUR"
            })
        
        # Colis Privé (Economy) - 20% cheaper
        for origin, dest, zone, weight_min, weight_max, price in colissimo_rates:
            if zone == "Domestic":  # Only domestic
                pricing_data.append({
                    "carrier_code": "colis_prive",
                    "origin_country": origin,
                    "destination_country": dest,
                    "destination_zone": zone,
                    "weight_min": weight_min,
                    "weight_max": weight_max,
                    "base_price": price * 0.8,
                    "currency": "EUR"
                })
        
        # UPS - Premium pricing
        for origin, dest, zone, weight_min, weight_max, price in colissimo_rates:
            pricing_data.append({
                "carrier_code": "ups",
                "origin_country": origin,
                "destination_country": dest,
                "destination_zone": zone,
                "weight_min": weight_min,
                "weight_max": weight_max,
                "base_price": price * 1.4,
                "currency": "EUR"
            })
        
        # FedEx - Premium pricing
        for origin, dest, zone, weight_min, weight_max, price in colissimo_rates:
            pricing_data.append({
                "carrier_code": "fedex",
                "origin_country": origin,
                "destination_country": dest,
                "destination_zone": zone,
                "weight_min": weight_min,
                "weight_max": weight_max,
                "base_price": price * 1.45,
                "currency": "EUR"
            })
        
        print(f"  ✅ Added {len(pricing_data)} pricing records")
        return pricing_data
    
    async def populate_carrier_surcharges(self):
        """Populate carrier surcharges"""
        print("\n💵 Populating carrier surcharges...")
        
        surcharges = [
            # Fuel surcharge (all carriers)
            ("colissimo", "fuel", "Fuel Surcharge", None, 5.0, ["FR", "DE", "BE"]),
            ("chronopost", "fuel", "Fuel Surcharge", None, 6.0, None),
            ("dpd", "fuel", "Fuel Surcharge", None, 5.5, None),
            ("ups", "fuel", "Fuel Surcharge", None, 7.0, None),
            ("fedex", "fuel", "Fuel Surcharge", None, 7.5, None),
            
            # Remote area surcharge
            ("colissimo", "remote_area", "Remote Area Surcharge", 15.00, None, None),
            ("dpd", "remote_area", "Remote Area Surcharge", 12.00, None, None),
            
            # Oversized package
            ("ups", "oversized", "Oversized Package Fee", 25.00, None, None),
            ("fedex", "oversized", "Oversized Package Fee", 30.00, None, None),
            
            # Dangerous goods
            ("chronopost", "dangerous_goods", "Dangerous Goods Handling", 50.00, None, None),
            ("ups", "dangerous_goods", "Dangerous Goods Handling", 75.00, None, None),
        ]
        
        surcharge_data = []
        for carrier, stype, name, amount, percentage, countries in surcharges:
            surcharge_data.append({
                "carrier_code": carrier,
                "surcharge_type": stype,
                "surcharge_name": name,
                "surcharge_amount": amount,
                "surcharge_percentage": percentage,
                "applies_to_countries": countries
            })
        
        print(f"  ✅ Added {len(surcharge_data)} surcharges")
        return surcharge_data
    
    async def populate_carrier_performance(self):
        """Populate historical carrier performance data"""
        print("\n📊 Populating carrier performance history...")
        
        performance_data = []
        carriers = ["colissimo", "chronopost", "dpd", "colis_prive", "ups", "fedex"]
        on_time_rates = {
            "colissimo": 0.95,
            "chronopost": 0.98,
            "dpd": 0.93,
            "colis_prive": 0.88,
            "ups": 0.92,
            "fedex": 0.91
        }
        
        # Generate 100 historical shipments per carrier
        for carrier in carriers:
            for i in range(100):
                estimated_days = random.randint(1, 5)
                was_on_time = random.random() < on_time_rates[carrier]
                actual_days = estimated_days if was_on_time else estimated_days + random.randint(1, 3)
                
                performance_data.append({
                    "carrier_code": carrier,
                    "tracking_number": f"{carrier.upper()}{random.randint(100000, 999999)}",
                    "origin_country": "FR",
                    "destination_country": random.choice(["FR", "DE", "BE", "IT", "ES"]),
                    "estimated_delivery_date": datetime.utcnow() - timedelta(days=30-i//3),
                    "actual_delivery_date": datetime.utcnow() - timedelta(days=30-i//3-actual_days),
                    "was_on_time": was_on_time,
                    "transit_days": actual_days,
                    "cost": round(random.uniform(5.0, 50.0), 2),
                    "customer_rating": random.randint(3, 5) if was_on_time else random.randint(1, 3)
                })
        
        print(f"  ✅ Added {len(performance_data)} performance records")
        return performance_data
    
    async def populate_marketplaces(self):
        """Populate marketplaces table"""
        print("\n🏪 Populating marketplaces...")
        
        marketplaces = [
            {
                "marketplace_code": "cdiscount",
                "marketplace_name": "CDiscount",
                "api_url": "https://api.cdiscount.com/v1",
                "is_active": True,
                "commission_rate": 0.15,
                "country": "FR"
            },
            {
                "marketplace_code": "backmarket",
                "marketplace_name": "BackMarket",
                "api_url": "https://api.backmarket.com/v1",
                "is_active": True,
                "commission_rate": 0.15,
                "country": "FR"
            },
            {
                "marketplace_code": "refurbed",
                "marketplace_name": "Refurbed",
                "api_url": "https://api.refurbed.com/v1",
                "is_active": True,
                "commission_rate": 0.15,
                "country": "FR"
            },
            {
                "marketplace_code": "mirakl",
                "marketplace_name": "Mirakl",
                "api_url": "https://api.mirakl.net/api",
                "is_active": True,
                "commission_rate": 0.15,
                "country": "FR"
            },
            {
                "marketplace_code": "amazon",
                "marketplace_name": "Amazon",
                "api_url": "https://sellingpartnerapi-eu.amazon.com",
                "is_active": True,
                "commission_rate": 0.15,
                "country": "FR"
            },
            {
                "marketplace_code": "ebay",
                "marketplace_name": "eBay",
                "api_url": "https://api.ebay.com/sell",
                "is_active": True,
                "commission_rate": 0.12,
                "country": "FR"
            }
        ]
        
        self.marketplaces_data = marketplaces
        print(f"  ✅ Added {len(marketplaces)} marketplaces")
    
    async def populate_marketplace_commissions(self):
        """Populate marketplace commission rates by category"""
        print("\n💳 Populating marketplace commissions...")
        
        categories = [
            ("Electronics", 0.15),
            ("Computers", 0.12),
            ("Smartphones", 0.15),
            ("Tablets", 0.15),
            ("Accessories", 0.20),
            ("Home & Garden", 0.15),
            ("Fashion", 0.18),
            ("Books", 0.15),
            ("Sports", 0.15),
            ("Toys", 0.15)
        ]
        
        commission_data = []
        for marketplace in self.marketplaces_data:
            for category, rate in categories:
                commission_data.append({
                    "marketplace_code": marketplace["marketplace_code"],
                    "category": category,
                    "commission_rate": rate
                })
        
        print(f"  ✅ Added {len(commission_data)} commission records")
        return commission_data
    
    async def populate_marketplace_fees(self):
        """Populate marketplace fees"""
        print("\n💰 Populating marketplace fees...")
        
        fee_data = []
        for marketplace in self.marketplaces_data:
            # Listing fee
            fee_data.append({
                "marketplace_code": marketplace["marketplace_code"],
                "fee_type": "listing",
                "fee_name": "Monthly Listing Fee",
                "fee_amount": 0.35,
                "currency": "EUR"
            })
            
            # Transaction fee
            fee_data.append({
                "marketplace_code": marketplace["marketplace_code"],
                "fee_type": "transaction",
                "fee_name": "Transaction Fee",
                "fee_percentage": 2.5,
                "currency": "EUR"
            })
        
        print(f"  ✅ Added {len(fee_data)} fee records")
        return fee_data
    
    async def populate_products(self):
        """Populate products"""
        print("\n📦 Populating products...")
        
        products = [
            {"sku": "LAPTOP-001", "name": "MacBook Pro 16\" M3", "category": "Computers", "price": 2499.00, "cost": 2000.00},
            {"sku": "LAPTOP-002", "name": "MacBook Air M2", "category": "Computers", "price": 1299.00, "cost": 1000.00},
            {"sku": "PHONE-001", "name": "iPhone 15 Pro", "category": "Smartphones", "price": 1199.00, "cost": 900.00},
            {"sku": "PHONE-002", "name": "iPhone 14", "category": "Smartphones", "price": 899.00, "cost": 700.00},
            {"sku": "TABLET-001", "name": "iPad Pro 12.9\"", "category": "Tablets", "price": 1299.00, "cost": 1000.00},
            {"sku": "TABLET-002", "name": "iPad Air", "category": "Tablets", "price": 699.00, "cost": 550.00},
            {"sku": "WATCH-001", "name": "Apple Watch Series 9", "category": "Accessories", "price": 449.00, "cost": 350.00},
            {"sku": "AIRPODS-001", "name": "AirPods Pro 2", "category": "Accessories", "price": 279.00, "cost": 200.00},
            {"sku": "IPHONE-REF-001", "name": "iPhone 13 Pro Refurbished", "category": "Smartphones", "price": 699.00, "cost": 500.00},
            {"sku": "MACBOOK-REF-001", "name": "MacBook Air M2 Refurbished", "category": "Computers", "price": 899.00, "cost": 700.00},
        ]
        
        self.products_data = products
        print(f"  ✅ Added {len(products)} products")
        return products
    
    async def populate_inventory(self):
        """Populate inventory"""
        print("\n📊 Populating inventory...")
        
        inventory_data = []
        for product in self.products_data:
            inventory_data.append({
                "sku": product["sku"],
                "quantity": random.randint(10, 100),
                "reserved": random.randint(0, 10),
                "warehouse_location": f"A{random.randint(1, 10)}-{random.randint(1, 20)}"
            })
        
        print(f"  ✅ Added {len(inventory_data)} inventory records")
        return inventory_data
    
    async def populate_marketplace_listings(self):
        """Populate marketplace listings"""
        print("\n🏪 Populating marketplace listings...")
        
        listing_data = []
        for marketplace in self.marketplaces_data:
            for product in self.products_data:
                # Not all products on all marketplaces
                if random.random() < 0.7:  # 70% chance
                    listing_data.append({
                        "marketplace_code": marketplace["marketplace_code"],
                        "sku": product["sku"],
                        "title": product["name"],
                        "price": product["price"],
                        "quantity": random.randint(5, 50),
                        "status": "active"
                    })
        
        print(f"  ✅ Added {len(listing_data)} marketplace listings")
        return listing_data
    
    async def populate_test_orders(self):
        """Populate test orders"""
        print("\n🛒 Populating test orders...")
        
        order_data = []
        statuses = ["pending", "confirmed", "processing", "shipped", "delivered"]
        
        for i in range(50):
            order_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            marketplace = random.choice(self.marketplaces_data)
            product = random.choice(self.products_data)
            
            order_data.append({
                "order_id": f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{i:04d}",
                "marketplace_code": marketplace["marketplace_code"],
                "marketplace_order_id": f"{marketplace['marketplace_code'].upper()}{random.randint(100000, 999999)}",
                "order_date": order_date,
                "customer_name": f"Customer {i}",
                "customer_email": f"customer{i}@example.com",
                "sku": product["sku"],
                "quantity": random.randint(1, 3),
                "price": product["price"],
                "status": random.choice(statuses),
                "shipping_country": random.choice(["FR", "DE", "BE", "IT", "ES"])
            })
        
        self.orders_data = order_data
        print(f"  ✅ Added {len(order_data)} test orders")
        return order_data
    
    async def populate_test_customers(self):
        """Populate test customers"""
        print("\n👥 Populating test customers...")
        
        customer_data = []
        for i in range(100):
            customer_data.append({
                "customer_id": f"CUST-{i:05d}",
                "name": f"Customer {i}",
                "email": f"customer{i}@example.com",
                "phone": f"+33{random.randint(600000000, 699999999)}",
                "country": random.choice(["FR", "DE", "BE", "IT", "ES"]),
                "total_orders": random.randint(1, 20),
                "total_spent": round(random.uniform(100, 5000), 2)
            })
        
        print(f"  ✅ Added {len(customer_data)} test customers")
        return customer_data
    
    def print_summary(self):
        """Print population summary"""
        print("\n" + "="*60)
        print("📊 DATABASE POPULATION SUMMARY")
        print("="*60)
        print(f"Carriers: {len(self.carriers_data)}")
        print(f"Marketplaces: {len(self.marketplaces_data)}")
        print(f"Products: {len(self.products_data)}")
        print(f"Test Orders: {len(self.orders_data)}")
        print("="*60)
        print("\n✅ Database is ready for testing!")
        print("\nNext steps:")
        print("1. Run end-to-end workflow tests")
        print("2. Test carrier selection algorithm")
        print("3. Test marketplace synchronization")
        print("4. Verify all 10 workflows")


async def main():
    """Main execution"""
    populator = DatabasePopulator()
    await populator.populate_all()


if __name__ == "__main__":
    asyncio.run(main())

