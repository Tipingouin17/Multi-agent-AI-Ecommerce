"""
Order Agent V3 - Production Ready with New Schema
Manages orders using the unified database schema
"""

import os
import sys
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import shared modules
from shared.db_models import Order, OrderItem, Customer, Product, User, Address, Inventory
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Order Agent V3", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class OrderCreate(BaseModel):
    customer_id: int
    merchant_id: Optional[int] = None
    items: List[OrderItemCreate]
    shipping_address_id: int
    billing_address_id: Optional[int] = None
    notes: Optional[str] = None
    customer_notes: Optional[str] = None

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    notes: Optional[str] = None

# ============================================================================
# ORDER ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "order_agent_v3", "version": "3.0.0"}

@app.get("/api/orders")
def get_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    merchant_id: Optional[int] = None,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    fulfillment_status: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|total|order_number)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    Get all orders with filtering, pagination, and sorting
    """
    try:
        # Build query
        query = db.query(Order)
        
        # Apply filters
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        
        if merchant_id:
            query = query.filter(Order.merchant_id == merchant_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        if payment_status:
            query = query.filter(Order.payment_status == payment_status)
        
        if fulfillment_status:
            query = query.filter(Order.fulfillment_status == fulfillment_status)
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(Order, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * limit
        orders = query.offset(offset).limit(limit).all()
        
        # Build response with related data
        order_list = []
        for order in orders:
            order_dict = order.to_dict()
            
            # Add customer info
            if order.customer:
                customer = order.customer
                if customer.user:
                    order_dict['customer'] = {
                        'id': customer.id,
                        'name': f"{customer.user.first_name} {customer.user.last_name}",
                        'email': customer.user.email
                    }
            
            # Add items count
            order_dict['items_count'] = len(order.order_items)
            
            order_list.append(order_dict)
        
        return {
            "orders": order_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a single order by ID with full details"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order_dict = order.to_dict()
        
        # Add customer information
        if order.customer and order.customer.user:
            user = order.customer.user
            order_dict['customer'] = {
                'id': order.customer.id,
                'user_id': user.id,
                'name': f"{user.first_name} {user.last_name}",
                'email': user.email,
                'phone': user.phone
            }
        
        # Add order items with product details
        items = []
        for item in order.order_items:
            item_dict = item.to_dict()
            if item.product:
                item_dict['product'] = {
                    'id': item.product.id,
                    'name': item.product.name,
                    'sku': item.product.sku,
                    'images': item.product.images
                }
            items.append(item_dict)
        order_dict['items'] = items
        
        # Add shipping address
        if order.shipping_address_id:
            shipping_addr = db.query(Address).filter(
                Address.id == order.shipping_address_id
            ).first()
            if shipping_addr:
                order_dict['shipping_address'] = shipping_addr.to_dict()
        
        # Add billing address
        if order.billing_address_id:
            billing_addr = db.query(Address).filter(
                Address.id == order.billing_address_id
            ).first()
            if billing_addr:
                order_dict['billing_address'] = billing_addr.to_dict()
        
        return order_dict
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orders")
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order"""
    try:
        # Verify customer exists
        customer = db.query(Customer).filter(Customer.id == order_data.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Calculate order totals
        subtotal = Decimal('0.00')
        items_data = []
        
        for item in order_data.items:
            # Verify product exists
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            
            # Check inventory availability
            total_available = db.query(func.sum(Inventory.quantity)).filter(
                Inventory.product_id == item.product_id
            ).scalar() or 0
            
            if total_available < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient inventory for product {product.name}. Available: {total_available}, Requested: {item.quantity}"
                )
            
            unit_price = Decimal(str(item.unit_price))
            quantity = item.quantity
            total_price = unit_price * quantity
            subtotal += total_price
            
            items_data.append({
                'product_id': item.product_id,
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price
            })
        
        # Calculate tax and total (simplified - 10% tax)
        tax = subtotal * Decimal('0.10')
        shipping_cost = Decimal('10.00')  # Flat shipping
        total = subtotal + tax + shipping_cost
        
        # Generate order number
        order_count = db.query(func.count(Order.id)).scalar()
        order_number = f"ORD-{order_count + 1:06d}"
        
        # Create order
        order = Order(
            order_number=order_number,
            customer_id=order_data.customer_id,
            merchant_id=order_data.merchant_id,
            status="pending",
            payment_status="pending",
            fulfillment_status="unfulfilled",
            subtotal=subtotal,
            tax=tax,
            shipping_cost=shipping_cost,
            total=total,
            shipping_address_id=order_data.shipping_address_id,
            billing_address_id=order_data.billing_address_id or order_data.shipping_address_id,
            notes=order_data.notes,
            customer_notes=order_data.customer_notes
        )
        
        db.add(order)
        db.flush()  # Get order ID
        
        # Create order items and reserve inventory
        for item_data in items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                sku=item_data['product'].sku,
                name=item_data['product'].name,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
            db.add(order_item)
            
            # Deduct inventory (FIFO - deduct from warehouses with stock)
            remaining_qty = item_data['quantity']
            inventory_items = db.query(Inventory).filter(
                and_(
                    Inventory.product_id == item_data['product_id'],
                    Inventory.quantity > 0
                )
            ).order_by(Inventory.quantity.desc()).all()
            
            for inv_item in inventory_items:
                if remaining_qty <= 0:
                    break
                    
                deduct_qty = min(remaining_qty, inv_item.quantity)
                inv_item.quantity -= deduct_qty
                inv_item.reserved_quantity = (inv_item.reserved_quantity or 0) + deduct_qty
                inv_item.updated_at = datetime.utcnow()
                remaining_qty -= deduct_qty
                
                logger.info(f"Reserved {deduct_qty} units of product {item_data['product_id']} from warehouse {inv_item.warehouse_id}")
        
        db.commit()
        db.refresh(order)
        
        return order.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/orders/{order_id}")
def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db)
):
    """Update an order"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update fields
        update_data = order_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        
        # Update timestamps based on status changes
        if order_data.status == "confirmed" and not order.confirmed_at:
            order.confirmed_at = datetime.utcnow()
        elif order_data.fulfillment_status == "shipped" and not order.shipped_at:
            order.shipped_at = datetime.utcnow()
        elif order_data.fulfillment_status == "delivered" and not order.delivered_at:
            order.delivered_at = datetime.utcnow()
        elif order_data.status == "cancelled" and not order.cancelled_at:
            order.cancelled_at = datetime.utcnow()
        
        order.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(order)
        
        return order.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Update order status"""
    return update_order(order_id, OrderUpdate(status=status), db)

@app.post("/api/orders/{order_id}/cancel")
def cancel_order(
    order_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Cancel an order"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status == "cancelled":
            raise HTTPException(status_code=400, detail="Order already cancelled")
        
        if order.status in ["shipped", "delivered"]:
            raise HTTPException(status_code=400, detail="Cannot cancel shipped/delivered order")
        
        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()
        if reason:
            order.notes = f"Cancellation reason: {reason}\n{order.notes or ''}"
        
        db.commit()
        db.refresh(order)
        
        return order.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/stats")
def get_order_stats(
    time_range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    merchant_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get order statistics"""
    try:
        query = db.query(Order)
        
        if merchant_id:
            query = query.filter(Order.merchant_id == merchant_id)
        
        # Calculate statistics
        total_orders = query.count()
        total_revenue = db.query(func.sum(Order.total)).filter(
            Order.status != "cancelled"
        ).scalar() or 0
        
        pending_orders = query.filter(Order.status == "pending").count()
        confirmed_orders = query.filter(Order.status == "confirmed").count()
        shipped_orders = query.filter(Order.fulfillment_status == "shipped").count()
        delivered_orders = query.filter(Order.fulfillment_status == "delivered").count()
        cancelled_orders = query.filter(Order.status == "cancelled").count()
        
        avg_order_value = float(total_revenue) / total_orders if total_orders > 0 else 0
        
        return {
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "average_order_value": avg_order_value,
            "pending_orders": pending_orders,
            "confirmed_orders": confirmed_orders,
            "shipped_orders": shipped_orders,
            "delivered_orders": delivered_orders,
            "cancelled_orders": cancelled_orders
        }
    
    except Exception as e:
        logger.error(f"Error getting order stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/kpis")
def get_merchant_kpis(
    timeRange: str = Query("7d", regex="^(7d|30d|90d|1y)$"),
    merchant_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get merchant KPIs for dashboard"""
    try:
        from datetime import timedelta
        
        # Parse time range
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(timeRange, 7)
        start_date = datetime.now() - timedelta(days=days)
        
        # Build query
        query = db.query(Order).filter(Order.created_at >= start_date)
        if merchant_id:
            query = query.filter(Order.merchant_id == merchant_id)
        
        # Calculate current period metrics
        orders = query.all()
        total_orders = len(orders)
        
        # Calculate revenue (excluding cancelled orders)
        active_orders = [o for o in orders if o.status != "cancelled"]
        total_sales = sum(float(o.total or 0) for o in active_orders)
        
        # Calculate average order value
        average_order_value = total_sales / len(active_orders) if active_orders else 0
        
        # Calculate conversion rate (simplified - would need visit data for real calculation)
        conversion_rate = 3.45  # Mock value - would need analytics integration
        
        # Calculate growth (compare to previous period)
        prev_start_date = start_date - timedelta(days=days)
        prev_query = db.query(Order).filter(
            Order.created_at >= prev_start_date,
            Order.created_at < start_date
        )
        if merchant_id:
            prev_query = prev_query.filter(Order.merchant_id == merchant_id)
        
        prev_orders = prev_query.all()
        prev_active_orders = [o for o in prev_orders if o.status != "cancelled"]
        prev_total_sales = sum(float(o.total or 0) for o in prev_active_orders)
        prev_total_orders = len(prev_orders)
        
        # Calculate growth percentages
        sales_growth = ((total_sales - prev_total_sales) / prev_total_sales * 100) if prev_total_sales > 0 else 0
        orders_growth = ((total_orders - prev_total_orders) / prev_total_orders * 100) if prev_total_orders > 0 else 0
        
        return {
            "totalSales": round(total_sales, 2),
            "totalOrders": total_orders,
            "averageOrderValue": round(average_order_value, 2),
            "conversionRate": conversion_rate,
            "salesGrowth": round(sales_growth, 2),
            "ordersGrowth": round(orders_growth, 2)
        }
    
    except Exception as e:
        logger.error(f"Error getting merchant KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/recent")
def get_recent_orders_simple(
    limit: int = Query(10, ge=1, le=50),
    merchant_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get recent orders (simple path for frontend compatibility)"""
    try:
        query = db.query(Order).order_by(desc(Order.created_at))
        
        if merchant_id:
            query = query.filter(Order.merchant_id == merchant_id)
        
        orders = query.limit(limit).all()
        
        # Format for frontend
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                "id": f"ORD-{order.id}",
                "customer": order.customer.name if order.customer else "Unknown",
                "total": float(order.total or 0),
                "status": order.status,
                "created_at": order.created_at.isoformat() if order.created_at else None
            })
        
        return formatted_orders
    
    except Exception as e:
        logger.error(f"Error getting recent orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/recent")
def get_recent_orders(
    limit: int = Query(10, ge=1, le=50),
    merchant_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get recent orders"""
    try:
        query = db.query(Order).order_by(desc(Order.created_at))
        
        if merchant_id:
            query = query.filter(Order.merchant_id == merchant_id)
        
        orders = query.limit(limit).all()
        
        return {"orders": [order.to_dict() for order in orders]}
    
    except Exception as e:
        logger.error(f"Error getting recent orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SHOPPING CART ENDPOINTS
# ============================================================================

@app.get("/cart")
def get_cart(
    customer_id: Optional[int] = Query(None),
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get customer's shopping cart"""
    try:
        from shared.db_models import Cart, CartItem
        
        # Find or create cart
        cart = None
        if customer_id:
            cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        elif session_id:
            cart = db.query(Cart).filter(Cart.session_id == session_id).first()
        
        if not cart:
            # Return empty cart
            return {
                "items": [],
                "subtotal": 0,
                "tax": 0,
                "shipping": 10.00,
                "total": 10.00
            }
        
        # Calculate totals
        subtotal = sum(float(item.price) * item.quantity for item in cart.items)
        tax = subtotal * 0.10  # 10% tax
        shipping = 10.00 if subtotal > 0 else 0
        total = subtotal + tax + shipping
        
        return {
            "id": cart.id,
            "items": [item.to_dict() for item in cart.items],
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "shipping": shipping,
            "total": round(total, 2)
        }
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cart/add")
def add_to_cart(
    product_id: int,
    quantity: int = 1,
    customer_id: Optional[int] = None,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Add item to shopping cart"""
    try:
        from shared.db_models import Cart, CartItem
        
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Find or create cart
        cart = None
        if customer_id:
            cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
            if not cart:
                cart = Cart(customer_id=customer_id)
                db.add(cart)
                db.flush()
        elif session_id:
            cart = db.query(Cart).filter(Cart.session_id == session_id).first()
            if not cart:
                cart = Cart(session_id=session_id)
                db.add(cart)
                db.flush()
        else:
            raise HTTPException(status_code=400, detail="customer_id or session_id required")
        
        # Check if item already in cart
        existing_item = db.query(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        ).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += quantity
        else:
            # Add new item
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                price=product.price
            )
            db.add(cart_item)
        
        db.commit()
        return {"success": True, "message": "Item added to cart", "cart_id": cart.id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding to cart: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/cart/items/{item_id}")
def update_cart_item(
    item_id: int,
    quantity: int,
    db: Session = Depends(get_db)
):
    """Update cart item quantity"""
    try:
        from shared.db_models import CartItem
        
        cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        if quantity <= 0:
            # Remove item if quantity is 0 or negative
            db.delete(cart_item)
        else:
            cart_item.quantity = quantity
        
        db.commit()
        return {"success": True, "message": "Cart item updated"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating cart item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cart/items/{item_id}")
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    try:
        from shared.db_models import CartItem
        
        cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        db.delete(cart_item)
        db.commit()
        return {"success": True, "message": "Item removed from cart"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing cart item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cart/apply-coupon")
def apply_coupon(
    couponCode: str,
    cart_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Apply coupon code to cart"""
    try:
        from shared.db_models import Promotion
        
        # Find promotion by code
        promotion = db.query(Promotion).filter(
            Promotion.code == couponCode,
            Promotion.status == 'active'
        ).first()
        
        if not promotion:
            raise HTTPException(status_code=404, detail="Invalid coupon code")
        
        # Check if promotion is valid
        now = datetime.utcnow()
        if now < promotion.valid_from or now > promotion.valid_until:
            raise HTTPException(status_code=400, detail="Coupon has expired")
        
        if promotion.max_uses and promotion.uses_count >= promotion.max_uses:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")
        
        # Calculate discount
        discount = 0
        if promotion.discount_type == 'percentage':
            # Discount will be calculated on frontend based on cart total
            discount = float(promotion.discount_value)
        else:  # fixed
            discount = float(promotion.discount_value)
        
        return {
            "success": True,
            "message": "Coupon applied successfully",
            "discount": discount,
            "discount_type": promotion.discount_type,
            "promotion": promotion.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying coupon: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@app.post("/orders/export")
def export_orders(
    orderIds: List[int],
    db: Session = Depends(get_db)
):
    """Export orders to CSV"""
    try:
        orders = db.query(Order).filter(Order.id.in_(orderIds)).all()
        
        # Generate CSV data
        csv_lines = ["Order ID,Customer,Total,Status,Date"]
        for order in orders:
            customer_name = order.customer.name if order.customer else "Unknown"
            csv_lines.append(
                f"{order.id},{customer_name},{order.total},{order.status},{order.created_at}"
            )
        
        return "\n".join(csv_lines)
    except Exception as e:
        logger.error(f"Error exporting orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/orders/bulk-update-status")
def bulk_update_order_status(
    orderIds: List[int],
    status: str,
    db: Session = Depends(get_db)
):
    """Update status for multiple orders"""
    try:
        updated_count = db.query(Order).filter(
            Order.id.in_(orderIds)
        ).update(
            {"status": status, "updated_at": datetime.utcnow()},
            synchronize_session=False
        )
        
        db.commit()
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Updated {updated_count} orders to {status}"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error bulk updating orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/customer/orders")
def get_customer_orders(
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get orders for a specific customer"""
    try:
        if not customer_id:
            return {"orders": []}
        
        orders = db.query(Order).filter(
            Order.customer_id == customer_id
        ).order_by(desc(Order.created_at)).all()
        
        return {"orders": [order.to_dict() for order in orders]}
    except Exception as e:
        logger.error(f"Error getting customer orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
