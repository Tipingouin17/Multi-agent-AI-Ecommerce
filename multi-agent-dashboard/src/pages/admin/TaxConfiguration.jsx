import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Plus, Edit, Trash2, Save, X, Receipt, Globe, 
  MapPin, Archive, CheckCircle2, AlertCircle
} from 'lucide-react';

/**
 * Tax Configuration UI
 * 
 * Features:
 * - Manage tax rules by country/region
 * - Configure tax rates (VAT, GST, Sales Tax)
 * - Set product-specific tax categories
 * - Handle tax exemptions
 * - Multi-jurisdiction support
 */

const TaxConfiguration = () => {
  const [taxRules, setTaxRules] = useState([]);
  const [error, setError] = useState(null);
  const [taxCategories, setTaxCategories] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState('rule'); // 'rule', 'category'
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({});

  const countries = [
    'United States', 'United Kingdom', 'Germany', 'France', 'Spain', 'Italy',
    'Canada', 'Australia', 'Japan', 'China', 'India', 'Brazil'
  ];

  const taxTypes = ['VAT', 'GST', 'Sales Tax', 'Excise Tax', 'Import Duty'];

  useEffect(() => {
    fetchTaxRules();
    fetchTaxCategories();
  }, []);

  const fetchTaxRules = async () => {
    try {
      const response = await fetch('http://localhost:8011/api/tax/rules');
      const data = await response.json();
      setTaxRules(data);
    } catch (error) {
      console.error('Error fetching taxRules:', error);
      setError({
        message: 'Failed to load taxRules from database',
        details: error.message,
        retry: fetchTaxRules
      });
      setTaxRules([]); // Empty array, NO mock data
    }
  };

  const fetchTaxCategories = async () => {
    try {
      const response = await fetch('http://localhost:8011/api/tax/rules');
      const data = await response.json();
      setTaxCategories(data);
    } catch (error) {
      console.error('Error fetching taxRules:', error);
      setError({
        message: 'Failed to load taxRules from database',
        details: error.message,
        retry: fetchTaxCategories
      });
      setTaxCategories([]); // Empty array, NO mock data
    }
  };

  const handleCreate = (type) => {
    setDialogType(type);
    setEditingItem(null);
    
    if (type === 'rule') {
      setFormData({
        rule_name: '',
        country: '',
        region: '',
        tax_type: 'VAT',
        tax_rate: 0,
        is_compound: false,
        is_active: true,
        priority: 1,
        applies_to: 'All Products'
      });
    } else if (type === 'category') {
      setFormData({
        category_name: '',
        description: '',
        default_rate: 0
      });
    }
    
    setIsDialogOpen(true);
  };

  const handleEdit = (item, type) => {
    setDialogType(type);
    setEditingItem(item);
    setFormData({ ...item });
    setIsDialogOpen(true);
  };

  const handleDelete = async (id, type) => {
    if (!confirm(`Are you sure you want to delete this ${type}?`)) return;
    
    try {
      const endpoints = {
        rule: 'tax-rules',
        category: 'tax-categories'
      };
      
      await fetch(`http://localhost:8000/api/${endpoints[type]}/${id}`, {
        method: 'DELETE'
      });
      
      if (type === 'rule') fetchTaxRules();
      else if (type === 'category') fetchTaxCategories();
    } catch (error) {
      console.error(`Error deleting ${type}:`, error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const endpoints = {
        rule: 'tax-rules',
        category: 'tax-categories'
      };
      
      const idFields = {
        rule: 'rule_id',
        category: 'category_id'
      };
      
      const url = editingItem 
        ? `http://localhost:8000/api/${endpoints[dialogType]}/${editingItem[idFields[dialogType]]}`
        : `http://localhost:8000/api/${endpoints[dialogType]}`;
      
      const method = editingItem ? 'PUT' : 'POST';
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      setIsDialogOpen(false);
      
      if (dialogType === 'rule') fetchTaxRules();
      else if (dialogType === 'category') fetchTaxCategories();
    } catch (error) {
      console.error(`Error saving ${dialogType}:`, error);
    }
  };

  const groupedRules = taxRules.reduce((acc, rule) => {
    const key = rule.country;
    if (!acc[key]) acc[key] = [];
    acc[key].push(rule);
    return acc;
  }, {});

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Receipt className="w-8 h-8" />
            Tax Configuration
          </h1>
          <p className="text-muted-foreground">
            Manage tax rules and categories for different regions
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Tax Rules
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{taxRules.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {taxRules.filter(r => r.is_active).length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Countries
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{Object.keys(groupedRules).length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              with tax configuration
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Tax Categories
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{taxCategories.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              for product classification
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg Tax Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {(taxRules.reduce((sum, r) => sum + r.tax_rate, 0) / taxRules.length).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              across all rules
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="rules">
        <TabsList>
          <TabsTrigger value="rules">
            <Globe className="w-4 h-4 mr-2" />
            Tax Rules
          </TabsTrigger>
          <TabsTrigger value="categories">
            <Receipt className="w-4 h-4 mr-2" />
            Tax Categories
          </TabsTrigger>
        </TabsList>

        {/* Tax Rules Tab */}
        <TabsContent value="rules" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => handleCreate('rule')} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Tax Rule
            </Button>
          </div>

          <Alert>
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              Tax rules are applied based on priority (lower number = higher priority). 
              Compound taxes are calculated on top of other taxes.
            </AlertDescription>
          </Alert>

          {Object.entries(groupedRules).map(([country, rules]) => (
            <Card key={country}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="w-5 h-5" />
                  {country}
                  <Badge variant="outline">{rules.length} rules</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {rules.map(rule => (
                  <div key={rule.rule_id} className="flex justify-between items-center p-3 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">{rule.rule_name}</span>
                        {rule.is_active ? (
                          <Badge className="bg-green-500 text-white text-xs">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Active
                          </Badge>
                        ) : (
                          <Badge className="bg-gray-500 text-white text-xs">Inactive</Badge>
                        )}
                        <Badge variant="outline" className="text-xs">{rule.tax_type}</Badge>
                        {rule.is_compound && (
                          <Badge className="bg-orange-500 text-white text-xs">Compound</Badge>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {rule.region && `${rule.region} • `}
                        {rule.applies_to} • Priority: {rule.priority}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-2xl font-bold text-blue-600">{rule.tax_rate}%</div>
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleEdit(rule, 'rule')}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleDelete(rule.rule_id, 'rule')}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Tax Categories Tab */}
        <TabsContent value="categories" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => handleCreate('category')} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Tax Category
            </Button>
          </div>

          {taxCategories.map(category => (
            <Card key={category.category_id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {category.category_name}
                      <Badge variant="outline">{category.default_rate}%</Badge>
                    </CardTitle>
                    <CardDescription>{category.description}</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleEdit(category, 'category')}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleDelete(category.category_id, 'category')}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Products Using</p>
                    <p className="text-2xl font-bold">{category.product_count || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingItem ? `Edit ${dialogType}` : `Add New ${dialogType}`}
            </DialogTitle>
            <DialogDescription>
              {dialogType === 'rule' && 'Configure tax rules for specific countries and regions'}
              {dialogType === 'category' && 'Create tax categories for product classification'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {dialogType === 'rule' && (
              <>
                <div>
                  <Label htmlFor="rule_name">Rule Name *</Label>
                  <Input
                    id="rule_name"
                    value={formData.rule_name || ''}
                    onChange={(e) => setFormData({ ...formData, rule_name: e.target.value })}
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="country">Country *</Label>
                    <Select 
                      value={formData.country || ''} 
                      onValueChange={(value) => setFormData({ ...formData, country: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select country" />
                      </SelectTrigger>
                      <SelectContent>
                        {countries.map(country => (
                          <SelectItem key={country} value={country}>{country}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="region">Region/State</Label>
                    <Input
                      id="region"
                      value={formData.region || ''}
                      onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                      placeholder="Optional"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="tax_type">Tax Type *</Label>
                    <Select 
                      value={formData.tax_type || 'VAT'} 
                      onValueChange={(value) => setFormData({ ...formData, tax_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {taxTypes.map(type => (
                          <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="tax_rate">Tax Rate (%) *</Label>
                    <Input
                      id="tax_rate"
                      type="number"
                      step="0.01"
                      value={formData.tax_rate || 0}
                      onChange={(e) => setFormData({ ...formData, tax_rate: parseFloat(e.target.value) })}
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="priority">Priority *</Label>
                    <Input
                      id="priority"
                      type="number"
                      value={formData.priority || 1}
                      onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                      required
                    />
                    <p className="text-xs text-muted-foreground mt-1">Lower number = higher priority</p>
                  </div>
                  <div>
                    <Label htmlFor="applies_to">Applies To</Label>
                    <Input
                      id="applies_to"
                      value={formData.applies_to || 'All Products'}
                      onChange={(e) => setFormData({ ...formData, applies_to: e.target.value })}
                    />
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="is_compound"
                    checked={formData.is_compound || false}
                    onChange={(e) => setFormData({ ...formData, is_compound: e.target.checked })}
                    className="rounded"
                  />
                  <Label htmlFor="is_compound">Compound Tax (calculated on top of other taxes)</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active !== false}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="rounded"
                  />
                  <Label htmlFor="is_active">Active</Label>
                </div>
              </>
            )}

            {dialogType === 'category' && (
              <>
                <div>
                  <Label htmlFor="category_name">Category Name *</Label>
                  <Input
                    id="category_name"
                    value={formData.category_name || ''}
                    onChange={(e) => setFormData({ ...formData, category_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description || ''}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="default_rate">Default Tax Rate (%)</Label>
                  <Input
                    id="default_rate"
                    type="number"
                    step="0.01"
                    value={formData.default_rate || 0}
                    onChange={(e) => setFormData({ ...formData, default_rate: parseFloat(e.target.value) })}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    This is a reference rate; actual rates are determined by tax rules
                  </p>
                </div>
              </>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                <Save className="w-4 h-4 mr-2" />
                {editingItem ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TaxConfiguration;

