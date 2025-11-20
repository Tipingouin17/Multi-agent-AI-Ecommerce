import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '@/lib/api'
import { formatDateTime } from '@/utils/dateFormatter'

/**
 * Product Management
 * 
 * Interface for managing products across all marketplaces,
 * including creation, editing, and synchronization.
 */
function ProductManagement() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    marketplace: ''
  });
  const [sort, setSort] = useState({ field: 'updatedAt', direction: 'desc' });
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    itemsPerPage: 10
  });
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [bulkActionMenuOpen, setBulkActionMenuOpen] = useState(false);
  const [categories, setCategories] = useState([]);
  const [marketplaces, setMarketplaces] = useState([]);
  const [showAddProductModal, setShowAddProductModal] = useState(false);
  const [newProduct, setNewProduct] = useState({
    name: '',
    sku: '',
    description: '',
    price: '',
    cost: '',
    category: '',
    images: [],
    inventory: {
      quantity: '',
      warehouse: '',
      reorderLevel: '',
      lowStockAlert: true
    }
  });
  const [syncStatus, setSyncStatus] = useState({
    inProgress: false,
    lastSync: null,
    marketplaces: {}
  });
  
  // Load products on component mount and when filters, sort, or pagination change
  useEffect(() => {
    loadProducts();
  }, [filters, sort, pagination.currentPage, pagination.itemsPerPage]);
  
  // Load categories and marketplaces on component mount
  useEffect(() => {
    async function loadFilterOptions() {
      try {
        const categoriesData = await apiService.getProductCategories();
        setCategories(categoriesData.categories || categoriesData || []);
        
        const marketplacesData = await apiService.getMarketplaces();
        setMarketplaces(marketplacesData || []);
      } catch (err) {
        console.error("Failed to load filter options:", err);
        // Set empty arrays on error
        setCategories([]);
        setMarketplaces([]);
      }
    }
    
    loadFilterOptions();
  }, []);
  
  // Load products from API
  async function loadProducts() {
    try {
      setLoading(true);
      
      const params = {
        page: pagination.currentPage,
        limit: pagination.itemsPerPage,
        search: searchTerm,
        sortBy: sort.field,
        sortDirection: sort.direction,
        ...filters
      };
      
      const data = await apiService.getProducts(params);
      
      setProducts(data.products || []);
      setPagination({
        ...pagination,
        totalPages: data.totalPages || 1,
        totalItems: data.totalItems || 0
      });
      
      setError(null);
    } catch (err) {
      setError("Failed to load products: " + err.message);
      console.error(err);
      // Set empty array on error to prevent undefined errors
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }
  
  // Handle search
  function handleSearch(e) {
    e.preventDefault();
    loadProducts();
  }
  
  // Handle filter change
  function handleFilterChange(e) {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
    setPagination(prev => ({
      ...prev,
      currentPage: 1 // Reset to first page when filters change
    }));
  }
  
  // Handle sort change
  function handleSortChange(field) {
    setSort(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  }
  
  // Handle page change
  function handlePageChange(page) {
    setPagination(prev => ({
      ...prev,
      currentPage: page
    }));
  }
  
  // Handle product selection
  function handleProductSelection(productId) {
    setSelectedProducts(prev => {
      if (prev.includes(productId)) {
        return prev.filter(id => id !== productId);
      } else {
        return [...prev, productId];
      }
    });
  }
  
  // Handle select all products
  function handleSelectAllProducts() {
    if (selectedProducts.length === products.length) {
      setSelectedProducts([]);
    } else {
      setSelectedProducts(products.map(product => product.id));
    }
  }
  
  // Handle bulk action
  async function handleBulkAction(action) {
    if (selectedProducts.length === 0) return;
    
    try {
      switch (action) {
        case 'delete':
          if (window.confirm(`Are you sure you want to delete ${selectedProducts.length} products?`)) {
            await apiService.bulkDeleteProducts(selectedProducts);
            loadProducts();
            setSelectedProducts([]);
          }
          break;
        case 'sync':
          await apiService.bulkSyncProducts(selectedProducts);
          loadProducts();
          break;
        case 'activate':
          await apiService.bulkUpdateProductStatus(selectedProducts, 'active');
          loadProducts();
          break;
        case 'deactivate':
          await apiService.bulkUpdateProductStatus(selectedProducts, 'inactive');
          loadProducts();
          break;
        default:
          break;
      }
      
      setBulkActionMenuOpen(false);
    } catch (err) {
      setError(`Failed to perform bulk action: ${err.message}`);
      console.error(err);
    }
  }
  
  // Handle new product input change
  function handleNewProductChange(e) {
    const { name, value } = e.target;
    setNewProduct(prev => ({
      ...prev,
      [name]: value
    }));
  }
  
  // Handle inventory field changes
  function handleInventoryChange(e) {
    const { name, value, type, checked } = e.target;
    setNewProduct(prev => ({
      ...prev,
      inventory: {
        ...prev.inventory,
        [name]: type === 'checkbox' ? checked : value
      }
    }));
  }
  
  // Handle image upload
  function handleImageUpload(e) {
    const files = Array.from(e.target.files);
    // In a real app, you would upload these files to your server
    // For now, we'll just create object URLs
    const imageUrls = files.map(file => URL.createObjectURL(file));
    
    setNewProduct(prev => ({
      ...prev,
      images: [...prev.images, ...imageUrls]
    }));
  }
  
  // Handle add product form submission
  async function handleAddProduct(e) {
    e.preventDefault();
    
    try {
      // Add merchant_id (hardcoded for now, should come from auth context)
      const productData = {
        ...newProduct,
        merchant_id: 1 // TODO: Get from auth context
      };
      await apiService.createProduct(productData);
      setShowAddProductModal(false);
      setNewProduct({
        name: '',
        sku: '',
        description: '',
        price: '',
        cost: '',
        category: '',
        images: [],
        inventory: {
          quantity: '',
          warehouse: '',
          reorderLevel: '',
          lowStockAlert: true
        }
      });
      loadProducts();
    } catch (err) {
      setError(`Failed to create product: ${err.message}`);
      console.error(err);
    }
  }
  
  // Handle sync with marketplaces
  async function handleSyncWithMarketplaces() {
    try {
      setSyncStatus(prev => ({
        ...prev,
        inProgress: true
      }));
      
      const result = await apiService.syncProductsWithMarketplaces();
      
      setSyncStatus({
        inProgress: false,
        lastSync: new Date().toISOString(),
        marketplaces: result.marketplaces
      });
      
      loadProducts();
    } catch (err) {
      setError(`Failed to sync with marketplaces: ${err.message}`);
      console.error(err);
      setSyncStatus(prev => ({
        ...prev,
        inProgress: false
      }));
    }
  }
  
  // Format date
  // Using centralized date formatter utility
  
  // Format currency
  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  }
  
  return (
    <div className="p-6">
      <div className="mb-6 flex flex-col md:flex-row md:justify-between md:items-center space-y-4 md:space-y-0">
        <h1 className="text-2xl font-bold text-gray-900">Product Management</h1>
        
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
          <button
            onClick={() => setShowAddProductModal(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
          >
            Add Product
          </button>
          
          <button
            onClick={handleSyncWithMarketplaces}
            disabled={syncStatus.inProgress}
            className={`flex items-center ${
              syncStatus.inProgress
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-green-500 hover:bg-green-600'
            } text-white px-4 py-2 rounded-md`}
          >
            {syncStatus.inProgress ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Syncing...
              </>
             ) : (
              'Sync with Marketplaces'
            )}
          </button>
          
          {selectedProducts.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setBulkActionMenuOpen(!bulkActionMenuOpen)}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-md"
              >
                Bulk Actions ({selectedProducts.length})
              </button>
              
              {bulkActionMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10">
                  <div className="py-1">
                    <button
                      onClick={() => handleBulkAction('sync')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Sync Selected
                    </button>
                    <button
                      onClick={() => handleBulkAction('activate')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Activate Selected
                    </button>
                    <button
                      onClick={() => handleBulkAction('deactivate')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Deactivate Selected
                    </button>
                    <button
                      onClick={() => handleBulkAction('delete')}
                      className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                    >
                      Delete Selected
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {syncStatus.lastSync && (
        <div className="mb-4 text-sm text-gray-500">
          Last sync: {formatDateTime(syncStatus.lastSync)}
          {Object.keys(syncStatus.marketplaces).length > 0 && (
            <span className="ml-2">
              ({Object.entries(syncStatus.marketplaces).map(([name, count]) => (
                `${name}: ${count} products`
              )).join(', ')})
            </span>
          )}
        </div>
      )}
      
      {/* Search and Filters */}
      <div className="bg-white p-4 rounded-lg shadow-md mb-6">
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row md:items-end space-y-4 md:space-y-0 md:space-x-4">
          <div className="flex-1">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">Search Products</label>
            <input
              type="text"
              id="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name, SKU, or description"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              id="category"
              name="category"
              value={filters.category}
              onChange={handleFilterChange}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              {categories.map(category => (
                <option key={category.id} value={category.id}>{category.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              id="status"
              name="status"
              value={filters.status}
              onChange={handleFilterChange}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="draft">Draft</option>
            </select>
          </div>
          
          <div>
            <label htmlFor="marketplace" className="block text-sm font-medium text-gray-700 mb-1">Marketplace</label>
            <select
              id="marketplace"
              name="marketplace"
              value={filters.marketplace}
              onChange={handleFilterChange}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Marketplaces</option>
              {marketplaces.map(marketplace => (
                <option key={marketplace.id} value={marketplace.id}>{marketplace.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <button
              type="submit"
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
            >
              Search
            </button>
          </div>
        </form>
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
            onClick={loadProducts}
            className="mt-2 bg-red-200 hover:bg-red-300 text-red-700 px-3 py-1 rounded"
          >
            Try Again
          </button>
        </div>
      )}
      
      {!loading && !error && (
        <>
          {/* Products Table */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden mb-6">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedProducts.length === products.length && products.length > 0}
                          onChange={handleSelectAllProducts}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </div>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('name')}
                        className="flex items-center focus:outline-none"
                      >
                        Product
                        {sort.field === 'name' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('sku')}
                        className="flex items-center focus:outline-none"
                      >
                        SKU
                        {sort.field === 'sku' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('price')}
                        className="flex items-center focus:outline-none"
                      >
                        Price
                        {sort.field === 'price' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('inventory')}
                        className="flex items-center focus:outline-none"
                      >
                        Inventory
                        {sort.field === 'inventory' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('status')}
                        className="flex items-center focus:outline-none"
                      >
                        Status
                        {sort.field === 'status' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('updatedAt')}
                        className="flex items-center focus:outline-none"
                      >
                        Last Updated
                        {sort.field === 'updatedAt' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Marketplaces
                    </th>
                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {products.length === 0 ? (
                    <tr>
                      <td colSpan="9" className="px-6 py-4 text-center text-gray-500">
                        No products found. Try adjusting your search or filters.
                      </td>
                    </tr>
                  ) : (
                    products.map(product => (
                      <tr key={product.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedProducts.includes(product.id)}
                            onChange={() => handleProductSelection(product.id)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {product.images && product.images.length > 0 ? (
                              <img
                                src={product.images[0]}
                                alt={product.name}
                                className="h-10 w-10 rounded-md object-cover mr-3"
                              />
                            ) : (
                              <div className="h-10 w-10 rounded-md bg-gray-200 flex items-center justify-center mr-3">
                                <span className="text-gray-500 text-xs">No img</span>
                              </div>
                            )}
                            <div>
                              <div className="font-medium text-gray-900">{product.name}</div>
                              <div className="text-sm text-gray-500">{product.category}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {product.sku}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(product.price)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {product.inventory?.total_quantity || 0} in stock
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            product.status === 'active' ? 'bg-green-100 text-green-800' :
                            product.status === 'inactive' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {product.status ? product.status.charAt(0).toUpperCase() + product.status.slice(1) : 'Unknown'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDateTime(product.updatedAt)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex -space-x-1">
                            {(product.marketplaces || []).map(marketplace => (
                              <img
                                key={marketplace.id}
                                src={marketplace.icon}
                                alt={marketplace.name}
                                title={marketplace.name}
                                className="h-6 w-6 rounded-full border border-white"
                              />
                            ))}
                            {(product.marketplaces || []).length === 0 && (
                              <span className="text-sm text-gray-500">Not listed</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link
                            to={`/merchant/products/${product.id}`}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            Edit
                          </Link>
                          <button
                            onClick={() => {
                              if (window.confirm(`Are you sure you want to delete ${product.name}?`)) {
                                apiService.deleteProduct(product.id).then(loadProducts);
                              }
                            }}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Pagination */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing <span className="font-medium">{(pagination.currentPage - 1) * pagination.itemsPerPage + 1}</span> to{' '}
              <span className="font-medium">
                {Math.min(pagination.currentPage * pagination.itemsPerPage, pagination.totalItems)}
              </span>{' '}
              of <span className="font-medium">{pagination.totalItems}</span> products
            </div>
            
            <div className="flex items-center space-x-2">
              <select
                value={pagination.itemsPerPage}
                onChange={(e) => setPagination(prev => ({
                  ...prev,
                  itemsPerPage: Number(e.target.value),
                  currentPage: 1
                }))}
                className="border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="10">10 per page</option>
                <option value="25">25 per page</option>
                <option value="50">50 per page</option>
                <option value="100">100 per page</option>
              </select>
              
              <nav className="flex items-center">
                <button
                  onClick={() => handlePageChange(pagination.currentPage - 1)}
                  disabled={pagination.currentPage === 1}
                  className={`px-3 py-1 rounded-md ${
                    pagination.currentPage === 1
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Previous
                </button>
                
                <div className="flex items-center mx-2">
                  {Array.from({ length: pagination.totalPages }, (_, i) => i + 1)
                    .filter(pageNum => {
                      // Show first page, last page, and pages around current page
                      return (
                        pageNum === 1 ||
                        pageNum === pagination.totalPages ||
                        (pageNum >= pagination.currentPage - 2 && pageNum <= pagination.currentPage + 2)
                      );
                    })
                    .map((pageNum, index, array) => {
                      // Add ellipsis between non-consecutive pages
                      if (index > 0 && pageNum - array[index - 1] > 1) {
                        return (
                          <span key={`ellipsis-${pageNum}`} className="px-1">...</span>
                        );
                      }
                      
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`w-8 h-8 flex items-center justify-center rounded-md mx-1 ${
                            pagination.currentPage === pageNum
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                </div>
                
                <button
                  onClick={() => handlePageChange(pagination.currentPage + 1)}
                  disabled={pagination.currentPage === pagination.totalPages}
                  className={`px-3 py-1 rounded-md ${
                    pagination.currentPage === pagination.totalPages
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        </>
      )}
      
      {/* Add Product Modal */}
      {showAddProductModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">Add New Product</h2>
                <button
                  onClick={() => setShowAddProductModal(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <form onSubmit={handleAddProduct}>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">Product Name *</label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={newProduct.name}
                      onChange={handleNewProductChange}
                      required
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="sku" className="block text-sm font-medium text-gray-700 mb-1">SKU *</label>
                    <input
                      type="text"
                      id="sku"
                      name="sku"
                      value={newProduct.sku}
                      onChange={handleNewProductChange}
                      required
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="price" className="block text-sm font-medium text-gray-700 mb-1">Price *</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <span className="text-gray-500">$</span>
                        </div>
                        <input
                          type="number"
                          id="price"
                          name="price"
                          value={newProduct.price}
                          onChange={handleNewProductChange}
                          required
                          min="0"
                          step="0.01"
                          className="w-full border border-gray-300 rounded-md pl-7 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label htmlFor="cost" className="block text-sm font-medium text-gray-700 mb-1">Cost</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <span className="text-gray-500">$</span>
                        </div>
                        <input
                          type="number"
                          id="cost"
                          name="cost"
                          value={newProduct.cost}
                          onChange={handleNewProductChange}
                          min="0"
                          step="0.01"
                          className="w-full border border-gray-300 rounded-md pl-7 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                    <select
                      id="category"
                      name="category"
                      value={newProduct.category}
                      onChange={handleNewProductChange}
                      required
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Category</option>
                      {categories.map(category => (
                        <option key={category.id} value={category.id}>{category.name}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea
                      id="description"
                      name="description"
                      value={newProduct.description}
                      onChange={handleNewProductChange}
                      rows="4"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    ></textarea>
                  </div>
                  
                  {/* Inventory Section */}
                  <div className="border-t border-gray-200 pt-4 mt-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">Inventory</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-1">Initial Quantity</label>
                        <input
                          type="number"
                          id="quantity"
                          name="quantity"
                          value={newProduct.inventory.quantity}
                          onChange={handleInventoryChange}
                          min="0"
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="0"
                        />
                      </div>
                      
                      <div>
                        <label htmlFor="warehouse" className="block text-sm font-medium text-gray-700 mb-1">Warehouse Location</label>
                        <input
                          type="text"
                          id="warehouse"
                          name="warehouse"
                          value={newProduct.inventory.warehouse}
                          onChange={handleInventoryChange}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="Main Warehouse"
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                      <div>
                        <label htmlFor="reorderLevel" className="block text-sm font-medium text-gray-700 mb-1">Reorder Level</label>
                        <input
                          type="number"
                          id="reorderLevel"
                          name="reorderLevel"
                          value={newProduct.inventory.reorderLevel}
                          onChange={handleInventoryChange}
                          min="0"
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="10"
                        />
                      </div>
                      
                      <div className="flex items-center pt-6">
                        <input
                          type="checkbox"
                          id="lowStockAlert"
                          name="lowStockAlert"
                          checked={newProduct.inventory.lowStockAlert}
                          onChange={handleInventoryChange}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor="lowStockAlert" className="ml-2 block text-sm text-gray-700">
                          Enable low stock alerts
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Images</label>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {newProduct.images.map((image, index) => (
                        <div key={index} className="relative w-20 h-20">
                          <img
                            src={image}
                            alt={`Product ${index + 1}`}
                            className="w-full h-full object-cover rounded-md"
                          />
                          <button
                            type="button"
                            onClick={() => {
                              setNewProduct(prev => ({
                                ...prev,
                                images: prev.images.filter((_, i) => i !== index)
                              }));
                            }}
                            className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center"
                          >
                            &times;
                          </button>
                        </div>
                      ))}
                    </div>
                    <label className="block w-full border-2 border-dashed border-gray-300 rounded-md p-4 text-center cursor-pointer hover:bg-gray-50">
                      <span className="text-gray-600">Click to upload images</span>
                      <input
                        type="file"
                        accept="image/*"
                        multiple
                        onChange={handleImageUpload}
                        className="hidden"
                      />
                    </label>
                  </div>
                </div>
                
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowAddProductModal(false)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
                  >
                    Add Product
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

export default ProductManagement;
