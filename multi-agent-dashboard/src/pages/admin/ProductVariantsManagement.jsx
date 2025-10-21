import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Edit, Trash2, Package, DollarSign, BarChart3 } from 'lucide-react';

/**
 * Product Variants Management Component
 * 
 * Manages product variants including:
 * - Creating variants with attributes (size, color, etc.)
 * - Managing variant pricing
 * - Tracking variant inventory
 * - Variant performance analytics
 */
const ProductVariantsManagement = () => {
  const [variants, setVariants] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  
  // Form state for creating new variant
  const [newVariant, setNewVariant] = useState({
    parent_product_id: '',
    variant_sku: '',
    variant_name: '',
    attributes: [],
    price: '',
    compare_at_price: '',
    stock_quantity: 0
  });

  useEffect(() => {
    fetchVariants();
  }, []);

  const fetchVariants = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/products/variants');
      const data = await response.json();
      setVariants(data);
    } catch (err) {
      setError('Failed to load variants');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVariant = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch('/api/products/variants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newVariant)
      });
      
      if (response.ok) {
        await fetchVariants();
        setShowCreateForm(false);
        setNewVariant({
          parent_product_id: '',
          variant_sku: '',
          variant_name: '',
          attributes: [],
          price: '',
          compare_at_price: '',
          stock_quantity: 0
        });
      }
    } catch (err) {
      setError('Failed to create variant');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteVariant = async (variantId) => {
    if (!confirm('Are you sure you want to delete this variant?')) return;
    
    try {
      await fetch(`/api/products/variants/${variantId}`, {
        method: 'DELETE'
      });
      await fetchVariants();
    } catch (err) {
      setError('Failed to delete variant');
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Product Variants</h1>
            <p className="text-muted-foreground mt-1">
              Manage product variations, pricing, and inventory
            </p>
          </div>
          <Button 
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-primary hover:bg-primary/90"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Variant
          </Button>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Create Variant Form */}
        {showCreateForm && (
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle>Create New Variant</CardTitle>
              <CardDescription>Add a new product variant with attributes</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateVariant} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="parent_product_id">Product ID</Label>
                    <Input
                      id="parent_product_id"
                      value={newVariant.parent_product_id}
                      onChange={(e) => setNewVariant({...newVariant, parent_product_id: e.target.value})}
                      placeholder="prod-001"
                      required
                      className="bg-background border-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="variant_sku">Variant SKU</Label>
                    <Input
                      id="variant_sku"
                      value={newVariant.variant_sku}
                      onChange={(e) => setNewVariant({...newVariant, variant_sku: e.target.value})}
                      placeholder="TSHIRT-RED-L"
                      required
                      className="bg-background border-input"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="variant_name">Variant Name</Label>
                  <Input
                    id="variant_name"
                    value={newVariant.variant_name}
                    onChange={(e) => setNewVariant({...newVariant, variant_name: e.target.value})}
                    placeholder="Red T-Shirt - Large"
                    className="bg-background border-input"
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="price">Price ($)</Label>
                    <Input
                      id="price"
                      type="number"
                      step="0.01"
                      value={newVariant.price}
                      onChange={(e) => setNewVariant({...newVariant, price: e.target.value})}
                      placeholder="29.99"
                      required
                      className="bg-background border-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="compare_at_price">Compare Price ($)</Label>
                    <Input
                      id="compare_at_price"
                      type="number"
                      step="0.01"
                      value={newVariant.compare_at_price}
                      onChange={(e) => setNewVariant({...newVariant, compare_at_price: e.target.value})}
                      placeholder="39.99"
                      className="bg-background border-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="stock_quantity">Stock</Label>
                    <Input
                      id="stock_quantity"
                      type="number"
                      value={newVariant.stock_quantity}
                      onChange={(e) => setNewVariant({...newVariant, stock_quantity: parseInt(e.target.value)})}
                      placeholder="100"
                      required
                      className="bg-background border-input"
                    />
                  </div>
                </div>

                <div className="flex gap-2 justify-end">
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setShowCreateForm(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Creating...' : 'Create Variant'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Variants List */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle>All Variants</CardTitle>
            <CardDescription>
              {variants.length} variants across all products
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading && <p className="text-muted-foreground">Loading variants...</p>}
            
            {!loading && variants.length === 0 && (
              <div className="text-center py-12">
                <Package className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No variants found</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Create your first product variant to get started
                </p>
              </div>
            )}

            {!loading && variants.length > 0 && (
              <div className="space-y-4">
                {variants.map((variant) => (
                  <div 
                    key={variant.variant_id}
                    className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-foreground">
                          {variant.variant_name || variant.variant_sku}
                        </h3>
                        <Badge variant={variant.is_active ? "default" : "secondary"}>
                          {variant.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      <div className="flex gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Package className="w-4 h-4" />
                          SKU: {variant.variant_sku}
                        </span>
                        <span className="flex items-center gap-1">
                          <DollarSign className="w-4 h-4" />
                          ${variant.price}
                        </span>
                        <span className="flex items-center gap-1">
                          <BarChart3 className="w-4 h-4" />
                          Stock: {variant.stock_quantity}
                        </span>
                      </div>
                      {variant.attributes && variant.attributes.length > 0 && (
                        <div className="flex gap-2 mt-2">
                          {variant.attributes.map((attr, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {attr.attribute_name}: {attr.attribute_value}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleDeleteVariant(variant.variant_id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Analytics Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-sm font-medium">Total Variants</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{variants.length}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Across all products
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-sm font-medium">Active Variants</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                {variants.filter(v => v.is_active).length}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Currently available
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-sm font-medium">Total Inventory</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                {variants.reduce((sum, v) => sum + (v.stock_quantity || 0), 0)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Units in stock
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ProductVariantsManagement;

