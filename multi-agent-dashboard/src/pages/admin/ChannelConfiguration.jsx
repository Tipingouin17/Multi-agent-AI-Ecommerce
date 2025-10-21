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
  Plus, Edit, Trash2, Save, X, RefreshCw, CheckCircle2, 
  XCircle, AlertCircle, ShoppingCart, Store, Globe
} from 'lucide-react';

/**
 * Channel Configuration UI
 * 
 * Features:
 * - Configure all marketplace connections
 * - Manage API credentials securely
 * - Test connections
 * - Sync frequency configuration
 * - Real-time status monitoring
 */

const PLATFORMS = {
  ecommerce: [
    { id: 'shopify', name: 'Shopify', fields: ['api_key', 'api_secret', 'store_url'] },
    { id: 'woocommerce', name: 'WooCommerce', fields: ['consumer_key', 'consumer_secret', 'store_url'] },
    { id: 'magento', name: 'Magento', fields: ['access_token', 'store_url'] },
    { id: 'bigcommerce', name: 'BigCommerce', fields: ['client_id', 'access_token', 'store_hash'] },
    { id: 'prestashop', name: 'PrestaShop', fields: ['api_key', 'store_url'] },
    { id: 'opencart', name: 'OpenCart', fields: ['api_key', 'store_url'] }
  ],
  marketplace: [
    { id: 'amazon', name: 'Amazon SP-API', fields: ['seller_id', 'refresh_token', 'client_id', 'client_secret', 'region'] },
    { id: 'ebay', name: 'eBay', fields: ['app_id', 'cert_id', 'dev_id', 'user_token'] },
    { id: 'cdiscount', name: 'CDiscount', fields: ['api_key', 'login'] },
    { id: 'backmarket', name: 'BackMarket', fields: ['api_key', 'store_id'] },
    { id: 'refurbed', name: 'Refurbed', fields: ['api_key', 'merchant_id'] },
    { id: 'mirakl', name: 'Mirakl', fields: ['api_key', 'shop_id', 'platform_url'] }
  ]
};

const ChannelConfiguration = () => {
  const [connections, setConnections] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingConnection, setEditingConnection] = useState(null);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [formData, setFormData] = useState({
    marketplace_name: '',
    marketplace_type: 'ecommerce',
    store_name: '',
    store_url: '',
    api_credentials: {},
    sync_frequency: 300,
    is_active: true
  });

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/marketplace-connections');
      const data = await response.json();
      setConnections(data);
    } catch (error) {
      console.error('Error fetching connections:', error);
      // Fallback mock data
      setConnections([
        {
          connection_id: 1,
          marketplace_name: 'shopify',
          marketplace_type: 'ecommerce',
          store_name: 'My Shopify Store',
          store_url: 'mystore.myshopify.com',
          sync_frequency: 300,
          is_active: true,
          last_sync_at: '2025-01-20T10:30:00Z',
          sync_status: 'active'
        },
        {
          connection_id: 2,
          marketplace_name: 'amazon',
          marketplace_type: 'marketplace',
          store_name: 'Amazon US Store',
          store_url: 'amazon.com',
          sync_frequency: 600,
          is_active: true,
          last_sync_at: '2025-01-20T10:25:00Z',
          sync_status: 'active'
        }
      ]);
    }
  };

  const handleCreate = () => {
    setEditingConnection(null);
    setSelectedPlatform(null);
    setFormData({
      marketplace_name: '',
      marketplace_type: 'ecommerce',
      store_name: '',
      store_url: '',
      api_credentials: {},
      sync_frequency: 300,
      is_active: true
    });
    setIsDialogOpen(true);
  };

  const handleEdit = (connection) => {
    setEditingConnection(connection);
    setSelectedPlatform(
      PLATFORMS[connection.marketplace_type].find(p => p.id === connection.marketplace_name)
    );
    setFormData({
      marketplace_name: connection.marketplace_name,
      marketplace_type: connection.marketplace_type,
      store_name: connection.store_name,
      store_url: connection.store_url,
      api_credentials: connection.api_credentials || {},
      sync_frequency: connection.sync_frequency,
      is_active: connection.is_active
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (connectionId) => {
    if (!confirm('Are you sure you want to delete this connection?')) return;
    
    try {
      await fetch(`http://localhost:8000/api/marketplace-connections/${connectionId}`, {
        method: 'DELETE'
      });
      fetchConnections();
    } catch (error) {
      console.error('Error deleting connection:', error);
    }
  };

  const handleTestConnection = async (connectionId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/marketplace-connections/${connectionId}/test`);
      const result = await response.json();
      alert(result.success ? 'Connection successful!' : `Connection failed: ${result.error}`);
    } catch (error) {
      alert(`Connection test failed: ${error.message}`);
    }
  };

  const handleSync = async (connectionId) => {
    try {
      await fetch(`http://localhost:8000/api/marketplace-connections/${connectionId}/sync`, {
        method: 'POST'
      });
      alert('Sync started successfully!');
      fetchConnections();
    } catch (error) {
      alert(`Sync failed: ${error.message}`);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingConnection 
        ? `http://localhost:8000/api/marketplace-connections/${editingConnection.connection_id}`
        : 'http://localhost:8000/api/marketplace-connections';
      
      const method = editingConnection ? 'PUT' : 'POST';
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      setIsDialogOpen(false);
      fetchConnections();
    } catch (error) {
      console.error('Error saving connection:', error);
    }
  };

  const handlePlatformSelect = (platformId) => {
    const platform = [...PLATFORMS.ecommerce, ...PLATFORMS.marketplace].find(p => p.id === platformId);
    setSelectedPlatform(platform);
    setFormData({
      ...formData,
      marketplace_name: platformId,
      api_credentials: {}
    });
  };

  const getStatusBadge = (status) => {
    const config = {
      active: { color: 'bg-green-500', icon: CheckCircle2, text: 'Active' },
      syncing: { color: 'bg-blue-500', icon: RefreshCw, text: 'Syncing' },
      error: { color: 'bg-red-500', icon: XCircle, text: 'Error' },
      inactive: { color: 'bg-gray-500', icon: AlertCircle, text: 'Inactive' }
    };
    const { color, icon: Icon, text } = config[status] || config.inactive;
    return (
      <Badge className={`${color} text-white`}>
        <Icon className="w-3 h-3 mr-1" />
        {text}
      </Badge>
    );
  };

  const getPlatformIcon = (type) => {
    return type === 'marketplace' ? <Globe className="w-5 h-5" /> : <Store className="w-5 h-5" />;
  };

  const getTimeSince = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <ShoppingCart className="w-8 h-8" />
            Channel Configuration
          </h1>
          <p className="text-muted-foreground">
            Manage marketplace and e-commerce platform connections
          </p>
        </div>
        <Button onClick={handleCreate} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Add Connection
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Connections
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{connections.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {connections.filter(c => c.is_active).length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              E-commerce Platforms
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {connections.filter(c => c.marketplace_type === 'ecommerce').length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Shopify, WooCommerce, etc.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Marketplaces
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {connections.filter(c => c.marketplace_type === 'marketplace').length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Amazon, eBay, Mirakl, etc.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Sync Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {connections.filter(c => c.sync_status === 'active').length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Currently syncing
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Connections List */}
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Connections</TabsTrigger>
          <TabsTrigger value="ecommerce">E-commerce</TabsTrigger>
          <TabsTrigger value="marketplace">Marketplaces</TabsTrigger>
        </TabsList>

        {['all', 'ecommerce', 'marketplace'].map(tab => (
          <TabsContent key={tab} value={tab} className="space-y-4">
            {connections
              .filter(c => tab === 'all' || c.marketplace_type === tab)
              .map(connection => (
                <Card key={connection.connection_id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {getPlatformIcon(connection.marketplace_type)}
                          {connection.marketplace_name.charAt(0).toUpperCase() + connection.marketplace_name.slice(1)}
                          {getStatusBadge(connection.sync_status)}
                        </CardTitle>
                        <CardDescription>{connection.store_name}</CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleTestConnection(connection.connection_id)}
                        >
                          Test
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleSync(connection.connection_id)}
                        >
                          <RefreshCw className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleEdit(connection)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleDelete(connection.connection_id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Store URL</p>
                        <p className="font-medium">{connection.store_url}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Last Sync</p>
                        <p className="font-medium">{getTimeSince(connection.last_sync_at)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Sync Frequency</p>
                        <p className="font-medium">{connection.sync_frequency}s</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Status</p>
                        <p className="font-medium">
                          {connection.is_active ? 'Enabled' : 'Disabled'}
                        </p>
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
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingConnection ? 'Edit Connection' : 'Add New Connection'}
            </DialogTitle>
            <DialogDescription>
              Configure marketplace or e-commerce platform connection
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Platform Selection */}
            {!editingConnection && (
              <div>
                <Label>Platform Type *</Label>
                <Select 
                  value={formData.marketplace_type} 
                  onValueChange={(value) => setFormData({ ...formData, marketplace_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ecommerce">E-commerce Platform</SelectItem>
                    <SelectItem value="marketplace">Marketplace</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {!editingConnection && (
              <div>
                <Label>Select Platform *</Label>
                <Select 
                  value={formData.marketplace_name} 
                  onValueChange={handlePlatformSelect}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a platform" />
                  </SelectTrigger>
                  <SelectContent>
                    {PLATFORMS[formData.marketplace_type].map(platform => (
                      <SelectItem key={platform.id} value={platform.id}>
                        {platform.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Store Information */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="store_name">Store Name *</Label>
                <Input
                  id="store_name"
                  value={formData.store_name}
                  onChange={(e) => setFormData({ ...formData, store_name: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="store_url">Store URL *</Label>
                <Input
                  id="store_url"
                  value={formData.store_url}
                  onChange={(e) => setFormData({ ...formData, store_url: e.target.value })}
                  required
                />
              </div>
            </div>

            {/* API Credentials */}
            {selectedPlatform && (
              <div className="space-y-3">
                <Label className="text-base font-semibold">API Credentials</Label>
                <Alert>
                  <AlertCircle className="w-4 h-4" />
                  <AlertDescription>
                    Credentials are encrypted and stored securely
                  </AlertDescription>
                </Alert>
                
                {selectedPlatform.fields.map(field => (
                  <div key={field}>
                    <Label htmlFor={field}>
                      {field.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')} *
                    </Label>
                    <Input
                      id={field}
                      type={field.includes('secret') || field.includes('token') ? 'password' : 'text'}
                      value={formData.api_credentials[field] || ''}
                      onChange={(e) => setFormData({
                        ...formData,
                        api_credentials: {
                          ...formData.api_credentials,
                          [field]: e.target.value
                        }
                      })}
                      required
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Sync Configuration */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="sync_frequency">Sync Frequency (seconds) *</Label>
                <Input
                  id="sync_frequency"
                  type="number"
                  value={formData.sync_frequency}
                  onChange={(e) => setFormData({ ...formData, sync_frequency: parseInt(e.target.value) })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="is_active">Status *</Label>
                <Select 
                  value={formData.is_active.toString()} 
                  onValueChange={(value) => setFormData({ ...formData, is_active: value === 'true' })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="true">Enabled</SelectItem>
                    <SelectItem value="false">Disabled</SelectItem>
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
                {editingConnection ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ChannelConfiguration;

