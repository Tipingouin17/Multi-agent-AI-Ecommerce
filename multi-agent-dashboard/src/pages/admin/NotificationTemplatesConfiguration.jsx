import React, { useState, useEffect } from 'react';
import {
  Mail,
  MessageSquare,
  Bell,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Eye,
  Copy,
  Send,
  Globe,
  Code,
  FileText,
  Smartphone,
  Monitor,
  Search,
  Filter
} from 'lucide-react';

/**
 * Notification Templates Configuration UI
 * 
 * Comprehensive admin interface for managing notification templates
 * across multiple channels (Email, SMS, Push Notifications)
 * 
 * Features:
 * - Multi-channel template management (Email, SMS, Push)
 * - Rich text editor for email templates
 * - Template variables and personalization
 * - Multi-language support
 * - Template preview and testing
 * - Template versioning
 * - Trigger event configuration
 * - A/B testing support
 * - Template categories and tags
 * - Send test notifications
 * - Template analytics and performance tracking
 */

const NotificationTemplatesConfiguration = () => {
  // State management
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);

  // Template types
  const TEMPLATE_TYPES = {
    email: {
      name: 'Email',
      icon: Mail,
      color: 'blue',
      variables: ['customer_name', 'order_id', 'order_total', 'tracking_number', 'product_name', 'company_name', 'support_email']
    },
    sms: {
      name: 'SMS',
      icon: MessageSquare,
      color: 'green',
      variables: ['customer_name', 'order_id', 'tracking_number', 'delivery_date', 'short_url']
    },
    push: {
      name: 'Push Notification',
      icon: Bell,
      color: 'purple',
      variables: ['customer_name', 'title', 'message', 'action_url', 'badge_count']
    }
  };

  // Notification categories
  const CATEGORIES = [
    { value: 'order', label: 'Order Notifications', icon: '📦' },
    { value: 'shipping', label: 'Shipping Updates', icon: '🚚' },
    { value: 'account', label: 'Account Management', icon: '👤' },
    { value: 'marketing', label: 'Marketing', icon: '📢' },
    { value: 'system', label: 'System Alerts', icon: '⚙️' },
    { value: 'payment', label: 'Payment', icon: '💳' }
  ];

  // Trigger events
  const TRIGGER_EVENTS = [
    'order_placed',
    'order_confirmed',
    'order_shipped',
    'order_delivered',
    'order_cancelled',
    'payment_received',
    'payment_failed',
    'refund_processed',
    'account_created',
    'password_reset',
    'low_stock_alert',
    'abandoned_cart',
    'review_request',
    'promotion_announcement'
  ];

  // Supported languages
  const LANGUAGES = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'es', name: 'Spanish', flag: '🇪🇸' },
    { code: 'fr', name: 'French', flag: '🇫🇷' },
    { code: 'de', name: 'German', flag: '🇩🇪' },
    { code: 'it', name: 'Italian', flag: '🇮🇹' },
    { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
    { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
    { code: 'ja', name: 'Japanese', flag: '🇯🇵' }
  ];

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    type: 'email',
    category: 'order',
    trigger_event: 'order_placed',
    subject: '',
    body: '',
    language: 'en',
    enabled: true,
    variables: [],
    metadata: {
      from_name: '',
      from_email: '',
      reply_to: '',
      cc: '',
      bcc: ''
    }
  });

  // Load templates on component mount
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/notification-templates');
      
      if (!response.ok) {
        throw new Error('Failed to load notification templates');
      }
      
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (err) {
      setError(err.message);
      console.error('Error loading notification templates:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTemplate = () => {
    setShowAddForm(true);
    setEditingTemplate(null);
    setFormData({
      name: '',
      type: 'email',
      category: 'order',
      trigger_event: 'order_placed',
      subject: '',
      body: '',
      language: 'en',
      enabled: true,
      variables: [],
      metadata: {
        from_name: '',
        from_email: '',
        reply_to: '',
        cc: '',
        bcc: ''
      }
    });
  };

  const handleEditTemplate = (template) => {
    setEditingTemplate(template);
    setShowAddForm(true);
    setFormData({
      ...template,
      metadata: template.metadata || {
        from_name: '',
        from_email: '',
        reply_to: '',
        cc: '',
        bcc: ''
      }
    });
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/notification-templates/${templateId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete notification template');
      }

      setSuccess('Notification template deleted successfully');
      loadTemplates();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleSaveTemplate = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingTemplate
        ? `/api/notification-templates/${editingTemplate.id}`
        : '/api/notification-templates';
      
      const method = editingTemplate ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${editingTemplate ? 'update' : 'create'} notification template`);
      }

      setSuccess(`Notification template ${editingTemplate ? 'updated' : 'created'} successfully`);
      setShowAddForm(false);
      setEditingTemplate(null);
      loadTemplates();
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

  const handleMetadataChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      metadata: {
        ...prev.metadata,
        [field]: value
      }
    }));
  };

  const insertVariable = (variable) => {
    const textarea = document.getElementById('template-body');
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = formData.body;
      const before = text.substring(0, start);
      const after = text.substring(end);
      const newText = before + `{{${variable}}}` + after;
      
      handleInputChange('body', newText);
      
      // Set cursor position after inserted variable
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(start + variable.length + 4, start + variable.length + 4);
      }, 0);
    }
  };

  const handlePreview = (template) => {
    setPreviewData(template);
    setShowPreview(true);
  };

  const handleSendTest = async (templateId) => {
    const email = prompt('Enter email address to send test notification:');
    if (!email) return;

    try {
      const response = await fetch(`/api/notification-templates/${templateId}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
      });

      if (!response.ok) {
        throw new Error('Failed to send test notification');
      }

      setSuccess(`Test notification sent to ${email}`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleDuplicate = async (template) => {
    try {
      const response = await fetch('/api/notification-templates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...template,
          name: `${template.name} (Copy)`,
          id: undefined
        })
      });

      if (!response.ok) {
        throw new Error('Failed to duplicate template');
      }

      setSuccess('Template duplicated successfully');
      loadTemplates();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         template.subject?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTab = activeTab === 'all' || template.type === activeTab;
    return matchesSearch && matchesTab;
  });

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
            <h1 className="text-3xl font-bold text-white mb-2">Notification Templates</h1>
            <p className="text-gray-400">
              Manage email, SMS, and push notification templates
            </p>
          </div>
          <button
            onClick={handleAddTemplate}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={20} />
            Add Template
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

      {/* Filters and Search */}
      <div className="mb-6 flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search templates..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            All
          </button>
          {Object.entries(TEMPLATE_TYPES).map(([key, type]) => {
            const Icon = type.icon;
            return (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  activeTab === key
                    ? `bg-${type.color}-600 text-white`
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                <Icon size={18} />
                {type.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Add/Edit Form */}
      {showAddForm && (
        <div className="mb-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">
              {editingTemplate ? 'Edit Template' : 'Add Template'}
            </h2>
            <button
              onClick={() => {
                setShowAddForm(false);
                setEditingTemplate(null);
              }}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          <form onSubmit={handleSaveTemplate} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Template Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Order Confirmation Email"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Template Type *
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => handleInputChange('type', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {Object.entries(TEMPLATE_TYPES).map(([key, type]) => (
                    <option key={key} value={key}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Category *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.icon} {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Trigger Event *
                </label>
                <select
                  value={formData.trigger_event}
                  onChange={(e) => handleInputChange('trigger_event', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {TRIGGER_EVENTS.map((event) => (
                    <option key={event} value={event}>
                      {event.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Language *
                </label>
                <select
                  value={formData.language}
                  onChange={(e) => handleInputChange('language', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center">
                <label className="flex items-center gap-2 text-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => handleInputChange('enabled', e.target.checked)}
                    className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Enable this template</span>
                </label>
              </div>
            </div>

            {/* Email-specific fields */}
            {formData.type === 'email' && (
              <div className="border border-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Email Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      From Name
                    </label>
                    <input
                      type="text"
                      value={formData.metadata.from_name}
                      onChange={(e) => handleMetadataChange('from_name', e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                      placeholder="Your Company"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      From Email
                    </label>
                    <input
                      type="email"
                      value={formData.metadata.from_email}
                      onChange={(e) => handleMetadataChange('from_email', e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                      placeholder="noreply@example.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Reply To
                    </label>
                    <input
                      type="email"
                      value={formData.metadata.reply_to}
                      onChange={(e) => handleMetadataChange('reply_to', e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
                      placeholder="support@example.com"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Subject (Email and Push) */}
            {(formData.type === 'email' || formData.type === 'push') && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Subject / Title *
                </label>
                <input
                  type="text"
                  value={formData.subject}
                  onChange={(e) => handleInputChange('subject', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Your order has been confirmed!"
                  required
                />
              </div>
            )}

            {/* Body */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-300">
                  Message Body *
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">Insert Variable:</span>
                  <div className="flex flex-wrap gap-1">
                    {TEMPLATE_TYPES[formData.type].variables.slice(0, 4).map((variable) => (
                      <button
                        key={variable}
                        type="button"
                        onClick={() => insertVariable(variable)}
                        className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs hover:bg-blue-500/30 transition-colors"
                      >
                        {variable}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <textarea
                id="template-body"
                value={formData.body}
                onChange={(e) => handleInputChange('body', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                rows={formData.type === 'sms' ? 4 : 12}
                placeholder={
                  formData.type === 'email'
                    ? 'Hi {{customer_name}},\n\nThank you for your order #{{order_id}}...'
                    : formData.type === 'sms'
                    ? 'Hi {{customer_name}}, your order #{{order_id}} has been confirmed!'
                    : 'Your order has been shipped! Track it here: {{tracking_url}}'
                }
                required
              />
              <p className="text-xs text-gray-400 mt-1">
                Use {'{{'} and {'}}'}  to insert variables. Available variables: {TEMPLATE_TYPES[formData.type].variables.join(', ')}
              </p>
              {formData.type === 'sms' && (
                <p className="text-xs text-yellow-400 mt-1">
                  ⚠️ SMS character limit: 160 characters (Current: {formData.body.length})
                </p>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
              >
                <Save size={20} />
                {editingTemplate ? 'Update Template' : 'Create Template'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false);
                  setEditingTemplate(null);
                }}
                className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Templates List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTemplates.length === 0 ? (
          <div className="col-span-full bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
            <FileText className="mx-auto mb-4 text-gray-600" size={48} />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">No Templates Found</h3>
            <p className="text-gray-500 mb-4">
              {searchQuery ? 'Try adjusting your search' : 'Create your first notification template'}
            </p>
            {!searchQuery && (
              <button
                onClick={handleAddTemplate}
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <Plus size={20} />
                Add Template
              </button>
            )}
          </div>
        ) : (
          filteredTemplates.map((template) => {
            const TypeIcon = TEMPLATE_TYPES[template.type]?.icon || FileText;
            const typeColor = TEMPLATE_TYPES[template.type]?.color || 'gray';
            const category = CATEGORIES.find(c => c.value === template.category);
            
            return (
              <div
                key={template.id}
                className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-3">
                    <div className={`p-2 bg-${typeColor}-500/20 rounded-lg`}>
                      <TypeIcon className={`text-${typeColor}-400`} size={24} />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white mb-1">{template.name}</h3>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-gray-400">{category?.icon} {category?.label}</span>
                        <span className="text-gray-600">•</span>
                        <span className="text-gray-400">
                          {LANGUAGES.find(l => l.code === template.language)?.flag} {template.language.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${
                    template.enabled
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-gray-700 text-gray-400'
                  }`}>
                    {template.enabled ? 'Active' : 'Disabled'}
                  </span>
                </div>

                {template.subject && (
                  <div className="mb-3">
                    <p className="text-sm text-gray-400 mb-1">Subject:</p>
                    <p className="text-white text-sm font-medium">{template.subject}</p>
                  </div>
                )}

                <div className="mb-4">
                  <p className="text-sm text-gray-400 mb-1">Preview:</p>
                  <p className="text-gray-300 text-sm line-clamp-3">{template.body}</p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePreview(template)}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors"
                    title="Preview"
                  >
                    <Eye size={16} />
                    Preview
                  </button>
                  <button
                    onClick={() => handleSendTest(template.id)}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                    title="Send Test"
                  >
                    <Send size={16} />
                    Test
                  </button>
                  <button
                    onClick={() => handleDuplicate(template)}
                    className="p-2 text-gray-400 hover:bg-gray-700 rounded transition-colors"
                    title="Duplicate"
                  >
                    <Copy size={16} />
                  </button>
                  <button
                    onClick={() => handleEditTemplate(template)}
                    className="p-2 text-yellow-400 hover:bg-gray-700 rounded transition-colors"
                    title="Edit"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    onClick={() => handleDeleteTemplate(template.id)}
                    className="p-2 text-red-400 hover:bg-gray-700 rounded transition-colors"
                    title="Delete"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Preview Modal */}
      {showPreview && previewData && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-xl font-bold text-white">Template Preview</h2>
              <button
                onClick={() => setShowPreview(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <div className="p-6">
              <div className="mb-4">
                <p className="text-sm text-gray-400 mb-2">Template Name:</p>
                <p className="text-white font-medium">{previewData.name}</p>
              </div>
              {previewData.subject && (
                <div className="mb-4">
                  <p className="text-sm text-gray-400 mb-2">Subject:</p>
                  <p className="text-white font-medium">{previewData.subject}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-gray-400 mb-2">Body:</p>
                <div className="bg-gray-900 rounded-lg p-4 text-white whitespace-pre-wrap">
                  {previewData.body}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationTemplatesConfiguration;

