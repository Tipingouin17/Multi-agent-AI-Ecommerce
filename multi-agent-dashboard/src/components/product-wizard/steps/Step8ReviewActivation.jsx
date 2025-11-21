import React from 'react';

/**
 * Step 8: Review & Activation
 * 
 * Final review and product activation
 */
const Step8ReviewActivation = ({ formData, onChange }) => {
  const handleChange = (e) => {
    const { name, value } = e.target;
    onChange({ ...formData, [name]: value });
  };

  const renderSection = (title, data) => {
    if (!data || Object.keys(data).length === 0) return null;
    
    return (
      <div className="mb-6">
        <h5 className="text-sm font-semibold text-gray-800 mb-2">{title}</h5>
        <div className="space-y-1">
          {Object.entries(data).map(([key, value]) => {
            if (value === null || value === undefined || value === '') return null;
            if (typeof value === 'object') return null; // Skip complex objects
            
            return (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}:</span>
                <span className="text-gray-900 font-medium">{String(value)}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const getCompletionStatus = () => {
    const requiredFields = ['name', 'sku', 'category', 'description', 'price'];
    const missingFields = requiredFields.filter(field => !formData[field]);
    return {
      complete: missingFields.length === 0,
      missing: missingFields
    };
  };

  const status = getCompletionStatus();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Review & Activation</h3>
        <p className="text-sm text-gray-600">Review all product information and publish</p>
      </div>

      {/* Validation Status */}
      <div className={`p-4 rounded-lg border-2 ${
        status.complete 
          ? 'bg-green-50 border-green-200' 
          : 'bg-yellow-50 border-yellow-200'
      }`}>
        <div className="flex items-start">
          {status.complete ? (
            <svg className="w-6 h-6 text-green-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : (
            <svg className="w-6 h-6 text-yellow-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
          <div className="ml-3">
            <h4 className={`text-sm font-semibold ${
              status.complete ? 'text-green-800' : 'text-yellow-800'
            }`}>
              {status.complete ? 'Product is ready to publish' : 'Missing required information'}
            </h4>
            {!status.complete && (
              <p className="text-sm text-yellow-700 mt-1">
                Please complete the following fields: {status.missing.join(', ')}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Product Summary */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Product Summary</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Basic Information */}
          <div>
            {renderSection('Basic Information', {
              name: formData.name,
              display_name: formData.display_name,
              sku: formData.sku,
              category: formData.category,
              brand: formData.brand,
              model_number: formData.model_number,
              product_type: formData.product_type
            })}
          </div>

          {/* Pricing */}
          <div>
            {renderSection('Pricing', {
              price: formData.price ? `$${formData.price}` : null,
              cost: formData.cost ? `$${formData.cost}` : null,
              compare_price: formData.compare_price ? `$${formData.compare_price}` : null,
              profit_margin: formData.profit_margin ? `${formData.profit_margin}%` : null,
              currency: formData.currency
            })}
          </div>

          {/* Specifications */}
          {(formData.length || formData.width || formData.height || formData.weight) && (
            <div>
              {renderSection('Dimensions & Weight', {
                length: formData.length ? `${formData.length} cm` : null,
                width: formData.width ? `${formData.width} cm` : null,
                height: formData.height ? `${formData.height} cm` : null,
                weight: formData.weight ? `${formData.weight} kg` : null
              })}
            </div>
          )}

          {/* Inventory */}
          <div>
            {renderSection('Inventory', {
              track_inventory: formData.track_inventory ? 'Yes' : 'No',
              low_stock_threshold: formData.low_stock_threshold,
              reorder_point: formData.reorder_point,
              reorder_quantity: formData.reorder_quantity
            })}
          </div>
        </div>

        {/* Description */}
        {formData.description && (
          <div className="mt-6">
            <h5 className="text-sm font-semibold text-gray-800 mb-2">Description</h5>
            <p className="text-sm text-gray-700 bg-white p-3 rounded border border-gray-200">
              {formData.description}
            </p>
          </div>
        )}

        {/* Key Features */}
        {formData.key_features && formData.key_features.length > 0 && (
          <div className="mt-6">
            <h5 className="text-sm font-semibold text-gray-800 mb-2">Key Features</h5>
            <ul className="list-disc list-inside space-y-1">
              {formData.key_features.map((feature, index) => (
                <li key={index} className="text-sm text-gray-700">{feature}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Images */}
        {formData.images && formData.images.length > 0 && (
          <div className="mt-6">
            <h5 className="text-sm font-semibold text-gray-800 mb-2">
              Product Images ({formData.images.length})
            </h5>
            <div className="flex gap-2 overflow-x-auto">
              {formData.images.map((image, index) => (
                <img
                  key={index}
                  src={image}
                  alt={`Product ${index + 1}`}
                  className="w-20 h-20 object-cover rounded border border-gray-200"
                />
              ))}
            </div>
          </div>
        )}

        {/* Marketplaces */}
        {formData.selected_marketplaces && formData.selected_marketplaces.length > 0 && (
          <div className="mt-6">
            <h5 className="text-sm font-semibold text-gray-800 mb-2">
              Selected Marketplaces ({formData.selected_marketplaces.length})
            </h5>
            <p className="text-sm text-gray-700">
              Product will be listed on {formData.selected_marketplaces.length} marketplace(s)
            </p>
          </div>
        )}
      </div>

      {/* Activation Options */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Activation Options</h4>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="publish_status" className="block text-sm font-medium text-gray-700 mb-2">
              Publishing Status
            </label>
            <select
              id="publish_status"
              name="publish_status"
              value={formData.publish_status || 'draft'}
              onChange={handleChange}
              className="w-full md:w-1/2 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="draft">Save as Draft</option>
              <option value="active">Publish Immediately</option>
              <option value="scheduled">Schedule Publishing</option>
            </select>
          </div>

          {formData.publish_status === 'scheduled' && (
            <div>
              <label htmlFor="publish_date" className="block text-sm font-medium text-gray-700 mb-1">
                Publish Date & Time
              </label>
              <input
                type="datetime-local"
                id="publish_date"
                name="publish_date"
                value={formData.publish_date || ''}
                onChange={handleChange}
                className="w-full md:w-1/2 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <div className="flex items-center">
            <input
              type="checkbox"
              id="notify_subscribers"
              name="notify_subscribers"
              checked={formData.notify_subscribers || false}
              onChange={(e) => onChange({ ...formData, notify_subscribers: e.target.checked })}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="notify_subscribers" className="ml-2 block text-sm text-gray-700">
              Notify subscribers about this new product
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="feature_product"
              name="feature_product"
              checked={formData.feature_product || false}
              onChange={(e) => onChange({ ...formData, feature_product: e.target.checked })}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="feature_product" className="ml-2 block text-sm text-gray-700">
              Feature this product on homepage
            </label>
          </div>
        </div>
      </div>

      {/* Final Notes */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="ml-3">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Once published, this product will be visible to customers and available for purchase. 
              You can edit or unpublish it at any time from the Products page.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Step8ReviewActivation;
