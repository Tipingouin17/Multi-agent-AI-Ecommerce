import React from 'react';

/**
 * Step 5: Inventory & Logistics
 * 
 * Stock levels, warehouses, and shipping configuration
 */
const Step5InventoryLogistics = ({ formData, onChange, warehouses = [] }) => {
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    onChange({ ...formData, [name]: type === 'checkbox' ? checked : value });
  };

  const handleWarehouseInventory = (warehouseId, field, value) => {
    const warehouseInventory = formData.warehouse_inventory || {};
    const updatedInventory = {
      ...warehouseInventory,
      [warehouseId]: {
        ...(warehouseInventory[warehouseId] || {}),
        [field]: value
      }
    };
    onChange({ ...formData, warehouse_inventory: updatedInventory });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Inventory & Logistics</h3>
        <p className="text-sm text-gray-600">Stock levels, warehouses, and shipping configuration</p>
      </div>

      {/* Inventory Tracking */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Inventory Tracking</h4>
        
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="track_inventory"
              name="track_inventory"
              checked={formData.track_inventory !== false}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="track_inventory" className="ml-2 block text-sm text-gray-700">
              Track inventory for this product
            </label>
          </div>

          {formData.track_inventory !== false && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label htmlFor="low_stock_threshold" className="block text-sm font-medium text-gray-700 mb-1">
                    Low Stock Threshold
                  </label>
                  <input
                    type="number"
                    id="low_stock_threshold"
                    name="low_stock_threshold"
                    value={formData.low_stock_threshold || ''}
                    onChange={handleChange}
                    min="0"
                    placeholder="10"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Alert when stock falls below this number</p>
                </div>

                <div>
                  <label htmlFor="reorder_point" className="block text-sm font-medium text-gray-700 mb-1">
                    Reorder Point
                  </label>
                  <input
                    type="number"
                    id="reorder_point"
                    name="reorder_point"
                    value={formData.reorder_point || ''}
                    onChange={handleChange}
                    min="0"
                    placeholder="20"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Trigger reorder when stock reaches this level</p>
                </div>

                <div>
                  <label htmlFor="reorder_quantity" className="block text-sm font-medium text-gray-700 mb-1">
                    Reorder Quantity
                  </label>
                  <input
                    type="number"
                    id="reorder_quantity"
                    name="reorder_quantity"
                    value={formData.reorder_quantity || ''}
                    onChange={handleChange}
                    min="0"
                    placeholder="100"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Quantity to reorder automatically</p>
                </div>
              </div>

              <div className="flex items-center mt-4">
                <input
                  type="checkbox"
                  id="enable_low_stock_alerts"
                  name="enable_low_stock_alerts"
                  checked={formData.enable_low_stock_alerts || false}
                  onChange={handleChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="enable_low_stock_alerts" className="ml-2 block text-sm text-gray-700">
                  Enable low stock email alerts
                </label>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Warehouse Inventory */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Warehouse Inventory</h4>
        
        {warehouses && warehouses.length > 0 ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-600 mb-4">
              Set stock quantities for each warehouse location
            </p>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                      Warehouse
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                      Stock Quantity
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                      SKU (Optional)
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {warehouses.map((warehouse) => (
                    <tr key={warehouse.id}>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {warehouse.name}
                        <p className="text-xs text-gray-500">{warehouse.location}</p>
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          value={formData.warehouse_inventory?.[warehouse.id]?.quantity || ''}
                          onChange={(e) => handleWarehouseInventory(warehouse.id, 'quantity', e.target.value)}
                          min="0"
                          placeholder="0"
                          className="w-24 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={formData.warehouse_inventory?.[warehouse.id]?.sku || ''}
                          onChange={(e) => handleWarehouseInventory(warehouse.id, 'sku', e.target.value)}
                          placeholder="Optional"
                          className="w-32 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="mt-2 text-sm text-gray-600">No warehouses configured</p>
            <p className="text-xs text-gray-500">Add warehouses in the admin panel first</p>
          </div>
        )}
      </div>

      {/* Shipping Configuration */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Shipping Configuration</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="shipping_weight" className="block text-sm font-medium text-gray-700 mb-1">
              Shipping Weight (kg)
            </label>
            <input
              type="number"
              id="shipping_weight"
              name="shipping_weight"
              value={formData.shipping_weight || ''}
              onChange={handleChange}
              step="0.01"
              min="0"
              placeholder="0.00"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="handling_time" className="block text-sm font-medium text-gray-700 mb-1">
              Handling Time (days)
            </label>
            <input
              type="number"
              id="handling_time"
              name="handling_time"
              value={formData.handling_time || ''}
              onChange={handleChange}
              min="0"
              placeholder="1"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="md:col-span-2">
            <label htmlFor="fulfillment_method" className="block text-sm font-medium text-gray-700 mb-1">
              Fulfillment Method
            </label>
            <select
              id="fulfillment_method"
              name="fulfillment_method"
              value={formData.fulfillment_method || 'standard'}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="standard">Standard Shipping</option>
              <option value="express">Express Shipping</option>
              <option value="dropship">Dropshipping</option>
              <option value="fba">Fulfillment by Amazon (FBA)</option>
              <option value="local_pickup">Local Pickup Only</option>
            </select>
          </div>
        </div>

        <div className="mt-4 flex items-center">
          <input
            type="checkbox"
            id="free_shipping"
            name="free_shipping"
            checked={formData.free_shipping || false}
            onChange={handleChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="free_shipping" className="ml-2 block text-sm text-gray-700">
            Offer free shipping for this product
          </label>
        </div>
      </div>
    </div>
  );
};

export default Step5InventoryLogistics;
