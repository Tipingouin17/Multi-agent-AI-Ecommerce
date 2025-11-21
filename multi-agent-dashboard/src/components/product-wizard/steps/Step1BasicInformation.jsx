import React, { useState } from 'react';

/**
 * Step 1: Basic Information
 * 
 * Product name, SKU, category, and core details
 */
const Step1BasicInformation = ({ formData, onChange, categories }) => {
  const [keyFeature, setKeyFeature] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    onChange({ ...formData, [name]: value });
  };

  const handleGenerateSKU = () => {
    const timestamp = Date.now().toString().slice(-6);
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    const category = formData.category ? formData.category.substring(0, 3).toUpperCase() : 'PRD';
    const generatedSKU = `${category}-${timestamp}-${random}`;
    onChange({ ...formData, sku: generatedSKU });
  };

  const handleAddKeyFeature = () => {
    if (keyFeature.trim()) {
      const updatedFeatures = [...(formData.key_features || []), keyFeature.trim()];
      onChange({ ...formData, key_features: updatedFeatures });
      setKeyFeature('');
    }
  };

  const handleRemoveKeyFeature = (index) => {
    const updatedFeatures = formData.key_features.filter((_, i) => i !== index);
    onChange({ ...formData, key_features: updatedFeatures });
  };

  const productTypes = [
    { value: 'simple', label: 'Simple Product' },
    { value: 'variable', label: 'Variable Product' },
    { value: 'grouped', label: 'Grouped Product' },
    { value: 'external', label: 'External/Affiliate Product' }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Basic Information</h3>
        <p className="text-sm text-gray-600">Product name, SKU, category, and core details</p>
      </div>

      {/* Product Identity Section */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Product Identity</h4>
        
        <div className="space-y-4">
          {/* Product Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Product Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name || ''}
              onChange={handleChange}
              required
              placeholder="Enter product name"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Display Name */}
          <div>
            <label htmlFor="display_name" className="block text-sm font-medium text-gray-700 mb-1">
              Display Name
            </label>
            <input
              type="text"
              id="display_name"
              name="display_name"
              value={formData.display_name || ''}
              onChange={handleChange}
              placeholder="Display name (optional)"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">Alternative name for marketplace listings</p>
          </div>

          {/* SKU */}
          <div>
            <label htmlFor="sku" className="block text-sm font-medium text-gray-700 mb-1">
              SKU *
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                id="sku"
                name="sku"
                value={formData.sku || ''}
                onChange={handleChange}
                required
                placeholder="Product SKU"
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={handleGenerateSKU}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-md font-medium transition-colors"
              >
                Generate
              </button>
            </div>
          </div>

          {/* Category */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
              Category *
            </label>
            <select
              id="category"
              name="category"
              value={formData.category || ''}
              onChange={handleChange}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select category</option>
              {categories && categories.map((cat) => (
                <option key={cat.id || cat} value={cat.name || cat}>
                  {cat.name || cat}
                </option>
              ))}
            </select>
          </div>

          {/* Product Type */}
          <div>
            <label htmlFor="product_type" className="block text-sm font-medium text-gray-700 mb-1">
              Product Type
            </label>
            <select
              id="product_type"
              name="product_type"
              value={formData.product_type || 'simple'}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {productTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Brand */}
          <div>
            <label htmlFor="brand" className="block text-sm font-medium text-gray-700 mb-1">
              Brand
            </label>
            <input
              type="text"
              id="brand"
              name="brand"
              value={formData.brand || ''}
              onChange={handleChange}
              placeholder="Product brand"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Model Number */}
          <div>
            <label htmlFor="model_number" className="block text-sm font-medium text-gray-700 mb-1">
              Model Number
            </label>
            <input
              type="text"
              id="model_number"
              name="model_number"
              value={formData.model_number || ''}
              onChange={handleChange}
              placeholder="Model number"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Product Description Section */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Product Description</h4>
        
        <div className="space-y-4">
          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description *
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description || ''}
              onChange={handleChange}
              required
              rows="6"
              placeholder="Enter detailed product description"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Key Features */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Key Features
            </label>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={keyFeature}
                onChange={(e) => setKeyFeature(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddKeyFeature())}
                placeholder="Add a key feature"
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={handleAddKeyFeature}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md font-medium transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>

            {/* Features List */}
            {formData.key_features && formData.key_features.length > 0 && (
              <ul className="space-y-2">
                {formData.key_features.map((feature, index) => (
                  <li
                    key={index}
                    className="flex items-center justify-between bg-white border border-gray-200 rounded-md px-3 py-2"
                  >
                    <span className="text-sm text-gray-700">{feature}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveKeyFeature(index)}
                      className="text-red-500 hover:text-red-700 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Step1BasicInformation;
