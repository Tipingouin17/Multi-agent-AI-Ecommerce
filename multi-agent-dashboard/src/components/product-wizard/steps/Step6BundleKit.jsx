import React, { useState } from 'react';

/**
 * Step 6: Bundle & Kit Configuration
 * 
 * Product bundles and kit configurations
 */
const Step6BundleKit = ({ formData, onChange, availableProducts = [] }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    onChange({ ...formData, [name]: type === 'checkbox' ? checked : value });
  };

  const handleAddBundleProduct = (product) => {
    const bundleProducts = formData.bundle_products || [];
    const exists = bundleProducts.find(p => p.id === product.id);
    
    if (!exists) {
      const updatedBundle = [...bundleProducts, { ...product, quantity: 1, is_optional: false }];
      onChange({ ...formData, bundle_products: updatedBundle });
    }
  };

  const handleUpdateBundleProduct = (productId, field, value) => {
    const bundleProducts = formData.bundle_products || [];
    const updatedBundle = bundleProducts.map(p =>
      p.id === productId ? { ...p, [field]: value } : p
    );
    onChange({ ...formData, bundle_products: updatedBundle });
  };

  const handleRemoveBundleProduct = (productId) => {
    const bundleProducts = formData.bundle_products || [];
    const updatedBundle = bundleProducts.filter(p => p.id !== productId);
    onChange({ ...formData, bundle_products: updatedBundle });
  };

  const filteredProducts = availableProducts.filter(p =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const calculateBundlePrice = () => {
    if (!formData.bundle_products || formData.bundle_products.length === 0) return 0;
    
    return formData.bundle_products.reduce((total, product) => {
      return total + (parseFloat(product.price || 0) * parseInt(product.quantity || 1));
    }, 0).toFixed(2);
  };

  const bundlePrice = calculateBundlePrice();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Bundle & Kit Configuration</h3>
        <p className="text-sm text-gray-600">Create product bundles and kits</p>
      </div>

      {/* Bundle Settings */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Bundle Settings</h4>
        
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_bundle"
              name="is_bundle"
              checked={formData.is_bundle || false}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_bundle" className="ml-2 block text-sm text-gray-700">
              This product is a bundle
            </label>
          </div>

          {formData.is_bundle && (
            <>
              <div>
                <label htmlFor="bundle_type" className="block text-sm font-medium text-gray-700 mb-1">
                  Bundle Type
                </label>
                <select
                  id="bundle_type"
                  name="bundle_type"
                  value={formData.bundle_type || 'fixed'}
                  onChange={handleChange}
                  className="w-full md:w-1/2 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="fixed">Fixed Bundle - All items included</option>
                  <option value="flexible">Flexible Bundle - Customer can choose items</option>
                </select>
              </div>

              <div>
                <label htmlFor="bundle_pricing" className="block text-sm font-medium text-gray-700 mb-1">
                  Bundle Pricing
                </label>
                <select
                  id="bundle_pricing"
                  name="bundle_pricing"
                  value={formData.bundle_pricing || 'calculated'}
                  onChange={handleChange}
                  className="w-full md:w-1/2 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="calculated">Calculated - Sum of component prices</option>
                  <option value="fixed">Fixed Price - Custom bundle price</option>
                </select>
              </div>

              {formData.bundle_pricing === 'fixed' && (
                <div>
                  <label htmlFor="bundle_fixed_price" className="block text-sm font-medium text-gray-700 mb-1">
                    Bundle Price
                  </label>
                  <div className="relative w-full md:w-1/2">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <span className="text-gray-500">$</span>
                    </div>
                    <input
                      type="number"
                      id="bundle_fixed_price"
                      name="bundle_fixed_price"
                      value={formData.bundle_fixed_price || ''}
                      onChange={handleChange}
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      className="w-full border border-gray-300 rounded-md pl-7 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              )}

              <div>
                <label htmlFor="bundle_discount" className="block text-sm font-medium text-gray-700 mb-1">
                  Bundle Discount (%)
                </label>
                <input
                  type="number"
                  id="bundle_discount"
                  name="bundle_discount"
                  value={formData.bundle_discount || ''}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  max="100"
                  placeholder="0"
                  className="w-full md:w-1/2 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Discount applied to calculated bundle price</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Bundle Products */}
      {formData.is_bundle && (
        <div className="bg-gray-50 p-6 rounded-lg">
          <h4 className="text-md font-semibold text-gray-800 mb-4">Bundle Products</h4>
          
          {/* Product Search */}
          <div className="mb-4">
            <label htmlFor="product_search" className="block text-sm font-medium text-gray-700 mb-1">
              Add Products to Bundle
            </label>
            <input
              type="text"
              id="product_search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search products by name or SKU..."
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Search Results */}
          {searchTerm && filteredProducts.length > 0 && (
            <div className="mb-4 max-h-48 overflow-y-auto border border-gray-200 rounded-md">
              {filteredProducts.map((product) => (
                <div
                  key={product.id}
                  className="flex items-center justify-between p-3 hover:bg-gray-100 cursor-pointer"
                  onClick={() => handleAddBundleProduct(product)}
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{product.name}</p>
                    <p className="text-xs text-gray-500">SKU: {product.sku} | ${product.price}</p>
                  </div>
                  <button
                    type="button"
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                  >
                    Add
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Selected Bundle Products */}
          {formData.bundle_products && formData.bundle_products.length > 0 ? (
            <div className="space-y-3">
              <p className="text-sm font-medium text-gray-700">
                Bundle Components ({formData.bundle_products.length})
              </p>
              
              {formData.bundle_products.map((product) => (
                <div key={product.id} className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{product.name}</p>
                    <p className="text-xs text-gray-500">SKU: {product.sku} | ${product.price}</p>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-gray-600">Qty:</label>
                    <input
                      type="number"
                      value={product.quantity}
                      onChange={(e) => handleUpdateBundleProduct(product.id, 'quantity', e.target.value)}
                      min="1"
                      className="w-16 border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={product.is_optional}
                      onChange={(e) => handleUpdateBundleProduct(product.id, 'is_optional', e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label className="ml-2 text-xs text-gray-600">Optional</label>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveBundleProduct(product.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}

              {/* Bundle Price Summary */}
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-700">
                    {formData.bundle_pricing === 'calculated' ? 'Calculated Bundle Price' : 'Custom Bundle Price'}
                  </p>
                  <p className="text-xl font-bold text-blue-600">
                    ${formData.bundle_pricing === 'fixed' ? formData.bundle_fixed_price || '0.00' : bundlePrice}
                  </p>
                </div>
                {formData.bundle_discount > 0 && (
                  <p className="text-xs text-gray-600 mt-1">
                    After {formData.bundle_discount}% discount: ${(bundlePrice * (1 - formData.bundle_discount / 100)).toFixed(2)}
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              <p className="mt-2 text-sm text-gray-600">No products added to bundle yet</p>
              <p className="text-xs text-gray-500">Search and add products above</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Step6BundleKit;
