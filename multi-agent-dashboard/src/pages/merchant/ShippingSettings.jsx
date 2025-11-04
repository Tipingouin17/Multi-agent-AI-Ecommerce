import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { 
  Truck, 
  Plus,
  Trash2,
  Edit,
  MapPin,
  Package,
  DollarSign
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Shipping Zones & Rates
 * 
 * Configure geographic shipping zones and rates:
 * - Create shipping zones
 * - Define shipping methods per zone
 * - Configure rate calculation (weight, price, flat)
 * - Set delivery time estimates
 * - Manage carrier integrations
 */
const ShippingSettings = () => {
  const queryClient = useQueryClient()
  const [isCreatingZone, setIsCreatingZone] = useState(false)
  const [isAddingMethod, setIsAddingMethod] = useState(false)
  const [selectedZone, setSelectedZone] = useState(null)
  
  const [newZone, setNewZone] = useState({
    name: '',
    countries: [],
    states: [],
    postal_codes: ''
  })

  const [newMethod, setNewMethod] = useState({
    name: '',
    rate_type: 'flat',
    flat_rate: '',
    min_weight: '',
    max_weight: '',
    weight_rate: '',
    min_price: '',
    max_price: '',
    price_rate: '',
    free_shipping_threshold: '',
    delivery_time: '',
    carrier: 'custom'
  })

  // Fetch shipping zones
  const { data: zones, isLoading } = useQuery({
    queryKey: ['shipping-zones'],
    queryFn: () => api.settings.getShippingZones()
  })

  // Create zone mutation
  const createZoneMutation = useMutation({
    mutationFn: (data) => api.settings.createShippingZone(data),
    onSuccess: () => {
      toast.success('Shipping zone created')
      queryClient.invalidateQueries(['shipping-zones'])
      setIsCreatingZone(false)
      setNewZone({ name: '', countries: [], states: [], postal_codes: '' })
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create zone')
    }
  })

  // Add shipping method mutation
  const addMethodMutation = useMutation({
    mutationFn: ({ zoneId, data }) => api.settings.addShippingMethod(zoneId, data),
    onSuccess: () => {
      toast.success('Shipping method added')
      queryClient.invalidateQueries(['shipping-zones'])
      setIsAddingMethod(false)
      setSelectedZone(null)
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to add method')
    }
  })

  // Delete zone mutation
  const deleteZoneMutation = useMutation({
    mutationFn: (zoneId) => api.settings.deleteShippingZone(zoneId),
    onSuccess: () => {
      toast.success('Shipping zone deleted')
      queryClient.invalidateQueries(['shipping-zones'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete zone')
    }
  })

  const handleCreateZone = () => {
    if (!newZone.name || newZone.countries.length === 0) {
      toast.error('Please provide zone name and at least one country')
      return
    }
    createZoneMutation.mutate(newZone)
  }

  const handleAddMethod = () => {
    if (!newMethod.name) {
      toast.error('Please provide method name')
      return
    }
    addMethodMutation.mutate({ zoneId: selectedZone, data: newMethod })
  }

  const handleDeleteZone = (zoneId) => {
    if (window.confirm('Are you sure you want to delete this shipping zone?')) {
      deleteZoneMutation.mutate(zoneId)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading shipping settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Shipping Zones & Rates</h1>
          <p className="text-gray-600">Configure shipping zones and delivery methods</p>
        </div>
        <Dialog open={isCreatingZone} onOpenChange={setIsCreatingZone}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Create Shipping Zone
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create Shipping Zone</DialogTitle>
              <DialogDescription>Define a geographic zone for shipping</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Zone Name *</Label>
                <Input
                  value={newZone.name}
                  onChange={(e) => setNewZone({ ...newZone, name: e.target.value })}
                  placeholder="United States"
                />
              </div>

              <div className="space-y-2">
                <Label>Countries *</Label>
                <Select 
                  value={newZone.countries[0]} 
                  onValueChange={(value) => setNewZone({ ...newZone, countries: [value] })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select country" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="US">United States</SelectItem>
                    <SelectItem value="CA">Canada</SelectItem>
                    <SelectItem value="GB">United Kingdom</SelectItem>
                    <SelectItem value="AU">Australia</SelectItem>
                    <SelectItem value="DE">Germany</SelectItem>
                    <SelectItem value="FR">France</SelectItem>
                    <SelectItem value="ES">Spain</SelectItem>
                    <SelectItem value="IT">Italy</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>States/Provinces (Optional)</Label>
                <Input
                  value={newZone.states}
                  onChange={(e) => setNewZone({ ...newZone, states: e.target.value.split(',') })}
                  placeholder="CA, NY, TX (comma-separated)"
                />
              </div>

              <div className="space-y-2">
                <Label>Postal Codes (Optional)</Label>
                <Input
                  value={newZone.postal_codes}
                  onChange={(e) => setNewZone({ ...newZone, postal_codes: e.target.value })}
                  placeholder="90001-90099, 10001-10999"
                />
                <p className="text-sm text-gray-500">Use ranges (e.g., 90001-90099) or wildcards (e.g., 900*)</p>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button variant="outline" onClick={() => setIsCreatingZone(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateZone} disabled={createZoneMutation.isPending}>
                  {createZoneMutation.isPending ? 'Creating...' : 'Create Zone'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Shipping Zones */}
      <div className="space-y-6">
        {zones?.map((zone) => (
          <Card key={zone.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <MapPin className="w-5 h-5 text-blue-500" />
                  <div>
                    <CardTitle>{zone.name}</CardTitle>
                    <CardDescription>
                      {zone.countries?.join(', ')} 
                      {zone.states?.length > 0 && ` • ${zone.states.length} states`}
                    </CardDescription>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button size="sm" variant="outline">
                    <Edit className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
                  <Button 
                    size="sm" 
                    variant="destructive"
                    onClick={() => handleDeleteZone(zone.id)}
                  >
                    <Trash2 className="w-4 h-4 mr-1" />
                    Delete
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Shipping Methods */}
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-3">
                  <Label className="text-base">Shipping Methods</Label>
                  <Dialog 
                    open={isAddingMethod && selectedZone === zone.id} 
                    onOpenChange={(open) => {
                      setIsAddingMethod(open)
                      if (open) setSelectedZone(zone.id)
                      else setSelectedZone(null)
                    }}
                  >
                    <DialogTrigger asChild>
                      <Button size="sm" variant="outline">
                        <Plus className="w-4 h-4 mr-1" />
                        Add Method
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Add Shipping Method</DialogTitle>
                        <DialogDescription>Configure a shipping method for {zone.name}</DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Method Name *</Label>
                            <Input
                              value={newMethod.name}
                              onChange={(e) => setNewMethod({ ...newMethod, name: e.target.value })}
                              placeholder="Standard Shipping"
                            />
                          </div>

                          <div className="space-y-2">
                            <Label>Carrier</Label>
                            <Select 
                              value={newMethod.carrier} 
                              onValueChange={(value) => setNewMethod({ ...newMethod, carrier: value })}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="custom">Custom</SelectItem>
                                <SelectItem value="usps">USPS</SelectItem>
                                <SelectItem value="fedex">FedEx</SelectItem>
                                <SelectItem value="ups">UPS</SelectItem>
                                <SelectItem value="dhl">DHL</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label>Rate Type *</Label>
                          <Select 
                            value={newMethod.rate_type} 
                            onValueChange={(value) => setNewMethod({ ...newMethod, rate_type: value })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="flat">Flat Rate</SelectItem>
                              <SelectItem value="weight">Weight-Based</SelectItem>
                              <SelectItem value="price">Price-Based</SelectItem>
                              <SelectItem value="free">Free Shipping</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        {newMethod.rate_type === 'flat' && (
                          <div className="space-y-2">
                            <Label>Flat Rate *</Label>
                            <Input
                              type="number"
                              step="0.01"
                              value={newMethod.flat_rate}
                              onChange={(e) => setNewMethod({ ...newMethod, flat_rate: e.target.value })}
                              placeholder="9.99"
                            />
                          </div>
                        )}

                        {newMethod.rate_type === 'weight' && (
                          <div className="grid grid-cols-3 gap-4">
                            <div className="space-y-2">
                              <Label>Min Weight (kg)</Label>
                              <Input
                                type="number"
                                step="0.1"
                                value={newMethod.min_weight}
                                onChange={(e) => setNewMethod({ ...newMethod, min_weight: e.target.value })}
                                placeholder="0"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Max Weight (kg)</Label>
                              <Input
                                type="number"
                                step="0.1"
                                value={newMethod.max_weight}
                                onChange={(e) => setNewMethod({ ...newMethod, max_weight: e.target.value })}
                                placeholder="10"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Rate per kg</Label>
                              <Input
                                type="number"
                                step="0.01"
                                value={newMethod.weight_rate}
                                onChange={(e) => setNewMethod({ ...newMethod, weight_rate: e.target.value })}
                                placeholder="2.50"
                              />
                            </div>
                          </div>
                        )}

                        {newMethod.rate_type === 'price' && (
                          <div className="grid grid-cols-3 gap-4">
                            <div className="space-y-2">
                              <Label>Min Order Value</Label>
                              <Input
                                type="number"
                                step="0.01"
                                value={newMethod.min_price}
                                onChange={(e) => setNewMethod({ ...newMethod, min_price: e.target.value })}
                                placeholder="0"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Max Order Value</Label>
                              <Input
                                type="number"
                                step="0.01"
                                value={newMethod.max_price}
                                onChange={(e) => setNewMethod({ ...newMethod, max_price: e.target.value })}
                                placeholder="100"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Shipping Rate</Label>
                              <Input
                                type="number"
                                step="0.01"
                                value={newMethod.price_rate}
                                onChange={(e) => setNewMethod({ ...newMethod, price_rate: e.target.value })}
                                placeholder="5.99"
                              />
                            </div>
                          </div>
                        )}

                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Free Shipping Threshold (Optional)</Label>
                            <Input
                              type="number"
                              step="0.01"
                              value={newMethod.free_shipping_threshold}
                              onChange={(e) => setNewMethod({ ...newMethod, free_shipping_threshold: e.target.value })}
                              placeholder="50.00"
                            />
                            <p className="text-sm text-gray-500">Free shipping for orders above this amount</p>
                          </div>

                          <div className="space-y-2">
                            <Label>Delivery Time</Label>
                            <Input
                              value={newMethod.delivery_time}
                              onChange={(e) => setNewMethod({ ...newMethod, delivery_time: e.target.value })}
                              placeholder="3-5 business days"
                            />
                          </div>
                        </div>

                        <div className="flex justify-end space-x-2 pt-4">
                          <Button 
                            variant="outline" 
                            onClick={() => {
                              setIsAddingMethod(false)
                              setSelectedZone(null)
                            }}
                          >
                            Cancel
                          </Button>
                          <Button onClick={handleAddMethod} disabled={addMethodMutation.isPending}>
                            {addMethodMutation.isPending ? 'Adding...' : 'Add Method'}
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>

                {zone.methods?.map((method, index) => (
                  <Card key={index} className="bg-gray-50">
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <Truck className="w-5 h-5 text-gray-600" />
                          <div>
                            <p className="font-medium">{method.name}</p>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge variant="outline">{method.carrier}</Badge>
                              <span className="text-sm text-gray-600">
                                {method.rate_type === 'flat' && `$${method.flat_rate}`}
                                {method.rate_type === 'weight' && `$${method.weight_rate}/kg`}
                                {method.rate_type === 'price' && `$${method.price_rate}`}
                                {method.rate_type === 'free' && 'Free'}
                              </span>
                              {method.delivery_time && (
                                <span className="text-sm text-gray-500">• {method.delivery_time}</span>
                              )}
                            </div>
                          </div>
                        </div>
                        <Button size="sm" variant="ghost">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {(!zone.methods || zone.methods.length === 0) && (
                  <div className="text-center py-8 text-gray-500 border-2 border-dashed rounded">
                    <Package className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p className="text-sm">No shipping methods configured for this zone</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}

        {(!zones || zones.length === 0) && (
          <Card>
            <CardContent className="pt-12 pb-12">
              <div className="text-center text-gray-500">
                <MapPin className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No shipping zones configured</p>
                <p className="text-sm mt-2">Create a shipping zone to start offering delivery</p>
                <Button className="mt-4" onClick={() => setIsCreatingZone(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Shipping Zone
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

export default ShippingSettings
