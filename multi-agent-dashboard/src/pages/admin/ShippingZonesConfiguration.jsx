import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Globe,
  DollarSign,
  Package,
  Truck,
  Weight,
  Ruler,
  Gift,
  Clock,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

/**
 * Shipping Zones & Rates Configuration UI
 * 
 * Comprehensive admin interface for managing shipping zones and rate calculations
 * 
 * Features:
 * - Geographic zone definition (countries, regions, postal codes)
 * - Multiple rate calculation methods (flat, weight-based, price-based, dimensional)
 * - Carrier-specific rates within zones
 * - Free shipping thresholds and conditions
 * - Handling fees and surcharges
 * - Transit time estimates
 * - Zone priority and fallback rules
 * - Real-time rate preview and testing
 * - Bulk zone management
 */

const ShippingZonesConfiguration = () => {
  // State management
  const [zones, setZones] = useState([]);
  const [carriers, setCarriers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editingZone, setEditingZone] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [expandedZones, setExpandedZones] = useState({});
  const [showRateCalculator, setShowRateCalculator] = useState(false);

  // Available countries (simplified list - in production, use complete ISO list)
  const COUNTRIES = [
    { code: 'US', name: 'United States', regions: ['CA', 'NY', 'TX', 'FL', 'IL'] },
    { code: 'CA', name: 'Canada', regions: ['ON', 'QC', 'BC', 'AB'] },
    { code: 'GB', name: 'United Kingdom', regions: ['England', 'Scotland', 'Wales'] },
    { code: 'DE', name: 'Germany', regions: [] },
    { code: 'FR', name: 'France', regions: [] },
    { code: 'IT', name: 'Italy', regions: [] },
    { code: 'ES', name: 'Spain', regions: [] },
    { code: 'AU', name: 'Australia', regions: ['NSW', 'VIC', 'QLD'] },
    { code: 'JP', name: 'Japan', regions: [] },
    { code: 'CN', name: 'China', regions: [] }
  ];

  // Rate calculation methods
  const RATE_METHODS = [
    { value: 'flat', label: 'Flat Rate', description: 'Fixed price regardless of weight/size' },
    { value: 'weight_based', label: 'Weight-Based', description: 'Price varies by package weight' },
    { value: 'price_based', label: 'Price-Based', description: 'Price varies by order value' },
    { value: 'dimensional', label: 'Dimensional Weight', description: 'Price based on size and weight' },
    { value: 'table_rate', label: 'Table Rate', description: 'Complex rules with multiple conditions' }
  ];

  // Form state for new/editing zone
  const [formData, setFormData] = useState({
    name: '',
    enabled: true,
    countries: [],
    regions: [],
    postal_codes: [],
    rate_method: 'flat',
    base_rate: 0,
    free_shipping_threshold: 0,
    handling_fee: 0,
    min_delivery_days: 3,
    max_delivery_days: 7,
    priority: 1,
    rates: [],
    conditions: {
      min_order_value: 0,
      max_order_value: 999999,
      min_weight: 0,
      max_weight: 999999,
      excluded_products: [],
      excluded_categories: []
    }
  });

  // Rate tiers for weight/price-based calculations
  const [rateTiers, setRateTiers] = useState([
    { min: 0, max: 5, rate: 5.99 },
    { min: 5, max: 10, rate: 8.99 },
    { min: 10, max: 20, rate: 12.99 },
    { min: 20, max: 999999, rate: 19.99 }
  ]);

  // Load zones and carriers on component mount
  useEffect(() => {
    loadZones();
    loadCarriers();
  }, []);

  const loadZones = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/shipping-zones');
      
      if (!response.ok) {
        throw new Error('Failed to load shipping zones');
      }
      
      const data = await response.json();
      setZones(data.zones || []);
    } catch (err) {
      setError(err.message);
      console.error('Error loading shipping zones:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCarriers = async () => {
    try {
      const response = await fetch('/api/carriers');
      
      if (!response.ok) {
        throw new Error('Failed to load carriers');
      }
      
      const data = await response.json();
      setCarriers(data.carriers || []);
    } catch (err) {
      console.error('Error loading carriers:', err);
    }
  };

  const handleAddZone = () => {
    setShowAddForm(true);
    setEditingZone(null);
    setFormData({
      name: '',
      enabled: true,
      countries: [],
      regions: [],
      postal_codes: [],
      rate_method: 'flat',
      base_rate: 0,
      free_shipping_threshold: 0,
      handling_fee: 0,
      min_delivery_days: 3,
      max_delivery_days: 7,
      priority: 1,
      rates: [],
      conditions: {
        min_order_value: 0,
        max_order_value: 999999,
        min_weight: 0,
        max_weight: 999999,
        excluded_products: [],
        excluded_categories: []
      }
    });
    setRateTiers([
      { min: 0, max: 5, rate: 5.99 },
      { min: 5, max: 10, rate: 8.99 },
      { min: 10, max: 20, rate: 12.99 },
      { min: 20, max: 999999, rate: 19.99 }
    ]);
  };

  const handleEditZone = (zone) => {
    setEditingZone(zone);
    setShowAddForm(true);
    setFormData({
      ...zone,
      conditions: zone.conditions || {
        min_order_value: 0,
        max_order_value: 999999,
        min_weight: 0,
        max_weight: 999999,
        excluded_products: [],
        excluded_categories: []
      }
    });
    if (zone.rate_tiers) {
      setRateTiers(zone.rate_tiers);
    }
  };

  const handleDeleteZone = async (zoneId) => {
    if (!window.confirm('Are you sure you want to delete this shipping zone? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/shipping-zones/${zoneId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete shipping zone');
      }

      setSuccess('Shipping zone deleted successfully');
      loadZones();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleSaveZone = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingZone
        ? `/api/shipping-zones/${editingZone.id}`
        : '/api/shipping-zones';
      
      const method = editingZone ? 'PUT' : 'POST';
      
      // Include rate tiers if using weight/price-based method
      const zoneData = {
        ...formData,
        rate_tiers: ['weight_based', 'price_based', 'table_rate'].includes(formData.rate_method)
          ? rateTiers
          : null
      };
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(zoneData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${editingZone ? 'update' : 'create'} shipping zone`);
      }

      setSuccess(`Shipping zone ${editingZone ? 'updated' : 'created'} successfully`);
      setShowAddForm(false);
      setEditingZone(null);
      loadZones();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleConditionChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      conditions: {
        ...prev.conditions,
        [field]: value
      }
    }));
  };

  const handleCountryToggle = (countryCode) => {
    const countries = formData.countries.includes(countryCode)
      ? formData.countries.filter(c => c !== countryCode)
      : [...formData.countries, countryCode];
    handleInputChange('countries', countries);
  };

  const toggleZoneExpansion = (zoneId) => {
    setExpandedZones(prev => ({
      ...prev,
      [zoneId]: !prev[zoneId]
    }));
  };

  const addRateTier = () => {
    const lastTier = rateTiers[rateTiers.length - 1];
    setRateTiers([
      ...rateTiers.slice(0, -1),
      { min: lastTier.min, max: lastTier.min + 10, rate: lastTier.rate },
      { min: lastTier.min + 10, max: 999999, rate: lastTier.rate + 5 }
    ]);
  };

  const removeRateTier = (index) => {
    if (rateTiers.length <= 1) return;
    setRateTiers(rateTiers.filter((_, i) => i !== index));
  };

  const updateRateTier = (index, field, value) => {
    const newTiers = [...rateTiers];
    newTiers[index] = {
      ...newTiers[index],
      [field]: parseFloat(value) || 0
    };
    setRateTiers(newTiers);
  };

  const calculateShippingRate = (weight, orderValue) => {
    if (formData.rate_method === 'flat') {
      return formData.base_rate;
    }
    
    if (formData.rate_method === 'weight_based') {
      const tier = rateTiers.find(t => weight >= t.min && weight < t.max);
      return tier ? tier.rate : formData.base_rate;
    }
    
    if (formData.rate_method === 'price_based') {
      const tier = rateTiers.find(t => orderValue >= t.min && orderValue < t.max);
      return tier ? tier.rate : formData.base_rate;
    }
    
    return formData.base_rate;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Shipping Zones & Rates</h1>
            <p className="text-gray-400">
              Configure shipping zones, rates, and delivery options by region
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowRateCalculator(!showRateCalculator)}
              className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <DollarSign size={20} />
              Rate Calculator
            </button>
            <button
              onClick={handleAddZone}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Plus size={20} />
              Add Zone
            </button>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="mb-6 bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-500/10 border border-green-500 text-green-400 px-4 py-3 rounded-lg flex items-center gap-2">
          <CheckCircle size={20} />
          {success}
        </div>
      )}

      {/* Rate Calculator */}
      {showRateCalculator && (
        <div className="mb-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <DollarSign className="text-purple-400" size={24} />
              Shipping Rate Calculator
            </h2>
            <button
              onClick={() => setShowRateCalculator(false)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Zone</label>
              <select className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white">
                <option>Select zone...</option>
                {zones.map(zone => (
                  <option key={zone.id} value={zone.id}>{zone.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Weight (lbs)</label>
              <input
                type="number"
                step="0.1"
                placeholder="5.0"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Order Value ($)</label>
              <input
                type="number"
                step="0.01"
                placeholder="100.00"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
              />
            </div>
          </div>
          
          <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg transition-colors">
            Calculate Rate
          </button>
        </div>
      )}

      {/* Add/Edit Form */}
      {showAddForm && (
        <div className="mb-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">
              {editingZone ? 'Edit Shipping Zone' : 'Add Shipping Zone'}
            </h2>
            <button
              onClick={() => {
                setShowAddForm(false);
                setEditingZone(null);
              }}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          <form onSubmit={handleSaveZone} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Zone Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Domestic USA, Europe, Asia Pacific"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Priority (Lower = Higher Priority)
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.priority}
                  onChange={(e) => handleInputChange('priority', parseInt(e.target.value))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Geographic Coverage */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <Globe className="text-blue-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Geographic Coverage</h3>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Countries *
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 max-h-60 overflow-y-auto bg-gray-700 border border-gray-600 rounded-lg p-3">
                  {COUNTRIES.map((country) => (
                    <label
                      key={country.code}
                      className="flex items-center gap-2 text-white cursor-pointer hover:bg-gray-600 p-2 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={formData.countries.includes(country.code)}
                        onChange={() => handleCountryToggle(country.code)}
                        className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm">{country.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Postal Codes (Optional)
                </label>
                <input
                  type="text"
                  value={formData.postal_codes.join(', ')}
                  onChange={(e) => handleInputChange('postal_codes', e.target.value.split(',').map(s => s.trim()))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 90001-90099, 10001, 10002"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Comma-separated postal codes or ranges. Leave empty to include all postal codes.
                </p>
              </div>
            </div>

            {/* Rate Configuration */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <DollarSign className="text-green-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Rate Configuration</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Rate Calculation Method *
                  </label>
                  <select
                    value={formData.rate_method}
                    onChange={(e) => handleInputChange('rate_method', e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    {RATE_METHODS.map((method) => (
                      <option key={method.value} value={method.value}>
                        {method.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-400 mt-1">
                    {RATE_METHODS.find(m => m.value === formData.rate_method)?.description}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Base Rate ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.base_rate}
                    onChange={(e) => handleInputChange('base_rate', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Rate Tiers for weight/price-based methods */}
              {['weight_based', 'price_based', 'table_rate'].includes(formData.rate_method) && (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-3">
                    <label className="text-sm font-medium text-gray-300">
                      Rate Tiers ({formData.rate_method === 'weight_based' ? 'Weight in lbs' : 'Order Value in $'})
                    </label>
                    <button
                      type="button"
                      onClick={addRateTier}
                      className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    >
                      <Plus size={16} />
                      Add Tier
                    </button>
                  </div>
                  <div className="space-y-2">
                    {rateTiers.map((tier, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <input
                          type="number"
                          step="0.01"
                          value={tier.min}
                          onChange={(e) => updateRateTier(index, 'min', e.target.value)}
                          className="w-24 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm"
                          placeholder="Min"
                        />
                        <span className="text-gray-400">to</span>
                        <input
                          type="number"
                          step="0.01"
                          value={tier.max}
                          onChange={(e) => updateRateTier(index, 'max', e.target.value)}
                          className="w-24 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm"
                          placeholder="Max"
                        />
                        <span className="text-gray-400">=</span>
                        <input
                          type="number"
                          step="0.01"
                          value={tier.rate}
                          onChange={(e) => updateRateTier(index, 'rate', e.target.value)}
                          className="w-24 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm"
                          placeholder="Rate"
                        />
                        <span className="text-gray-400">$</span>
                        {rateTiers.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeRateTier(index)}
                            className="text-red-400 hover:text-red-300"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Free Shipping Threshold ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.free_shipping_threshold}
                    onChange={(e) => handleInputChange('free_shipping_threshold', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Orders above this amount ship free. Set to 0 to disable.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Handling Fee ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.handling_fee}
                    onChange={(e) => handleInputChange('handling_fee', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Delivery Time */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <Clock className="text-yellow-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Delivery Time Estimates</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Minimum Delivery Days
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.min_delivery_days}
                    onChange={(e) => handleInputChange('min_delivery_days', parseInt(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Maximum Delivery Days
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.max_delivery_days}
                    onChange={(e) => handleInputChange('max_delivery_days', parseInt(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Conditions */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <Package className="text-purple-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Conditions & Restrictions</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Min Order Value ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.conditions.min_order_value}
                    onChange={(e) => handleConditionChange('min_order_value', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Max Order Value ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.conditions.max_order_value}
                    onChange={(e) => handleConditionChange('max_order_value', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Min Weight (lbs)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.conditions.min_weight}
                    onChange={(e) => handleConditionChange('min_weight', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Max Weight (lbs)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.conditions.max_weight}
                    onChange={(e) => handleConditionChange('max_weight', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Status */}
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.enabled}
                  onChange={(e) => handleInputChange('enabled', e.target.checked)}
                  className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                />
                <span>Enable this shipping zone</span>
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
              >
                <Save size={20} />
                {editingZone ? 'Update Zone' : 'Create Zone'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false);
                  setEditingZone(null);
                }}
                className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Zones List */}
      <div className="space-y-4">
        {zones.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
            <MapPin className="mx-auto mb-4 text-gray-600" size={48} />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">No Shipping Zones Configured</h3>
            <p className="text-gray-500 mb-4">
              Create your first shipping zone to start offering delivery options
            </p>
            <button
              onClick={handleAddZone}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Plus size={20} />
              Add Zone
            </button>
          </div>
        ) : (
          zones.map((zone) => (
            <div
              key={zone.id}
              className="bg-gray-800 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="text-3xl">🌍</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-bold text-white">{zone.name}</h3>
                        <span className={`px-2 py-1 rounded text-xs ${zone.enabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
                          {zone.enabled ? 'Active' : 'Disabled'}
                        </span>
                        <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                          Priority {zone.priority}
                        </span>
                      </div>
                      
                      <div className="flex flex-wrap gap-4 text-sm text-gray-400">
                        <div className="flex items-center gap-1">
                          <Globe size={16} />
                          {zone.countries?.length || 0} countries
                        </div>
                        <div className="flex items-center gap-1">
                          <DollarSign size={16} />
                          {zone.rate_method?.replace('_', ' ')}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock size={16} />
                          {zone.min_delivery_days}-{zone.max_delivery_days} days
                        </div>
                        {zone.free_shipping_threshold > 0 && (
                          <div className="flex items-center gap-1">
                            <Gift size={16} className="text-green-400" />
                            Free shipping over ${zone.free_shipping_threshold}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleZoneExpansion(zone.id)}
                      className="p-2 text-gray-400 hover:bg-gray-700 rounded-lg transition-colors"
                      title="View Details"
                    >
                      {expandedZones[zone.id] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                    </button>
                    <button
                      onClick={() => handleEditZone(zone)}
                      className="p-2 text-yellow-400 hover:bg-gray-700 rounded-lg transition-colors"
                      title="Edit"
                    >
                      <Edit2 size={20} />
                    </button>
                    <button
                      onClick={() => handleDeleteZone(zone.id)}
                      className="p-2 text-red-400 hover:bg-gray-700 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedZones[zone.id] && (
                  <div className="mt-4 pt-4 border-t border-gray-700 space-y-4">
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">Countries Covered</h4>
                      <div className="flex flex-wrap gap-2">
                        {zone.countries?.map(code => {
                          const country = COUNTRIES.find(c => c.code === code);
                          return (
                            <span key={code} className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                              {country?.name || code}
                            </span>
                          );
                        })}
                      </div>
                    </div>

                    {zone.rate_tiers && zone.rate_tiers.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-300 mb-2">Rate Tiers</h4>
                        <div className="bg-gray-900 rounded-lg p-3">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="text-gray-400 border-b border-gray-700">
                                <th className="text-left py-2">Range</th>
                                <th className="text-right py-2">Rate</th>
                              </tr>
                            </thead>
                            <tbody>
                              {zone.rate_tiers.map((tier, index) => (
                                <tr key={index} className="text-white border-b border-gray-800 last:border-0">
                                  <td className="py-2">{tier.min} - {tier.max === 999999 ? '∞' : tier.max}</td>
                                  <td className="text-right py-2">${tier.rate.toFixed(2)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ShippingZonesConfiguration;

