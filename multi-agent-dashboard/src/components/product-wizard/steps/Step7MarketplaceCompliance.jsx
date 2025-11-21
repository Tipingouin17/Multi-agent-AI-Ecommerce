import React from 'react';

/**
 * Step 7: Marketplace & Compliance
 * 
 * Multi-channel publishing and regulatory compliance
 */
const Step7MarketplaceCompliance = ({ formData, onChange, marketplaces = [] }) => {
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    onChange({ ...formData, [name]: type === 'checkbox' ? checked : value });
  };

  const handleMarketplaceToggle = (marketplaceId) => {
    const selectedMarketplaces = formData.selected_marketplaces || [];
    const isSelected = selectedMarketplaces.includes(marketplaceId);
    
    const updated = isSelected
      ? selectedMarketplaces.filter(id => id !== marketplaceId)
      : [...selectedMarketplaces, marketplaceId];
    
    onChange({ ...formData, selected_marketplaces: updated });
  };

  const handleMarketplaceConfig = (marketplaceId, field, value) => {
    const marketplaceConfig = formData.marketplace_config || {};
    const updatedConfig = {
      ...marketplaceConfig,
      [marketplaceId]: {
        ...(marketplaceConfig[marketplaceId] || {}),
        [field]: value
      }
    };
    onChange({ ...formData, marketplace_config: updatedConfig });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Marketplace & Compliance</h3>
        <p className="text-sm text-gray-600">Multi-channel publishing and regulatory compliance</p>
      </div>

      {/* Marketplace Selection */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Marketplace Channels</h4>
        
        {marketplaces && marketplaces.length > 0 ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-600 mb-4">
              Select marketplaces where this product will be listed
            </p>
            
            {marketplaces.map((marketplace) => (
              <div key={marketplace.id} className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="flex items-start">
                  <input
                    type="checkbox"
                    id={`marketplace_${marketplace.id}`}
                    checked={formData.selected_marketplaces?.includes(marketplace.id) || false}
                    onChange={() => handleMarketplaceToggle(marketplace.id)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-1"
                  />
                  <div className="ml-3 flex-1">
                    <label htmlFor={`marketplace_${marketplace.id}`} className="font-medium text-gray-900 cursor-pointer">
                      {marketplace.name}
                    </label>
                    <p className="text-xs text-gray-500">{marketplace.description || 'List on this marketplace'}</p>
                    
                    {/* Marketplace-specific config */}
                    {formData.selected_marketplaces?.includes(marketplace.id) && (
                      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Marketplace SKU
                          </label>
                          <input
                            type="text"
                            value={formData.marketplace_config?.[marketplace.id]?.sku || ''}
                            onChange={(e) => handleMarketplaceConfig(marketplace.id, 'sku', e.target.value)}
                            placeholder="Optional custom SKU"
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Marketplace Price
                          </label>
                          <input
                            type="number"
                            value={formData.marketplace_config?.[marketplace.id]?.price || ''}
                            onChange={(e) => handleMarketplaceConfig(marketplace.id, 'price', e.target.value)}
                            step="0.01"
                            placeholder="Use base price"
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div className="md:col-span-2">
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Marketplace Category
                          </label>
                          <input
                            type="text"
                            value={formData.marketplace_config?.[marketplace.id]?.category || ''}
                            onChange={(e) => handleMarketplaceConfig(marketplace.id, 'category', e.target.value)}
                            placeholder="e.g., Electronics > Computers"
                            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p className="mt-2 text-sm text-gray-600">No marketplaces configured</p>
            <p className="text-xs text-gray-500">Configure marketplaces in the admin panel first</p>
          </div>
        )}
      </div>

      {/* Product Identifiers */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Product Identifiers</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="gtin" className="block text-sm font-medium text-gray-700 mb-1">
              GTIN (Global Trade Item Number)
            </label>
            <input
              type="text"
              id="gtin"
              name="gtin"
              value={formData.gtin || ''}
              onChange={handleChange}
              placeholder="e.g., 00012345678905"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="upc" className="block text-sm font-medium text-gray-700 mb-1">
              UPC (Universal Product Code)
            </label>
            <input
              type="text"
              id="upc"
              name="upc"
              value={formData.upc || ''}
              onChange={handleChange}
              placeholder="e.g., 123456789012"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="ean" className="block text-sm font-medium text-gray-700 mb-1">
              EAN (European Article Number)
            </label>
            <input
              type="text"
              id="ean"
              name="ean"
              value={formData.ean || ''}
              onChange={handleChange}
              placeholder="e.g., 1234567890123"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="isbn" className="block text-sm font-medium text-gray-700 mb-1">
              ISBN (for books)
            </label>
            <input
              type="text"
              id="isbn"
              name="isbn"
              value={formData.isbn || ''}
              onChange={handleChange}
              placeholder="e.g., 978-3-16-148410-0"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Compliance & Safety */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Compliance & Safety</h4>
        
        <div className="space-y-4">
          {/* Age Restrictions */}
          <div>
            <div className="flex items-center mb-2">
              <input
                type="checkbox"
                id="has_age_restriction"
                name="has_age_restriction"
                checked={formData.has_age_restriction || false}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="has_age_restriction" className="ml-2 block text-sm text-gray-700">
                This product has age restrictions
              </label>
            </div>
            
            {formData.has_age_restriction && (
              <div className="ml-6">
                <label htmlFor="min_age" className="block text-sm font-medium text-gray-700 mb-1">
                  Minimum Age
                </label>
                <select
                  id="min_age"
                  name="min_age"
                  value={formData.min_age || ''}
                  onChange={handleChange}
                  className="w-full md:w-1/3 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select age</option>
                  <option value="13">13+</option>
                  <option value="16">16+</option>
                  <option value="18">18+</option>
                  <option value="21">21+</option>
                </select>
              </div>
            )}
          </div>

          {/* Hazmat */}
          <div>
            <div className="flex items-center mb-2">
              <input
                type="checkbox"
                id="is_hazmat"
                name="is_hazmat"
                checked={formData.is_hazmat || false}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="is_hazmat" className="ml-2 block text-sm text-gray-700">
                This product is hazardous material (HAZMAT)
              </label>
            </div>
            
            {formData.is_hazmat && (
              <div className="ml-6">
                <label htmlFor="hazmat_class" className="block text-sm font-medium text-gray-700 mb-1">
                  HAZMAT Classification
                </label>
                <input
                  type="text"
                  id="hazmat_class"
                  name="hazmat_class"
                  value={formData.hazmat_class || ''}
                  onChange={handleChange}
                  placeholder="e.g., Class 3 - Flammable Liquids"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}
          </div>

          {/* Certifications */}
          <div>
            <label htmlFor="certifications" className="block text-sm font-medium text-gray-700 mb-1">
              Certifications
            </label>
            <textarea
              id="certifications"
              name="certifications"
              value={formData.certifications || ''}
              onChange={handleChange}
              rows="3"
              placeholder="e.g., CE, FCC, RoHS (one per line)"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Safety Warnings */}
          <div>
            <label htmlFor="safety_warnings" className="block text-sm font-medium text-gray-700 mb-1">
              Safety Warnings
            </label>
            <textarea
              id="safety_warnings"
              name="safety_warnings"
              value={formData.safety_warnings || ''}
              onChange={handleChange}
              rows="3"
              placeholder="e.g., Choking hazard, Keep away from children"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Export Restrictions */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="has_export_restrictions"
              name="has_export_restrictions"
              checked={formData.has_export_restrictions || false}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="has_export_restrictions" className="ml-2 block text-sm text-gray-700">
              This product has export restrictions
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Step7MarketplaceCompliance;
