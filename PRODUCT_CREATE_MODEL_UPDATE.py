# Updated ProductCreate model to replace lines 61-72 in product_agent_v3.py

class ProductCreate(BaseModel):
    # Basic Information (Step 1)
    merchant_id: int
    category_id: Optional[int] = None
    sku: str
    name: str
    display_name: Optional[str] = None
    brand: Optional[str] = None
    model_number: Optional[str] = None
    product_type: str = "simple"  # simple, variable, grouped, external
    description: Optional[str] = None
    short_description: Optional[str] = None
    key_features: Optional[List[str]] = []
    
    # Specifications (Step 2)
    dimensions_length: Optional[float] = None
    dimensions_width: Optional[float] = None
    dimensions_height: Optional[float] = None
    dimensions_unit: str = "cm"
    weight: Optional[float] = None
    weight_unit: str = "kg"
    material: Optional[str] = None
    color: Optional[str] = None
    warranty_period: Optional[int] = None  # in months
    country_of_origin: Optional[str] = None
    specifications: Optional[List[Dict[str, Any]]] = []  # [{name, value, unit, group}]
    
    # Visual Assets (Step 3)
    images: Optional[List[Dict[str, Any]]] = []  # [{url, alt_text, is_primary, display_order}]
    media: Optional[List[Dict[str, Any]]] = []  # [{type, url, caption}]
    
    # Pricing & Costs (Step 4)
    price: float
    cost: Optional[float] = None
    compare_at_price: Optional[float] = None
    currency: str = "USD"
    profit_margin: Optional[float] = None  # Auto-calculated
    pricing_tiers: Optional[List[Dict[str, Any]]] = []  # [{min_qty, max_qty, price}]
    tax_config: Optional[Dict[str, Any]] = None  # {tax_class, tax_rate, tax_region}
    
    # Inventory & Logistics (Step 5)
    warehouse_inventory: Optional[List[Dict[str, Any]]] = []  # [{warehouse_id, quantity, threshold}]
    shipping_weight: Optional[float] = None
    shipping_length: Optional[float] = None
    shipping_width: Optional[float] = None
    shipping_height: Optional[float] = None
    handling_time_days: int = 1
    requires_shipping: bool = True
    is_fragile: bool = False
    is_perishable: bool = False
    
    # Bundle & Kit Config (Step 6)
    is_bundle: bool = False
    bundle_components: Optional[List[Dict[str, Any]]] = []  # [{product_id, quantity, is_required}]
    bundle_type: Optional[str] = None  # fixed, flexible, custom
    bundle_pricing_strategy: Optional[str] = None  # fixed_price, percentage_discount
    
    # Marketplace & Compliance (Step 7)
    marketplace_listings: Optional[List[Dict[str, Any]]] = []  # [{marketplace, sku, category, price}]
    product_identifiers: Optional[List[Dict[str, Any]]] = []  # [{type, value}] - GTIN, UPC, EAN
    compliance_certifications: Optional[List[Dict[str, Any]]] = []  # [{type, number, expiry}]
    has_age_restriction: bool = False
    min_age: Optional[int] = None
    is_hazmat: bool = False
    hazmat_class: Optional[str] = None
    requires_signature: bool = False
    has_export_restrictions: bool = False
    export_restriction_countries: Optional[List[str]] = []
    safety_warnings: Optional[List[str]] = []
    
    # Review & Activation (Step 8)
    status: str = "draft"  # draft, active, inactive
    is_draft: bool = True
    scheduled_publish_at: Optional[datetime] = None
