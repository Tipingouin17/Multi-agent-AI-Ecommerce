import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Customer Account Page
 * 
 * Displays customer account information, order history,
 * saved addresses, payment methods, and account settings.
 */
function Account() {
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('profile');
  const [profile, setProfile] = useState(null);
  const [orders, setOrders] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: ''
  });
  
  // Load account data on component mount
  useEffect(() => {
    loadAccountData();
  }, []);
  
  // Load account data from API
  async function loadAccountData() {
    try {
      setLoading(true);
      
      // Load profile data
      const profileData = await apiService.getCustomerProfile();
      setProfile(profileData);
      setFormData({
        first_name: profileData.first_name,
        last_name: profileData.last_name,
        email: profileData.email,
        phone: profileData.phone || ''
      });
      
      // Load orders
      const ordersData = await apiService.getCustomerOrders();
      setOrders(ordersData);
      
      // Load addresses
      const addressesData = await apiService.getCustomerAddresses();
      setAddresses(addressesData);
      
      // Load payment methods
      const paymentData = await apiService.getCustomerPaymentMethods();
      setPaymentMethods(paymentData);
      
      setError(null);
    } catch (err) {
      setError("Failed to load account data: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Handle form input change
  function handleInputChange(e) {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  }
  
  // Handle profile update
  async function handleProfileUpdate(e) {
    e.preventDefault();
    
    try {
      setLoading(true);
      
      await apiService.updateCustomerProfile(formData);
      
      // Update local state
      setProfile({
        ...profile,
        ...formData
      });
      
      setEditMode(false);
      setError(null);
    } catch (err) {
      setError("Failed to update profile: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Handle address deletion
  async function handleDeleteAddress(addressId) {
    if (!window.confirm('Are you sure you want to delete this address?')) {
      return;
    }
    
    try {
      setLoading(true);
      
      await apiService.deleteCustomerAddress(addressId);
      
      // Update local state
      setAddresses(addresses.filter(address => address.id !== addressId));
      
      setError(null);
    } catch (err) {
      setError("Failed to delete address: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Handle payment method deletion
  async function handleDeletePaymentMethod(paymentId) {
    if (!window.confirm('Are you sure you want to delete this payment method?')) {
      return;
    }
    
    try {
      setLoading(true);
      
      await apiService.deleteCustomerPaymentMethod(paymentId);
      
      // Update local state
      setPaymentMethods(paymentMethods.filter(payment => payment.id !== paymentId));
      
      setError(null);
    } catch (err) {
      setError("Failed to delete payment method: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Format date
  function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  }
  
  // Get status color based on order status
  function getStatusColor(status) {
    switch (status.toLowerCase()) {
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'shipped':
        return 'bg-green-100 text-green-800';
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'returned':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }
  
  // Render loading state
  if (loading && !profile) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="md:col-span-1">
                <div className="bg-white p-4 rounded-lg shadow">
                  <div className="h-6 bg-gray-200 rounded mb-4"></div>
                  <div className="space-y-2">
                    {[...Array(4)].map((_, i) => (
                      <div key={i} className="h-4 bg-gray-200 rounded"></div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="md:col-span-3">
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="h-6 bg-gray-200 rounded w-1/3 mb-6"></div>
                  <div className="space-y-4">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="h-4 bg-gray-200 rounded"></div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  // Render error state
  if (error && !profile) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">My Account</h1>
          
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-8">
            <p>{error}</p>
            <button 
              onClick={loadAccountData} 
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
        <h1 className="text-3xl font-bold text-gray-900 mb-8">My Account</h1>
        
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-8">
            <p>{error}</p>
            <button 
              onClick={loadAccountData} 
              className="mt-2 bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded"
            >
              Try Again
            </button>
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Sidebar Navigation */}
          <div className="md:col-span-1">
            <div className="bg-white p-4 rounded-lg shadow">
              <nav className="space-y-1">
                <button
                  onClick={() => setActiveTab('profile')}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                    activeTab === 'profile'
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <svg className="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                  </svg>
                  Profile
                </button>
                
                <button
                  onClick={( ) => setActiveTab('orders')}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                    activeTab === 'orders'
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <svg className="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"></path>
                  </svg>
                  Orders
                </button>
                
                <button
                  onClick={( ) => setActiveTab('addresses')}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                    activeTab === 'addresses'
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <svg className="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  </svg>
                  Addresses
                </button>
                
                <button
                  onClick={( ) => setActiveTab('payment')}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                    activeTab === 'payment'
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <svg className="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"></path>
                  </svg>
                  Payment Methods
                </button>
                
                <button
                  onClick={( ) => setActiveTab('settings')}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                    activeTab === 'settings'
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <svg className="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  </svg>
                  Settings
                </button>
              </nav>
            </div>
          </div>
          
          {/* Main Content */}
          <div className="md:col-span-3">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-medium text-gray-900">Profile Information</h2>
                  <button
                    type="button"
                    onClick={( ) => setEditMode(!editMode)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    {editMode ? 'Cancel' : 'Edit'}
                  </button>
                </div>
                
                {editMode ? (
                  <form onSubmit={handleProfileUpdate}>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
                      <div>
                        <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
                          First Name
                        </label>
                        <input
                          type="text"
                          id="first_name"
                          name="first_name"
                          value={formData.first_name}
                          onChange={handleInputChange}
                          required
                          className="w-full border border-gray-300 rounded-lg py-2 px-3 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
                          Last Name
                        </label>
                        <input
                          type="text"
                          id="last_name"
                          name="last_name"
                          value={formData.last_name}
                          onChange={handleInputChange}
                          required
                          className="w-full border border-gray-300 rounded-lg py-2 px-3 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                          Email Address
                        </label>
                        <input
                          type="email"
                          id="email"
                          name="email"
                          value={formData.email}
                          onChange={handleInputChange}
                          required
                          className="w-full border border-gray-300 rounded-lg py-2 px-3 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                          Phone Number
                        </label>
                        <input
                          type="tel"
                          id="phone"
                          name="phone"
                          value={formData.phone}
                          onChange={handleInputChange}
                          className="w-full border border-gray-300 rounded-lg py-2 px-3 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                    
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
                      >
                        {loading ? 'Saving...' : 'Save Changes'}
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Name</h3>
                        <p className="mt-1 text-gray-900">{profile.first_name} {profile.last_name}</p>
                      </div>
                      
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Email Address</h3>
                        <p className="mt-1 text-gray-900">{profile.email}</p>
                      </div>
                      
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Phone Number</h3>
                        <p className="mt-1 text-gray-900">{profile.phone || 'Not provided'}</p>
                      </div>
                      
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Member Since</h3>
                        <p className="mt-1 text-gray-900">{formatDate(profile.created_at)}</p>
                      </div>
                    </div>
                    
                    <div className="pt-4 border-t border-gray-200">
                      <h3 className="text-sm font-medium text-gray-500">Account Status</h3>
                      <div className="mt-1 flex items-center">
                        <span className="inline-block h-2 w-2 rounded-full bg-green-400 mr-2"></span>
                        <span className="text-gray-900">Active</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {/* Orders Tab */}
            {activeTab === 'orders' && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-medium text-gray-900 mb-6">Order History</h2>
                
                {orders.length === 0 ? (
                  <div className="text-center py-8">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"></path>
                    </svg>
                    <h3 className="mt-2 text-lg font-medium text-gray-900">No orders yet</h3>
                    <p className="mt-1 text-gray-500">
                      When you place an order, it will appear here.
                    </p>
                    <Link 
                      to="/products" 
                      className="mt-4 inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                      Start Shopping
                    </Link>
                  </div>
                 ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Order #
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Date
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Total
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {orders.map(order => (
                          <tr key={order.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">
                                #{order.order_number}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900">
                                {formatDate(order.order_date)}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(order.status)}`}>
                                {order.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900">
                                ${order.total.toFixed(2)}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <Link 
                                to={`/orders/${order.id}`}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                View Details
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
            
            {/* Addresses Tab */}
            {activeTab === 'addresses' && (
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-medium text-gray-900">Saved Addresses</h2>
                  <Link 
                    to="/account/addresses/new"
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
                  >
                    Add New Address
                  </Link>
                </div>
                
                {addresses.length === 0 ? (
                  <div className="text-center py-8">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    <h3 className="mt-2 text-lg font-medium text-gray-900">No addresses saved</h3>
                    <p className="mt-1 text-gray-500">
                      Add an address to make checkout faster.
                    </p>
                  </div>
                 ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {addresses.map(address => (
                      <div key={address.id} className="border border-gray-200 rounded-lg p-4">
                        {address.is_default && (
                          <div className="mb-2">
                            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                              Default
                            </span>
                          </div>
                        )}
                        
                        <h3 className="font-medium text-gray-900">{address.name}</h3>
                        <address className="mt-1 text-sm text-gray-600 not-italic">
                          {address.street}  

                          {address.city}, {address.state} {address.zip}  

                          {address.country}
                        </address>
                        
                        <div className="mt-4 flex space-x-3">
                          <Link 
                            to={`/account/addresses/${address.id}/edit`}
                            className="text-sm text-blue-600 hover:text-blue-800"
                          >
                            Edit
                          </Link>
                          <button
                            type="button"
                            onClick={() => handleDeleteAddress(address.id)}
                            className="text-sm text-red-600 hover:text-red-800"
                          >
                            Delete
                          </button>
                          {!address.is_default && (
                            <button
                              type="button"
                              className="text-sm text-gray-600 hover:text-gray-800"
                            >
                              Set as Default
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Payment Methods Tab */}
            {activeTab === 'payment' && (
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-medium text-gray-900">Payment Methods</h2>
                  <Link 
                    to="/account/payment/new"
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
                  >
                    Add Payment Method
                  </Link>
                </div>
                
                {paymentMethods.length === 0 ? (
                  <div className="text-center py-8">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"></path>
                    </svg>
                    <h3 className="mt-2 text-lg font-medium text-gray-900">No payment methods saved</h3>
                    <p className="mt-1 text-gray-500">
                      Add a payment method to make checkout faster.
                    </p>
                  </div>
                 ) : (
                  <div className="space-y-4">
                    {paymentMethods.map(payment => (
                      <div key={payment.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            {payment.brand === 'visa' && (
                              <svg className="h-8 w-12 text-blue-700" viewBox="0 0 48 32" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                <rect width="48" height="32" rx="4" fill="currentColor" fillOpacity="0.1"/>
                                <path d="M18 21H15L17 11H20L18 21Z" fill="currentColor"/>
                                <path d="M27.5 11.2C26.8 11 25.8 10.8 24.5 10.8C22 10.8 20 12.1 20 14C20 15.5 21.4 16.2 22.5 16.7C23.6 17.2 24 17.5 24 18C24 18.7 23.2 19 22 19C20.8 19 20 18.8 18.8 18.3L18.4 18.1L18 20.5C18.8 20.8 20.2 21.1 21.6 21.1C24.3 21.1 26.2 19.8 26.2 17.8C26.2 16.6 25.5 15.7 23.8 14.9C22.8 14.4 22.1 14.1 22.1 13.6C22.1 13.1 22.6 12.7 23.8 12.7C24.8 12.7 25.5 12.9 26.1 13.1L26.4 13.2L26.8 11.1L27.5 11.2Z" fill="currentColor"/>
                                <path d="M35 11H33C32.4 11 31.9 11.2 31.7 11.7L28 21H30.7C30.7 21 31.1 19.9 31.2 19.7C31.5 19.7 34.1 19.7 34.5 19.7C34.6 20 34.8 21 34.8 21H37L35 11ZM32 17.5C32.2 17 33.1 14.8 33.1 14.8C33.1 14.8 33.3 14.3 33.4 14L33.6 14.7C33.6 14.7 34.1 17.1 34.2 17.5H32Z" fill="currentColor"/>
                              </svg>
                             )}
                            {payment.brand === 'mastercard' && (
                              <svg className="h-8 w-12" viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <rect width="48" height="32" rx="4" fill="#F9F9F9"/>
                                <path d="M18 10H30V22H18V10Z" fill="#FF5F00"/>
                                <path d="M19 16C19 13.7 20.1 11.7 21.8 10.5C20.6 9.6 19.1 9 17.5 9C13.9 9 11 12.1 11 16C11 19.9 13.9 23 17.5 23C19.1 23 20.6 22.4 21.8 21.5C20.1 20.3 19 18.3 19 16Z" fill="#EB001B"/>
                                <path d="M37 16C37 19.9 34.1 23 30.5 23C28.9 23 27.4 22.4 26.2 21.5C27.9 20.3 29 18.3 29 16C29 13.7 27.9 11.7 26.2 10.5C27.4 9.6 28.9 9 30.5 9C34.1 9 37 12.1 37 16Z" fill="#F79E1B"/>
                              </svg>
                             )}
                            {payment.brand === 'amex' && (
                              <svg className="h-8 w-12" viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <rect width="48" height="32" rx="4" fill="#F9F9F9"/>
                                <path d="M32.4 15H29.6C29.1 15 28.6 15.2 28.3 15.6C28 16 27.8 16.5 27.9 17L29.4 24.5C29.5 25 30 25.4 30.5 25.4H33.3C33.8 25.4 34.3 25.2 34.6 24.8C34.9 24.4 35.1 23.9 35 23.4L33.5 15.9C33.4 15.4 32.9 15 32.4 15Z" fill="#006FCF"/>
                                <path d="M24.4 15H21.6C21.1 15 20.6 15.2 20.3 15.6C20 16 19.8 16.5 19.9 17L21.4 24.5C21.5 25 22 25.4 22.5 25.4H25.3C25.8 25.4 26.3 25.2 26.6 24.8C26.9 24.4 27.1 23.9 27 23.4L25.5 15.9C25.4 15.4 24.9 15 24.4 15Z" fill="#006FCF"/>
                                <path d="M16.4 15H13.6C13.1 15 12.6 15.2 12.3 15.6C12 16 11.8 16.5 11.9 17L13.4 24.5C13.5 25 14 25.4 14.5 25.4H17.3C17.8 25.4 18.3 25.2 18.6 24.8C18.9 24.4 19.1 23.9 19 23.4L17.5 15.9C17.4 15.4 16.9 15 16.4 15Z" fill="#006FCF"/>
                              </svg>
                             )}
                            <div className="ml-3">
                              <p className="text-gray-900 font-medium">
                                {payment.brand} •••• {payment.last4}
                              </p>
                              <p className="text-sm text-gray-600">
                                Expires {payment.exp_month}/{payment.exp_year}
                              </p>
                            </div>
                          </div>
                          
                          {payment.is_default && (
                            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                              Default
                            </span>
                          )}
                        </div>
                        
                        <div className="mt-4 flex space-x-3">
                          <button
                            type="button"
                            onClick={() => handleDeletePaymentMethod(payment.id)}
                            className="text-sm text-red-600 hover:text-red-800"
                          >
                            Delete
                          </button>
                          {!payment.is_default && (
                            <button
                              type="button"
                              className="text-sm text-gray-600 hover:text-gray-800"
                            >
                              Set as Default
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-medium text-gray-900 mb-6">Account Settings</h2>
                
                <div className="space-y-6">
                  {/* Password Change */}
                  <div className="pb-6 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Password</h3>
                    <p className="text-gray-600 mb-4">
                      Change your password to keep your account secure.
                    </p>
                    <button
                      type="button"
                      onClick={() => navigate('/account/change-password')}
                      className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded-lg"
                    >
                      Change Password
                    </button>
                  </div>
                  
                  {/* Notification Preferences */}
                  <div className="pb-6 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Notification Preferences</h3>
                    <p className="text-gray-600 mb-4">
                      Manage how you receive notifications and updates.
                    </p>
                    <button
                      type="button"
                      onClick={() => navigate('/account/notifications')}
                      className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded-lg"
                    >
                      Manage Notifications
                    </button>
                  </div>
                  
                  {/* Privacy Settings */}
                  <div className="pb-6 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Privacy Settings</h3>
                    <p className="text-gray-600 mb-4">
                      Control how your information is used and shared.
                    </p>
                    <button
                      type="button"
                      onClick={() => navigate('/account/privacy')}
                      className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded-lg"
                    >
                      Manage Privacy
                    </button>
                  </div>
                  
                  {/* Delete Account */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Delete Account</h3>
                    <p className="text-gray-600 mb-4">
                      Permanently delete your account and all associated data.
                    </p>
                    <button
                      type="button"
                      className="bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded-lg"
                    >
                      Delete Account
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Account;
