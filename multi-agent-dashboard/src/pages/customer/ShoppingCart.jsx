import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Shopping Cart Page
 * 
 * Displays the user's shopping cart with product details,
 * quantity controls, and checkout options.
 */
function ShoppingCart() {
  const navigate = useNavigate();
  
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updating, setUpdating] = useState(false);
  const [couponCode, setCouponCode] = useState('');
  const [couponError, setCouponError] = useState(null);
  const [couponSuccess, setCouponSuccess] = useState(null);
  const [summary, setSummary] = useState({
    subtotal: 0,
    discount: 0,
    tax: 0,
    shipping: 0,
    total: 0
  });
  
  // Load cart data on component mount
  useEffect(() => {
    loadCartData();
  }, []);
  
  // Calculate summary whenever cart items change
  useEffect(() => {
    calculateSummary();
  }, [cartItems]);
  
  // Load cart data from API
  async function loadCartData() {
    try {
      setLoading(true);
      
      const data = await apiService.getCart();
      setCartItems(data.items || []);
      
      // If the API returns summary data, use it
      if (data.summary) {
        setSummary(data.summary);
      }
      
      setError(null);
    } catch (err) {
      setError("Failed to load cart: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Calculate cart summary
  function calculateSummary() {
    const subtotal = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const tax = subtotal * 0.08; // Assuming 8% tax rate
    const shipping = subtotal > 50 ? 0 : 5.99; // Free shipping over $50
    const discount = 0; // Will be updated when coupon is applied
    
    setSummary({
      subtotal,
      tax,
      shipping,
      discount,
      total: subtotal + tax + shipping - discount
    });
  }
  
  // Update item quantity
  async function updateItemQuantity(itemId, newQuantity) {
    if (newQuantity < 1) return;
    
    try {
      setUpdating(true);
      
      await apiService.updateCartItem(itemId, newQuantity);
      
      // Update local state
      setCartItems(cartItems.map(item => 
        item.id === itemId ? { ...item, quantity: newQuantity } : item
      ));
      
    } catch (err) {
      console.error("Failed to update quantity:", err);
      alert("Failed to update quantity: " + err.message);
    } finally {
      setUpdating(false);
    }
  }
  
  // Remove item from cart
  async function removeItem(itemId) {
    try {
      setUpdating(true);
      
      await apiService.removeCartItem(itemId);
      
      // Update local state
      setCartItems(cartItems.filter(item => item.id !== itemId));
      
    } catch (err) {
      console.error("Failed to remove item:", err);
      alert("Failed to remove item: " + err.message);
    } finally {
      setUpdating(false);
    }
  }
  
  // Apply coupon code
  async function applyCoupon(e) {
    e.preventDefault();
    
    if (!couponCode.trim()) return;
    
    try {
      setUpdating(true);
      setCouponError(null);
      setCouponSuccess(null);
      
      const result = await apiService.applyCoupon(couponCode);
      
      // Update summary with discount
      setSummary({
        ...summary,
        discount: result.discount,
        total: summary.subtotal + summary.tax + summary.shipping - result.discount
      });
      
      setCouponSuccess(`Coupon applied: ${result.message}`);
    } catch (err) {
      setCouponError(err.message || "Invalid coupon code");
      console.error("Failed to apply coupon:", err);
    } finally {
      setUpdating(false);
    }
  }
  
  // Proceed to checkout
  function proceedToCheckout() {
    navigate('/checkout');
  }
  
  // Render loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="md:col-span-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="bg-white p-4 rounded-lg shadow mb-4 flex">
                    <div className="h-24 w-24 bg-gray-200 rounded"></div>
                    <div className="ml-4 flex-1">
                      <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
                      <div className="h-8 bg-gray-200 rounded w-1/3"></div>
                    </div>
                  </div>
                ))}
              </div>
              <div>
                <div className="bg-white p-4 rounded-lg shadow">
                  <div className="h-6 bg-gray-200 rounded mb-4"></div>
                  <div className="space-y-2">
                    <div className="h-4 bg-gray-200 rounded"></div>
                    <div className="h-4 bg-gray-200 rounded"></div>
                    <div className="h-4 bg-gray-200 rounded"></div>
                    <div className="h-4 bg-gray-200 rounded"></div>
                  </div>
                  <div className="h-10 bg-gray-200 rounded mt-4"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  // Render empty cart
  if (cartItems.length === 0 && !error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Shopping Cart</h1>
          
          <div className="bg-white p-8 rounded-lg shadow text-center">
            <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path>
            </svg>
            <h2 className="mt-4 text-xl font-medium text-gray-900">Your cart is empty</h2>
            <p className="mt-2 text-gray-500">
              Looks like you haven't added any products to your cart yet.
            </p>
            <Link 
              to="/products" 
              className="mt-6 inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Start Shopping
            </Link>
          </div>
        </div>
      </div>
     );
  }
  
  // Render error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Shopping Cart</h1>
          
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-8">
            <p>{error}</p>
            <button 
              onClick={loadCartData} 
              className="mt-2 bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Shopping Cart</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Cart Items */}
          <div className="md:col-span-2">
            {cartItems.map(item => (
              <div key={item.id} className="bg-white p-4 rounded-lg shadow mb-4">
                <div className="flex flex-col sm:flex-row">
                  {/* Product Image */}
                  <div className="w-full sm:w-24 h-24 mb-4 sm:mb-0">
                    <img 
                      src={item.image_url} 
                      alt={item.name}
                      className="w-full h-full object-cover rounded"
                    />
                  </div>
                  
                  {/* Product Details */}
                  <div className="flex-1 sm:ml-4">
                    <div className="flex flex-col sm:flex-row sm:justify-between">
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">
                          <Link to={`/products/${item.product_id}`} className="hover:text-blue-600">
                            {item.name}
                          </Link>
                        </h3>
                        
                        {item.variant && (
                          <p className="text-sm text-gray-600 mt-1">
                            {Object.entries(item.variant).map(([key, value]) => (
                              <span key={key} className="mr-2">
                                {key}: {value}
                              </span>
                            ))}
                          </p>
                        )}
                        
                        <p className="text-lg font-bold text-gray-900 mt-2">
                          ${item.price.toFixed(2)}
                        </p>
                      </div>
                      
                      <div className="mt-4 sm:mt-0">
                        <div className="flex items-center">
                          <button
                            type="button"
                            onClick={() => updateItemQuantity(item.id, item.quantity - 1)}
                            disabled={updating || item.quantity <= 1}
                            className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-l-md disabled:opacity-50"
                          >
                            -
                          </button>
                          <input
                            type="number"
                            min="1"
                            value={item.quantity}
                            onChange={(e) => updateItemQuantity(item.id, parseInt(e.target.value))}
                            className="w-12 text-center border-t border-b border-gray-300 py-1"
                            disabled={updating}
                          />
                          <button
                            type="button"
                            onClick={() => updateItemQuantity(item.id, item.quantity + 1)}
                            disabled={updating}
                            className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-r-md disabled:opacity-50"
                          >
                            +
                          </button>
                        </div>
                        
                        <button
                          type="button"
                          onClick={() => removeItem(item.id)}
                          disabled={updating}
                          className="mt-2 text-sm text-red-600 hover:text-red-800 flex items-center"
                        >
                          <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                          </svg>
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
             ))}
            
            {/* Continue Shopping */}
            <div className="mt-6">
              <Link 
                to="/products" 
                className="text-blue-600 hover:text-blue-800 flex items-center"
              >
                <svg className="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                </svg>
                Continue Shopping
              </Link>
            </div>
          </div>
          
          {/* Order Summary */}
          <div>
            <div className="bg-white p-6 rounded-lg shadow sticky top-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Order Summary</h2>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="text-gray-900">${summary.subtotal.toFixed(2 )}</span>
                </div>
                
                {summary.discount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount</span>
                    <span>-${summary.discount.toFixed(2)}</span>
                  </div>
                )}
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Shipping</span>
                  <span className="text-gray-900">
                    {summary.shipping === 0 ? 'Free' : `$${summary.shipping.toFixed(2)}`}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Tax</span>
                  <span className="text-gray-900">${summary.tax.toFixed(2)}</span>
                </div>
                
                <div className="border-t border-gray-200 pt-3 mt-3">
                  <div className="flex justify-between font-medium">
                    <span className="text-gray-900">Total</span>
                    <span className="text-gray-900">${summary.total.toFixed(2)}</span>
                  </div>
                </div>
              </div>
              
              {/* Coupon Code */}
              <div className="mt-6">
                <form onSubmit={applyCoupon}>
                  <label htmlFor="coupon" className="block text-sm font-medium text-gray-700 mb-1">
                    Coupon Code
                  </label>
                  <div className="flex">
                    <input
                      type="text"
                      id="coupon"
                      value={couponCode}
                      onChange={(e) => setCouponCode(e.target.value)}
                      className="flex-1 border border-gray-300 rounded-l-lg py-2 px-3 text-sm focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter coupon code"
                    />
                    <button
                      type="submit"
                      disabled={updating || !couponCode.trim()}
                      className="bg-gray-100 hover:bg-gray-200 text-gray-800 py-2 px-4 rounded-r-lg disabled:opacity-50"
                    >
                      Apply
                    </button>
                  </div>
                  
                  {couponError && (
                    <p className="mt-1 text-sm text-red-600">{couponError}</p>
                  )}
                  
                  {couponSuccess && (
                    <p className="mt-1 text-sm text-green-600">{couponSuccess}</p>
                  )}
                </form>
              </div>
              
              {/* Checkout Button */}
              <button
                type="button"
                onClick={proceedToCheckout}
                className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-medium"
              >
                Proceed to Checkout
              </button>
              
              {/* Payment Methods */}
              <div className="mt-4 flex justify-center space-x-2">
                <span className="text-gray-400">
                  <svg className="h-6 w-10" viewBox="0 0 40 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="40" height="24" rx="4" fill="currentColor" fillOpacity="0.1"/>
                    <path d="M15 7H25V17H15V7Z" fill="#FF5F00"/>
                    <path d="M15.5 12C15.5 9.7 16.6 7.7 18.3 6.5C17.1 5.6 15.6 5 14 5C9.6 5 6 8.1 6 12C6 15.9 9.6 19 14 19C15.6 19 17.1 18.4 18.3 17.5C16.6 16.3 15.5 14.3 15.5 12Z" fill="#EB001B"/>
                    <path d="M34 12C34 15.9 30.4 19 26 19C24.4 19 22.9 18.4 21.7 17.5C23.4 16.3 24.5 14.3 24.5 12C24.5 9.7 23.4 7.7 21.7 6.5C22.9 5.6 24.4 5 26 5C30.4 5 34 8.1 34 12Z" fill="#F79E1B"/>
                  </svg>
                </span>
                <span className="text-gray-400">
                  <svg className="h-6 w-10" viewBox="0 0 40 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="40" height="24" rx="4" fill="currentColor" fillOpacity="0.1"/>
                    <path d="M15 7H11V17H15V7Z" fill="#0079BE"/>
                    <path d="M11.5 12C11.5 9.7 12.6 7.7 14.3 6.5C13.1 5.6 11.6 5 10 5C5.6 5 2 8.1 2 12C2 15.9 5.6 19 10 19C11.6 19 13.1 18.4 14.3 17.5C12.6 16.3 11.5 14.3 11.5 12Z" fill="#0079BE"/>
                    <path d="M38 12C38 15.9 34.4 19 30 19C28.4 19 26.9 18.4 25.7 17.5C27.4 16.3 28.5 14.3 28.5 12C28.5 9.7 27.4 7.7 25.7 6.5C26.9 5.6 28.4 5 30 5C34.4 5 38 8.1 38 12Z" fill="#0079BE"/>
                    <path d="M29 7H25V17H29V7Z" fill="#0079BE"/>
                  </svg>
                </span>
                <span className="text-gray-400">
                  <svg className="h-6 w-10" viewBox="0 0 40 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="40" height="24" rx="4" fill="currentColor" fillOpacity="0.1"/>
                    <path d="M28.4 7.6H25.6C25.1 7.6 24.6 7.8 24.3 8.2C24 8.6 23.8 9.1 23.9 9.6L25.4 17.1C25.5 17.6 26 18 26.5 18H29.3C29.8 18 30.3 17.8 30.6 17.4C30.9 17 31.1 16.5 31 16L29.5 8.5C29.4 8 28.9 7.6 28.4 7.6Z" fill="#006FCF"/>
                    <path d="M20.4 7.6H17.6C17.1 7.6 16.6 7.8 16.3 8.2C16 8.6 15.8 9.1 15.9 9.6L17.4 17.1C17.5 17.6 18 18 18.5 18H21.3C21.8 18 22.3 17.8 22.6 17.4C22.9 17 23.1 16.5 23 16L21.5 8.5C21.4 8 20.9 7.6 20.4 7.6Z" fill="#006FCF"/>
                    <path d="M12.4 7.6H9.6C9.1 7.6 8.6 7.8 8.3 8.2C8 8.6 7.8 9.1 7.9 9.6L9.4 17.1C9.5 17.6 10 18 10.5 18H13.3C13.8 18 14.3 17.8 14.6 17.4C14.9 17 15.1 16.5 15 16L13.5 8.5C13.4 8 12.9 7.6 12.4 7.6Z" fill="#006FCF"/>
                  </svg>
                </span>
                <span className="text-gray-400">
                  <svg className="h-6 w-10" viewBox="0 0 40 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="40" height="24" rx="4" fill="currentColor" fillOpacity="0.1"/>
                    <path d="M29.5 9.5C29.5 11.4 28 13 26 13C24 13 22.5 11.4 22.5 9.5C22.5 7.6 24 6 26 6C28 6 29.5 7.6 29.5 9.5Z" fill="#253B80"/>
                    <path d="M33 9.5H31V15H33V9.5Z" fill="#253B80"/>
                    <path d="M21 9.5H19V15H21V9.5Z" fill="#253B80"/>
                    <path d="M17.5 9.5C17.5 11.4 16 13 14 13C12 13 10.5 11.4 10.5 9.5C10.5 7.6 12 6 14 6C16 6 17.5 7.6 17.5 9.5Z" fill="#253B80"/>
                    <path d="M9 9.5H7V15H9V9.5Z" fill="#253B80"/>
                  </svg>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
   );
}

export default ShoppingCart;
