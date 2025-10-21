import React, { useState, useEffect } from 'react';
import {
  FileText,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Eye,
  Download,
  Copy,
  Code,
  Settings,
  Printer
} from 'lucide-react';

/**
 * Document Template Configuration UI
 * 
 * Admin interface for managing document templates used by the Document Generation Agent
 * 
 * Features:
 * - Template CRUD operations
 * - Template editor with HTML/Jinja2 support
 * - Variable management
 * - Format selection (PDF, PNG, ZPL)
 * - Page size configuration
 * - Template preview
 * - Default template selection
 * - Integration with Document Generation Agent
 */

const DocumentTemplateConfiguration = () => {
  // State management
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [activeTab, setActiveTab] = useState('all');

  // Template types
  const TEMPLATE_TYPES = {
    invoice: { name: 'Invoice', icon: '💰', color: 'blue' },
    shipping_label: { name: 'Shipping Label', icon: '📦', color: 'green' },
    packing_slip: { name: 'Packing Slip', icon: '📋', color: 'purple' },
    return_label: { name: 'Return Label', icon: '↩️', color: 'orange' },
    report: { name: 'Report', icon: '📊', color: 'indigo' },
    custom: { name: 'Custom', icon: '📄', color: 'gray' }
  };

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    type: 'invoice',
    description: '',
    template_content: '',
    format: 'PDF',
    page_size: 'LETTER',
    orientation: 'portrait',
    variables: {},
    enabled: true,
    is_default: false
  });

  // Load templates on component mount
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/document-templates');
      
      if (!response.ok) {
        throw new Error('Failed to load document templates');
      }
      
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (err) {
      setError(err.message);
      console.error('Error loading document templates:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTemplate = () => {
    setShowAddForm(true);
    setEditingTemplate(null);
    setFormData({
      name: '',
      type: 'invoice',
      description: '',
      template_content: '',
      format: 'PDF',
      page_size: 'LETTER',
      orientation: 'portrait',
      variables: {},
      enabled: true,
      is_default: false
    });
  };

  const handleEditTemplate = (template) => {
    setEditingTemplate(template);
    setShowAddForm(true);
    setFormData({
      ...template,
      variables: template.variables || {}
    });
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      const response = await fetch(`/api/document-templates/${templateId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete template');
      }

      setSuccess('Template deleted successfully');
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
        ? `/api/document-templates/${editingTemplate.id}`
        : '/api/document-templates';
      
      const method = editingTemplate ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${editingTemplate ? 'update' : 'create'} template`);
      }

      setSuccess(`Template ${editingTemplate ? 'updated' : 'created'} successfully`);
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

  const handleTestGeneration = async (templateId) => {
    try {
      const response = await fetch(`/api/document-templates/${templateId}/test`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Failed to generate test document');
      }

      const data = await response.json();
      setSuccess(`Test document generated: ${data.file_path}`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const filteredTemplates = templates.filter(template => 
    activeTab === 'all' || template.type === activeTab
  );

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
              <FileText className="text-blue-400" size={36} />
              Document Template Configuration
            </h1>
            <p className="text-gray-400">
              Manage templates for automated document generation
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

      {/* Tabs */}
      <div className="mb-6 flex flex-wrap gap-2">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          All Templates
        </button>
        {Object.entries(TEMPLATE_TYPES).map(([key, type]) => (
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
                  placeholder="e.g., Standard Invoice Template"
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
                      {type.icon} {type.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={2}
                  placeholder="Describe this template..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Format *
                </label>
                <select
                  value={formData.format}
                  onChange={(e) => handleInputChange('format', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="PDF">PDF</option>
                  <option value="PNG">PNG Image</option>
                  <option value="ZPL">ZPL (Zebra Printer)</option>
                  <option value="HTML">HTML</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Page Size *
                </label>
                <select
                  value={formData.page_size}
                  onChange={(e) => handleInputChange('page_size', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="LETTER">Letter (8.5" x 11")</option>
                  <option value="A4">A4</option>
                  <option value="LABEL_4X6">Label 4" x 6"</option>
                  <option value="LABEL_4X4">Label 4" x 4"</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Orientation
                </label>
                <select
                  value={formData.orientation}
                  onChange={(e) => handleInputChange('orientation', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="portrait">Portrait</option>
                  <option value="landscape">Landscape</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Template Content *
              </label>
              <textarea
                value={formData.template_content}
                onChange={(e) => handleInputChange('template_content', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                rows={12}
                placeholder="<html><body><h1>{{title}}</h1></body></html>"
                required
              />
              <p className="text-xs text-gray-400 mt-1">
                Use Jinja2 syntax for variables: {'{{'} variable_name {'}}'}
              </p>
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.enabled}
                  onChange={(e) => handleInputChange('enabled', e.target.checked)}
                  className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                />
                <span>Enable this template</span>
              </label>
              <label className="flex items-center gap-2 text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_default}
                  onChange={(e) => handleInputChange('is_default', e.target.checked)}
                  className="rounded border-gray-500 text-blue-600 focus:ring-blue-500"
                />
                <span>Set as default template</span>
              </label>
            </div>

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
              Create your first document template
            </p>
            <button
              onClick={handleAddTemplate}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Plus size={20} />
              Add Template
            </button>
          </div>
        ) : (
          filteredTemplates.map((template) => {
            const typeInfo = TEMPLATE_TYPES[template.type];
            
            return (
              <div
                key={template.id}
                className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl">{typeInfo?.icon}</span>
                      <h3 className="text-lg font-bold text-white">{template.name}</h3>
                    </div>
                    <p className="text-gray-400 text-sm">{template.description}</p>
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className={`px-2 py-1 rounded text-xs ${
                      template.enabled
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-gray-700 text-gray-400'
                    }`}>
                      {template.enabled ? 'Active' : 'Disabled'}
                    </span>
                    {template.is_default && (
                      <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                        Default
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                  <div>
                    <p className="text-gray-400 mb-1">Format</p>
                    <p className="text-white font-medium">{template.format}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 mb-1">Page Size</p>
                    <p className="text-white font-medium">{template.page_size}</p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleTestGeneration(template.id)}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
                  >
                    <Printer size={14} />
                    Test
                  </button>
                  <button
                    onClick={() => handleEditTemplate(template)}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors"
                  >
                    <Edit2 size={14} />
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteTemplate(template.id)}
                    className="p-2 text-red-400 hover:bg-gray-700 rounded transition-colors"
                  >
                    <Trash2 size={14} />
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

export default DocumentTemplateConfiguration;

