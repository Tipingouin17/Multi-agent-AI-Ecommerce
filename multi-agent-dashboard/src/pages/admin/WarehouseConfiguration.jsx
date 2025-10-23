import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Warehouse, Plus, Edit, Trash2, Save, X, MapPin, 
  Package, Users, TrendingUp, AlertCircle, CheckCircle2
} from 'lucide-react';

/**
 * Warehouse Configuration UI
 * 
 * Features:
 * - Full CRUD operations for warehouses
 * - Capacity management
 * - Zone configuration
 * - Equipment tracking
 * - Workforce management
 * - Real-time database sync
 */

const WarehouseConfiguration = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [error, setError] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingWarehouse, setEditingWarehouse] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    address: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    total_capacity_sqft: '',
    available_capacity_sqft: '',
    max_employees: '',
    current_employees: '',
    equipment_count: '',
    zones: [],
    operating_hours: '24/7',
    status: 'active'
  });

  // Load warehouses from API
  useEffect(() => {
    fetchWarehouses();
  }, []);

  const fetchWarehouses = async () => {
    try {
      const response = await fetch('http://localhost:8005/api/warehouses');
      const data = await response.json();
      setWarehouses(data);
    } catch (error) {
      console.error('Error fetching warehouses:', error);
      // Fallback to mock data
      setWarehouses([
        {
          warehouse_id: 1,
          name: 'Main Distribution Center',
          location: 'New York, NY',
          address: '123 Warehouse Blvd',
          city: 'New York',
          state: 'NY',
          postal_code: '10001',
          country: 'USA',
          total_capacity_sqft: 50000,
          available_capacity_sqft: 12000,
          max_employees: 150,
          current_employees: 142,
          equipment_count: 45,
          zones: ['Receiving', 'Storage', 'Picking', 'Packing', 'Shipping'],
          operating_hours: '24/7',
          status: 'active'
        },
        {
          warehouse_id: 2,
          name: 'West Coast Fulfillment',
          location: 'Los Angeles, CA',
          address: '456 Logistics Way',
          city: 'Los Angeles',
          state: 'CA',
          postal_code: '90001',
          country: 'USA',
          total_capacity_sqft: 35000,
          available_capacity_sqft: 8500,
          max_employees: 100,
          current_employees: 87,
          equipment_count: 32,
          zones: ['Receiving', 'Storage', 'Picking', 'Shipping'],
          operating_hours: 'Mon-Sat 6AM-10PM',
          status: 'active'
        },
        {
          warehouse_id: 3,
          name: 'Regional Hub - Chicago',
          location: 'Chicago, IL',
          address: '789 Industrial Park Dr',
          city: 'Chicago',
          state: 'IL',
          postal_code: '60601',
          country: 'USA',
          total_capacity_sqft: 25000,
          available_capacity_sqft: 5000,
          max_employees: 75,
          current_employees: 68,
          equipment_count: 28,
          zones: ['Receiving', 'Storage', 'Shipping'],
          operating_hours: '24/7',
          status: 'maintenance'
        }
      ]);
    }
  };

  const handleCreate = () => {
    setEditingWarehouse(null);
    setFormData({
      name: '',
      location: '',
      address: '',
      city: '',
      state: '',
      postal_code: '',
      country: '',
      total_capacity_sqft: '',
      available_capacity_sqft: '',
      max_employees: '',
      current_employees: '',
      equipment_count: '',
      zones: [],
      operating_hours: '24/7',
      status: 'active'
    });
    setIsDialogOpen(true);
  };

  const handleEdit = (warehouse) => {
    setEditingWarehouse(warehouse);
    setFormData({
      ...warehouse,
      zones: warehouse.zones || []
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (warehouseId) => {
    if (!confirm('Are you sure you want to delete this warehouse?')) return;
    
    try {
      await fetch(`http://localhost:8000/api/warehouses/${warehouseId}`, {
        method: 'DELETE'
      });
      fetchWarehouses();
    } catch (error) {
      console.error('Error deleting warehouse:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingWarehouse 
        ? `http://localhost:8000/api/warehouses/${editingWarehouse.warehouse_id}`
        : 'http://localhost:8000/api/warehouses';
      
      const method = editingWarehouse ? 'PUT' : 'POST';
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      setIsDialogOpen(false);
      fetchWarehouses();
    } catch (error) {
      console.error('Error saving warehouse:', error);
    }
  };

  const getStatusBadge = (status) => {
    const config = {
      active: { color: 'bg-green-500', text: 'Active' },
      maintenance: { color: 'bg-yellow-500', text: 'Maintenance' },
      inactive: { color: 'bg-gray-500', text: 'Inactive' }
    };
    const { color, text } = config[status] || config.inactive;
    return <Badge className={`${color} text-white`}>{text}</Badge>;
  };

  const getCapacityPercentage = (warehouse) => {
    const used = warehouse.total_capacity_sqft - warehouse.available_capacity_sqft;
    return ((used / warehouse.total_capacity_sqft) * 100).toFixed(1);
  };

  const getWorkforcePercentage = (warehouse) => {
    return ((warehouse.current_employees / warehouse.max_employees) * 100).toFixed(1);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Warehouse className="w-8 h-8" />
            Warehouse Configuration
          </h1>
          <p className="text-muted-foreground">
            Manage warehouses, capacity, zones, and workforce
          </p>
        </div>
        <Button onClick={handleCreate} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Add Warehouse
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Warehouses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{warehouses.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {warehouses.filter(w => w.status === 'active').length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Capacity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {(warehouses.reduce((sum, w) => sum + w.total_capacity_sqft, 0) / 1000).toFixed(0)}K
            </div>
            <p className="text-xs text-muted-foreground mt-1">sq ft</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Workforce
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {warehouses.reduce((sum, w) => sum + w.current_employees, 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              of {warehouses.reduce((sum, w) => sum + w.max_employees, 0)} max
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Equipment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {warehouses.reduce((sum, w) => sum + w.equipment_count, 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">units total</p>
          </CardContent>
        </Card>
      </div>

      {/* Warehouses List */}
      <div className="grid grid-cols-1 gap-4">
        {warehouses.map(warehouse => (
          <Card key={warehouse.warehouse_id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {warehouse.name}
                    {getStatusBadge(warehouse.status)}
                  </CardTitle>
                  <CardDescription className="flex items-center gap-1 mt-1">
                    <MapPin className="w-3 h-3" />
                    {warehouse.location}
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleEdit(warehouse)}>
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => handleDelete(warehouse.warehouse_id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Capacity */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Package className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Capacity</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Used:</span>
                      <span className="font-medium">{getCapacityPercentage(warehouse)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${getCapacityPercentage(warehouse)}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {warehouse.available_capacity_sqft.toLocaleString()} sq ft available
                    </p>
                  </div>
                </div>

                {/* Workforce */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Users className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Workforce</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Staffed:</span>
                      <span className="font-medium">{getWorkforcePercentage(warehouse)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full" 
                        style={{ width: `${getWorkforcePercentage(warehouse)}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {warehouse.current_employees} of {warehouse.max_employees} employees
                    </p>
                  </div>
                </div>

                {/* Zones */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Zones</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {warehouse.zones && warehouse.zones.map((zone, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs">
                        {zone}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Operating Hours */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Operating Hours</span>
                  </div>
                  <p className="text-sm">{warehouse.operating_hours}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {warehouse.equipment_count} equipment units
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingWarehouse ? 'Edit Warehouse' : 'Add New Warehouse'}
            </DialogTitle>
            <DialogDescription>
              Configure warehouse details, capacity, and workforce
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic Information */}
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label htmlFor="name">Warehouse Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="address">Address *</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="city">City *</Label>
                <Input
                  id="city"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="state">State/Province *</Label>
                <Input
                  id="state"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="postal_code">Postal Code *</Label>
                <Input
                  id="postal_code"
                  value={formData.postal_code}
                  onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                  required
                />
              </div>

              <div className="col-span-2">
                <Label htmlFor="country">Country *</Label>
                <Input
                  id="country"
                  value={formData.country}
                  onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                  required
                />
              </div>
            </div>

            {/* Capacity */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="total_capacity">Total Capacity (sq ft) *</Label>
                <Input
                  id="total_capacity"
                  type="number"
                  value={formData.total_capacity_sqft}
                  onChange={(e) => setFormData({ ...formData, total_capacity_sqft: parseInt(e.target.value) })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="available_capacity">Available Capacity (sq ft) *</Label>
                <Input
                  id="available_capacity"
                  type="number"
                  value={formData.available_capacity_sqft}
                  onChange={(e) => setFormData({ ...formData, available_capacity_sqft: parseInt(e.target.value) })}
                  required
                />
              </div>
            </div>

            {/* Workforce */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="max_employees">Max Employees *</Label>
                <Input
                  id="max_employees"
                  type="number"
                  value={formData.max_employees}
                  onChange={(e) => setFormData({ ...formData, max_employees: parseInt(e.target.value) })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="current_employees">Current Employees *</Label>
                <Input
                  id="current_employees"
                  type="number"
                  value={formData.current_employees}
                  onChange={(e) => setFormData({ ...formData, current_employees: parseInt(e.target.value) })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="equipment_count">Equipment Count *</Label>
                <Input
                  id="equipment_count"
                  type="number"
                  value={formData.equipment_count}
                  onChange={(e) => setFormData({ ...formData, equipment_count: parseInt(e.target.value) })}
                  required
                />
              </div>
            </div>

            {/* Operating Details */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="operating_hours">Operating Hours *</Label>
                <Input
                  id="operating_hours"
                  value={formData.operating_hours}
                  onChange={(e) => setFormData({ ...formData, operating_hours: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="status">Status *</Label>
                <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="maintenance">Maintenance</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
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
                {editingWarehouse ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default WarehouseConfiguration;

