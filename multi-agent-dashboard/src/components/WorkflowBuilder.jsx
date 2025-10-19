import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Workflow, 
  Plus, 
  Save, 
  Play, 
  Trash2,
  Settings,
  ArrowRight,
  Bot,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

// Available agent nodes
const AGENT_TYPES = [
  { id: 'order', name: 'Order Agent', color: '#3B82F6', icon: '📦' },
  { id: 'product', name: 'Product Agent', color: '#10B981', icon: '🏷️' },
  { id: 'inventory', name: 'Inventory Agent', color: '#F59E0B', icon: '📊' },
  { id: 'warehouse', name: 'Warehouse Selection', color: '#8B5CF6', icon: '🏭' },
  { id: 'carrier', name: 'Carrier Selection', color: '#EF4444', icon: '🚚' },
  { id: 'pricing', name: 'Dynamic Pricing', color: '#EC4899', icon: '💰' },
  { id: 'customer', name: 'Customer Communication', color: '#14B8A6', icon: '💬' },
  { id: 'ai_monitor', name: 'AI Monitoring', color: '#6366F1', icon: '🤖' },
];

// Workflow node component
const WorkflowNode = ({ node, onSelect, onDelete, isSelected }) => {
  const agentType = AGENT_TYPES.find(t => t.id === node.type);
  
  return (
    <div
      className={`relative cursor-pointer transition-all ${
        isSelected ? 'ring-4 ring-blue-500' : ''
      }`}
      onClick={() => onSelect(node.id)}
      style={{
        position: 'absolute',
        left: node.x,
        top: node.y,
      }}
    >
      <div 
        className="w-40 p-4 rounded-lg shadow-lg border-2 hover:shadow-xl transition-shadow"
        style={{ 
          backgroundColor: agentType?.color || '#6B7280',
          borderColor: isSelected ? '#3B82F6' : 'transparent'
        }}
      >
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">{agentType?.icon}</span>
          <div className="flex-1">
            <h3 className="text-white font-semibold text-sm">{agentType?.name}</h3>
          </div>
        </div>
        <div className="text-xs text-white opacity-90">
          ID: {node.id}
        </div>
        {node.config && (
          <div className="mt-2 text-xs text-white opacity-75">
            {Object.keys(node.config).length} settings
          </div>
        )}
      </div>
      
      {/* Delete button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete(node.id);
        }}
        className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white hover:bg-red-600 transition-colors"
      >
        <Trash2 className="w-3 h-3" />
      </button>

      {/* Connection points */}
      <div className="absolute -right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 bg-white rounded-full border-2 border-blue-500"></div>
      <div className="absolute -left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 bg-white rounded-full border-2 border-green-500"></div>
    </div>
  );
};

// Connection line component
const ConnectionLine = ({ from, to, nodes }) => {
  const fromNode = nodes.find(n => n.id === from);
  const toNode = nodes.find(n => n.id === to);
  
  if (!fromNode || !toNode) return null;

  const x1 = fromNode.x + 160; // Right edge of from node
  const y1 = fromNode.y + 40;  // Middle of from node
  const x2 = toNode.x;         // Left edge of to node
  const y2 = toNode.y + 40;    // Middle of to node

  // Calculate control points for curved line
  const midX = (x1 + x2) / 2;

  return (
    <g>
      <path
        d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
        stroke="#3B82F6"
        strokeWidth="3"
        fill="none"
        markerEnd="url(#arrowhead)"
      />
      {/* Arrow marker */}
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="3"
          orient="auto"
        >
          <polygon points="0 0, 10 3, 0 6" fill="#3B82F6" />
        </marker>
      </defs>
    </g>
  );
};

export default function WorkflowBuilder() {
  const [nodes, setNodes] = useState([
    { id: 'node-1', type: 'order', x: 50, y: 100, config: {} },
    { id: 'node-2', type: 'warehouse', x: 300, y: 100, config: {} },
    { id: 'node-3', type: 'carrier', x: 550, y: 100, config: {} },
  ]);

  const [connections, setConnections] = useState([
    { from: 'node-1', to: 'node-2' },
    { from: 'node-2', to: 'node-3' },
  ]);

  const [selectedNode, setSelectedNode] = useState(null);
  const [workflowName, setWorkflowName] = useState('Order Fulfillment Workflow');
  const [draggingType, setDraggingType] = useState(null);

  const addNode = (type, x = 50, y = 50) => {
    const newNode = {
      id: `node-${Date.now()}`,
      type,
      x,
      y,
      config: {},
    };
    setNodes([...nodes, newNode]);
  };

  const deleteNode = (id) => {
    setNodes(nodes.filter(n => n.id !== id));
    setConnections(connections.filter(c => c.from !== id && c.to !== id));
    if (selectedNode === id) setSelectedNode(null);
  };

  const handleCanvasDrop = (e) => {
    e.preventDefault();
    if (draggingType) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left - 80; // Center the node
      const y = e.clientY - rect.top - 40;
      addNode(draggingType, x, y);
      setDraggingType(null);
    }
  };

  const saveWorkflow = () => {
    const workflow = {
      name: workflowName,
      nodes,
      connections,
      createdAt: new Date().toISOString(),
    };
    console.log('Saving workflow:', workflow);
    alert('Workflow saved successfully!');
  };

  const executeWorkflow = () => {
    alert('Workflow execution started! Check the AI Monitoring dashboard for progress.');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Workflow className="w-8 h-8 text-blue-600" />
            Workflow Builder
          </h1>
          <p className="text-gray-600 mt-1">
            Design and automate multi-agent workflows with drag-and-drop
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={saveWorkflow}>
            <Save className="w-4 h-4 mr-2" />
            Save
          </Button>
          <Button onClick={executeWorkflow}>
            <Play className="w-4 h-4 mr-2" />
            Execute
          </Button>
        </div>
      </div>

      {/* Workflow Name */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <Label className="text-sm font-semibold text-gray-700">Workflow Name:</Label>
            <Input
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="max-w-md"
            />
            <Badge variant="success" className="ml-auto">
              {nodes.length} nodes, {connections.length} connections
            </Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-4 gap-6">
        {/* Agent Palette */}
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Agent Palette</CardTitle>
            <CardDescription>
              Drag agents to the canvas
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {AGENT_TYPES.map((agent) => (
                <div
                  key={agent.id}
                  draggable
                  onDragStart={() => setDraggingType(agent.id)}
                  onDragEnd={() => setDraggingType(null)}
                  className="p-3 rounded-lg border-2 border-gray-200 hover:border-blue-500 cursor-move transition-colors"
                  style={{ backgroundColor: `${agent.color}20` }}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{agent.icon}</span>
                    <span className="text-sm font-medium text-gray-900">{agent.name}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Canvas */}
        <div className="col-span-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Workflow Canvas</CardTitle>
              <CardDescription>
                Design your agent workflow by connecting nodes
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className="relative w-full h-[600px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 overflow-hidden"
                onDrop={handleCanvasDrop}
                onDragOver={(e) => e.preventDefault()}
              >
                {/* Grid background */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                  <defs>
                    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                      <circle cx="1" cy="1" r="1" fill="#D1D5DB" />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#grid)" />
                </svg>

                {/* Connection lines */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                  {connections.map((conn, idx) => (
                    <ConnectionLine key={idx} from={conn.from} to={conn.to} nodes={nodes} />
                  ))}
                </svg>

                {/* Nodes */}
                {nodes.map((node) => (
                  <WorkflowNode
                    key={node.id}
                    node={node}
                    onSelect={setSelectedNode}
                    onDelete={deleteNode}
                    isSelected={selectedNode === node.id}
                  />
                ))}

                {/* Empty state */}
                {nodes.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <Workflow className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600 font-medium">Drag agents from the palette to start building</p>
                      <p className="text-gray-500 text-sm mt-1">Connect nodes to create your workflow</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Node Configuration */}
          {selectedNode && (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Node Configuration
                </CardTitle>
                <CardDescription>
                  Configure selected agent: {nodes.find(n => n.id === selectedNode)?.type}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label>Node ID</Label>
                    <Input value={selectedNode} disabled className="mt-1" />
                  </div>
                  <div>
                    <Label>Agent Type</Label>
                    <Input 
                      value={AGENT_TYPES.find(t => t.id === nodes.find(n => n.id === selectedNode)?.type)?.name || ''} 
                      disabled 
                      className="mt-1" 
                    />
                  </div>
                  <div>
                    <Label>Custom Configuration (JSON)</Label>
                    <textarea
                      className="w-full mt-1 p-2 border rounded-md font-mono text-sm"
                      rows="4"
                      placeholder='{"key": "value"}'
                    />
                  </div>
                  <Button className="w-full">
                    Save Configuration
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Workflow Templates */}
      <Card>
        <CardHeader>
          <CardTitle>Workflow Templates</CardTitle>
          <CardDescription>
            Quick start with pre-built workflow templates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 cursor-pointer transition-colors">
              <h3 className="font-semibold text-gray-900 mb-2">Order Fulfillment</h3>
              <p className="text-sm text-gray-600 mb-3">
                Order → Warehouse → Carrier → Customer
              </p>
              <Badge variant="secondary">4 agents</Badge>
            </div>
            <div className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 cursor-pointer transition-colors">
              <h3 className="font-semibold text-gray-900 mb-2">Product Launch</h3>
              <p className="text-sm text-gray-600 mb-3">
                Product → Pricing → Inventory → Marketplace
              </p>
              <Badge variant="secondary">5 agents</Badge>
            </div>
            <div className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 cursor-pointer transition-colors">
              <h3 className="font-semibold text-gray-900 mb-2">Customer Support</h3>
              <p className="text-sm text-gray-600 mb-3">
                Customer → Communication → Order → Returns
              </p>
              <Badge variant="secondary">4 agents</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

