import React, { useState, useEffect } from 'react';
import {
  Brain,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Activity,
  TrendingUp,
  Zap,
  Settings,
  Play,
  Pause,
  RotateCcw,
  BarChart3,
  Cpu,
  Database,
  GitBranch,
  Target,
  Clock,
  AlertTriangle
} from 'lucide-react';

/**
 * AI Model Configuration UI
 * 
 * Comprehensive admin interface for managing AI/ML models used throughout the platform
 * 
 * Features:
 * - Model registry and version management
 * - Model parameter tuning and configuration
 * - Training data management
 * - Performance monitoring and metrics
 * - A/B testing configuration
 * - Model deployment and rollback
 * - Inference settings and optimization
 * - Model health monitoring
 * - Auto-retraining configuration
 * - Fallback rules and error handling
 * - Resource allocation and scaling
 */

const AIModelConfiguration = () => {
  // State management
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editingModel, setEditingModel] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [selectedModel, setSelectedModel] = useState(null);
  const [showMetrics, setShowMetrics] = useState(false);

  // Model types and their configurations
  const MODEL_TYPES = {
    recommendation: {
      name: 'Product Recommendation',
      icon: '🎯',
      color: 'blue',
      description: 'Collaborative filtering and content-based recommendations',
      algorithms: ['Collaborative Filtering', 'Content-Based', 'Hybrid', 'Deep Learning'],
      metrics: ['precision', 'recall', 'ndcg', 'coverage']
    },
    pricing: {
      name: 'Dynamic Pricing',
      icon: '💰',
      color: 'green',
      description: 'AI-powered pricing optimization',
      algorithms: ['Linear Regression', 'Random Forest', 'XGBoost', 'Neural Network'],
      metrics: ['mae', 'rmse', 'mape', 'r2_score']
    },
    demand_forecasting: {
      name: 'Demand Forecasting',
      icon: '📈',
      color: 'purple',
      description: 'Predict future product demand',
      algorithms: ['ARIMA', 'LSTM', 'Prophet', 'XGBoost'],
      metrics: ['mae', 'rmse', 'mape', 'forecast_accuracy']
    },
    fraud_detection: {
      name: 'Fraud Detection',
      icon: '🛡️',
      color: 'red',
      description: 'Identify fraudulent transactions',
      algorithms: ['Isolation Forest', 'Autoencoder', 'Random Forest', 'XGBoost'],
      metrics: ['precision', 'recall', 'f1_score', 'auc_roc']
    },
    sentiment_analysis: {
      name: 'Sentiment Analysis',
      icon: '😊',
      color: 'yellow',
      description: 'Analyze customer reviews and feedback',
      algorithms: ['BERT', 'RoBERTa', 'DistilBERT', 'LSTM'],
      metrics: ['accuracy', 'precision', 'recall', 'f1_score']
    },
    inventory_optimization: {
      name: 'Inventory Optimization',
      icon: '📦',
      color: 'indigo',
      description: 'Optimize stock levels and reorder points',
      algorithms: ['Linear Programming', 'Reinforcement Learning', 'Genetic Algorithm'],
      metrics: ['stockout_rate', 'holding_cost', 'service_level', 'turnover_rate']
    },
    churn_prediction: {
      name: 'Customer Churn Prediction',
      icon: '👤',
      color: 'pink',
      description: 'Predict customer churn probability',
      algorithms: ['Logistic Regression', 'Random Forest', 'XGBoost', 'Neural Network'],
      metrics: ['precision', 'recall', 'f1_score', 'auc_roc']
    },
    image_recognition: {
      name: 'Image Recognition',
      icon: '🖼️',
      color: 'cyan',
      description: 'Product image classification and tagging',
      algorithms: ['ResNet', 'EfficientNet', 'YOLO', 'Vision Transformer'],
      metrics: ['accuracy', 'precision', 'recall', 'map']
    }
  };

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    type: 'recommendation',
    algorithm: '',
    version: '1.0.0',
    enabled: true,
    status: 'draft',
    parameters: {},
    training_config: {
      dataset_size: 10000,
      train_test_split: 0.8,
      batch_size: 32,
      epochs: 10,
      learning_rate: 0.001,
      optimizer: 'adam'
    },
    inference_config: {
      batch_size: 1,
      timeout_ms: 1000,
      cache_enabled: true,
      cache_ttl: 3600
    },
    auto_retrain: {
      enabled: false,
      frequency: 'weekly',
      min_accuracy: 0.85,
      trigger_on_drift: true
    },
    fallback: {
      enabled: true,
      fallback_model_id: null,
      fallback_strategy: 'rule_based'
    },
    resources: {
      cpu_cores: 2,
      memory_gb: 4,
      gpu_enabled: false
    }
  });

  // Load models on component mount
  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/ai-models');
      
      if (!response.ok) {
        throw new Error('Failed to load AI models');
      }
      
      const data = await response.json();
      setModels(data.models || []);
    } catch (err) {
      setError(err.message);
      console.error('Error loading AI models:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddModel = () => {
    setShowAddForm(true);
    setEditingModel(null);
    const firstType = Object.keys(MODEL_TYPES)[0];
    setFormData({
      name: '',
      type: firstType,
      algorithm: MODEL_TYPES[firstType].algorithms[0],
      version: '1.0.0',
      enabled: true,
      status: 'draft',
      parameters: {},
      training_config: {
        dataset_size: 10000,
        train_test_split: 0.8,
        batch_size: 32,
        epochs: 10,
        learning_rate: 0.001,
        optimizer: 'adam'
      },
      inference_config: {
        batch_size: 1,
        timeout_ms: 1000,
        cache_enabled: true,
        cache_ttl: 3600
      },
      auto_retrain: {
        enabled: false,
        frequency: 'weekly',
        min_accuracy: 0.85,
        trigger_on_drift: true
      },
      fallback: {
        enabled: true,
        fallback_model_id: null,
        fallback_strategy: 'rule_based'
      },
      resources: {
        cpu_cores: 2,
        memory_gb: 4,
        gpu_enabled: false
      }
    });
  };

  const handleEditModel = (model) => {
    setEditingModel(model);
    setShowAddForm(true);
    setFormData({
      ...model,
      training_config: model.training_config || {},
      inference_config: model.inference_config || {},
      auto_retrain: model.auto_retrain || {},
      fallback: model.fallback || {},
      resources: model.resources || {}
    });
  };

  const handleDeleteModel = async (modelId) => {
    if (!window.confirm('Are you sure you want to delete this AI model? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/ai-models/${modelId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete AI model');
      }

      setSuccess('AI model deleted successfully');
      loadModels();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleSaveModel = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingModel
        ? `/api/ai-models/${editingModel.id}`
        : '/api/ai-models';
      
      const method = editingModel ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${editingModel ? 'update' : 'create'} AI model`);
      }

      setSuccess(`AI model ${editingModel ? 'updated' : 'created'} successfully`);
      setShowAddForm(false);
      setEditingModel(null);
      loadModels();
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

  const handleNestedChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const handleTypeChange = (type) => {
    setFormData(prev => ({
      ...prev,
      type,
      algorithm: MODEL_TYPES[type].algorithms[0]
    }));
  };

  const handleModelAction = async (modelId, action) => {
    try {
      const response = await fetch(`/api/ai-models/${modelId}/${action}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`Failed to ${action} model`);
      }

      setSuccess(`Model ${action} successful`);
      loadModels();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      draft: 'gray',
      training: 'yellow',
      deployed: 'green',
      testing: 'blue',
      failed: 'red',
      deprecated: 'gray'
    };
    return colors[status] || 'gray';
  };

  const getStatusIcon = (status) => {
    const icons = {
      draft: Settings,
      training: Activity,
      deployed: CheckCircle,
      testing: Zap,
      failed: AlertTriangle,
      deprecated: Clock
    };
    return icons[status] || Settings;
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
              <Brain className="text-purple-400" size={36} />
              AI Model Configuration
            </h1>
            <p className="text-gray-400">
              Manage and monitor AI/ML models across the platform
            </p>
          </div>
          <button
            onClick={handleAddModel}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={20} />
            Add Model
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

      {/* Model Type Tabs */}
      <div className="mb-6 flex flex-wrap gap-2">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          All Models
        </button>
        {Object.entries(MODEL_TYPES).map(([key, type]) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === key
                ? `bg-${type.color}-600 text-white`
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            {type.icon} {type.name}
          </button>
        ))}
      </div>

      {/* Add/Edit Form */}
      {showAddForm && (
        <div className="mb-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">
              {editingModel ? 'Edit AI Model' : 'Add AI Model'}
            </h2>
            <button
              onClick={() => {
                setShowAddForm(false);
                setEditingModel(null);
              }}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          <form onSubmit={handleSaveModel} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Model Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Product Recommendation v2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Model Type *
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => handleTypeChange(e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {Object.entries(MODEL_TYPES).map(([key, type]) => (
                    <option key={key} value={key}>
                      {type.icon} {type.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Algorithm *
                </label>
                <select
                  value={formData.algorithm}
                  onChange={(e) => handleInputChange('algorithm', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {MODEL_TYPES[formData.type].algorithms.map((algo) => (
                    <option key={algo} value={algo}>
                      {algo}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Version *
                </label>
                <input
                  type="text"
                  value={formData.version}
                  onChange={(e) => handleInputChange('version', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1.0.0"
                  required
                />
              </div>
            </div>

            {/* Training Configuration */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <Database className="text-blue-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Training Configuration</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Dataset Size
                  </label>
                  <input
                    type="number"
                    value={formData.training_config.dataset_size}
                    onChange={(e) => handleNestedChange('training_config', 'dataset_size', parseInt(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Train/Test Split
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={formData.training_config.train_test_split}
                    onChange={(e) => handleNestedChange('training_config', 'train_test_split', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Batch Size
                  </label>
                  <input
                    type="number"
                    value={formData.training_config.batch_size}
                    onChange={(e) => handleNestedChange('training_config', 'batch_size', parseInt(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Epochs
                  </label>
                  <input
                    type="number"
                    value={formData.training_config.epochs}
                    onChange={(e) => handleNestedChange('training_config', 'epochs', parseInt(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Learning Rate
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    value={formData.training_config.learning_rate}
                    onChange={(e) => handleNestedChange('training_config', 'learning_rate', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Optimizer
                  </label>
                  <select
                    value={formData.training_config.optimizer}
                    onChange={(e) => handleNestedChange('training_config', 'optimizer', e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  >
                    <option value="adam">Adam</option>
                    <option value="sgd">SGD</option>
                    <option value="rmsprop">RMSprop</option>
                    <option value="adagrad">Adagrad</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Inference Configuration */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <Zap className="text-yellow-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Inference Configuration</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Batch Size
                  </label>
                  <input
                    type="number"
                    value={formData.inference_config.batch_size}
                    onChange={(e) => handleNestedChange('inference_config', 'batch_size', parseInt(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Timeout (ms)
                  </label>
                  <input
                    type="number"
                    value={formData.inference_config.timeout_ms}
                    onChange={(e) => handleNestedChange('inference_config', 'timeout_ms', parseInt(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  />
                </div>
                <div className="col-span-2">
                  <label className="flex items-center gap-2 text-white cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.inference_config.cache_enabled}
                      onChange={(e) => handleNestedChange('inference_config', 'cache_enabled', e.target.checked)}
                      className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                    />
                    <span>Enable caching (TTL: {formData.inference_config.cache_ttl}s)</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Resource Allocation */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <Cpu className="text-green-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Resource Allocation</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    CPU Cores
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.resources.cpu_cores}
                    onChange={(e) => handleNestedChange('resources', 'cpu_cores', parseInt(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Memory (GB)
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.resources.memory_gb}
                    onChange={(e) => handleNestedChange('resources', 'memory_gb', parseInt(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                  />
                </div>
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-white cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.resources.gpu_enabled}
                      onChange={(e) => handleNestedChange('resources', 'gpu_enabled', e.target.checked)}
                      className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                    />
                    <span>Enable GPU</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Auto-Retrain Configuration */}
            <div className="border border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <RotateCcw className="text-purple-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Auto-Retrain Configuration</h3>
              </div>
              <div className="space-y-4">
                <label className="flex items-center gap-2 text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.auto_retrain.enabled}
                    onChange={(e) => handleNestedChange('auto_retrain', 'enabled', e.target.checked)}
                    className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Enable automatic retraining</span>
                </label>
                {formData.auto_retrain.enabled && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 ml-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Frequency
                      </label>
                      <select
                        value={formData.auto_retrain.frequency}
                        onChange={(e) => handleNestedChange('auto_retrain', 'frequency', e.target.value)}
                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                      >
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Min Accuracy Threshold
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={formData.auto_retrain.min_accuracy}
                        onChange={(e) => handleNestedChange('auto_retrain', 'min_accuracy', parseFloat(e.target.value))}
                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                      />
                    </div>
                  </div>
                )}
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
                <span>Enable this model</span>
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
              >
                <Save size={20} />
                {editingModel ? 'Update Model' : 'Create Model'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false);
                  setEditingModel(null);
                }}
                className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Models List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {models.length === 0 ? (
          <div className="col-span-full bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
            <Brain className="mx-auto mb-4 text-gray-600" size={48} />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">No AI Models Configured</h3>
            <p className="text-gray-500 mb-4">
              Add your first AI model to start leveraging machine learning
            </p>
            <button
              onClick={handleAddModel}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Plus size={20} />
              Add Model
            </button>
          </div>
        ) : (
          models
            .filter(model => activeTab === 'all' || model.type === activeTab)
            .map((model) => {
              const modelType = MODEL_TYPES[model.type];
              const StatusIcon = getStatusIcon(model.status);
              const statusColor = getStatusColor(model.status);
              
              return (
                <div
                  key={model.id}
                  className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-3">
                      <div className="text-3xl">{modelType?.icon || '🤖'}</div>
                      <div>
                        <h3 className="text-xl font-bold text-white mb-1">{model.name}</h3>
                        <p className="text-gray-400 text-sm">{modelType?.name}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`flex items-center gap-1 px-2 py-1 bg-${statusColor}-500/20 text-${statusColor}-400 rounded text-xs`}>
                        <StatusIcon size={14} />
                        {model.status}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        model.enabled
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-700 text-gray-400'
                      }`}>
                        {model.enabled ? 'Active' : 'Disabled'}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                    <div>
                      <p className="text-gray-400 mb-1">Algorithm</p>
                      <p className="text-white font-medium">{model.algorithm}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-1">Version</p>
                      <p className="text-white font-medium">{model.version}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-1">Accuracy</p>
                      <p className="text-white font-medium">{model.accuracy ? `${(model.accuracy * 100).toFixed(1)}%` : 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-1">Predictions</p>
                      <p className="text-white font-medium">{model.prediction_count?.toLocaleString() || 0}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {model.status === 'deployed' && (
                      <button
                        onClick={() => handleModelAction(model.id, 'pause')}
                        className="flex items-center gap-1 px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-sm transition-colors"
                      >
                        <Pause size={14} />
                        Pause
                      </button>
                    )}
                    {model.status === 'draft' && (
                      <button
                        onClick={() => handleModelAction(model.id, 'deploy')}
                        className="flex items-center gap-1 px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
                      >
                        <Play size={14} />
                        Deploy
                      </button>
                    )}
                    <button
                      onClick={() => handleModelAction(model.id, 'retrain')}
                      className="flex items-center gap-1 px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm transition-colors"
                    >
                      <RotateCcw size={14} />
                      Retrain
                    </button>
                    <button
                      onClick={() => {
                        setSelectedModel(model);
                        setShowMetrics(true);
                      }}
                      className="flex items-center gap-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                    >
                      <BarChart3 size={14} />
                      Metrics
                    </button>
                    <button
                      onClick={() => handleEditModel(model)}
                      className="flex items-center gap-1 px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors"
                    >
                      <Edit2 size={14} />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteModel(model.id)}
                      className="flex items-center gap-1 px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
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
    </div>
  );
};

export default AIModelConfiguration;

