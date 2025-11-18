import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Inventory Management
 * 
 * Interface for managing inventory across all warehouses,
 * including stock levels, transfers, and reordering.
 */
function InventoryManagement() {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    warehouse: '',
    stockStatus: '' // all, low, out
  });
  const [sort, setSort] = useState({ field: 'sku', direction: 'asc' });
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    itemsPerPage: 10
  });
  const [selectedItems, setSelectedItems] = useState([]);
  const [bulkActionMenuOpen, setBulkActionMenuOpen] = useState(false);
  const [categories, setCategories] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [transferData, setTransferData] = useState({
    items: [],
    sourceWarehouse: '',
    destinationWarehouse: '',
    quantities: {}
  });
  const [adjustData, setAdjustData] = useState({
    item: null,
    warehouse: '',
    quantity: 0,
    reason: 'damaged'
  });
  
  // Load inventory on component mount and when filters, sort, or pagination change
  useEffect(() => {
    loadInventory();
  }, [filters, sort, pagination.currentPage, pagination.itemsPerPage]);
  
  // Load categories and warehouses on component mount
  useEffect(() => {
    async function loadFilterOptions() {
      try {
        const categoriesData = await apiService.getProductCategories();
        setCategories(categoriesData.categories || categoriesData || []);
        
        const warehousesData = await apiService.getWarehouses();
        setWarehouses(warehousesData.warehouses || warehousesData || []);
      } catch (err) {
        console.error("Failed to load filter options:", err);
        // Set empty arrays on error
        setCategories([]);
        setWarehouses([]);
      }
    }
    
    loadFilterOptions();
  }, []);
  
  // Load inventory from API
  async function loadInventory() {
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
      
      const data = await apiService.getInventory(params);
      
      setInventory(data.inventory || []);
      setPagination({
        ...pagination,
        totalPages: data.totalPages || 1,
        totalItems: data.totalItems || 0
      });
      
      setError(null);
    } catch (err) {
      setError("Failed to load inventory: " + err.message);
      console.error(err);
      // Set empty array on error to prevent undefined errors
      setInventory([]);
    } finally {
      setLoading(false);
    }
  }
  
  // Handle search
  function handleSearch(e) {
    e.preventDefault();
    loadInventory();
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
  
  // Handle item selection
  function handleItemSelection(itemId) {
    setSelectedItems(prev => {
      if (prev.includes(itemId)) {
        return prev.filter(id => id !== itemId);
      } else {
        return [...prev, itemId];
      }
    });
  }
  
  // Handle select all items
  function handleSelectAllItems() {
    if (selectedItems.length === inventory.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(inventory.map(item => item.id));
    }
  }
  
  // Handle bulk action
  async function handleBulkAction(action) {
    if (selectedItems.length === 0) return;
    
    try {
      switch (action) {
        case 'transfer':
          // Open transfer modal with selected items
          setTransferData({
            items: selectedItems,
            sourceWarehouse: '',
            destinationWarehouse: '',
            quantities: {}
          });
          setShowTransferModal(true);
          break;
        case 'export':
          // Export inventory to CSV
          const csvData = await apiService.exportInventory(selectedItems);
          const blob = new Blob([csvData], { type: 'text/csv' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.setAttribute('hidden', '');
          a.setAttribute('href', url);
          a.setAttribute('download', `inventory-export-${new Date().toISOString().slice(0, 10)}.csv`);
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          break;
        case 'reorder':
          // Reorder selected items
          await apiService.bulkReorderItems(selectedItems);
          loadInventory();
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
  
  // Handle transfer modal input change
  function handleTransferInputChange(e) {
    const { name, value } = e.target;
    setTransferData(prev => ({
      ...prev,
      [name]: value
    }));
  }
  
  // Handle transfer quantity change
  function handleTransferQuantityChange(itemId, quantity) {
    setTransferData(prev => ({
      ...prev,
      quantities: {
        ...prev.quantities,
        [itemId]: parseInt(quantity, 10) || 0
      }
    }));
  }
  
  // Handle submit transfer
  async function handleSubmitTransfer(e) {
    e.preventDefault();
    
    try {
      await apiService.transferInventory({
        sourceWarehouseId: transferData.sourceWarehouse,
        destinationWarehouseId: transferData.destinationWarehouse,
        items: Object.entries(transferData.quantities).map(([itemId, quantity]) => ({
          itemId,
          quantity
        }))
      });
      
      setShowTransferModal(false);
      loadInventory();
    } catch (err) {
      setError(`Failed to transfer inventory: ${err.message}`);
      console.error(err);
    }
  }
  
  // Handle adjust modal input change
  function handleAdjustInputChange(e) {
    const { name, value } = e.target;
    setAdjustData(prev => ({
      ...prev,
      [name]: value
    }));
  }
  
  // Handle submit adjustment
  async function handleSubmitAdjustment(e) {
    e.preventDefault();
    
    try {
      await apiService.adjustInventory({
        itemId: adjustData.item.id,
        warehouseId: adjustData.warehouse,
        quantity: parseInt(adjustData.quantity, 10),
        reason: adjustData.reason
      });
      
      setShowAdjustModal(false);
      loadInventory();
    } catch (err) {
      setError(`Failed to adjust inventory: ${err.message}`);
      console.error(err);
    }
  }
  
  // Open adjust modal for an item
  function openAdjustModal(item) {
    setAdjustData({
      item,
      warehouse: item.warehouses[0]?.id || '',
      quantity: 0,
      reason: 'damaged'
    });
    setShowAdjustModal(true);
  }
  
  // Format currency
  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  }
  
  // Get stock status class
  function getStockStatusClass(quantity, threshold) {
    if (quantity <= 0) {
      return 'bg-red-100 text-red-800';
    } else if (quantity <= threshold) {
      return 'bg-yellow-100 text-yellow-800';
    } else {
      return 'bg-green-100 text-green-800';
    }
  }
  
  // Get stock status text
  function getStockStatusText(quantity, threshold) {
    if (quantity <= 0) {
      return 'Out of Stock';
    } else if (quantity <= threshold) {
      return 'Low Stock';
    } else {
      return 'In Stock';
    }
  }
  
  return (
    <div className="p-6">
      <div className="mb-6 flex flex-col md:flex-row md:justify-between md:items-center space-y-4 md:space-y-0">
        <h1 className="text-2xl font-bold text-gray-900">Inventory Management</h1>
        
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
          {selectedItems.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setBulkActionMenuOpen(!bulkActionMenuOpen)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
              >
                Actions ({selectedItems.length})
              </button>
              
              {bulkActionMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10">
                  <div className="py-1">
                    <button
                      onClick={() => handleBulkAction('transfer')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Transfer Items
                    </button>
                    <button
                      onClick={() => handleBulkAction('export')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Export to CSV
                    </button>
                    <button
                      onClick={() => handleBulkAction('reorder')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Reorder Items
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <Link
            to="/merchant/inventory/import"
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md"
          >
            Import Inventory
          </Link>
        </div>
      </div>
      
      {/* Search and Filters */}
      <div className="bg-white p-4 rounded-lg shadow-md mb-6">
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row md:items-end space-y-4 md:space-y-0 md:space-x-4">
          <div className="flex-1">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">Search Inventory</label>
            <input
              type="text"
              id="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by SKU, name, or barcode"
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
            <label htmlFor="warehouse" className="block text-sm font-medium text-gray-700 mb-1">Warehouse</label>
            <select
              id="warehouse"
              name="warehouse"
              value={filters.warehouse}
              onChange={handleFilterChange}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Warehouses</option>
              {warehouses.map(warehouse => (
                <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label htmlFor="stockStatus" className="block text-sm font-medium text-gray-700 mb-1">Stock Status</label>
            <select
              id="stockStatus"
              name="stockStatus"
              value={filters.stockStatus}
              onChange={handleFilterChange}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Stock Levels</option>
              <option value="low">Low Stock</option>
              <option value="out">Out of Stock</option>
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
            onClick={loadInventory}
            className="mt-2 bg-red-200 hover:bg-red-300 text-red-700 px-3 py-1 rounded"
          >
            Try Again
          </button>
        </div>
      )}
      
      {!loading && !error && (
        <>
          {/* Inventory Table */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden mb-6">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedItems.length === inventory.length && inventory.length > 0}
                          onChange={handleSelectAllItems}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </div>
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
                        onClick={() => handleSortChange('category')}
                        className="flex items-center focus:outline-none"
                      >
                        Category
                        {sort.field === 'category' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('totalStock')}
                        className="flex items-center focus:outline-none"
                      >
                        Total Stock
                        {sort.field === 'totalStock' && (
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
                      Warehouses
                    </th>
                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {inventory.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="px-6 py-4 text-center text-gray-500">
                        No inventory items found. Try adjusting your search or filters.
                      </td>
                    </tr>
                  ) : (
                    inventory.map(item => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedItems.includes(item.id)}
                            onChange={() => handleItemSelection(item.id)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {item.sku}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {item.image ? (
                              <img
                                src={item.image}
                                alt={item.name}
                                className="h-10 w-10 rounded-md object-cover mr-3"
                              />
                            ) : (
                              <div className="h-10 w-10 rounded-md bg-gray-200 flex items-center justify-center mr-3">
                                <span className="text-gray-500 text-xs">No img</span>
                              </div>
                            )}
                            <div>
                              <div className="font-medium text-gray-900">{item.name}</div>
                              <div className="text-sm text-gray-500">{formatCurrency(item.price)}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.category}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item.totalStock}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStockStatusClass(item.totalStock, item.lowStockThreshold)}`}>
                            {getStockStatusText(item.totalStock, item.lowStockThreshold)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex flex-col space-y-1">
                            {item.warehouses.map(warehouse => (
                              <div key={warehouse.id} className="flex justify-between">
                                <span>{warehouse.name}:</span>
                                <span className="font-medium">{warehouse.quantity}</span>
                              </div>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => openAdjustModal(item)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            Adjust
                          </button>
                          <Link
                            to={`/merchant/products/${item.productId}`}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            View Product
                          </Link>
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
              of <span className="font-medium">{pagination.totalItems}</span> items
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
      
      {/* Transfer Modal */}
      {showTransferModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">Transfer Inventory</h2>
                <button
                  onClick={() => setShowTransferModal(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <form onSubmit={handleSubmitTransfer}>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="sourceWarehouse" className="block text-sm font-medium text-gray-700 mb-1">Source Warehouse *</label>
                    <select
                      id="sourceWarehouse"
                      name="sourceWarehouse"
                      value={transferData.sourceWarehouse}
                      onChange={handleTransferInputChange}
                      required
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Source Warehouse</option>
                      {warehouses.map(warehouse => (
                        <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label htmlFor="destinationWarehouse" className="block text-sm font-medium text-gray-700 mb-1">Destination Warehouse *</label>
                    <select
                      id="destinationWarehouse"
                      name="destinationWarehouse"
                      value={transferData.destinationWarehouse}
                      onChange={handleTransferInputChange}
                      required
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Destination Warehouse</option>
                      {warehouses
                        .filter(warehouse => warehouse.id !== transferData.sourceWarehouse)
                        .map(warehouse => (
                          <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>
                        ))}
                    </select>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Items to Transfer</h3>
                    <div className="border border-gray-300 rounded-md overflow-hidden">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              SKU
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Product
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Available
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Quantity to Transfer
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {inventory
                            .filter(item => transferData.items.includes(item.id))
                            .map(item => {
                              const sourceWarehouse = item.warehouses.find(wh => wh.id === transferData.sourceWarehouse);
                              const availableQuantity = sourceWarehouse ? sourceWarehouse.quantity : 0;
                              
                              return (
                                <tr key={item.id}>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {item.sku}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {item.name}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {availableQuantity}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap">
                                    <input
                                      type="number"
                                      min="1"
                                      max={availableQuantity}
                                      value={transferData.quantities[item.id] || ''}
                                      onChange={(e) => handleTransferQuantityChange(item.id, e.target.value)}
                                      required
                                      className="w-20 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                  </td>
                                </tr>
                              );
                            })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowTransferModal(false)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
                  >
                    Transfer Items
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
      
      {/* Adjust Modal */}
      {showAdjustModal && adjustData.item && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">Adjust Inventory</h2>
                <button
                  onClick={() => setShowAdjustModal(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="mb-4">
                <div className="flex items-center mb-2">
                  {adjustData.item.image ? (
                    <img
                      src={adjustData.item.image}
                      alt={adjustData.item.name}
                      className="h-10 w-10 rounded-md object-cover mr-3"
                    />
                  ) : (
                    <div className="h-10 w-10 rounded-md bg-gray-200 flex items-center justify-center mr-3">
                      <span className="text-gray-500 text-xs">No img</span>
                    </div>
                  )}
                  <div>
                    <div className="font-medium text-gray-900">{adjustData.item.name}</div>
                    <div className="text-sm text-gray-500">SKU: {adjustData.item.sku}</div>
                  </div>
                </div>
              </div>
              
              <form onSubmit={handleSubmitAdjustment}>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="warehouse" className="block text-sm font-medium text-gray-700 mb-1">Warehouse *</label>
                    <select
                      id="warehouse"
                      name="warehouse"
                      value={adjustData.warehouse}
                      onChange={handleAdjustInputChange}
                      required
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Warehouse</option>
                      {adjustData.item.warehouses.map(warehouse => (
                        <option key={warehouse.id} value={warehouse.id}>
                          {warehouse.name} (Current: {warehouse.quantity})
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-1">Adjustment Quantity *</label>
                    <div className="flex items-center">
                      <select
                        className="border-r-0 rounded-r-none border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="add">Add</option>
                        <option value="subtract">Subtract</option>
                        <option value="set">Set to</option>
                      </select>
                      <input
                        type="number"
                        id="quantity"
                        name="quantity"
                        value={adjustData.quantity}
                        onChange={handleAdjustInputChange}
                        min="0"
                        required
                        className="flex-1 rounded-l-none border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-1">Reason *</label>
                    <select
                      id="reason"
                      name="reason"
                      value={adjustData.reason}
                      onChange={handleAdjustInputChange}
                      required
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="damaged">Damaged</option>
                      <option value="lost">Lost</option>
                      <option value="found">Found</option>
                      <option value="returned">Returned</option>
                      <option value="correction">Correction</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>
                
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowAdjustModal(false)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
                  >
                    Adjust Inventory
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

export default InventoryManagement;
