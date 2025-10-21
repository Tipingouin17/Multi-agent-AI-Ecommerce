import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Plus, Edit, Trash2, Save, X, Play, CheckCircle2, 
  XCircle, AlertTriangle, Code, FileText, Settings
} from 'lucide-react';

/**
 * Business Rules Configuration UI
 * 
 * Features:
 * - Create, edit, delete business rules
 * - Test rules with sample data
 * - Rule versioning and history
 * - Rule categories (pricing, inventory, shipping, etc.)
 * - Priority management
 * - Enable/disable rules
 * - Real-time validation
 */

const RULE_CATEGORIES = [
  { id: 'pricing', name: 'Pricing Rules', description: 'Dynamic pricing, discounts, promotions' },
  { id: 'inventory', name: 'Inventory Rules', description: 'Stock management, reorder points' },
  { id: 'shipping', name: 'Shipping Rules', description: 'Carrier selection, shipping costs' },
  { id: 'tax', name: 'Tax Rules', description: 'Tax calculation by region' },
  { id: 'validation', name: 'Validation Rules', description: 'Data validation, business logic' },
  { id: 'workflow', name: 'Workflow Rules', description: 'Order processing, approvals' },
  { id: 'marketplace', name: 'Marketplace Rules', description: 'Channel-specific rules' }
];

const RULE_TYPES = [
  { id: 'condition', name: 'Conditional Rule', description: 'IF-THEN logic' },
  { id: 'calculation', name: 'Calculation Rule', description: 'Mathematical calculations' },
  { id: 'validation', name: 'Validation Rule', description: 'Data validation' },
  { id: 'transformation', name: 'Transformation Rule', description: 'Data transformation' }
];

const BusinessRulesConfiguration = () => {
  const [rules, setRules] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isTestDialogOpen, setIsTestDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [testingRule, setTestingRule] = useState(null);
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [formData, setFormData] = useState({
    rule_name: '',
    category: 'pricing',
    rule_type: 'condition',
    description: '',
    condition: '',
    action: '',
    priority: 100,
    is_active: true,
    applies_to: 'all'
  });

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/business-rules');
      const data = await response.json();
      setRules(data);
    } catch (error) {
      console.error('Error fetching rules:', error);
      // Fallback mock data
      setRules([
        {
          rule_id: 1,
          rule_name: 'Free Shipping Over $50',
          category: 'shipping',
          rule_type: 'condition',
          description: 'Offer free shipping for orders over $50',
          condition: 'order.total >= 50',
          action: 'shipping_cost = 0',
          priority: 100,
          is_active: true,
          applies_to: 'all',
          execution_count: 1523,
          success_rate: 99.8,
          created_at: '2025-01-15T10:00:00Z'
        },
        {
          rule_id: 2,
          rule_name: 'Bulk Discount 10%',
          category: 'pricing',
          rule_type: 'condition',
          description: 'Apply 10% discount for orders with 5+ items',
          condition: 'order.item_count >= 5',
          action: 'discount = order.subtotal * 0.10',
          priority: 90,
          is_active: true,
          applies_to: 'all',
          execution_count: 892,
          success_rate: 100.0,
          created_at: '2025-01-10T14:30:00Z'
        },
        {
          rule_id: 3,
          rule_name: 'Low Stock Alert',
          category: 'inventory',
          rule_type: 'condition',
          description: 'Trigger alert when stock falls below 10 units',
          condition: 'product.stock < 10',
          action: 'send_alert("low_stock", product.id)',
          priority: 200,
          is_active: true,
          applies_to: 'all',
          execution_count: 345,
          success_rate: 98.5,
          created_at: '2025-01-05T09:15:00Z'
        }
      ]);
    }
  };

  const handleCreate = () => {
    setEditingRule(null);
    setFormData({
      rule_name: '',
      category: 'pricing',
      rule_type: 'condition',
      description: '',
      condition: '',
      action: '',
      priority: 100,
      is_active: true,
      applies_to: 'all'
    });
    setIsDialogOpen(true);
  };

  const handleEdit = (rule) => {
    setEditingRule(rule);
    setFormData({
      rule_name: rule.rule_name,
      category: rule.category,
      rule_type: rule.rule_type,
      description: rule.description,
      condition: rule.condition,
      action: rule.action,
      priority: rule.priority,
      is_active: rule.is_active,
      applies_to: rule.applies_to
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (ruleId) => {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    
    try {
      await fetch(`http://localhost:8000/api/business-rules/${ruleId}`, {
        method: 'DELETE'
      });
      fetchRules();
    } catch (error) {
      console.error('Error deleting rule:', error);
    }
  };

  const handleTest = (rule) => {
    setTestingRule(rule);
    setTestInput('{\n  "order": {\n    "total": 75.00,\n    "item_count": 3\n  }\n}');
    setTestResult(null);
    setIsTestDialogOpen(true);
  };

  const handleRunTest = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/business-rules/${testingRule.rule_id}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: testInput
      });
      const result = await response.json();
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        error: error.message,
        output: null
      });
    }
  };

  const handleToggleActive = async (rule) => {
    try {
      await fetch(`http://localhost:8000/api/business-rules/${rule.rule_id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !rule.is_active })
      });
      fetchRules();
    } catch (error) {
      console.error('Error toggling rule:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingRule 
        ? `http://localhost:8000/api/business-rules/${editingRule.rule_id}`
        : 'http://localhost:8000/api/business-rules';
      
      const method = editingRule ? 'PUT' : 'POST';
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      setIsDialogOpen(false);
      fetchRules();
    } catch (error) {
      console.error('Error saving rule:', error);
    }
  };

  const getCategoryBadge = (category) => {
    const colors = {
      pricing: 'bg-green-500',
      inventory: 'bg-blue-500',
      shipping: 'bg-purple-500',
      tax: 'bg-yellow-500',
      validation: 'bg-red-500',
      workflow: 'bg-indigo-500',
      marketplace: 'bg-pink-500'
    };
    return <Badge className={`${colors[category]} text-white`}>{category}</Badge>;
  };

  const getStatusBadge = (isActive) => {
    return isActive ? (
      <Badge className="bg-green-500 text-white">
        <CheckCircle2 className="w-3 h-3 mr-1" />
        Active
      </Badge>
    ) : (
      <Badge className="bg-gray-500 text-white">
        <XCircle className="w-3 h-3 mr-1" />
        Inactive
      </Badge>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Settings className="w-8 h-8" />
            Business Rules Configuration
          </h1>
          <p className="text-muted-foreground">
            Create and manage business rules for automated decision-making
          </p>
        </div>
        <Button onClick={handleCreate} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Add Rule
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Rules
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{rules.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {rules.filter(r => r.is_active).length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Executions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {rules.reduce((sum, r) => sum + (r.execution_count || 0), 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              All time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {rules.length > 0 
                ? (rules.reduce((sum, r) => sum + (r.success_rate || 0), 0) / rules.length).toFixed(1)
                : 0}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Across all rules
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Categories
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {new Set(rules.map(r => r.category)).size}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              In use
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Rules List */}
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Rules</TabsTrigger>
          {RULE_CATEGORIES.map(cat => (
            <TabsTrigger key={cat.id} value={cat.id}>
              {cat.name}
            </TabsTrigger>
          ))}
        </TabsList>

        {['all', ...RULE_CATEGORIES.map(c => c.id)].map(tab => (
          <TabsContent key={tab} value={tab} className="space-y-4">
            {rules
              .filter(r => tab === 'all' || r.category === tab)
              .sort((a, b) => b.priority - a.priority)
              .map(rule => (
                <Card key={rule.rule_id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <CardTitle className="flex items-center gap-2">
                          {rule.rule_name}
                          {getCategoryBadge(rule.category)}
                          {getStatusBadge(rule.is_active)}
                        </CardTitle>
                        <CardDescription>{rule.description}</CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleTest(rule)}
                        >
                          <Play className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleToggleActive(rule)}
                        >
                          {rule.is_active ? 'Disable' : 'Enable'}
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleEdit(rule)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleDelete(rule.rule_id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {/* Rule Logic */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-xs text-muted-foreground">Condition</Label>
                          <div className="mt-1 p-2 bg-gray-900 rounded text-sm font-mono text-green-400">
                            {rule.condition}
                          </div>
                        </div>
                        <div>
                          <Label className="text-xs text-muted-foreground">Action</Label>
                          <div className="mt-1 p-2 bg-gray-900 rounded text-sm font-mono text-blue-400">
                            {rule.action}
                          </div>
                        </div>
                      </div>

                      {/* Metrics */}
                      <div className="grid grid-cols-4 gap-4 pt-2 border-t">
                        <div>
                          <p className="text-xs text-muted-foreground">Priority</p>
                          <p className="text-sm font-medium">{rule.priority}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Executions</p>
                          <p className="text-sm font-medium">{rule.execution_count?.toLocaleString() || 0}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Success Rate</p>
                          <p className="text-sm font-medium text-green-600">{rule.success_rate?.toFixed(1) || 0}%</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Applies To</p>
                          <p className="text-sm font-medium capitalize">{rule.applies_to}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
          </TabsContent>
        ))}
      </Tabs>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingRule ? 'Edit Business Rule' : 'Add New Business Rule'}
            </DialogTitle>
            <DialogDescription>
              Define conditions and actions for automated business logic
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic Information */}
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label htmlFor="rule_name">Rule Name *</Label>
                <Input
                  id="rule_name"
                  value={formData.rule_name}
                  onChange={(e) => setFormData({ ...formData, rule_name: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="category">Category *</Label>
                <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {RULE_CATEGORIES.map(cat => (
                      <SelectItem key={cat.id} value={cat.id}>
                        {cat.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="rule_type">Rule Type *</Label>
                <Select value={formData.rule_type} onValueChange={(value) => setFormData({ ...formData, rule_type: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {RULE_TYPES.map(type => (
                      <SelectItem key={type.id} value={type.id}>
                        {type.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="col-span-2">
                <Label htmlFor="description">Description *</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                  required
                />
              </div>
            </div>

            {/* Rule Logic */}
            <div className="space-y-3">
              <Alert>
                <Code className="w-4 h-4" />
                <AlertDescription>
                  Use JavaScript-like syntax. Available objects: order, product, customer, inventory
                </AlertDescription>
              </Alert>

              <div>
                <Label htmlFor="condition">Condition (IF) *</Label>
                <Textarea
                  id="condition"
                  value={formData.condition}
                  onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                  placeholder="order.total >= 50 && customer.tier === 'premium'"
                  rows={3}
                  className="font-mono text-sm"
                  required
                />
              </div>

              <div>
                <Label htmlFor="action">Action (THEN) *</Label>
                <Textarea
                  id="action"
                  value={formData.action}
                  onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                  placeholder="shipping_cost = 0; discount = order.total * 0.10"
                  rows={3}
                  className="font-mono text-sm"
                  required
                />
              </div>
            </div>

            {/* Configuration */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="priority">Priority *</Label>
                <Input
                  id="priority"
                  type="number"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">Higher = executes first</p>
              </div>

              <div>
                <Label htmlFor="applies_to">Applies To *</Label>
                <Select value={formData.applies_to} onValueChange={(value) => setFormData({ ...formData, applies_to: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="marketplace">Marketplace Only</SelectItem>
                    <SelectItem value="d2c">D2C Only</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="is_active">Status *</Label>
                <Select value={formData.is_active.toString()} onValueChange={(value) => setFormData({ ...formData, is_active: value === 'true' })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="true">Active</SelectItem>
                    <SelectItem value="false">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                <Save className="w-4 h-4 mr-2" />
                {editingRule ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Test Dialog */}
      <Dialog open={isTestDialogOpen} onOpenChange={setIsTestDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Test Rule: {testingRule?.rule_name}</DialogTitle>
            <DialogDescription>
              Provide sample input data to test the rule
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="test_input">Input Data (JSON)</Label>
              <Textarea
                id="test_input"
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                rows={8}
                className="font-mono text-sm"
              />
            </div>

            {testResult && (
              <Alert className={testResult.success ? 'border-green-500' : 'border-red-500'}>
                {testResult.success ? (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-500" />
                )}
                <AlertDescription>
                  <div className="space-y-2">
                    <p className="font-semibold">
                      {testResult.success ? 'Test Passed' : 'Test Failed'}
                    </p>
                    {testResult.error && (
                      <p className="text-sm text-red-600">{testResult.error}</p>
                    )}
                    {testResult.output && (
                      <div>
                        <p className="text-sm font-medium">Output:</p>
                        <pre className="mt-1 p-2 bg-gray-900 rounded text-xs text-green-400 overflow-x-auto">
                          {JSON.stringify(testResult.output, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsTestDialogOpen(false)}>
              Close
            </Button>
            <Button onClick={handleRunTest} className="bg-blue-600 hover:bg-blue-700">
              <Play className="w-4 h-4 mr-2" />
              Run Test
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BusinessRulesConfiguration;

