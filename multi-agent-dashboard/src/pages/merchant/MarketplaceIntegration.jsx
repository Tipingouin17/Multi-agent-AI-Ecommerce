import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Marketplace Integration
 * 
 * Interface for managing connections to various marketplaces,
 * including Amazon, eBay, Back Market, Refurbed, and Mirakl.
 */
function MarketplaceIntegration() {
  const [marketplaces, setMarketplaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('connected');
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [selectedMarketplace, setSelectedMarketplace] = useState(null);
  const [connectionForm, setConnectionForm] = useState({
    apiKey: '',
    secretKey: '',
    merchantId: '',
    region: 'us',
    autoSync: true
  });
  const [formErrors, setFormErrors] = useState({});
  const [connectingMarketplace, setConnectingMarketplace] = useState(false);
  const [availableMarketplaces, setAvailableMarketplaces] = useState([]);
  const [syncStatus, setSyncStatus] = useState({});
  const [showSyncModal, setShowSyncModal] = useState(false);
  const [syncOptions, setSyncOptions] = useState({
    products: true,
    inventory: true,
    orders: true,
    prices: true
  });
  const [selectedMarketplaceForSync, setSelectedMarketplaceForSync] = useState(null);
  const [syncing, setSyncing] = useState(false);
  
  // Load marketplaces on component mount
  useEffect(() => {
    loadMarketplaces();
    loadAvailableMarketplaces();
  }, []);
  
  // Load connected marketplaces from API
  async function loadMarketplaces() {
    try {
      setLoading(true);
      const data = await apiService.getConnectedMarketplaces();
      setMarketplaces(data);
      
      // Load sync status for each marketplace
      const statusPromises = data.map(marketplace => 
        apiService.getMarketplaceSyncStatus(marketplace.id)
      );
      
      const statuses = await Promise.all(statusPromises);
      
      const syncStatusMap = {};
      data.forEach((marketplace, index) => {
        syncStatusMap[marketplace.id] = statuses[index];
      });
      
      setSyncStatus(syncStatusMap);
      
      setError(null);
    } catch (err) {
      setError("Failed to load marketplaces: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Load available marketplaces from API
  async function loadAvailableMarketplaces() {
    try {
      const data = await apiService.getAvailableMarketplaces();
      setAvailableMarketplaces(data);
    } catch (err) {
      console.error("Failed to load available marketplaces:", err);
    
      // Set empty arrays on error to prevent undefined errors
      setMarketplaces([]);
      setAvailableMarketplaces([]);
    }
  }
  
  // Open connect modal for a marketplace
  function openConnectModal(marketplace) {
    setSelectedMarketplace(marketplace);
    setConnectionForm({
      apiKey: '',
      secretKey: '',
      merchantId: '',
      region: 'us',
      autoSync: true
    });
    setFormErrors({});
    setShowConnectModal(true);
  }
  
  // Handle connection form input change
  function handleConnectionFormChange(e) {
    const { name, value, type, checked } = e.target;
    setConnectionForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error for this field
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  }
  
  // Validate connection form
  function validateConnectionForm() {
    const errors = {};
    
    if (!connectionForm.apiKey.trim()) {
      errors.apiKey = 'API Key is required';
    }
    
    if (!connectionForm.secretKey.trim()) {
      errors.secretKey = 'Secret Key is required';
    }
    
    if (selectedMarketplace?.requiresMerchantId && !connectionForm.merchantId.trim()) {
      errors.merchantId = 'Merchant ID is required';
    }
    
    return errors;
  }
  
  // Handle connect marketplace form submission
  async function handleConnectMarketplace(e) {
    e.preventDefault();
    
    const errors = validateConnectionForm();
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }
    
    try {
      setConnectingMarketplace(true);
      
      await apiService.connectMarketplace({
        marketplaceId: selectedMarketplace.id,
        ...connectionForm
      });
      
      setShowConnectModal(false);
      loadMarketplaces();
    } catch (err) {
      setFormErrors({
        submit: err.message || 'Failed to connect marketplace'
      });
      console.error(err);
    } finally {
      setConnectingMarketplace(false);
    }
  }
  
  // Handle disconnect marketplace
  async function handleDisconnectMarketplace(marketplaceId) {
    if (!window.confirm('Are you sure you want to disconnect this marketplace? This will stop all synchronization.')) {
      return;
    }
    
    try {
      await apiService.disconnectMarketplace(marketplaceId);
      loadMarketplaces();
    } catch (err) {
      setError(`Failed to disconnect marketplace: ${err.message}`);
      console.error(err);
    }
  }
  
  // Open sync modal for a marketplace
  function openSyncModal(marketplace) {
    setSelectedMarketplaceForSync(marketplace);
    setSyncOptions({
      products: true,
      inventory: true,
      orders: true,
      prices: true
    });
    setShowSyncModal(true);
  }
  
  // Handle sync options change
  function handleSyncOptionsChange(e) {
    const { name, checked } = e.target;
    setSyncOptions(prev => ({
      ...prev,
      [name]: checked
    }));
  }
  
  // Handle sync marketplace
  async function handleSyncMarketplace(e) {
    e.preventDefault();
    
    try {
      setSyncing(true);
      
      await apiService.syncMarketplace({
        marketplaceId: selectedMarketplaceForSync.id,
        options: syncOptions
      });
      
      setShowSyncModal(false);
      
      // Update sync status for this marketplace
      const status = await apiService.getMarketplaceSyncStatus(selectedMarketplaceForSync.id);
      setSyncStatus(prev => ({
        ...prev,
        [selectedMarketplaceForSync.id]: status
      }));
    } catch (err) {
      setError(`Failed to start synchronization: ${err.message}`);
      console.error(err);
    } finally {
      setSyncing(false);
    }
  }
  
  // Format date
  function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
  }
  
  // Get marketplace logo
  function getMarketplaceLogo(type) {
    switch (type.toLowerCase()) {
      case 'amazon':
        return 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/2560px-Amazon_logo.svg.png';
      case 'ebay':
        return 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/EBay_logo.svg/2560px-EBay_logo.svg.png';
      case 'back market':
        return 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Back_Market_logo.svg/2560px-Back_Market_logo.svg.png';
      case 'refurbed':
        return 'https://refurbed.com/static/images/logo.svg';
      case 'mirakl':
        return 'https://www.mirakl.com/wp-content/uploads/2021/05/mirakl-logo-color-1.svg';
      case 'shopify':
        return 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Shopify_logo_2018.svg/2560px-Shopify_logo_2018.svg.png';
      case 'woocommerce':
        return 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/WooCommerce_logo.svg/2560px-WooCommerce_logo.svg.png';
      case 'prestashop':
        return 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/PrestaShop_logo.svg/2560px-PrestaShop_logo.svg.png';
      default:
        return 'https://via.placeholder.com/150x50?text=Marketplace';
    }
  }
  
  // Get sync status badge class
  function getSyncStatusBadgeClass(status ) {
    switch (status) {
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }
  
  // Get sync status text
  function getSyncStatusText(status) {
    switch (status) {
      case 'in_progress':
        return 'In Progress';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'pending':
        return 'Pending';
      default:
        return 'Unknown';
    }
  }
  
  return (
    <div className="p-6">
      <div className="mb-6 flex flex-col md:flex-row md:justify-between md:items-center space-y-4 md:space-y-0">
        <h1 className="text-2xl font-bold text-gray-900">Marketplace Integration</h1>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('connected')}
            className={`px-4 py-2 rounded-md ${
              activeTab === 'connected'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Connected Marketplaces
          </button>
          <button
            onClick={() => setActiveTab('available')}
            className={`px-4 py-2 rounded-md ${
              activeTab === 'available'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Available Marketplaces
          </button>
        </div>
      </div>
      
      {loading && (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      )}
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <p>{error}</p>
          <button
            onClick={loadMarketplaces}
            className="mt-2 bg-red-200 hover:bg-red-300 text-red-700 px-3 py-1 rounded"
          >
            Try Again
          </button>
        </div>
      )}
      
      {!loading && !error && activeTab === 'connected' && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-6">
          {marketplaces.length === 0 ? (
            <div className="p-6 text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Connected Marketplaces</h3>
              <p className="text-gray-600 mb-4">
                You haven't connected any marketplaces yet. Go to the "Available Marketplaces" tab to connect your first marketplace.
              </p>
              <button
                onClick={() => setActiveTab('available')}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
              >
                Browse Available Marketplaces
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Marketplace
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Sync
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Products
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Orders
                    </th>
                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {marketplaces.map(marketplace => (
                    <tr key={marketplace.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <img
                            src={getMarketplaceLogo(marketplace.type)}
                            alt={marketplace.name}
                            className="h-8 object-contain mr-3"
                          />
                          <div>
                            <div className="font-medium text-gray-900">{marketplace.name}</div>
                            <div className="text-sm text-gray-500">{marketplace.type}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          marketplace.connected
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {marketplace.connected ? 'Connected' : 'Disconnected'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {syncStatus[marketplace.id]?.lastSync ? (
                          <div>
                            <div>{formatDate(syncStatus[marketplace.id].lastSync)}</div>
                            <div className="flex items-center mt-1">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                getSyncStatusBadgeClass(syncStatus[marketplace.id].status)
                              }`}>
                                {getSyncStatusText(syncStatus[marketplace.id].status)}
                              </span>
                            </div>
                          </div>
                        ) : (
                          'Never'
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {marketplace.productCount}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {marketplace.orderCount}
                        {marketplace.pendingOrderCount > 0 && (
                          <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            {marketplace.pendingOrderCount} pending
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => openSyncModal(marketplace)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                          disabled={syncStatus[marketplace.id]?.status === 'in_progress'}
                        >
                          Sync Now
                        </button>
                        <Link
                          to={`/merchant/marketplaces/${marketplace.id}/settings`}
                          className="text-indigo-600 hover:text-indigo-900 mr-3"
                        >
                          Settings
                        </Link>
                        <button
                          onClick={() => handleDisconnectMarketplace(marketplace.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Disconnect
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
      
      {!loading && !error && activeTab === 'available' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {availableMarketplaces.map(marketplace => {
            const isConnected = marketplaces.some(m => m.id === marketplace.id);
            
            return (
              <div key={marketplace.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <img
                      src={getMarketplaceLogo(marketplace.type)}
                      alt={marketplace.name}
                      className="h-8 object-contain"
                    />
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      isConnected
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {isConnected ? 'Connected' : 'Available'}
                    </span>
                  </div>
                  
                  <h3 className="text-lg font-medium text-gray-900 mb-2">{marketplace.name}</h3>
                  <p className="text-gray-600 mb-4">{marketplace.description}</p>
                  
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Features</h4>
                    <ul className="space-y-1">
                      {marketplace.features.map((feature, index) => (
                        <li key={index} className="flex items-center text-sm text-gray-600">
                          <svg className="h-4 w-4 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                          </svg>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  {isConnected ? (
                    <div className="flex space-x-2">
                      <Link
                        to={`/merchant/marketplaces/${marketplace.id}/settings`}
                        className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-800 text-center px-4 py-2 rounded-md"
                      >
                        Settings
                      </Link>
                      <button
                        onClick={() => handleDisconnectMarketplace(marketplace.id)}
                        className="flex-1 bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded-md"
                      >
                        Disconnect
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => openConnectModal(marketplace)}
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
                    >
                      Connect
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
      
      {/* Connect Marketplace Modal */}
      {showConnectModal && selectedMarketplace && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">Connect to {selectedMarketplace.name}</h2>
                <button
                  onClick={() => setShowConnectModal(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <form onSubmit={handleConnectMarketplace}>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mb-1">API Key *</label>
                    <input
                      type="text"
                      id="apiKey"
                      name="apiKey"
                      value={connectionForm.apiKey}
                      onChange={handleConnectionFormChange}
                      className={`w-full border ${
                        formErrors.apiKey ? 'border-red-500' : 'border-gray-300'
                      } rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    />
                    {formErrors.apiKey && (
                      <p className="mt-1 text-sm text-red-600">{formErrors.apiKey}</p>
                    )}
                  </div>
                  
                  <div>
                    <label htmlFor="secretKey" className="block text-sm font-medium text-gray-700 mb-1">Secret Key *</label>
                    <input
                      type="password"
                      id="secretKey"
                      name="secretKey"
                      value={connectionForm.secretKey}
                      onChange={handleConnectionFormChange}
                      className={`w-full border ${
                        formErrors.secretKey ? 'border-red-500' : 'border-gray-300'
                      } rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    />
                    {formErrors.secretKey && (
                      <p className="mt-1 text-sm text-red-600">{formErrors.secretKey}</p>
                    )}
                  </div>
                  
                  {selectedMarketplace.requiresMerchantId && (
                    <div>
                      <label htmlFor="merchantId" className="block text-sm font-medium text-gray-700 mb-1">Merchant ID *</label>
                      <input
                        type="text"
                        id="merchantId"
                        name="merchantId"
                        value={connectionForm.merchantId}
                        onChange={handleConnectionFormChange}
                        className={`w-full border ${
                          formErrors.merchantId ? 'border-red-500' : 'border-gray-300'
                        } rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500`}
                      />
                      {formErrors.merchantId && (
                        <p className="mt-1 text-sm text-red-600">{formErrors.merchantId}</p>
                      )}
                    </div>
                  )}
                  
                  {selectedMarketplace.hasRegions && (
                    <div>
                      <label htmlFor="region" className="block text-sm font-medium text-gray-700 mb-1">Region</label>
                      <select
                        id="region"
                        name="region"
                        value={connectionForm.region}
                        onChange={handleConnectionFormChange}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="us">United States</option>
                        <option value="eu">Europe</option>
                        <option value="ca">Canada</option>
                        <option value="uk">United Kingdom</option>
                        <option value="au">Australia</option>
                      </select>
                    </div>
                  )}
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="autoSync"
                      name="autoSync"
                      checked={connectionForm.autoSync}
                      onChange={handleConnectionFormChange}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="autoSync" className="ml-2 block text-sm text-gray-900">
                      Enable automatic synchronization
                    </label>
                  </div>
                  
                  {formErrors.submit && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                      <p>{formErrors.submit}</p>
                    </div>
                  )}
                </div>
                
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowConnectModal(false)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={connectingMarketplace}
                    className={`bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md ${
                      connectingMarketplace ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    {connectingMarketplace ? 'Connecting...' : 'Connect'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
      
      {/* Sync Marketplace Modal */}
      {showSyncModal && selectedMarketplaceForSync && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">Sync with {selectedMarketplaceForSync.name}</h2>
                <button
                  onClick={() => setShowSyncModal(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <form onSubmit={handleSyncMarketplace}>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Select what to synchronize:</h3>
                    
                    <div className="space-y-2">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="products"
                          name="products"
                          checked={syncOptions.products}
                          onChange={handleSyncOptionsChange}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor="products" className="ml-2 block text-sm text-gray-900">
                          Products
                        </label>
                      </div>
                      
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="inventory"
                          name="inventory"
                          checked={syncOptions.inventory}
                          onChange={handleSyncOptionsChange}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor="inventory" className="ml-2 block text-sm text-gray-900">
                          Inventory
                        </label>
                      </div>
                      
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="orders"
                          name="orders"
                          checked={syncOptions.orders}
                          onChange={handleSyncOptionsChange}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor="orders" className="ml-2 block text-sm text-gray-900">
                          Orders
                        </label>
                      </div>
                      
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="prices"
                          name="prices"
                          checked={syncOptions.prices}
                          onChange={handleSyncOptionsChange}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor="prices" className="ml-2 block text-sm text-gray-900">
                          Prices
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-yellow-700">
                          Synchronization may take several minutes depending on the amount of data.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowSyncModal(false)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={syncing || Object.values(syncOptions).every(v => !v)}
                    className={`bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md ${
                      syncing || Object.values(syncOptions).every(v => !v) ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    {syncing ? 'Starting Sync...' : 'Start Synchronization'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MarketplaceIntegration;
