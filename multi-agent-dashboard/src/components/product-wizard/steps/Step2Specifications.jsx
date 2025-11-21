import React, { useState } from 'react';

/**
 * Step 2: Specifications
 * 
 * Technical specifications and product attributes
 */
const Step2Specifications = ({ formData, onChange }) => {
  const [specName, setSpecName] = useState('');
  const [specValue, setSpecValue] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    onChange({ ...formData, [name]: value });
  };

  const handleAddSpecification = () => {
    if (specName.trim() && specValue.trim()) {
      const updatedSpecs = {
        ...(formData.specifications || {}),
        [specName.trim()]: specValue.trim()
      };
      onChange({ ...formData, specifications: updatedSpecs });
      setSpecName('');
      setSpecValue('');
    }
  };

  const handleRemoveSpecification = (key) => {
    const updatedSpecs = { ...formData.specifications };
    delete updatedSpecs[key];
    onChange({ ...formData, specifications: updatedSpecs });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Specifications</h3>
        <p className="text-sm text-gray-600">Technical specifications and product attributes</p>
      </div>

      {/* Physical Dimensions */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Physical Dimensions</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="length" className="block text-sm font-medium text-gray-700 mb-1">
              Length (cm)
            </label>
            <input
              type="number"
              id="length"
              name="length"
              value={formData.length || ''}
              onChange={handleChange}
              step="0.01"
              placeholder="0.00"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="width" className="block text-sm font-medium text-gray-700 mb-1">
              Width (cm)
            </label>
            <input
              type="number"
              id="width"
              name="width"
              value={formData.width || ''}
              onChange={handleChange}
              step="0.01"
              placeholder="0.00"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="height" className="block text-sm font-medium text-gray-700 mb-1">
              Height (cm)
            </label>
            <input
              type="number"
              id="height"
              name="height"
              value={formData.height || ''}
              onChange={handleChange}
              step="0.01"
              placeholder="0.00"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="mt-4">
          <label htmlFor="weight" className="block text-sm font-medium text-gray-700 mb-1">
            Weight (kg)
          </label>
          <input
            type="number"
            id="weight"
            name="weight"
            value={formData.weight || ''}
            onChange={handleChange}
            step="0.01"
            placeholder="0.00"
            className="w-full md:w-1/3 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Product Attributes */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Product Attributes</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="material" className="block text-sm font-medium text-gray-700 mb-1">
              Material
            </label>
            <input
              type="text"
              id="material"
              name="material"
              value={formData.material || ''}
              onChange={handleChange}
              placeholder="e.g., Aluminum, Plastic, Wood"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="color" className="block text-sm font-medium text-gray-700 mb-1">
              Color
            </label>
            <input
              type="text"
              id="color"
              name="color"
              value={formData.color || ''}
              onChange={handleChange}
              placeholder="e.g., Black, White, Red"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="warranty" className="block text-sm font-medium text-gray-700 mb-1">
              Warranty Period
            </label>
            <input
              type="text"
              id="warranty"
              name="warranty"
              value={formData.warranty || ''}
              onChange={handleChange}
              placeholder="e.g., 1 year, 2 years"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="country_of_origin" className="block text-sm font-medium text-gray-700 mb-1">
              Country of Origin
            </label>
            <input
              type="text"
              id="country_of_origin"
              name="country_of_origin"
              value={formData.country_of_origin || ''}
              onChange={handleChange}
              placeholder="e.g., USA, China, Germany"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Custom Specifications */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-md font-semibold text-gray-800 mb-4">Custom Specifications</h4>
        
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="spec_name" className="block text-sm font-medium text-gray-700 mb-1">
                Specification Name
              </label>
              <input
                type="text"
                id="spec_name"
                value={specName}
                onChange={(e) => setSpecName(e.target.value)}
                placeholder="e.g., Battery Life, Screen Size"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="spec_value" className="block text-sm font-medium text-gray-700 mb-1">
                Value
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  id="spec_value"
                  value={specValue}
                  onChange={(e) => setSpecValue(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSpecification())}
                  placeholder="e.g., 10 hours, 15.6 inches"
                  className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="button"
                  onClick={handleAddSpecification}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md font-medium transition-colors"
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          {/* Specifications List */}
          {formData.specifications && Object.keys(formData.specifications).length > 0 && (
            <div className="mt-4">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      Specification
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                      Value
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-700 uppercase">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(formData.specifications).map(([key, value]) => (
                    <tr key={key}>
                      <td className="px-4 py-2 text-sm text-gray-900">{key}</td>
                      <td className="px-4 py-2 text-sm text-gray-700">{value}</td>
                      <td className="px-4 py-2 text-right">
                        <button
                          type="button"
                          onClick={() => handleRemoveSpecification(key)}
                          className="text-red-500 hover:text-red-700 transition-colors"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Step2Specifications;
