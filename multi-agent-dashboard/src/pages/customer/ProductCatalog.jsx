import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Product Catalog Page
 * 
 * Displays a filterable, searchable catalog of all products
 * with sorting, filtering, and pagination.
 */
function ProductCatalog() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalProducts, setTotalProducts] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filtersOpen, setFiltersOpen] = useState(false);
  
  // Get query parameters
  const query = searchParams.get('query') || '';
  const category = searchParams.get('category') || '';
  const sort = searchParams.get('sort') || 'popular';
  const minPrice = searchParams.get('minPrice') || '';
  const maxPrice = searchParams.get('maxPrice') || '';
  const page = parseInt(searchParams.get('page') || '1');
  
  // Load products on component mount and when filters change
  useEffect(() => {
    loadProducts();
  }, [query, category, sort, minPrice, maxPrice, page]);
  
  // Load categories on component mount
  useEffect(() => {
    loadCategories();
  }, []);
  
  // Load products from API
  async function loadProducts() {
    try {
      setLoading(true);
      
      const filters = {
        query,
        category,
        sort,
        minPrice: minPrice ? parseFloat(minPrice) : undefined,
        maxPrice: maxPrice ? parseFloat(maxPrice) : undefined,
        page,
        limit: 20
      };
      
      const data = await apiService.getProducts(filters);
      
      setProducts(data.products);
      setTotalProducts(data.total);
      setTotalPages(data.totalPages);
      setCurrentPage(data.currentPage);
      setError(null);
    } catch (err) {
      setError("Failed to load products: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Load categories from API
  async function loadCategories() {
    try {
      const data = await apiService.getCategories();
      setCategories(data.categories || data || []);
    } catch (err) {
      console.error("Failed to load categories:", err);
    }
  }
  
  // Handle search form submission
  function handleSearch(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const newQuery = formData.get('query');
    
    const newParams = new URLSearchParams(searchParams);
    if (newQuery) {
      newParams.set('query', newQuery);
    } else {
      newParams.delete('query');
    }
    newParams.set('page', '1'); // Reset to first page on new search
    setSearchParams(newParams);
  }
  
  // Handle filter changes
  function handleFilterChange(name, value) {
    const newParams = new URLSearchParams(searchParams);
    
    if (value) {
      newParams.set(name, value);
    } else {
      newParams.delete(name);
    }
    
    newParams.set('page', '1'); // Reset to first page on filter change
    setSearchParams(newParams);
  }
  
  // Handle sort change
  function handleSortChange(e) {
    handleFilterChange('sort', e.target.value);
  }
  
  // Handle pagination
  function handlePageChange(newPage) {
    if (newPage < 1 || newPage > totalPages) return;
    
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', newPage.toString());
    setSearchParams(newParams);
    
    // Scroll to top of product list
    window.scrollTo({
      top: document.getElementById('product-list').offsetTop - 100,
      behavior: 'smooth'
    });
  }
  
  // Clear all filters
  function clearFilters() {
    setSearchParams({});
  }
  
  // Render loading state
  if (loading && products.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-12 bg-gray-200 rounded mb-8 w-1/3"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="bg-white p-4 rounded-lg shadow">
                  <div className="h-40 bg-gray-200 rounded-lg mb-4"></div>
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Search and Sort Bar */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative flex gap-2">
                <div className="relative flex-1">
                  <input
                    type="text"
                    name="query"
                    placeholder="Search products..."
                    defaultValue={query}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                  </div>
                </div>
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 whitespace-nowrap"
                >
                  Search
                </button>
              </div>
            </form>
            
            <div className="flex items-center gap-2">
              <label htmlFor="sort" className="text-sm font-medium text-gray-700 whitespace-nowrap">
                Sort by:
              </label>
              <select
                id="sort"
                value={sort}
                onChange={handleSortChange}
                className="border border-gray-300 rounded-lg py-2 pl-3 pr-10 text-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="popular">Most Popular</option>
                <option value="newest">Newest</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="rating">Highest Rated</option>
              </select>
              
              <button
                type="button"
                onClick={( ) => setFiltersOpen(!filtersOpen)}
                className="md:hidden bg-gray-100 p-2 rounded-lg"
              >
                <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path>
                </svg>
              </button>
            </div>
          </div>
          
          {/* Mobile Filters */}
          {filtersOpen && (
            <div className="mt-4 md:hidden border-t pt-4">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e ) => handleFilterChange('category', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg py-2 pl-3 pr-10 text-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Categories</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Price Range
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={minPrice}
                    onChange={(e) => handleFilterChange('minPrice', e.target.value)}
                    className="w-full border border-gray-300 rounded-lg py-2 px-3 text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                  <span className="text-gray-500">to</span>
                  <input
                    type="number"
                    placeholder="Max"
                    value={maxPrice}
                    onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
                    className="w-full border border-gray-300 rounded-lg py-2 px-3 text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              {(query || category || minPrice || maxPrice) && (
                <button
                  onClick={clearFilters}
                  className="w-full bg-gray-100 hover:bg-gray-200 text-gray-800 py-2 px-4 rounded-lg text-sm"
                >
                  Clear All Filters
                </button>
              )}
            </div>
          )}
        </div>
        
        <div className="flex flex-col md:flex-row gap-6">
          {/* Desktop Filters Sidebar */}
          <div className="hidden md:block w-64 flex-shrink-0">
            <div className="bg-white p-4 rounded-lg shadow sticky top-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Filters</h3>
              
              <div className="mb-6">
                <h4 className="font-medium text-gray-700 mb-2">Category</h4>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <input
                      id="category-all"
                      type="radio"
                      name="category"
                      checked={!category}
                      onChange={() => handleFilterChange('category', '')}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <label htmlFor="category-all" className="ml-2 text-sm text-gray-700">
                      All Categories
                    </label>
                  </div>
                  
                  {categories.map(cat => (
                    <div key={cat.id} className="flex items-center">
                      <input
                        id={`category-${cat.id}`}
                        type="radio"
                        name="category"
                        checked={category === cat.id}
                        onChange={() => handleFilterChange('category', cat.id)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                      />
                      <label htmlFor={`category-${cat.id}`} className="ml-2 text-sm text-gray-700">
                        {cat.name}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="mb-6">
                <h4 className="font-medium text-gray-700 mb-2">Price Range</h4>
                <div className="space-y-2">
                  <input
                    type="number"
                    placeholder="Min Price"
                    value={minPrice}
                    onChange={(e) => handleFilterChange('minPrice', e.target.value)}
                    className="w-full border border-gray-300 rounded-lg py-2 px-3 text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                  <input
                    type="number"
                    placeholder="Max Price"
                    value={maxPrice}
                    onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
                    className="w-full border border-gray-300 rounded-lg py-2 px-3 text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              {(query || category || minPrice || maxPrice) && (
                <button
                  onClick={clearFilters}
                  className="w-full bg-gray-100 hover:bg-gray-200 text-gray-800 py-2 px-4 rounded-lg text-sm"
                >
                  Clear All Filters
                </button>
              )}
            </div>
          </div>
          
          {/* Product Grid */}
          <div className="flex-1" id="product-list">
            {/* Results Summary */}
            <div className="mb-4">
              <h1 className="text-2xl font-bold text-gray-900">
                {query ? `Search results for "${query}"` : 'All Products'}
              </h1>
              <p className="text-sm text-gray-600">
                {totalProducts} {totalProducts === 1 ? 'product' : 'products'} found
              </p>
            </div>
            
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-6">
                <p>{error}</p>
                <button 
                  onClick={loadProducts} 
                  className="mt-2 bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded"
                >
                  Try Again
                </button>
              </div>
            )}
            
            {/* No Results */}
            {!loading && products.length === 0 && !error && (
              <div className="bg-white p-8 rounded-lg shadow text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <h3 className="mt-2 text-lg font-medium text-gray-900">No products found</h3>
                <p className="mt-1 text-gray-500">
                  Try adjusting your search or filter criteria.
                </p>
                <button
                  onClick={clearFilters}
                  className="mt-4 bg-blue-100 hover:bg-blue-200 text-blue-700 py-2 px-4 rounded-lg text-sm"
                >
                  Clear All Filters
                </button>
              </div>
             )}
            
            {/* Product Grid */}
            {products.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {products.map(product => (
                  <Link 
                    key={product.id} 
                    to={`/products/${product.id}`}
                    className="bg-white rounded-lg shadow overflow-hidden hover:shadow-md transition-shadow"
                  >
                    <div className="h-48 overflow-hidden">
                      <img 
                        src={product.image_url} 
                        alt={product.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="p-4">
                      <h3 className="text-lg font-medium text-gray-900 mb-1">{product.name}</h3>
                      <div className="flex justify-between items-center">
                        <span className="text-lg font-bold text-gray-900">${product.price.toFixed(2)}</span>
                        {product.rating && (
                          <div className="flex items-center">
                            <span className="text-yellow-400">★</span>
                            <span className="ml-1 text-sm text-gray-600">{product.rating}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 flex justify-center">
                <nav className="flex items-center space-x-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className={`px-3 py-1 rounded-md ${
                      currentPage === 1 
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Previous
                  </button>
                  
                  {[...Array(totalPages)].map((_, i) => {
                    const pageNum = i + 1;
                    // Show first page, last page, current page, and pages around current page
                    if (
                      pageNum === 1 || 
                      pageNum === totalPages || 
                      (pageNum >= currentPage - 2 && pageNum <= currentPage + 2)
                    ) {
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`px-3 py-1 rounded-md ${
                            currentPage === pageNum
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    } else if (
                      (pageNum === currentPage - 3 && currentPage > 4) || 
                      (pageNum === currentPage + 3 && currentPage < totalPages - 3)
                    ) {
                      return <span key={pageNum} className="px-1">...</span>;
                    }
                    return null;
                  })}
                  
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className={`px-3 py-1 rounded-md ${
                      currentPage === totalPages 
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Next
                  </button>
                </nav>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductCatalog;
