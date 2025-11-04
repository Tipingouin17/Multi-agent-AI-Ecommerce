import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Truck, 
  Package,
  MapPin,
  Clock,
  CheckCircle,
  AlertTriangle,
  Search,
  Printer,
  Download
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Shipping Management Page
 * 
 * Manage all shipments and shipping operations:
 * - View all shipments
 * - Track shipment status
 * - Print shipping labels in bulk
 * - Update tracking information
 * - Manage carriers
 * - View shipping analytics
 */
const ShippingManagement = () => {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedShipments, setSelectedShipments] = useState([])

  // Fetch shipments
  const { data: shipments, isLoading } = useQuery({
    queryKey: ['shipments', statusFilter, searchTerm],
    queryFn: () => api.shipping.getShipments({ status: statusFilter, search: searchTerm })
  })

  // Fetch carriers
  const { data: carriers = [] } = useQuery({
    queryKey: ['carriers'],
    queryFn: () => api.carrier.getCarriers()
  })

  // Print labels mutation
  const printLabelsMutation = useMutation({
    mutationFn: (shipmentIds) => api.shipping.printLabels(shipmentIds),
    onSuccess: () => {
      toast.success('Labels sent to printer')
      setSelectedShipments([])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to print labels')
    }
  })

  // Update tracking mutation
  const updateTrackingMutation = useMutation({
    mutationFn: ({ shipmentId, trackingNumber }) => 
      api.shipping.updateTracking(shipmentId, trackingNumber),
    onSuccess: () => {
      toast.success('Tracking updated')
      queryClient.invalidateQueries(['shipments'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update tracking')
    }
  })

  const handleSelectShipment = (shipmentId) => {
    setSelectedShipments(prev => 
      prev.includes(shipmentId) 
        ? prev.filter(id => id !== shipmentId)
        : [...prev, shipmentId]
    )
  }

  const handleSelectAll = () => {
    if (selectedShipments.length === shipments?.length) {
      setSelectedShipments([])
    } else {
      setSelectedShipments(shipments?.map(s => s.id) || [])
    }
  }

  const handlePrintSelected = () => {
    if (selectedShipments.length === 0) {
      toast.error('Please select shipments to print')
      return
    }
    printLabelsMutation.mutate(selectedShipments)
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'secondary', icon: Clock, label: 'Pending' },
      in_transit: { variant: 'default', icon: Truck, label: 'In Transit' },
      delivered: { variant: 'default', icon: CheckCircle, label: 'Delivered' },
      exception: { variant: 'destructive', icon: AlertTriangle, label: 'Exception' }
    }

    const config = statusConfig[status] || statusConfig.pending
    const Icon = config.icon

    return (
      <Badge variant={config.variant} className="flex items-center space-x-1">
        <Icon className="w-3 h-3" />
        <span>{config.label}</span>
      </Badge>
    )
  }

  const filteredShipments = shipments?.filter(shipment => {
    if (statusFilter !== 'all' && shipment.status !== statusFilter) return false
    if (searchTerm && !shipment.tracking_number?.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !shipment.order_number?.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading shipments...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Shipping Management</h1>
          <p className="text-gray-600">Manage shipments and track deliveries</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handlePrintSelected} disabled={selectedShipments.length === 0}>
            <Printer className="w-4 h-4 mr-2" />
            Print Selected ({selectedShipments.length})
          </Button>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-2xl font-bold">{shipments?.filter(s => s.status === 'pending').length || 0}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">In Transit</p>
                <p className="text-2xl font-bold">{shipments?.filter(s => s.status === 'in_transit').length || 0}</p>
              </div>
              <Truck className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Delivered</p>
                <p className="text-2xl font-bold">{shipments?.filter(s => s.status === 'delivered').length || 0}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Exceptions</p>
                <p className="text-2xl font-bold">{shipments?.filter(s => s.status === 'exception').length || 0}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search by tracking number or order number..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="in_transit">In Transit</SelectItem>
                <SelectItem value="delivered">Delivered</SelectItem>
                <SelectItem value="exception">Exception</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Shipments List */}
      <Tabs defaultValue="list" className="space-y-6">
        <TabsList>
          <TabsTrigger value="list">Shipments List</TabsTrigger>
          <TabsTrigger value="carriers">Carriers</TabsTrigger>
        </TabsList>

        <TabsContent value="list">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Shipments</CardTitle>
                  <CardDescription>{filteredShipments?.length || 0} shipments found</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={handleSelectAll}>
                  {selectedShipments.length === shipments?.length ? 'Deselect All' : 'Select All'}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredShipments?.map((shipment) => (
                  <Card key={shipment.id}>
                    <CardContent className="pt-6">
                      <div className="flex items-start space-x-4">
                        <input
                          type="checkbox"
                          checked={selectedShipments.includes(shipment.id)}
                          onChange={() => handleSelectShipment(shipment.id)}
                          className="mt-1"
                        />
                        <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center">
                          <Package className="w-6 h-6 text-gray-400" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium">Order #{shipment.order_number}</h4>
                            {getStatusBadge(shipment.status)}
                          </div>
                          <p className="text-sm text-gray-600 mb-1">
                            <strong>Tracking:</strong> {shipment.tracking_number || 'Not assigned'}
                          </p>
                          <p className="text-sm text-gray-600 mb-1">
                            <strong>Carrier:</strong> {shipment.carrier_name}
                          </p>
                          <p className="text-sm text-gray-600 mb-1">
                            <strong>Destination:</strong> {shipment.destination_city}, {shipment.destination_state}
                          </p>
                          <p className="text-xs text-gray-400">
                            Shipped on {new Date(shipment.ship_date).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex flex-col space-y-2">
                          <Button size="sm" variant="outline">
                            <MapPin className="w-4 h-4 mr-1" />
                            Track
                          </Button>
                          <Button size="sm" variant="outline">
                            <Printer className="w-4 h-4 mr-1" />
                            Print Label
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {(!filteredShipments || filteredShipments.length === 0) && (
                  <div className="text-center py-12 text-gray-500">
                    <Package className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>No shipments found</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="carriers">
          <Card>
            <CardHeader>
              <CardTitle>Shipping Carriers</CardTitle>
              <CardDescription>Manage your shipping carrier integrations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {carriers.map((carrier) => (
                  <Card key={carrier.id}>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                            <Truck className="w-8 h-8 text-gray-400" />
                          </div>
                          <div>
                            <h4 className="font-medium">{carrier.name}</h4>
                            <p className="text-sm text-gray-600">Service: {carrier.service_type}</p>
                            <p className="text-sm text-gray-600">Avg. Transit: {carrier.avg_transit_days} days</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold">${carrier.base_rate}</p>
                          <Badge variant={carrier.active ? 'default' : 'secondary'}>
                            {carrier.active ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default ShippingManagement
