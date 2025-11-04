import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { 
  ArrowLeft, 
  Package, 
  Truck,
  CheckCircle,
  Printer,
  MapPin,
  User,
  Box
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Order Fulfillment Page
 * 
 * Workflow for fulfilling orders:
 * - Pick list generation
 * - Item verification
 * - Packing workflow
 * - Carrier selection
 * - Shipping label creation
 * - Tracking number entry
 */
const OrderFulfillment = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [step, setStep] = useState(1) // 1: Pick, 2: Pack, 3: Ship
  const [pickedItems, setPickedItems] = useState({})
  const [selectedCarrier, setSelectedCarrier] = useState('')
  const [trackingNumber, setTrackingNumber] = useState('')
  const [packageWeight, setPackageWeight] = useState('')
  const [packageDimensions, setPackageDimensions] = useState({
    length: '',
    width: '',
    height: ''
  })

  // Fetch order data
  const { data: order, isLoading: orderLoading } = useQuery({
    queryKey: ['order', id],
    queryFn: () => api.order.getOrder(id)
  })

  // Fetch carriers
  const { data: carriers = [] } = useQuery({
    queryKey: ['carriers'],
    queryFn: () => api.carrier.getCarriers()
  })

  // Create shipment mutation
  const createShipmentMutation = useMutation({
    mutationFn: (shipmentData) => api.order.createShipment(id, shipmentData),
    onSuccess: () => {
      toast.success('Shipment created successfully')
      queryClient.invalidateQueries(['order', id])
      navigate(`/orders/${id}`)
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create shipment')
    }
  })

  // Generate label mutation
  const generateLabelMutation = useMutation({
    mutationFn: () => api.order.generateShippingLabel(id, selectedCarrier),
    onSuccess: (data) => {
      toast.success('Shipping label generated')
      setTrackingNumber(data.tracking_number)
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to generate label')
    }
  })

  const handleItemPicked = (itemId, checked) => {
    setPickedItems(prev => ({ ...prev, [itemId]: checked }))
  }

  const handleNextStep = () => {
    if (step === 1) {
      // Verify all items are picked
      const allPicked = order?.items?.every(item => pickedItems[item.id])
      if (!allPicked) {
        toast.error('Please pick all items before continuing')
        return
      }
    }
    
    if (step === 2) {
      // Verify packing details
      if (!packageWeight || !packageDimensions.length || !packageDimensions.width || !packageDimensions.height) {
        toast.error('Please enter package dimensions and weight')
        return
      }
    }
    
    setStep(step + 1)
  }

  const handlePreviousStep = () => {
    setStep(step - 1)
  }

  const handleGenerateLabel = () => {
    if (!selectedCarrier) {
      toast.error('Please select a carrier')
      return
    }
    generateLabelMutation.mutate()
  }

  const handleCompleteShipment = () => {
    if (!trackingNumber) {
      toast.error('Please enter or generate a tracking number')
      return
    }

    const shipmentData = {
      carrier_id: selectedCarrier,
      tracking_number: trackingNumber,
      weight: parseFloat(packageWeight),
      dimensions: {
        length: parseFloat(packageDimensions.length),
        width: parseFloat(packageDimensions.width),
        height: parseFloat(packageDimensions.height)
      }
    }

    createShipmentMutation.mutate(shipmentData)
  }

  const handlePrintPickList = () => {
    window.print()
    toast.success('Pick list sent to printer')
  }

  if (orderLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading order...</p>
        </div>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-gray-600">Order not found</p>
          <Button className="mt-4" onClick={() => navigate('/orders')}>
            Back to Orders
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" onClick={() => navigate(`/orders/${id}`)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Order
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Fulfill Order #{order.order_number}</h1>
            <p className="text-gray-600">Complete the fulfillment workflow</p>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className={`flex items-center space-x-2 ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                {step > 1 ? <CheckCircle className="w-5 h-5" /> : '1'}
              </div>
              <span className="font-medium">Pick Items</span>
            </div>
            <div className="flex-1 h-1 bg-gray-200 mx-4">
              <div className={`h-full ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'} transition-all`} style={{ width: step >= 2 ? '100%' : '0%' }}></div>
            </div>
            <div className={`flex items-center space-x-2 ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                {step > 2 ? <CheckCircle className="w-5 h-5" /> : '2'}
              </div>
              <span className="font-medium">Pack Order</span>
            </div>
            <div className="flex-1 h-1 bg-gray-200 mx-4">
              <div className={`h-full ${step >= 3 ? 'bg-blue-600' : 'bg-gray-200'} transition-all`} style={{ width: step >= 3 ? '100%' : '0%' }}></div>
            </div>
            <div className={`flex items-center space-x-2 ${step >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                3
              </div>
              <span className="font-medium">Ship Order</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Step 1: Pick Items */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Pick Items</CardTitle>
                <CardDescription>Locate and verify all items for this order</CardDescription>
              </div>
              <Button variant="outline" onClick={handlePrintPickList}>
                <Printer className="w-4 h-4 mr-2" />
                Print Pick List
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {order.items?.map((item) => (
              <div key={item.id} className="flex items-center space-x-4 p-4 border rounded-lg">
                <Checkbox
                  checked={pickedItems[item.id] || false}
                  onCheckedChange={(checked) => handleItemPicked(item.id, checked)}
                />
                <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                  <Package className="w-8 h-8 text-gray-400" />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium">{item.product_name}</h4>
                  <p className="text-sm text-gray-600">SKU: {item.sku}</p>
                  <p className="text-sm text-gray-600">Location: {item.warehouse_location || 'A-12-3'}</p>
                </div>
                <div className="text-right">
                  <Badge>Qty: {item.quantity}</Badge>
                </div>
              </div>
            ))}

            <div className="flex justify-end space-x-2 mt-6">
              <Button onClick={handleNextStep}>
                Continue to Packing
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Pack Order */}
      {step === 2 && (
        <div className="grid grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Package Details</CardTitle>
              <CardDescription>Enter package dimensions and weight</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="weight">Weight (lbs)</Label>
                <Input
                  id="weight"
                  type="number"
                  step="0.1"
                  value={packageWeight}
                  onChange={(e) => setPackageWeight(e.target.value)}
                  placeholder="0.0"
                />
              </div>

              <Separator />

              <div className="space-y-4">
                <Label>Dimensions (inches)</Label>
                <div className="grid grid-cols-3 gap-2">
                  <div className="space-y-2">
                    <Label htmlFor="length" className="text-xs">Length</Label>
                    <Input
                      id="length"
                      type="number"
                      step="0.1"
                      value={packageDimensions.length}
                      onChange={(e) => setPackageDimensions(prev => ({ ...prev, length: e.target.value }))}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="width" className="text-xs">Width</Label>
                    <Input
                      id="width"
                      type="number"
                      step="0.1"
                      value={packageDimensions.width}
                      onChange={(e) => setPackageDimensions(prev => ({ ...prev, width: e.target.value }))}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="height" className="text-xs">Height</Label>
                    <Input
                      id="height"
                      type="number"
                      step="0.1"
                      value={packageDimensions.height}
                      onChange={(e) => setPackageDimensions(prev => ({ ...prev, height: e.target.value }))}
                      placeholder="0"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-between space-x-2 mt-6">
                <Button variant="outline" onClick={handlePreviousStep}>
                  Back
                </Button>
                <Button onClick={handleNextStep}>
                  Continue to Shipping
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Packing Checklist</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox id="check1" />
                <label htmlFor="check1" className="text-sm">All items securely packed</label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="check2" />
                <label htmlFor="check2" className="text-sm">Fragile items wrapped with bubble wrap</label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="check3" />
                <label htmlFor="check3" className="text-sm">Packing slip included</label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="check4" />
                <label htmlFor="check4" className="text-sm">Box sealed properly</label>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 3: Ship Order */}
      {step === 3 && (
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Shipping Details</CardTitle>
                <CardDescription>Select carrier and generate label</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="carrier">Carrier</Label>
                  <Select value={selectedCarrier} onValueChange={setSelectedCarrier}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select carrier" />
                    </SelectTrigger>
                    <SelectContent>
                      {carriers.map(carrier => (
                        <SelectItem key={carrier.id} value={carrier.id.toString()}>
                          {carrier.name} - ${carrier.estimated_cost}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  className="w-full" 
                  onClick={handleGenerateLabel}
                  disabled={!selectedCarrier || generateLabelMutation.isPending}
                >
                  <Printer className="w-4 h-4 mr-2" />
                  {generateLabelMutation.isPending ? 'Generating...' : 'Generate Shipping Label'}
                </Button>

                <Separator />

                <div className="space-y-2">
                  <Label htmlFor="tracking">Tracking Number</Label>
                  <Input
                    id="tracking"
                    value={trackingNumber}
                    onChange={(e) => setTrackingNumber(e.target.value)}
                    placeholder="Enter tracking number"
                  />
                </div>

                <div className="flex justify-between space-x-2 mt-6">
                  <Button variant="outline" onClick={handlePreviousStep}>
                    Back
                  </Button>
                  <Button 
                    onClick={handleCompleteShipment}
                    disabled={!trackingNumber || createShipmentMutation.isPending}
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    {createShipmentMutation.isPending ? 'Processing...' : 'Complete Shipment'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Shipping Address</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-start space-x-2">
                  <MapPin className="w-4 h-4 text-gray-400 mt-1" />
                  <div className="text-sm">
                    <p className="font-medium">{order.customer_name}</p>
                    <p className="mt-2">{order.shipping_address?.street}</p>
                    <p>
                      {order.shipping_address?.city}, {order.shipping_address?.state}{' '}
                      {order.shipping_address?.zip}
                    </p>
                    <p>{order.shipping_address?.country}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Package Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Weight:</span>
                  <span className="font-medium">{packageWeight} lbs</span>
                </div>
                <div className="flex justify-between">
                  <span>Dimensions:</span>
                  <span className="font-medium">
                    {packageDimensions.length} x {packageDimensions.width} x {packageDimensions.height} in
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Items:</span>
                  <span className="font-medium">{order.items?.length || 0}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}

export default OrderFulfillment
