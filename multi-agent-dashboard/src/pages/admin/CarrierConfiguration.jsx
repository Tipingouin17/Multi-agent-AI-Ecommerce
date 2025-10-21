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
  Plus, Edit, Trash2, Save, X, Upload, TrendingUp, 
  Truck, DollarSign, Clock, MapPin, FileText, Sparkles
} from 'lucide-react';

/**
 * Carrier Configuration UI
 * 
 * Features:
 * - Configure carriers and service levels
 * - Upload and parse pricelist documents (AI-powered)
 * - Define rates by region, weight, dimensions
 * - Set SLAs and delivery times
 * - Track carrier performance
 * - AI-powered carrier selection optimization
 */

const SERVICE_LEVELS = [
  { id: 'standard', name: 'Standard', description: '3-5 business days' },
  { id: 'express', name: 'Express', description: '1-2 business days' },
  { id: 'overnight', name: 'Overnight', description: 'Next business day' },
  { id: 'economy', name: 'Economy', description: '5-7 business days' }
];

const REGIONS = [
  { id: 'local', name: 'Local', description: 'Same city/region' },
  { id: 'national', name: 'National', description: 'Within country' },
  { id: 'eu', name: 'European Union', description: 'EU countries' },
  { id: 'international', name: 'International', description: 'Worldwide' }
];

const CarrierConfiguration = () => {
  const [carriers, setCarriers] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isPricelistDialogOpen, setIsPricelistDialogOpen] = useState(false);
  const [editingCarrier, setEditingCarrier] = useState(null);
  const [uploadingCarrier, setUploadingCarrier] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [formData, setFormData] = useState({
    carrier_name: '',
    carrier_code: '',
    service_level: 'standard',
    regions: [],
    base_rate: '',
    per_kg_rate: '',
    per_km_rate: '',
    min_delivery_days: '',
    max_delivery_days: '',
    sla_on_time_percentage: '',
    supports_tracking: true,
    supports_insurance: true,
    max_weight_kg: '',
    max_dimensions: '',
    is_active: true
  });

  useEffect(() => {
    fetchCarriers();
  }, []);

  const fetchCarriers = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/carriers');
      const data = await response.json();
      setCarriers(data);
    } catch (error) {
      console.error('Error fetching carriers:', error);
      // Fallback mock data
      setCarriers([
        {
          carrier_id: 1,
          carrier_name: 'Colis Privé',
          carrier_code: 'COLISPRIVE',
          service_level: 'standard',
          regions: ['local', 'national'],
          base_rate: 5.99,
          per_kg_rate: 0.50,
          per_km_rate: 0.10,
          min_delivery_days: 2,
          max_delivery_days: 3,
          sla_on_time_percentage: 96.5,
          supports_tracking: true,
          supports_insurance: true,
          max_weight_kg: 30,
          max_dimensions: '120x80x80',
          is_active: true,
          total_shipments: 15234,
          avg_delivery_time: 2.3,
          on_time_rate: 96.5
        },
        {
          carrier_id: 2,
          carrier_name: 'UPS',
          carrier_code: 'UPS',
          service_level: 'express',
          regions: ['national', 'eu', 'international'],
          base_rate: 12.99,
          per_kg_rate: 1.20,
          per_km_rate: 0.15,
          min_delivery_days: 1,
          max_delivery_days: 2,
          sla_on_time_percentage: 98.2,
          supports_tracking: true,
          supports_insurance: true,
          max_weight_kg: 70,
          max_dimensions: '150x100x100',
          is_active: true,
          total_shipments: 8932,
          avg_delivery_time: 1.5,
          on_time_rate: 98.2
        },
        {
          carrier_id: 3,
          carrier_name: 'Chronopost',
          carrier_code: 'CHRONOPOST',
          service_level: 'express',
          regions: ['local', 'national', 'eu'],
          base_rate: 10.99,
          per_kg_rate: 0.80,
          per_km_rate: 0.12,
          min_delivery_days: 1,
          max_delivery_days: 2,
          sla_on_time_percentage: 97.8,
          supports_tracking: true,
          supports_insurance: true,
          max_weight_kg: 50,
          max_dimensions: '130x90x90',
          is_active: false,
          total_shipments: 0,
          avg_delivery_time: 0,
          on_time_rate: 0
        }
      ]);
    }
  };

  const handleCreate = () => {
    setEditingCarrier(null);
    setFormData({
      carrier_name: '',
      carrier_code: '',
      service_level: 'standard',
      regions: [],
      base_rate: '',
      per_kg_rate: '',
      per_km_rate: '',
      min_delivery_days: '',
      max_delivery_days: '',
      sla_on_time_percentage: '',
      supports_tracking: true,
      supports_insurance: true,
      max_weight_kg: '',
      max_dimensions: '',
      is_active: true
    });
    setIsDialogOpen(true);
  };

  const handleEdit = (carrier) => {
    setEditingCarrier(carrier);
    setFormData({
      carrier_name: carrier.carrier_name,
      carrier_code: carrier.carrier_code,
      service_level: carrier.service_level,
      regions: carrier.regions || [],
      base_rate: carrier.base_rate,
      per_kg_rate: carrier.per_kg_rate,
      per_km_rate: carrier.per_km_rate,
      min_delivery_days: carrier.min_delivery_days,
      max_delivery_days: carrier.max_delivery_days,
      sla_on_time_percentage: carrier.sla_on_time_percentage,
      supports_tracking: carrier.supports_tracking,
      supports_insurance: carrier.supports_insurance,
      max_weight_kg: carrier.max_weight_kg,
      max_dimensions: carrier.max_dimensions,
      is_active: carrier.is_active
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (carrierId) => {
    if (!confirm('Are you sure you want to delete this carrier?')) return;
    
    try {
      await fetch(`http://localhost:8000/api/carriers/${carrierId}`, {
        method: 'DELETE'
      });
      fetchCarriers();
    } catch (error) {
      console.error('Error deleting carrier:', error);
    }
  };

  const handleUploadPricelist = (carrier) => {
    setUploadingCarrier(carrier);
    setSelectedFile(null);
    setUploadProgress(null);
    setIsPricelistDialogOpen(true);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('carrier_id', uploadingCarrier.carrier_id);

    try {
      setUploadProgress({ status: 'uploading', message: 'Uploading file...' });
      
      const response = await fetch('http://localhost:8000/api/carriers/upload-pricelist', {
        method: 'POST',
        body: formData
      });

      setUploadProgress({ status: 'processing', message: 'AI is analyzing the document...' });
      
      const result = await response.json();
      
      if (result.success) {
        setUploadProgress({ 
          status: 'success', 
          message: `Successfully parsed ${result.rates_count} rates from the document!`,
          details: result.summary
        });
        
        // Refresh carriers after successful upload
        setTimeout(() => {
          fetchCarriers();
          setIsPricelistDialogOpen(false);
        }, 2000);
      } else {
        setUploadProgress({ 
          status: 'error', 
          message: result.error || 'Failed to process document'
        });
      }
    } catch (error) {
      setUploadProgress({ 
        status: 'error', 
        message: `Upload failed: ${error.message}`
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingCarrier 
        ? `http://localhost:8000/api/carriers/${editingCarrier.carrier_id}`
        : 'http://localhost:8000/api/carriers';
      
      const method = editingCarrier ? 'PUT' : 'POST';
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      setIsDialogOpen(false);
      fetchCarriers();
    } catch (error) {
      console.error('Error saving carrier:', error);
    }
  };

  const getServiceLevelBadge = (level) => {
    const colors = {
      standard: 'bg-blue-500',
      express: 'bg-purple-500',
      overnight: 'bg-red-500',
      economy: 'bg-green-500'
    };
    return <Badge className={`${colors[level]} text-white`}>{level}</Badge>;
  };

  const getPerformanceColor = (rate) => {
    if (rate >= 98) return 'text-green-600';
    if (rate >= 95) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Truck className="w-8 h-8" />
            Carrier Configuration
          </h1>
          <p className="text-muted-foreground">
            Manage carriers, rates, and AI-powered selection
          </p>
        </div>
        <Button onClick={handleCreate} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Add Carrier
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Carriers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{carriers.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {carriers.filter(c => c.is_active).length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Shipments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {carriers.reduce((sum, c) => sum + (c.total_shipments || 0), 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              All time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg On-Time Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {carriers.filter(c => c.is_active).length > 0
                ? (carriers.filter(c => c.is_active).reduce((sum, c) => sum + (c.on_time_rate || 0), 0) / carriers.filter(c => c.is_active).length).toFixed(1)
                : 0}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Active carriers
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg Delivery Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {carriers.filter(c => c.is_active).length > 0
                ? (carriers.filter(c => c.is_active).reduce((sum, c) => sum + (c.avg_delivery_time || 0), 0) / carriers.filter(c => c.is_active).length).toFixed(1)
                : 0}d
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Carriers List */}
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Carriers</TabsTrigger>
          <TabsTrigger value="active">Active</TabsTrigger>
          <TabsTrigger value="inactive">Inactive</TabsTrigger>
        </TabsList>

        {['all', 'active', 'inactive'].map(tab => (
          <TabsContent key={tab} value={tab} className="space-y-4">
            {carriers
              .filter(c => tab === 'all' || (tab === 'active' ? c.is_active : !c.is_active))
              .map(carrier => (
                <Card key={carrier.carrier_id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {carrier.carrier_name}
                          {getServiceLevelBadge(carrier.service_level)}
                          {carrier.is_active ? (
                            <Badge className="bg-green-500 text-white">Active</Badge>
                          ) : (
                            <Badge className="bg-gray-500 text-white">Inactive</Badge>
                          )}
                        </CardTitle>
                        <CardDescription>Code: {carrier.carrier_code}</CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleUploadPricelist(carrier)}
                        >
                          <Upload className="w-4 h-4 mr-1" />
                          Upload Pricelist
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleEdit(carrier)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleDelete(carrier.carrier_id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Pricing */}
                      <div>
                        <Label className="text-sm font-semibold flex items-center gap-1">
                          <DollarSign className="w-4 h-4" />
                          Pricing Structure
                        </Label>
                        <div className="grid grid-cols-3 gap-4 mt-2">
                          <div>
                            <p className="text-xs text-muted-foreground">Base Rate</p>
                            <p className="text-sm font-medium">${carrier.base_rate?.toFixed(2)}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">Per KG</p>
                            <p className="text-sm font-medium">${carrier.per_kg_rate?.toFixed(2)}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">Per KM</p>
                            <p className="text-sm font-medium">${carrier.per_km_rate?.toFixed(2)}</p>
                          </div>
                        </div>
                      </div>

                      {/* Delivery & Performance */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-sm font-semibold flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            Delivery Time
                          </Label>
                          <div className="mt-2 space-y-1">
                            <p className="text-sm">
                              {carrier.min_delivery_days}-{carrier.max_delivery_days} business days
                            </p>
                            {carrier.avg_delivery_time > 0 && (
                              <p className="text-xs text-muted-foreground">
                                Avg: {carrier.avg_delivery_time} days ({carrier.total_shipments?.toLocaleString()} shipments)
                              </p>
                            )}
                          </div>
                        </div>

                        <div>
                          <Label className="text-sm font-semibold flex items-center gap-1">
                            <TrendingUp className="w-4 h-4" />
                            Performance
                          </Label>
                          <div className="mt-2">
                            <div className="flex items-baseline gap-2">
                              <span className={`text-2xl font-bold ${getPerformanceColor(carrier.on_time_rate)}`}>
                                {carrier.on_time_rate?.toFixed(1) || 0}%
                              </span>
                              <span className="text-xs text-muted-foreground">on-time delivery</span>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                              SLA Target: {carrier.sla_on_time_percentage}%
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Regions & Capabilities */}
                      <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                        <div>
                          <Label className="text-sm font-semibold flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            Regions
                          </Label>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {carrier.regions?.map((region, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {region}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        <div>
                          <Label className="text-sm font-semibold">Capabilities</Label>
                          <div className="mt-2 space-y-1 text-sm">
                            <p>✓ Tracking: {carrier.supports_tracking ? 'Yes' : 'No'}</p>
                            <p>✓ Insurance: {carrier.supports_insurance ? 'Yes' : 'No'}</p>
                            <p>✓ Max Weight: {carrier.max_weight_kg} kg</p>
                            <p>✓ Max Dimensions: {carrier.max_dimensions} cm</p>
                          </div>
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
              {editingCarrier ? 'Edit Carrier' : 'Add New Carrier'}
            </DialogTitle>
            <DialogDescription>
              Configure carrier details, pricing, and service levels
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic Information */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="carrier_name">Carrier Name *</Label>
                <Input
                  id="carrier_name"
                  value={formData.carrier_name}
                  onChange={(e) => setFormData({ ...formData, carrier_name: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="carrier_code">Carrier Code *</Label>
                <Input
                  id="carrier_code"
                  value={formData.carrier_code}
                  onChange={(e) => setFormData({ ...formData, carrier_code: e.target.value.toUpperCase() })}
                  placeholder="UPS, FEDEX, etc."
                  required
                />
              </div>

              <div>
                <Label htmlFor="service_level">Service Level *</Label>
                <Select value={formData.service_level} onValueChange={(value) => setFormData({ ...formData, service_level: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SERVICE_LEVELS.map(level => (
                      <SelectItem key={level.id} value={level.id}>
                        {level.name} - {level.description}
                      </SelectItem>
                    ))}
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

            {/* Pricing */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="base_rate">Base Rate ($) *</Label>
                <Input
                  id="base_rate"
                  type="number"
                  step="0.01"
                  value={formData.base_rate}
                  onChange={(e) => setFormData({ ...formData, base_rate: parseFloat(e.target.value) })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="per_kg_rate">Per KG Rate ($) *</Label>
                <Input
                  id="per_kg_rate"
                  type="number"
                  step="0.01"
                  value={formData.per_kg_rate}
                  onChange={(e) => setFormData({ ...formData, per_kg_rate: parseFloat(e.target.value) })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="per_km_rate">Per KM Rate ($) *</Label>
                <Input
                  id="per_km_rate"
                  type="number"
                  step="0.01"
                  value={formData.per_km_rate}
                  onChange={(e) => setFormData({ ...formData, per_km_rate: parseFloat(e.target.value) })}
                  required
                />
              </div>
            </div>

            {/* Delivery Times */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="min_delivery_days">Min Delivery (days) *</Label>
                <Input
                  id="min_delivery_days"
                  type="number"
                  value={formData.min_delivery_days}
                  onChange={(e) => setFormData({ ...formData, min_delivery_days: parseInt(e.target.value) })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="max_delivery_days">Max Delivery (days) *</Label>
                <Input
                  id="max_delivery_days"
                  type="number"
                  value={formData.max_delivery_days}
                  onChange={(e) => setFormData({ ...formData, max_delivery_days: parseInt(e.target.value) })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="sla_on_time_percentage">SLA On-Time % *</Label>
                <Input
                  id="sla_on_time_percentage"
                  type="number"
                  step="0.1"
                  value={formData.sla_on_time_percentage}
                  onChange={(e) => setFormData({ ...formData, sla_on_time_percentage: parseFloat(e.target.value) })}
                  required
                />
              </div>
            </div>

            {/* Capabilities */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="max_weight_kg">Max Weight (kg) *</Label>
                <Input
                  id="max_weight_kg"
                  type="number"
                  value={formData.max_weight_kg}
                  onChange={(e) => setFormData({ ...formData, max_weight_kg: parseInt(e.target.value) })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="max_dimensions">Max Dimensions (LxWxH cm) *</Label>
                <Input
                  id="max_dimensions"
                  value={formData.max_dimensions}
                  onChange={(e) => setFormData({ ...formData, max_dimensions: e.target.value })}
                  placeholder="120x80x80"
                  required
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="supports_tracking"
                  checked={formData.supports_tracking}
                  onChange={(e) => setFormData({ ...formData, supports_tracking: e.target.checked })}
                  className="rounded"
                />
                <Label htmlFor="supports_tracking">Supports Tracking</Label>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="supports_insurance"
                  checked={formData.supports_insurance}
                  onChange={(e) => setFormData({ ...formData, supports_insurance: e.target.checked })}
                  className="rounded"
                />
                <Label htmlFor="supports_insurance">Supports Insurance</Label>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                <Save className="w-4 h-4 mr-2" />
                {editingCarrier ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Upload Pricelist Dialog */}
      <Dialog open={isPricelistDialogOpen} onOpenChange={setIsPricelistDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-500" />
              AI-Powered Pricelist Upload
            </DialogTitle>
            <DialogDescription>
              Upload carrier pricelist documents (PDF, Excel, CSV). AI will automatically parse and extract rates.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <Alert>
              <FileText className="w-4 h-4" />
              <AlertDescription>
                <p className="font-semibold mb-1">Supported formats:</p>
                <ul className="text-sm space-y-1">
                  <li>• PDF documents with rate tables</li>
                  <li>• Excel spreadsheets (.xlsx, .xls)</li>
                  <li>• CSV files with pricing data</li>
                </ul>
              </AlertDescription>
            </Alert>

            <div>
              <Label htmlFor="pricelist_file">Select File</Label>
              <Input
                id="pricelist_file"
                type="file"
                accept=".pdf,.xlsx,.xls,.csv"
                onChange={handleFileSelect}
                className="mt-1"
              />
              {selectedFile && (
                <p className="text-sm text-muted-foreground mt-2">
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
                </p>
              )}
            </div>

            {uploadProgress && (
              <Alert className={
                uploadProgress.status === 'success' ? 'border-green-500' :
                uploadProgress.status === 'error' ? 'border-red-500' :
                'border-blue-500'
              }>
                <AlertDescription>
                  <div className="space-y-2">
                    <p className="font-semibold">{uploadProgress.message}</p>
                    {uploadProgress.details && (
                      <div className="text-sm">
                        <p>Parsed rates:</p>
                        <ul className="mt-1 space-y-1">
                          {Object.entries(uploadProgress.details).map(([key, value]) => (
                            <li key={key}>• {key}: {value}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsPricelistDialogOpen(false)}>
              Close
            </Button>
            <Button 
              onClick={handleFileUpload} 
              disabled={!selectedFile || uploadProgress?.status === 'uploading'}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              {uploadProgress?.status === 'uploading' ? 'Processing...' : 'Upload & Parse'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CarrierConfiguration;

