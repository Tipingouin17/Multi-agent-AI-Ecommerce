import React, { useEffect } from 'react';

/**
 * Step 4: Pricing & Costs
 * 
 * Pricing, costs, and profit margins
 */
const Step4PricingCosts = ({ formData, onChange }) => {
  const handleChange = (e) => {
    const { name, value } = e.target;
    onChange({ ...formData, [name]: value });
  };

  // Calculate profit margin automatically
  useEffect(() => {
    if (formData.price && formData.cost) {
      const price = parseFloat(formData.price);
      const cost = parseFloat(formData.cost);
      if (price > 0 && cost > 0) {
        const margin = ((price - cost) / price) * 100;
        onChange({ ...formData, profit_margin: margin.toFixed(2) });
      }
    }
  }, [formData.price, formData.cost]);

  const profitMargin = formData.profit_margin || 0;
  const profitAmount = formData.price && formData.cost 
    ? (parseFloat(formData.price) - parseFloat(formData.cost)).toFixed(2)
    : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Pricing & Costs</h3>
        <p className="text-sm text-gray-600">Pricing, costs, and profit margins</p>
      </div>

      {/* Base Pricing */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Base Pricing</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="price" className="block text-sm font-medium text-gray-700 mb-1">
              Selling Price *
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-gray-500">$</span>
              </div>
              <input
                type="number"
                id="price"
                name="price"
                value={formData.price || ''}
                onChange={handleChange}
                required
                step="0.01"
                min="0"
                placeholder="0.00"
                className="w-full border border-gray-300 rounded-md pl-7 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label htmlFor="cost" className="block text-sm font-medium text-gray-700 mb-1">
              Cost Price
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-gray-500">$</span>
              </div>
              <input
                type="number"
                id="cost"
                name="cost"
                value={formData.cost || ''}
                onChange={handleChange}
                step="0.01"
                min="0"
                placeholder="0.00"
                className="w-full border border-gray-300 rounded-md pl-7 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label htmlFor="compare_price" className="block text-sm font-medium text-gray-700 mb-1">
              Compare at Price (MSRP)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-gray-500">$</span>
              </div>
              <input
                type="number"
                id="compare_price"
                name="compare_price"
                value={formData.compare_price || ''}
                onChange={handleChange}
                step="0.01"
                min="0"
                placeholder="0.00"
                className="w-full border border-gray-300 rounded-md pl-7 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Original price for showing discounts</p>
          </div>

          <div>
            <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-1">
              Currency
            </label>
            <select
              id="currency"
              name="currency"
              value={formData.currency || 'USD'}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="USD">USD - US Dollar</option>
              <option value="EUR">EUR - Euro</option>
              <option value="GBP">GBP - British Pound</option>
              <option value="JPY">JPY - Japanese Yen</option>
              <option value="CAD">CAD - Canadian Dollar</option>
              <option value="AUD">AUD - Australian Dollar</option>
            </select>
          </div>
        </div>

        {/* Profit Margin Display */}
        {formData.price && formData.cost && (
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Profit Margin</p>
                <p className="text-2xl font-bold text-blue-600">{profitMargin}%</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-700">Profit Amount</p>
                <p className="text-2xl font-bold text-green-600">${profitAmount}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tax Configuration */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Tax Configuration</h4>
        
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="taxable"
              name="taxable"
              checked={formData.taxable || false}
              onChange={(e) => onChange({ ...formData, taxable: e.target.checked })}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="taxable" className="ml-2 block text-sm text-gray-700">
              This product is taxable
            </label>
          </div>

          {formData.taxable && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label htmlFor="tax_class" className="block text-sm font-medium text-gray-700 mb-1">
                  Tax Class
                </label>
                <select
                  id="tax_class"
                  name="tax_class"
                  value={formData.tax_class || 'standard'}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="standard">Standard Rate</option>
                  <option value="reduced">Reduced Rate</option>
                  <option value="zero">Zero Rate</option>
                </select>
              </div>

              <div>
                <label htmlFor="tax_rate" className="block text-sm font-medium text-gray-700 mb-1">
                  Tax Rate (%)
                </label>
                <input
                  type="number"
                  id="tax_rate"
                  name="tax_rate"
                  value={formData.tax_rate || ''}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  max="100"
                  placeholder="0.00"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bulk Pricing (Optional) */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Bulk Pricing (Optional)</h4>
        
        <div className="flex items-center mb-4">
          <input
            type="checkbox"
            id="enable_bulk_pricing"
            name="enable_bulk_pricing"
            checked={formData.enable_bulk_pricing || false}
            onChange={(e) => onChange({ ...formData, enable_bulk_pricing: e.target.checked })}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="enable_bulk_pricing" className="ml-2 block text-sm text-gray-700">
            Enable bulk pricing tiers
          </label>
        </div>

        {formData.enable_bulk_pricing && (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              Set discounted prices for bulk purchases
            </p>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Min Quantity
                </label>
                <input
                  type="number"
                  placeholder="10"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Max Quantity
                </label>
                <input
                  type="number"
                  placeholder="50"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Price
                </label>
                <input
                  type="number"
                  placeholder="0.00"
                  step="0.01"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Step4PricingCosts;
