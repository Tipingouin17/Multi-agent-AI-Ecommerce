import React, { useState, useEffect } from 'react';
import {
  RotateCcw,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Package,
  DollarSign,
  Calendar,
  FileText,
  Truck,
  CheckSquare,
  XSquare,
  Clock,
  Tag,
  Settings
} from 'lucide-react';

/**
 * Return/RMA Configuration UI
 * 
 * Comprehensive admin interface for managing return and RMA (Return Merchandise Authorization) policies
 * 
 * Features:
 * - Return policy configuration
 * - Return window settings
 * - Return reasons and categories
 * - Approval workflows
 * - Refund/exchange rules
 * - Restocking fees
 * - Return shipping label generation
 * - Quality inspection workflow
 * - Disposition rules (restock, refurbish, dispose)
 * - Return analytics and reporting
 */

const ReturnRMAConfiguration = () => {
  // State management
  const [policies, setPolicies] = useState([]);
  const [returnReasons, setReturnReasons] = useState([]);
  const [dispositionRules, setDispositionRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('policies');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  // Return policy categories
  const POLICY_CATEGORIES = [
    { value: 'electronics', label: 'Electronics', icon: '💻' },
    { value: 'clothing', label: 'Clothing & Apparel', icon: '👕' },
    { value: 'furniture', label: 'Furniture', icon: '🛋️' },
    { value: 'books', label: 'Books & Media', icon: '📚' },
    { value: 'food', label: 'Food & Beverages', icon: '🍔' },
    { value: 'health', label: 'Health & Beauty', icon: '💄' },
    { value: 'toys', label: 'Toys & Games', icon: '🎮' },
    { value: 'general', label: 'General Merchandise', icon: '📦' }
  ];

  // Return reasons
  const DEFAULT_RETURN_REASONS = [
    { value: 'defective', label: 'Defective or Damaged', requires_photo: true, auto_approve: false },
    { value: 'wrong_item', label: 'Wrong Item Received', requires_photo: true, auto_approve: false },
    { value: 'not_as_described', label: 'Not as Described', requires_photo: true, auto_approve: false },
    { value: 'size_fit', label: 'Size/Fit Issue', requires_photo: false, auto_approve: true },
    { value: 'changed_mind', label: 'Changed Mind', requires_photo: false, auto_approve: true },
    { value: 'better_price', label: 'Found Better Price', requires_photo: false, auto_approve: true },
    { value: 'late_delivery', label: 'Arrived Too Late', requires_photo: false, auto_approve: true },
    { value: 'quality', label: 'Quality Not Satisfactory', requires_photo: true, auto_approve: false },
    { value: 'other', label: 'Other', requires_photo: false, auto_approve: false }
  ];

  // Disposition actions
  const DISPOSITION_ACTIONS = [
    { value: 'restock', label: 'Restock for Resale', icon: '📦', color: 'green' },
    { value: 'refurbish', label: 'Refurbish/Repair', icon: '🔧', color: 'blue' },
    { value: 'liquidate', label: 'Liquidate/Clearance', icon: '💰', color: 'yellow' },
    { value: 'donate', label: 'Donate', icon: '❤️', color: 'pink' },
    { value: 'recycle', label: 'Recycle', icon: '♻️', color: 'teal' },
    { value: 'dispose', label: 'Dispose/Destroy', icon: '🗑️', color: 'red' }
  ];

  // Form state for return policy
  const [policyFormData, setPolicyFormData] = useState({
    name: '',
    category: 'general',
    return_window_days: 30,
    exchange_window_days: 30,
    refund_method: 'original_payment',
    restocking_fee_percent: 0,
    requires_original_packaging: false,
    requires_tags_attached: false,
    free_return_shipping: false,
    auto_approve_enabled: false,
    inspection_required: true,
    enabled: true
  });

  // Load data on component mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [policiesRes, reasonsRes, dispositionRes] = await Promise.all([
        fetch('/api/return-policies'),
        fetch('/api/return-reasons'),
        fetch('/api/disposition-rules')
      ]);
      
      if (!policiesRes.ok || !reasonsRes.ok || !dispositionRes.ok) {
        throw new Error('Failed to load return/RMA configuration');
      }
      
      const [policiesData, reasonsData, dispositionData] = await Promise.all([
        policiesRes.json(),
        reasonsRes.json(),
        dispositionRes.json()
      ]);
      
      setPolicies(policiesData.policies || []);
      setReturnReasons(reasonsData.reasons || DEFAULT_RETURN_REASONS);
      setDispositionRules(dispositionData.rules || []);
    } catch (err) {
      setError(err.message);
      console.error('Error loading return/RMA configuration:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddPolicy = () => {
    setShowAddForm(true);
    setEditingItem(null);
    setPolicyFormData({
      name: '',
      category: 'general',
      return_window_days: 30,
      exchange_window_days: 30,
      refund_method: 'original_payment',
      restocking_fee_percent: 0,
      requires_original_packaging: false,
      requires_tags_attached: false,
      free_return_shipping: false,
      auto_approve_enabled: false,
      inspection_required: true,
      enabled: true
    });
  };

  const handleEditPolicy = (policy) => {
    setEditingItem(policy);
    setShowAddForm(true);
    setPolicyFormData(policy);
  };

  const handleDeletePolicy = async (policyId) => {
    if (!window.confirm('Are you sure you want to delete this return policy?')) {
      return;
    }

    try {
      const response = await fetch(`/api/return-policies/${policyId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete return policy');
      }

      setSuccess('Return policy deleted successfully');
      loadData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleSavePolicy = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingItem
        ? `/api/return-policies/${editingItem.id}`
        : '/api/return-policies';
      
      const method = editingItem ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(policyFormData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${editingItem ? 'update' : 'create'} return policy`);
      }

      setSuccess(`Return policy ${editingItem ? 'updated' : 'created'} successfully`);
      setShowAddForm(false);
      setEditingItem(null);
      loadData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleInputChange = (field, value) => {
    setPolicyFormData(prev => ({
      ...prev,
      [field]: value
    }));
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
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <RotateCcw className="text-blue-400" size={36} />
              Return & RMA Configuration
            </h1>
            <p className="text-gray-400">
              Manage return policies, reasons, and disposition rules
            </p>
          </div>
          {activeTab === 'policies' && (
            <button
              onClick={handleAddPolicy}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Plus size={20} />
              Add Policy
            </button>
          )}
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

      {/* Tabs */}
      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setActiveTab('policies')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'policies'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          <FileText size={18} />
          Return Policies
        </button>
        <button
          onClick={() => setActiveTab('reasons')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'reasons'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          <Tag size={18} />
          Return Reasons
        </button>
        <button
          onClick={() => setActiveTab('disposition')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'disposition'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          <Settings size={18} />
          Disposition Rules
        </button>
      </div>

      {/* Add/Edit Policy Form */}
      {showAddForm && activeTab === 'policies' && (
        <div className="mb-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">
              {editingItem ? 'Edit Return Policy' : 'Add Return Policy'}
            </h2>
            <button
              onClick={() => {
                setShowAddForm(false);
                setEditingItem(null);
              }}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          <form onSubmit={handleSavePolicy} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Policy Name *
                </label>
                <input
                  type="text"
                  value={policyFormData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Standard Electronics Return Policy"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Category *
                </label>
                <select
                  value={policyFormData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {POLICY_CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.icon} {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Return Window (Days) *
                </label>
                <input
                  type="number"
                  min="0"
                  max="365"
                  value={policyFormData.return_window_days}
                  onChange={(e) => handleInputChange('return_window_days', parseInt(e.target.value))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Exchange Window (Days) *
                </label>
                <input
                  type="number"
                  min="0"
                  max="365"
                  value={policyFormData.exchange_window_days}
                  onChange={(e) => handleInputChange('exchange_window_days', parseInt(e.target.value))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Refund Method *
                </label>
                <select
                  value={policyFormData.refund_method}
                  onChange={(e) => handleInputChange('refund_method', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="original_payment">Original Payment Method</option>
                  <option value="store_credit">Store Credit Only</option>
                  <option value="exchange_only">Exchange Only</option>
                  <option value="both">Store Credit or Exchange</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Restocking Fee (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={policyFormData.restocking_fee_percent}
                  onChange={(e) => handleInputChange('restocking_fee_percent', parseFloat(e.target.value))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Policy Options */}
            <div className="border border-gray-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-4">Policy Requirements</h3>
              <div className="space-y-3">
                <label className="flex items-center gap-2 text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policyFormData.requires_original_packaging}
                    onChange={(e) => handleInputChange('requires_original_packaging', e.target.checked)}
                    className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Require original packaging</span>
                </label>
                <label className="flex items-center gap-2 text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policyFormData.requires_tags_attached}
                    onChange={(e) => handleInputChange('requires_tags_attached', e.target.checked)}
                    className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Require tags attached (for apparel)</span>
                </label>
                <label className="flex items-center gap-2 text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policyFormData.free_return_shipping}
                    onChange={(e) => handleInputChange('free_return_shipping', e.target.checked)}
                    className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Provide free return shipping label</span>
                </label>
                <label className="flex items-center gap-2 text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policyFormData.auto_approve_enabled}
                    onChange={(e) => handleInputChange('auto_approve_enabled', e.target.checked)}
                    className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Enable auto-approval for eligible returns</span>
                </label>
                <label className="flex items-center gap-2 text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policyFormData.inspection_required}
                    onChange={(e) => handleInputChange('inspection_required', e.target.checked)}
                    className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Require quality inspection upon receipt</span>
                </label>
                <label className="flex items-center gap-2 text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policyFormData.enabled}
                    onChange={(e) => handleInputChange('enabled', e.target.checked)}
                    className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Enable this policy</span>
                </label>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
              >
                <Save size={20} />
                {editingItem ? 'Update Policy' : 'Create Policy'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false);
                  setEditingItem(null);
                }}
                className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Content based on active tab */}
      {activeTab === 'policies' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {policies.length === 0 ? (
            <div className="col-span-full bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
              <Package className="mx-auto mb-4 text-gray-600" size={48} />
              <h3 className="text-xl font-semibold text-gray-400 mb-2">No Return Policies Configured</h3>
              <p className="text-gray-500 mb-4">
                Create your first return policy
              </p>
              <button
                onClick={handleAddPolicy}
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <Plus size={20} />
                Add Policy
              </button>
            </div>
          ) : (
            policies.map((policy) => {
              const category = POLICY_CATEGORIES.find(c => c.value === policy.category);
              
              return (
                <div
                  key={policy.id}
                  className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-white mb-1">{policy.name}</h3>
                      <p className="text-gray-400 text-sm">{category?.icon} {category?.label}</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      policy.enabled
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-gray-700 text-gray-400'
                    }`}>
                      {policy.enabled ? 'Active' : 'Disabled'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                    <div>
                      <p className="text-gray-400 mb-1">Return Window</p>
                      <p className="text-white font-medium">{policy.return_window_days} days</p>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-1">Exchange Window</p>
                      <p className="text-white font-medium">{policy.exchange_window_days} days</p>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-1">Refund Method</p>
                      <p className="text-white font-medium capitalize">{policy.refund_method.replace(/_/g, ' ')}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-1">Restocking Fee</p>
                      <p className="text-white font-medium">{policy.restocking_fee_percent}%</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-4 text-xs">
                    {policy.free_return_shipping && (
                      <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded">
                        Free Shipping
                      </span>
                    )}
                    {policy.auto_approve_enabled && (
                      <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded">
                        Auto-Approve
                      </span>
                    )}
                    {policy.inspection_required && (
                      <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded">
                        Inspection Required
                      </span>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEditPolicy(policy)}
                      className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors"
                    >
                      <Edit2 size={14} />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeletePolicy(policy.id)}
                      className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
                    >
                      <Trash2 size={14} />
                      Delete
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {activeTab === 'reasons' && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-4">Return Reasons</h2>
          <div className="space-y-2">
            {returnReasons.map((reason, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 bg-gray-700 rounded-lg"
              >
                <div>
                  <p className="text-white font-medium">{reason.label}</p>
                  <div className="flex gap-2 mt-1">
                    {reason.requires_photo && (
                      <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-400 rounded">
                        Photo Required
                      </span>
                    )}
                    {reason.auto_approve && (
                      <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded">
                        Auto-Approve
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'disposition' && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-4">Disposition Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {DISPOSITION_ACTIONS.map((action) => (
              <div
                key={action.value}
                className={`p-4 bg-${action.color}-500/20 border border-${action.color}-500/50 rounded-lg`}
              >
                <div className="text-2xl mb-2">{action.icon}</div>
                <p className={`text-${action.color}-400 font-medium`}>{action.label}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReturnRMAConfiguration;

