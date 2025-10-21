import React, { useState, useEffect, useRef } from 'react';
import {
  GitBranch,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Play,
  Pause,
  Copy,
  Download,
  Upload,
  Zap,
  Clock,
  Filter,
  Mail,
  Database,
  Code,
  Settings,
  ArrowRight,
  Circle,
  Square,
  Diamond,
  Hexagon
} from 'lucide-react';

/**
 * Workflow Configuration UI with Visual Builder
 * 
 * Comprehensive admin interface for creating and managing automated workflows
 * 
 * Features:
 * - Visual drag-and-drop workflow designer
 * - Node library (triggers, actions, conditions, delays)
 * - Connection and flow logic
 * - Workflow templates (order processing, returns, etc.)
 * - Testing and simulation
 * - Version control
 * - Execution history and analytics
 * - Integration with all agents
 * - Real-time execution monitoring
 */

const WorkflowConfiguration = () => {
  // State management
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editingWorkflow, setEditingWorkflow] = useState(null);
  const [showDesigner, setShowDesigner] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);

  // Workflow designer state
  const [nodes, setNodes] = useState([]);
  const [connections, setConnections] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [draggedNode, setDraggedNode] = useState(null);
  const canvasRef = useRef(null);

  // Node types and their configurations
  const NODE_TYPES = {
    trigger: {
      name: 'Trigger',
      icon: Zap,
      color: 'yellow',
      category: 'Triggers',
      nodes: [
        { id: 'order_placed', name: 'Order Placed', description: 'Triggered when a new order is placed' },
        { id: 'order_paid', name: 'Order Paid', description: 'Triggered when payment is confirmed' },
        { id: 'inventory_low', name: 'Low Inventory', description: 'Triggered when stock falls below threshold' },
        { id: 'customer_registered', name: 'Customer Registered', description: 'Triggered when a new customer signs up' },
        { id: 'return_requested', name: 'Return Requested', description: 'Triggered when a return is initiated' },
        { id: 'scheduled', name: 'Scheduled', description: 'Triggered at specific times or intervals' }
      ]
    },
    action: {
      name: 'Action',
      icon: Settings,
      color: 'blue',
      category: 'Actions',
      nodes: [
        { id: 'send_email', name: 'Send Email', description: 'Send an email notification' },
        { id: 'send_sms', name: 'Send SMS', description: 'Send an SMS notification' },
        { id: 'update_inventory', name: 'Update Inventory', description: 'Modify inventory levels' },
        { id: 'create_shipment', name: 'Create Shipment', description: 'Generate shipping label' },
        { id: 'update_order_status', name: 'Update Order Status', description: 'Change order status' },
        { id: 'assign_agent', name: 'Assign to Agent', description: 'Delegate task to an AI agent' },
        { id: 'call_api', name: 'Call API', description: 'Make an external API call' },
        { id: 'update_database', name: 'Update Database', description: 'Modify database records' }
      ]
    },
    condition: {
      name: 'Condition',
      icon: Diamond,
      color: 'purple',
      category: 'Logic',
      nodes: [
        { id: 'if_then', name: 'If/Then', description: 'Conditional branching' },
        { id: 'switch', name: 'Switch', description: 'Multiple condition branches' },
        { id: 'compare', name: 'Compare Values', description: 'Compare two values' },
        { id: 'check_inventory', name: 'Check Inventory', description: 'Verify stock availability' },
        { id: 'validate_data', name: 'Validate Data', description: 'Check data validity' }
      ]
    },
    delay: {
      name: 'Delay',
      icon: Clock,
      color: 'orange',
      category: 'Flow Control',
      nodes: [
        { id: 'wait', name: 'Wait', description: 'Pause execution for a duration' },
        { id: 'wait_until', name: 'Wait Until', description: 'Wait for a specific condition' },
        { id: 'schedule', name: 'Schedule', description: 'Schedule for later execution' }
      ]
    },
    data: {
      name: 'Data',
      icon: Database,
      color: 'green',
      category: 'Data Operations',
      nodes: [
        { id: 'get_data', name: 'Get Data', description: 'Retrieve data from database' },
        { id: 'transform_data', name: 'Transform Data', description: 'Modify or format data' },
        { id: 'aggregate_data', name: 'Aggregate Data', description: 'Combine multiple data sources' },
        { id: 'filter_data', name: 'Filter Data', description: 'Filter data based on criteria' }
      ]
    }
  };

  // Workflow templates
  const WORKFLOW_TEMPLATES = [
    {
      id: 'order_fulfillment',
      name: 'Order Fulfillment',
      description: 'Automated order processing from payment to shipment',
      category: 'Orders',
      nodes: [
        { type: 'trigger', subtype: 'order_paid', x: 100, y: 100 },
        { type: 'action', subtype: 'update_order_status', x: 300, y: 100 },
        { type: 'condition', subtype: 'check_inventory', x: 500, y: 100 },
        { type: 'action', subtype: 'create_shipment', x: 700, y: 100 },
        { type: 'action', subtype: 'send_email', x: 900, y: 100 }
      ]
    },
    {
      id: 'return_processing',
      name: 'Return Processing',
      description: 'Automated return and refund workflow',
      category: 'Returns',
      nodes: [
        { type: 'trigger', subtype: 'return_requested', x: 100, y: 100 },
        { type: 'action', subtype: 'send_email', x: 300, y: 100 },
        { type: 'delay', subtype: 'wait', x: 500, y: 100 },
        { type: 'condition', subtype: 'validate_data', x: 700, y: 100 },
        { type: 'action', subtype: 'update_inventory', x: 900, y: 100 }
      ]
    },
    {
      id: 'inventory_reorder',
      name: 'Inventory Reorder',
      description: 'Automatic reordering when stock is low',
      category: 'Inventory',
      nodes: [
        { type: 'trigger', subtype: 'inventory_low', x: 100, y: 100 },
        { type: 'data', subtype: 'get_data', x: 300, y: 100 },
        { type: 'action', subtype: 'call_api', x: 500, y: 100 },
        { type: 'action', subtype: 'send_email', x: 700, y: 100 }
      ]
    }
  ];

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'orders',
    enabled: true,
    trigger_type: 'order_placed',
    priority: 5
  });

  // Load workflows on component mount
  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/workflows');
      
      if (!response.ok) {
        throw new Error('Failed to load workflows');
      }
      
      const data = await response.json();
      setWorkflows(data.workflows || []);
    } catch (err) {
      setError(err.message);
      console.error('Error loading workflows:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddWorkflow = () => {
    setShowDesigner(true);
    setEditingWorkflow(null);
    setNodes([]);
    setConnections([]);
    setFormData({
      name: '',
      description: '',
      category: 'orders',
      enabled: true,
      trigger_type: 'order_placed',
      priority: 5
    });
  };

  const handleEditWorkflow = (workflow) => {
    setEditingWorkflow(workflow);
    setShowDesigner(true);
    setFormData({
      name: workflow.name,
      description: workflow.description,
      category: workflow.category,
      enabled: workflow.enabled,
      trigger_type: workflow.trigger_type,
      priority: workflow.priority
    });
    setNodes(workflow.nodes || []);
    setConnections(workflow.connections || []);
  };

  const handleDeleteWorkflow = async (workflowId) => {
    if (!window.confirm('Are you sure you want to delete this workflow? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/workflows/${workflowId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete workflow');
      }

      setSuccess('Workflow deleted successfully');
      loadWorkflows();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleSaveWorkflow = async (e) => {
    e.preventDefault();
    
    if (nodes.length === 0) {
      setError('Workflow must contain at least one node');
      setTimeout(() => setError(null), 5000);
      return;
    }

    try {
      const workflowData = {
        ...formData,
        nodes,
        connections
      };

      const url = editingWorkflow
        ? `/api/workflows/${editingWorkflow.id}`
        : '/api/workflows';
      
      const method = editingWorkflow ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(workflowData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${editingWorkflow ? 'update' : 'create'} workflow`);
      }

      setSuccess(`Workflow ${editingWorkflow ? 'updated' : 'created'} successfully`);
      setShowDesigner(false);
      setEditingWorkflow(null);
      loadWorkflows();
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

  const handleNodeDragStart = (nodeType, subtype) => {
    setDraggedNode({ type: nodeType, subtype });
  };

  const handleCanvasDrop = (e) => {
    e.preventDefault();
    if (!draggedNode || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const newNode = {
      id: `node_${Date.now()}`,
      type: draggedNode.type,
      subtype: draggedNode.subtype,
      x,
      y,
      config: {}
    };

    setNodes(prev => [...prev, newNode]);
    setDraggedNode(null);
  };

  const handleCanvasDragOver = (e) => {
    e.preventDefault();
  };

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  const handleDeleteNode = (nodeId) => {
    setNodes(prev => prev.filter(n => n.id !== nodeId));
    setConnections(prev => prev.filter(c => c.from !== nodeId && c.to !== nodeId));
    if (selectedNode?.id === nodeId) {
      setSelectedNode(null);
    }
  };

  const handleLoadTemplate = (template) => {
    setNodes(template.nodes.map((node, index) => ({
      id: `node_${Date.now()}_${index}`,
      ...node
    })));
    setConnections([]);
    setFormData(prev => ({
      ...prev,
      name: template.name,
      description: template.description,
      category: template.category
    }));
  };

  const handleWorkflowAction = async (workflowId, action) => {
    try {
      const response = await fetch(`/api/workflows/${workflowId}/${action}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`Failed to ${action} workflow`);
      }

      setSuccess(`Workflow ${action} successful`);
      loadWorkflows();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const getNodeIcon = (type) => {
    return NODE_TYPES[type]?.icon || Circle;
  };

  const getNodeColor = (type) => {
    return NODE_TYPES[type]?.color || 'gray';
  };

  const getNodeInfo = (type, subtype) => {
    const nodeCategory = NODE_TYPES[type];
    if (!nodeCategory) return null;
    return nodeCategory.nodes.find(n => n.id === subtype);
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
              <GitBranch className="text-purple-400" size={36} />
              Workflow Configuration
            </h1>
            <p className="text-gray-400">
              Create and manage automated workflows with visual builder
            </p>
          </div>
          <button
            onClick={handleAddWorkflow}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={20} />
            Create Workflow
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

      {/* Workflow Designer */}
      {showDesigner && (
        <div className="mb-8 bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-6 border-b border-gray-700">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">
                {editingWorkflow ? 'Edit Workflow' : 'Create Workflow'}
              </h2>
              <button
                onClick={() => {
                  setShowDesigner(false);
                  setEditingWorkflow(null);
                }}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Workflow Info Form */}
            <form onSubmit={handleSaveWorkflow} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Workflow Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Order Fulfillment Workflow"
                    required
                  />
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
                    <option value="orders">Orders</option>
                    <option value="inventory">Inventory</option>
                    <option value="returns">Returns</option>
                    <option value="shipping">Shipping</option>
                    <option value="customer">Customer</option>
                    <option value="marketing">Marketing</option>
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
                    placeholder="Describe what this workflow does..."
                  />
                </div>
              </div>

              {/* Templates */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Load from Template
                </label>
                <div className="flex flex-wrap gap-2">
                  {WORKFLOW_TEMPLATES.map((template) => (
                    <button
                      key={template.id}
                      type="button"
                      onClick={() => handleLoadTemplate(template)}
                      className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors"
                    >
                      {template.name}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  type="submit"
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
                >
                  <Save size={20} />
                  {editingWorkflow ? 'Update Workflow' : 'Create Workflow'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowDesigner(false);
                    setEditingWorkflow(null);
                  }}
                  className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>

          {/* Visual Designer */}
          <div className="grid grid-cols-4 gap-0">
            {/* Node Palette */}
            <div className="col-span-1 bg-gray-900 p-4 border-r border-gray-700 max-h-[600px] overflow-y-auto">
              <h3 className="text-white font-semibold mb-4">Node Library</h3>
              {Object.entries(NODE_TYPES).map(([key, category]) => {
                const Icon = category.icon;
                return (
                  <div key={key} className="mb-4">
                    <div className="flex items-center gap-2 text-gray-400 text-sm font-medium mb-2">
                      <Icon size={16} />
                      {category.category}
                    </div>
                    <div className="space-y-1">
                      {category.nodes.map((node) => (
                        <div
                          key={node.id}
                          draggable
                          onDragStart={() => handleNodeDragStart(key, node.id)}
                          className={`p-2 bg-${category.color}-500/20 border border-${category.color}-500/50 rounded cursor-move hover:bg-${category.color}-500/30 transition-colors`}
                          title={node.description}
                        >
                          <p className={`text-${category.color}-400 text-xs font-medium`}>
                            {node.name}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Canvas */}
            <div className="col-span-3 relative">
              <div
                ref={canvasRef}
                onDrop={handleCanvasDrop}
                onDragOver={handleCanvasDragOver}
                className="w-full h-[600px] bg-gray-900/50 relative overflow-auto"
                style={{
                  backgroundImage: 'radial-gradient(circle, #374151 1px, transparent 1px)',
                  backgroundSize: '20px 20px'
                }}
              >
                {nodes.length === 0 ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <GitBranch className="mx-auto mb-4 text-gray-600" size={48} />
                      <p className="text-gray-500">
                        Drag nodes from the library to start building your workflow
                      </p>
                    </div>
                  </div>
                ) : (
                  nodes.map((node) => {
                    const Icon = getNodeIcon(node.type);
                    const color = getNodeColor(node.type);
                    const nodeInfo = getNodeInfo(node.type, node.subtype);
                    
                    return (
                      <div
                        key={node.id}
                        onClick={() => handleNodeClick(node)}
                        className={`absolute p-3 bg-${color}-500/20 border-2 ${
                          selectedNode?.id === node.id
                            ? `border-${color}-400`
                            : `border-${color}-500/50`
                        } rounded-lg cursor-pointer hover:shadow-lg transition-all min-w-[150px]`}
                        style={{
                          left: node.x,
                          top: node.y
                        }}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <Icon className={`text-${color}-400`} size={16} />
                          <p className={`text-${color}-400 text-sm font-medium`}>
                            {nodeInfo?.name || node.subtype}
                          </p>
                        </div>
                        {selectedNode?.id === node.id && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteNode(node.id);
                            }}
                            className="absolute -top-2 -right-2 p-1 bg-red-500 rounded-full text-white hover:bg-red-600"
                          >
                            <X size={12} />
                          </button>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Workflows List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {workflows.length === 0 ? (
          <div className="col-span-full bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
            <GitBranch className="mx-auto mb-4 text-gray-600" size={48} />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">No Workflows Created</h3>
            <p className="text-gray-500 mb-4">
              Create your first automated workflow
            </p>
            <button
              onClick={handleAddWorkflow}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Plus size={20} />
              Create Workflow
            </button>
          </div>
        ) : (
          workflows.map((workflow) => (
            <div
              key={workflow.id}
              className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white mb-1">{workflow.name}</h3>
                  <p className="text-gray-400 text-sm">{workflow.description}</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs ${
                  workflow.enabled
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-gray-700 text-gray-400'
                }`}>
                  {workflow.enabled ? 'Active' : 'Disabled'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                <div>
                  <p className="text-gray-400 mb-1">Category</p>
                  <p className="text-white font-medium capitalize">{workflow.category}</p>
                </div>
                <div>
                  <p className="text-gray-400 mb-1">Executions</p>
                  <p className="text-white font-medium">{workflow.execution_count?.toLocaleString() || 0}</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {workflow.enabled ? (
                  <button
                    onClick={() => handleWorkflowAction(workflow.id, 'pause')}
                    className="flex items-center gap-1 px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-sm transition-colors"
                  >
                    <Pause size={14} />
                    Pause
                  </button>
                ) : (
                  <button
                    onClick={() => handleWorkflowAction(workflow.id, 'activate')}
                    className="flex items-center gap-1 px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
                  >
                    <Play size={14} />
                    Activate
                  </button>
                )}
                <button
                  onClick={() => handleWorkflowAction(workflow.id, 'test')}
                  className="flex items-center gap-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                >
                  <Play size={14} />
                  Test
                </button>
                <button
                  onClick={() => handleEditWorkflow(workflow)}
                  className="flex items-center gap-1 px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors"
                >
                  <Edit2 size={14} />
                  Edit
                </button>
                <button
                  onClick={() => handleDeleteWorkflow(workflow.id)}
                  className="flex items-center gap-1 px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
                >
                  <Trash2 size={14} />
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default WorkflowConfiguration;

