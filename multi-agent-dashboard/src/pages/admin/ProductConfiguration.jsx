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
  Plus, Edit, Trash2, Save, X, Package, Tag, 
  Grid, Archive, CheckCircle2, Layers
} from 'lucide-react';

/**
 * Product Configuration UI
 * 
 * Features:
 * - Manage product categories (hierarchical)
 * - Define product attributes (color, size, material, etc.)
 * - Create variant templates
 * - Configure product types
 * - Archive/restore functionality
 */

const ProductConfiguration = () => {
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState(null);
  const [attributes, setAttributes] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState('category'); // 'category', 'attribute', 'template'
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    fetchCategories();
    fetchAttributes();
    fetchTemplates();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await fetch('http://localhost:8003/api/categories');
      const data = await response.json();
      setCategories(data);
    } catch (error) {
      console.error('Error fetching categories:', error);
      setError({
        message: 'Failed to load categories from database',
        details: error.message,
        retry: fetchCategories
      });
      setCategories([]); // Empty array, NO mock data
    }
  };

  const fetchAttributes = async () => {
    try {
      const response = await fetch('http://localhost:8003/api/categories');
      const data = await response.json();
      setAttributes(data);
    } catch (error) {
      console.error('Error fetching attributes:', error);
      // Mock data
      setAttributes([
        {
          attribute_id: 1,
          attribute_name: 'Color',
          attribute_type: 'select',
          is_variant: true,
          is_filterable: true,
          values: ['Black', 'White', 'Red', 'Blue', 'Silver'],
          usage_count: 234
        },
        {
          attribute_id: 2,
          attribute_name: 'Size',
          attribute_type: 'select',
          is_variant: true,
          is_filterable: true,
          values: ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
          usage_count: 189
        },
        {
          attribute_id: 3,
          attribute_name: 'Storage',
          attribute_type: 'select',
          is_variant: true,
          is_filterable: true,
          values: ['64GB', '128GB', '256GB', '512GB', '1TB'],
          usage_count: 145
        },
        {
          attribute_id: 4,
          attribute_name: 'Material',
          attribute_type: 'text',
          is_variant: false,
          is_filterable: true,
          values: [],
          usage_count: 98
        }
      ]);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch('http://localhost:8003/api/categories');
      const data = await response.json();
      setTemplates(data);
    } catch (error) {
      console.error('Error fetching templates:', error);
      // Mock data
      setTemplates([
        {
          template_id: 1,
          template_name: 'Smartphone Template',
          category_id: 2,
          attributes: ['Color', 'Storage', 'RAM'],
          variant_attributes: ['Color', 'Storage'],
          is_active: true,
          usage_count: 45
        },
        {
          template_id: 2,
          template_name: 'Laptop Template',
          category_id: 3,
          attributes: ['Color', 'Storage', 'RAM', 'Processor', 'Screen Size'],
          variant_attributes: ['Color', 'Storage', 'RAM'],
          is_active: true,
          usage_count: 32
        },
        {
          template_id: 3,
          template_name: 'Clothing Template',
          category_id: 5,
          attributes: ['Color', 'Size', 'Material'],
          variant_attributes: ['Color', 'Size'],
          is_active: true,
          usage_count: 189
        }
      ]);
    }
  };

  const handleCreate = (type) => {
    setDialogType(type);
    setEditingItem(null);
    
    if (type === 'category') {
      setFormData({
        category_name: '',
        parent_category_id: null,
        description: '',
        slug: '',
        is_active: true
      });
    } else if (type === 'attribute') {
      setFormData({
        attribute_name: '',
        attribute_type: 'select',
        is_variant: false,
        is_filterable: true,
        values: []
      });
    } else if (type === 'template') {
      setFormData({
        template_name: '',
        category_id: null,
        attributes: [],
        variant_attributes: []
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
        category: 'product-categories',
        attribute: 'product-attributes',
        template: 'product-templates'
      };
      
      await fetch(`http://localhost:8000/api/${endpoints[type]}/${id}`, {
        method: 'DELETE'
      });
      
      if (type === 'category') fetchCategories();
      else if (type === 'attribute') fetchAttributes();
      else if (type === 'template') fetchTemplates();
    } catch (error) {
      console.error(`Error deleting ${type}:`, error);
    }
  };

  const handleArchive = async (id, type) => {
    try {
      const endpoints = {
        category: 'product-categories',
        attribute: 'product-attributes',
        template: 'product-templates'
      };
      
      await fetch(`http://localhost:8000/api/${endpoints[type]}/${id}/archive`, {
        method: 'PATCH'
      });
      
      if (type === 'category') fetchCategories();
      else if (type === 'attribute') fetchAttributes();
      else if (type === 'template') fetchTemplates();
    } catch (error) {
      console.error(`Error archiving ${type}:`, error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const endpoints = {
        category: 'product-categories',
        attribute: 'product-attributes',
        template: 'product-templates'
      };
      
      const idFields = {
        category: 'category_id',
        attribute: 'attribute_id',
        template: 'template_id'
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
      
      if (dialogType === 'category') fetchCategories();
      else if (dialogType === 'attribute') fetchAttributes();
      else if (dialogType === 'template') fetchTemplates();
    } catch (error) {
      console.error(`Error saving ${dialogType}:`, error);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Package className="w-8 h-8" />
            Product Configuration
          </h1>
          <p className="text-muted-foreground">
            Manage categories, attributes, and product templates
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Categories
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{categories.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {categories.filter(c => c.is_active).length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Attributes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{attributes.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {attributes.filter(a => a.is_variant).length} variant attributes
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Templates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{templates.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {templates.reduce((sum, t) => sum + (t.usage_count || 0), 0)} products using templates
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="categories">
        <TabsList>
          <TabsTrigger value="categories">
            <Grid className="w-4 h-4 mr-2" />
            Categories
          </TabsTrigger>
          <TabsTrigger value="attributes">
            <Tag className="w-4 h-4 mr-2" />
            Attributes
          </TabsTrigger>
          <TabsTrigger value="templates">
            <Layers className="w-4 h-4 mr-2" />
            Templates
          </TabsTrigger>
        </TabsList>

        {/* Categories Tab */}
        <TabsContent value="categories" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => handleCreate('category')} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Category
            </Button>
          </div>

          {categories.map(category => (
            <Card key={category.category_id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {category.category_name}
                      {category.is_active ? (
                        <Badge className="bg-green-500 text-white">Active</Badge>
                      ) : (
                        <Badge className="bg-gray-500 text-white">Archived</Badge>
                      )}
                      {category.parent_category_id && (
                        <Badge variant="outline">Subcategory</Badge>
                      )}
                    </CardTitle>
                    <CardDescription>{category.description}</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleArchive(category.category_id, 'category')}
                    >
                      <Archive className="w-4 h-4" />
                    </Button>
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
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Slug</p>
                    <p className="text-sm font-medium">{category.slug}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Products</p>
                    <p className="text-sm font-medium">{category.product_count || 0}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Subcategories</p>
                    <p className="text-sm font-medium">{category.subcategories || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Attributes Tab */}
        <TabsContent value="attributes" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => handleCreate('attribute')} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Attribute
            </Button>
          </div>

          {attributes.map(attribute => (
            <Card key={attribute.attribute_id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {attribute.attribute_name}
                      <Badge variant="outline">{attribute.attribute_type}</Badge>
                      {attribute.is_variant && (
                        <Badge className="bg-purple-500 text-white">Variant</Badge>
                      )}
                      {attribute.is_filterable && (
                        <Badge className="bg-blue-500 text-white">Filterable</Badge>
                      )}
                    </CardTitle>
                    <CardDescription>Used in {attribute.usage_count || 0} products</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleEdit(attribute, 'attribute')}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleDelete(attribute.attribute_id, 'attribute')}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              {attribute.values && attribute.values.length > 0 && (
                <CardContent>
                  <Label className="text-xs text-muted-foreground">Predefined Values</Label>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {attribute.values.map((value, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs">
                        {value}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              )}
            </Card>
          ))}
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => handleCreate('template')} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Template
            </Button>
          </div>

          {templates.map(template => (
            <Card key={template.template_id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {template.template_name}
                      {template.is_active ? (
                        <Badge className="bg-green-500 text-white">
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                          Active
                        </Badge>
                      ) : (
                        <Badge className="bg-gray-500 text-white">Inactive</Badge>
                      )}
                    </CardTitle>
                    <CardDescription>Used by {template.usage_count || 0} products</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleEdit(template, 'template')}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleDelete(template.template_id, 'template')}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <Label className="text-xs text-muted-foreground">All Attributes</Label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {template.attributes?.map((attr, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {attr}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Variant Attributes</Label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {template.variant_attributes?.map((attr, idx) => (
                        <Badge key={idx} className="bg-purple-500 text-white text-xs">
                          {attr}
                        </Badge>
                      ))}
                    </div>
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
              {dialogType === 'category' && 'Create product categories for organizing your catalog'}
              {dialogType === 'attribute' && 'Define product attributes for variants and filters'}
              {dialogType === 'template' && 'Create templates to standardize product creation'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
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
                  <Label htmlFor="slug">Slug *</Label>
                  <Input
                    id="slug"
                    value={formData.slug || ''}
                    onChange={(e) => setFormData({ ...formData, slug: e.target.value.toLowerCase().replace(/\s+/g, '-') })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description || ''}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                  />
                </div>
                <div>
                  <Label htmlFor="parent_category_id">Parent Category</Label>
                  <Select 
                    value={formData.parent_category_id?.toString() || 'none'} 
                    onValueChange={(value) => setFormData({ ...formData, parent_category_id: value === 'none' ? null : parseInt(value) })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None (Top Level)</SelectItem>
                      {categories.filter(c => !c.parent_category_id).map(cat => (
                        <SelectItem key={cat.category_id} value={cat.category_id.toString()}>
                          {cat.category_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            {dialogType === 'attribute' && (
              <>
                <div>
                  <Label htmlFor="attribute_name">Attribute Name *</Label>
                  <Input
                    id="attribute_name"
                    value={formData.attribute_name || ''}
                    onChange={(e) => setFormData({ ...formData, attribute_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="attribute_type">Attribute Type *</Label>
                  <Select 
                    value={formData.attribute_type || 'select'} 
                    onValueChange={(value) => setFormData({ ...formData, attribute_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="select">Select (Dropdown)</SelectItem>
                      <SelectItem value="text">Text</SelectItem>
                      <SelectItem value="number">Number</SelectItem>
                      <SelectItem value="boolean">Boolean</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {formData.attribute_type === 'select' && (
                  <div>
                    <Label htmlFor="values">Predefined Values (comma-separated)</Label>
                    <Textarea
                      id="values"
                      value={formData.values?.join(', ') || ''}
                      onChange={(e) => setFormData({ ...formData, values: e.target.value.split(',').map(v => v.trim()) })}
                      placeholder="Red, Blue, Green"
                      rows={2}
                    />
                  </div>
                )}
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="is_variant"
                    checked={formData.is_variant || false}
                    onChange={(e) => setFormData({ ...formData, is_variant: e.target.checked })}
                    className="rounded"
                  />
                  <Label htmlFor="is_variant">Use for Product Variants</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="is_filterable"
                    checked={formData.is_filterable !== false}
                    onChange={(e) => setFormData({ ...formData, is_filterable: e.target.checked })}
                    className="rounded"
                  />
                  <Label htmlFor="is_filterable">Show in Filters</Label>
                </div>
              </>
            )}

            {dialogType === 'template' && (
              <>
                <div>
                  <Label htmlFor="template_name">Template Name *</Label>
                  <Input
                    id="template_name"
                    value={formData.template_name || ''}
                    onChange={(e) => setFormData({ ...formData, template_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="category_id">Category *</Label>
                  <Select 
                    value={formData.category_id?.toString() || ''} 
                    onValueChange={(value) => setFormData({ ...formData, category_id: parseInt(value) })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map(cat => (
                        <SelectItem key={cat.category_id} value={cat.category_id.toString()}>
                          {cat.category_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Alert>
                  <AlertDescription>
                    Select attributes that will be included in products using this template.
                    Mark variant attributes to create product variations.
                  </AlertDescription>
                </Alert>
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

export default ProductConfiguration;

