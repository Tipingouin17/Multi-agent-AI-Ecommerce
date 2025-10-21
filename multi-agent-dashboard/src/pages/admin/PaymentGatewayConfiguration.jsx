import React, { useState, useEffect } from 'react';
import {
  CreditCard,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff,
  Globe,
  DollarSign,
  Zap,
  Shield,
  Settings,
  Activity,
  Webhook
} from 'lucide-react';

/**
 * Payment Gateway Configuration UI
 * 
 * Comprehensive admin interface for managing payment gateway integrations
 * including Stripe, PayPal, Square, Authorize.net, and custom providers.
 * 
 * Features:
 * - Multi-gateway support with provider-specific configurations
 * - Secure credential management with encryption
 * - Webhook URL management and verification
 * - Transaction fee configuration (fixed + percentage)
 * - Test mode and sandbox environment support
 * - Payment method enablement (cards, wallets, bank transfers)
 * - Currency and region support
 * - Connection testing and health monitoring
 * - Real-time status indicators
 */

const PaymentGatewayConfiguration = () => {
  // State management
  const [gateways, setGateways] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editingGateway, setEditingGateway] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showCredentials, setShowCredentials] = useState({});
  const [testingConnection, setTestingConnection] = useState(null);

  // Payment gateway providers with their configurations
  const GATEWAY_PROVIDERS = {
    stripe: {
      name: 'Stripe',
      icon: '💳',
      fields: [
        { key: 'publishable_key', label: 'Publishable Key', type: 'text', required: true },
        { key: 'secret_key', label: 'Secret Key', type: 'password', required: true },
        { key: 'webhook_secret', label: 'Webhook Secret', type: 'password', required: false }
      ],
      paymentMethods: ['card', 'apple_pay', 'google_pay', 'sepa_debit', 'ideal', 'bancontact'],
      currencies: ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'SEK', 'NOK', 'DKK'],
      documentation: 'https://stripe.com/docs/api'
    },
    paypal: {
      name: 'PayPal',
      icon: '🅿️',
      fields: [
        { key: 'client_id', label: 'Client ID', type: 'text', required: true },
        { key: 'client_secret', label: 'Client Secret', type: 'password', required: true },
        { key: 'webhook_id', label: 'Webhook ID', type: 'text', required: false }
      ],
      paymentMethods: ['paypal', 'card', 'venmo', 'pay_later'],
      currencies: ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY'],
      documentation: 'https://developer.paypal.com/docs/api/overview/'
    },
    square: {
      name: 'Square',
      icon: '⬛',
      fields: [
        { key: 'application_id', label: 'Application ID', type: 'text', required: true },
        { key: 'access_token', label: 'Access Token', type: 'password', required: true },
        { key: 'location_id', label: 'Location ID', type: 'text', required: true }
      ],
      paymentMethods: ['card', 'apple_pay', 'google_pay', 'cash_app'],
      currencies: ['USD', 'CAD', 'GBP', 'AUD', 'JPY'],
      documentation: 'https://developer.squareup.com/docs'
    },
    authorize_net: {
      name: 'Authorize.Net',
      icon: '🔐',
      fields: [
        { key: 'api_login_id', label: 'API Login ID', type: 'text', required: true },
        { key: 'transaction_key', label: 'Transaction Key', type: 'password', required: true },
        { key: 'signature_key', label: 'Signature Key', type: 'password', required: false }
      ],
      paymentMethods: ['card', 'echeck', 'apple_pay', 'paypal'],
      currencies: ['USD', 'CAD', 'GBP', 'EUR', 'AUD'],
      documentation: 'https://developer.authorize.net/api/reference/'
    },
    custom: {
      name: 'Custom Gateway',
      icon: '⚙️',
      fields: [
        { key: 'api_endpoint', label: 'API Endpoint', type: 'url', required: true },
        { key: 'api_key', label: 'API Key', type: 'password', required: true },
        { key: 'merchant_id', label: 'Merchant ID', type: 'text', required: true }
      ],
      paymentMethods: ['card'],
      currencies: ['USD', 'EUR', 'GBP'],
      documentation: ''
    }
  };

  // Form state for new/editing gateway
  const [formData, setFormData] = useState({
    provider: 'stripe',
    name: '',
    enabled: true,
    test_mode: true,
    credentials: {},
    webhook_url: '',
    supported_currencies: ['USD'],
    supported_payment_methods: ['card'],
    transaction_fee_fixed: 0.30,
    transaction_fee_percentage: 2.9,
    priority: 1,
    regions: ['US'],
    min_amount: 0.50,
    max_amount: 999999.99,
    auto_capture: true,
    three_d_secure: false,
    metadata: {}
  });

  // Load gateways on component mount
  useEffect(() => {
    loadGateways();
  }, []);

  const loadGateways = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // API call to fetch payment gateways
      const response = await fetch('/api/payment-gateways');
      
      if (!response.ok) {
        throw new Error('Failed to load payment gateways');
      }
      
      const data = await response.json();
      setGateways(data.gateways || []);
    } catch (err) {
      setError(err.message);
      console.error('Error loading payment gateways:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddGateway = () => {
    setShowAddForm(true);
    setEditingGateway(null);
    setFormData({
      provider: 'stripe',
      name: '',
      enabled: true,
      test_mode: true,
      credentials: {},
      webhook_url: '',
      supported_currencies: ['USD'],
      supported_payment_methods: ['card'],
      transaction_fee_fixed: 0.30,
      transaction_fee_percentage: 2.9,
      priority: 1,
      regions: ['US'],
      min_amount: 0.50,
      max_amount: 999999.99,
      auto_capture: true,
      three_d_secure: false,
      metadata: {}
    });
  };

  const handleEditGateway = (gateway) => {
    setEditingGateway(gateway);
    setShowAddForm(true);
    setFormData({
      ...gateway,
      credentials: gateway.credentials || {}
    });
  };

  const handleDeleteGateway = async (gatewayId) => {
    if (!window.confirm('Are you sure you want to delete this payment gateway? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/payment-gateways/${gatewayId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete payment gateway');
      }

      setSuccess('Payment gateway deleted successfully');
      loadGateways();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleSaveGateway = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingGateway
        ? `/api/payment-gateways/${editingGateway.id}`
        : '/api/payment-gateways';
      
      const method = editingGateway ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${editingGateway ? 'update' : 'create'} payment gateway`);
      }

      setSuccess(`Payment gateway ${editingGateway ? 'updated' : 'created'} successfully`);
      setShowAddForm(false);
      setEditingGateway(null);
      loadGateways();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleTestConnection = async (gatewayId) => {
    try {
      setTestingConnection(gatewayId);
      
      const response = await fetch(`/api/payment-gateways/${gatewayId}/test`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Connection test failed');
      }

      const result = await response.json();
      
      if (result.success) {
        setSuccess('Connection test successful! Gateway is properly configured.');
      } else {
        setError(`Connection test failed: ${result.message}`);
      }
      
      setTimeout(() => {
        setSuccess(null);
        setError(null);
      }, 5000);
    } catch (err) {
      setError(`Connection test failed: ${err.message}`);
      setTimeout(() => setError(null), 5000);
    } finally {
      setTestingConnection(null);
    }
  };

  const toggleCredentialVisibility = (gatewayId) => {
    setShowCredentials(prev => ({
      ...prev,
      [gatewayId]: !prev[gatewayId]
    }));
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCredentialChange = (key, value) => {
    setFormData(prev => ({
      ...prev,
      credentials: {
        ...prev.credentials,
        [key]: value
      }
    }));
  };

  const handleProviderChange = (provider) => {
    const providerConfig = GATEWAY_PROVIDERS[provider];
    setFormData(prev => ({
      ...prev,
      provider,
      name: providerConfig.name,
      credentials: {},
      supported_currencies: [providerConfig.currencies[0]],
      supported_payment_methods: [providerConfig.paymentMethods[0]]
    }));
  };

  const getStatusColor = (gateway) => {
    if (!gateway.enabled) return 'text-gray-500';
    if (gateway.test_mode) return 'text-yellow-400';
    return gateway.status === 'active' ? 'text-green-400' : 'text-red-400';
  };

  const getStatusText = (gateway) => {
    if (!gateway.enabled) return 'Disabled';
    if (gateway.test_mode) return 'Test Mode';
    return gateway.status === 'active' ? 'Active' : 'Error';
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
            <h1 className="text-3xl font-bold text-white mb-2">Payment Gateway Configuration</h1>
            <p className="text-gray-400">
              Manage payment processors, credentials, and transaction settings
            </p>
          </div>
          <button
            onClick={handleAddGateway}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={20} />
            Add Gateway
          </button>
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

      {/* Add/Edit Form */}
      {showAddForm && (
        <div className="mb-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">
              {editingGateway ? 'Edit Payment Gateway' : 'Add Payment Gateway'}
            </h2>
            <button
              onClick={() => {
                setShowAddForm(false);
                setEditingGateway(null);
              }}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          <form onSubmit={handleSaveGateway} className="space-y-6">
            {/* Provider Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Payment Provider *
                </label>
                <select
                  value={formData.provider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {Object.entries(GATEWAY_PROVIDERS).map(([key, provider]) => (
                    <option key={key} value={key}>
                      {provider.icon} {provider.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Gateway Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Stripe Production"
                  required
                />
              </div>
            </div>

            {/* Credentials */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="text-blue-400" size={20} />
                <h3 className="text-lg font-semibold text-white">API Credentials</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {GATEWAY_PROVIDERS[formData.provider].fields.map((field) => (
                  <div key={field.key}>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      {field.label} {field.required && '*'}
                    </label>
                    <div className="relative">
                      <input
                        type={field.type === 'password' && !showCredentials[field.key] ? 'password' : 'text'}
                        value={formData.credentials[field.key] || ''}
                        onChange={(e) => handleCredentialChange(field.key, e.target.value)}
                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                        placeholder={`Enter ${field.label.toLowerCase()}`}
                        required={field.required}
                      />
                      {field.type === 'password' && (
                        <button
                          type="button"
                          onClick={() => toggleCredentialVisibility(field.key)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                        >
                          {showCredentials[field.key] ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Webhook Configuration */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <Webhook className="text-purple-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Webhook Configuration</h3>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Webhook URL
                </label>
                <input
                  type="url"
                  value={formData.webhook_url}
                  onChange={(e) => handleInputChange('webhook_url', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="https://your-domain.com/webhooks/payment"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Configure this URL in your payment provider's dashboard to receive real-time notifications
                </p>
              </div>
            </div>

            {/* Transaction Fees */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <DollarSign className="text-green-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Transaction Fees</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Fixed Fee (USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.transaction_fee_fixed}
                    onChange={(e) => handleInputChange('transaction_fee_fixed', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Percentage Fee (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={formData.transaction_fee_percentage}
                    onChange={(e) => handleInputChange('transaction_fee_percentage', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Payment Methods & Currencies */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Supported Payment Methods
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto bg-gray-700 border border-gray-600 rounded-lg p-3">
                  {GATEWAY_PROVIDERS[formData.provider].paymentMethods.map((method) => (
                    <label key={method} className="flex items-center gap-2 text-white cursor-pointer hover:bg-gray-600 p-1 rounded">
                      <input
                        type="checkbox"
                        checked={formData.supported_payment_methods.includes(method)}
                        onChange={(e) => {
                          const methods = e.target.checked
                            ? [...formData.supported_payment_methods, method]
                            : formData.supported_payment_methods.filter(m => m !== method);
                          handleInputChange('supported_payment_methods', methods);
                        }}
                        className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="capitalize">{method.replace('_', ' ')}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Supported Currencies
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto bg-gray-700 border border-gray-600 rounded-lg p-3">
                  {GATEWAY_PROVIDERS[formData.provider].currencies.map((currency) => (
                    <label key={currency} className="flex items-center gap-2 text-white cursor-pointer hover:bg-gray-600 p-1 rounded">
                      <input
                        type="checkbox"
                        checked={formData.supported_currencies.includes(currency)}
                        onChange={(e) => {
                          const currencies = e.target.checked
                            ? [...formData.supported_currencies, currency]
                            : formData.supported_currencies.filter(c => c !== currency);
                          handleInputChange('supported_currencies', currencies);
                        }}
                        className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                      />
                      <span>{currency}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Transaction Limits */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Minimum Transaction Amount
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.min_amount}
                  onChange={(e) => handleInputChange('min_amount', parseFloat(e.target.value))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Maximum Transaction Amount
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.max_amount}
                  onChange={(e) => handleInputChange('max_amount', parseFloat(e.target.value))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <label className="flex items-center gap-2 text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.enabled}
                  onChange={(e) => handleInputChange('enabled', e.target.checked)}
                  className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                />
                <span>Enabled</span>
              </label>

              <label className="flex items-center gap-2 text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.test_mode}
                  onChange={(e) => handleInputChange('test_mode', e.target.checked)}
                  className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                />
                <span>Test Mode</span>
              </label>

              <label className="flex items-center gap-2 text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.auto_capture}
                  onChange={(e) => handleInputChange('auto_capture', e.target.checked)}
                  className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                />
                <span>Auto Capture</span>
              </label>

              <label className="flex items-center gap-2 text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.three_d_secure}
                  onChange={(e) => handleInputChange('three_d_secure', e.target.checked)}
                  className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                />
                <span>3D Secure</span>
              </label>
            </div>

            {/* Priority */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Priority (Lower number = higher priority)
              </label>
              <input
                type="number"
                min="1"
                value={formData.priority}
                onChange={(e) => handleInputChange('priority', parseInt(e.target.value))}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-400 mt-1">
                When multiple gateways are available, the system will use the one with the lowest priority number
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
              >
                <Save size={20} />
                {editingGateway ? 'Update Gateway' : 'Create Gateway'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false);
                  setEditingGateway(null);
                }}
                className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Gateways List */}
      <div className="space-y-4">
        {gateways.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
            <CreditCard className="mx-auto mb-4 text-gray-600" size={48} />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">No Payment Gateways Configured</h3>
            <p className="text-gray-500 mb-4">
              Add your first payment gateway to start processing transactions
            </p>
            <button
              onClick={handleAddGateway}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Plus size={20} />
              Add Gateway
            </button>
          </div>
        ) : (
          gateways.map((gateway) => (
            <div
              key={gateway.id}
              className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-4">
                  <div className="text-4xl">
                    {GATEWAY_PROVIDERS[gateway.provider]?.icon || '💳'}
                  </div>
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="text-xl font-bold text-white">{gateway.name}</h3>
                      <span className={`flex items-center gap-1 text-sm ${getStatusColor(gateway)}`}>
                        <Activity size={16} />
                        {getStatusText(gateway)}
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm">
                      {GATEWAY_PROVIDERS[gateway.provider]?.name || gateway.provider}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTestConnection(gateway.id)}
                    disabled={testingConnection === gateway.id}
                    className="p-2 text-blue-400 hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
                    title="Test Connection"
                  >
                    {testingConnection === gateway.id ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                    ) : (
                      <Zap size={20} />
                    )}
                  </button>
                  <button
                    onClick={() => handleEditGateway(gateway)}
                    className="p-2 text-yellow-400 hover:bg-gray-700 rounded-lg transition-colors"
                    title="Edit"
                  >
                    <Edit2 size={20} />
                  </button>
                  <button
                    onClick={() => handleDeleteGateway(gateway.id)}
                    className="p-2 text-red-400 hover:bg-gray-700 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <Trash2 size={20} />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-400 mb-1">Payment Methods</p>
                  <div className="flex flex-wrap gap-1">
                    {gateway.supported_payment_methods?.slice(0, 3).map((method) => (
                      <span
                        key={method}
                        className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs"
                      >
                        {method}
                      </span>
                    ))}
                    {gateway.supported_payment_methods?.length > 3 && (
                      <span className="px-2 py-1 bg-gray-700 text-gray-400 rounded text-xs">
                        +{gateway.supported_payment_methods.length - 3}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <p className="text-gray-400 mb-1">Currencies</p>
                  <div className="flex flex-wrap gap-1">
                    {gateway.supported_currencies?.slice(0, 3).map((currency) => (
                      <span
                        key={currency}
                        className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs"
                      >
                        {currency}
                      </span>
                    ))}
                    {gateway.supported_currencies?.length > 3 && (
                      <span className="px-2 py-1 bg-gray-700 text-gray-400 rounded text-xs">
                        +{gateway.supported_currencies.length - 3}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <p className="text-gray-400 mb-1">Transaction Fees</p>
                  <p className="text-white font-medium">
                    ${gateway.transaction_fee_fixed?.toFixed(2)} + {gateway.transaction_fee_percentage?.toFixed(1)}%
                  </p>
                </div>

                <div>
                  <p className="text-gray-400 mb-1">Priority</p>
                  <p className="text-white font-medium">Level {gateway.priority}</p>
                </div>
              </div>

              {gateway.webhook_url && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex items-center gap-2 text-sm">
                    <Webhook size={16} className="text-purple-400" />
                    <span className="text-gray-400">Webhook:</span>
                    <code className="text-purple-400 bg-gray-900 px-2 py-1 rounded text-xs">
                      {gateway.webhook_url}
                    </code>
                  </div>
                </div>
              )}

              {gateway.test_mode && (
                <div className="mt-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 flex items-center gap-2">
                  <AlertCircle size={16} className="text-yellow-400" />
                  <span className="text-yellow-400 text-sm">
                    This gateway is in test mode. No real transactions will be processed.
                  </span>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Documentation Links */}
      {gateways.length > 0 && (
        <div className="mt-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Globe size={20} />
            Provider Documentation
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(GATEWAY_PROVIDERS)
              .filter(([_, provider]) => provider.documentation)
              .map(([key, provider]) => (
                <a
                  key={key}
                  href={provider.documentation}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  <span className="text-2xl">{provider.icon}</span>
                  <div>
                    <p className="text-white font-medium">{provider.name}</p>
                    <p className="text-gray-400 text-xs">View API Documentation →</p>
                  </div>
                </a>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PaymentGatewayConfiguration;

