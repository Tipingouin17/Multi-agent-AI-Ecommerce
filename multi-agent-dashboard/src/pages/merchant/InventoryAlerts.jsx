import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { 
  AlertTriangle, 
  Package,
  TrendingDown,
  ShoppingCart,
  Bell,
  CheckCircle,
  XCircle
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Inventory Alerts Page
 * 
 * Monitor and manage inventory alerts:
 * - Low stock alerts
 * - Out of stock items
 * - Overstock warnings
 * - Reorder recommendations
 * - Alert configuration
 * - Quick reorder actions
 */
const InventoryAlerts = () => {
  const queryClient = useQueryClient()
  const [alertType, setAlertType] = useState('all')
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [reorderQuantity, setReorderQuantity] = useState('')

  // Fetch inventory alerts
  const { data: alerts, isLoading } = useQuery({
    queryKey: ['inventory-alerts', alertType],
    queryFn: () => api.inventory.getAlerts({ type: alertType })
  })

  // Create purchase order mutation
  const createPOMutation = useMutation({
    mutationFn: ({ productId, quantity }) => 
      api.inventory.createPurchaseOrder(productId, quantity),
    onSuccess: () => {
      toast.success('Purchase order created')
      queryClient.invalidateQueries(['inventory-alerts'])
      setSelectedProduct(null)
      setReorderQuantity('')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create purchase order')
    }
  })

  // Dismiss alert mutation
  const dismissAlertMutation = useMutation({
    mutationFn: (alertId) => api.inventory.dismissAlert(alertId),
    onSuccess: () => {
      toast.success('Alert dismissed')
      queryClient.invalidateQueries(['inventory-alerts'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to dismiss alert')
    }
  })

  const handleReorder = () => {
    if (!reorderQuantity || parseInt(reorderQuantity) <= 0) {
      toast.error('Please enter a valid quantity')
      return
    }

    createPOMutation.mutate({
      productId: selectedProduct.product_id,
      quantity: parseInt(reorderQuantity)
    })
  }

  const getAlertBadge = (type, severity) => {
    const config = {
      low_stock: { variant: 'secondary', icon: AlertTriangle, label: 'Low Stock', color: 'text-orange-500' },
      out_of_stock: { variant: 'destructive', icon: XCircle, label: 'Out of Stock', color: 'text-red-500' },
      overstock: { variant: 'default', icon: Package, label: 'Overstock', color: 'text-blue-500' },
      slow_moving: { variant: 'secondary', icon: TrendingDown, label: 'Slow Moving', color: 'text-gray-500' }
    }

    const alertConfig = config[type] || config.low_stock
    const Icon = alertConfig.icon

    return (
      <Badge variant={alertConfig.variant} className="flex items-center space-x-1">
        <Icon className="w-3 h-3" />
        <span>{alertConfig.label}</span>
      </Badge>
    )
  }

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'border-l-4 border-red-500 bg-red-50',
      high: 'border-l-4 border-orange-500 bg-orange-50',
      medium: 'border-l-4 border-yellow-500 bg-yellow-50',
      low: 'border-l-4 border-blue-500 bg-blue-50'
    }
    return colors[severity] || colors.medium
  }

  const filteredAlerts = alerts?.filter(alert => {
    if (alertType !== 'all' && alert.type !== alertType) return false
    return true
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading alerts...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Inventory Alerts</h1>
          <p className="text-gray-600">Monitor stock levels and manage reorders</p>
        </div>
        <Button variant="outline">
          <Bell className="w-4 h-4 mr-2" />
          Configure Alerts
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Critical Alerts</p>
                <p className="text-2xl font-bold text-red-600">
                  {alerts?.filter(a => a.severity === 'critical').length || 0}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Low Stock</p>
                <p className="text-2xl font-bold text-orange-600">
                  {alerts?.filter(a => a.type === 'low_stock').length || 0}
                </p>
              </div>
              <Package className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Out of Stock</p>
                <p className="text-2xl font-bold text-red-600">
                  {alerts?.filter(a => a.type === 'out_of_stock').length || 0}
                </p>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Reorder Needed</p>
                <p className="text-2xl font-bold text-blue-600">
                  {alerts?.filter(a => a.reorder_recommended).length || 0}
                </p>
              </div>
              <ShoppingCart className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter */}
      <Card>
        <CardContent className="pt-6">
          <Select value={alertType} onValueChange={setAlertType}>
            <SelectTrigger className="w-64">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Alerts</SelectItem>
              <SelectItem value="low_stock">Low Stock</SelectItem>
              <SelectItem value="out_of_stock">Out of Stock</SelectItem>
              <SelectItem value="overstock">Overstock</SelectItem>
              <SelectItem value="slow_moving">Slow Moving</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Alerts List */}
      <Card>
        <CardHeader>
          <CardTitle>Active Alerts</CardTitle>
          <CardDescription>{filteredAlerts?.length || 0} alerts require attention</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAlerts?.map((alert) => (
              <Card key={alert.id} className={getSeverityColor(alert.severity)}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className="w-16 h-16 bg-white rounded flex items-center justify-center">
                        <Package className="w-8 h-8 text-gray-400" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium">{alert.product_name}</h4>
                          {getAlertBadge(alert.type, alert.severity)}
                        </div>
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>SKU:</strong> {alert.sku}
                        </p>
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>Current Stock:</strong> {alert.current_stock} units
                        </p>
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>Threshold:</strong> {alert.threshold} units
                        </p>
                        {alert.reorder_recommended && (
                          <p className="text-sm font-medium text-blue-600 mt-2">
                            ⚡ Recommended reorder: {alert.recommended_quantity} units
                          </p>
                        )}
                        <p className="text-xs text-gray-400 mt-2">
                          Alert created {new Date(alert.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-col space-y-2">
                      {alert.type !== 'overstock' && alert.type !== 'slow_moving' && (
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button 
                              size="sm"
                              onClick={() => {
                                setSelectedProduct(alert)
                                setReorderQuantity(alert.recommended_quantity?.toString() || '')
                              }}
                            >
                              <ShoppingCart className="w-4 h-4 mr-1" />
                              Reorder
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Create Purchase Order</DialogTitle>
                              <DialogDescription>
                                Reorder {alert.product_name}
                              </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4">
                              <div className="space-y-2">
                                <Label>Product</Label>
                                <Input value={alert.product_name} disabled />
                              </div>
                              <div className="space-y-2">
                                <Label>Current Stock</Label>
                                <Input value={`${alert.current_stock} units`} disabled />
                              </div>
                              <div className="space-y-2">
                                <Label>Reorder Quantity *</Label>
                                <Input
                                  type="number"
                                  value={reorderQuantity}
                                  onChange={(e) => setReorderQuantity(e.target.value)}
                                  placeholder="Enter quantity"
                                />
                                {alert.recommended_quantity && (
                                  <p className="text-sm text-gray-500">
                                    Recommended: {alert.recommended_quantity} units
                                  </p>
                                )}
                              </div>
                              <div className="flex justify-end space-x-2">
                                <Button variant="outline" onClick={() => setSelectedProduct(null)}>
                                  Cancel
                                </Button>
                                <Button 
                                  onClick={handleReorder}
                                  disabled={createPOMutation.isPending}
                                >
                                  {createPOMutation.isPending ? 'Creating...' : 'Create PO'}
                                </Button>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      )}
                      
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => dismissAlertMutation.mutate(alert.id)}
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Dismiss
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {(!filteredAlerts || filteredAlerts.length === 0) && (
              <div className="text-center py-12 text-gray-500">
                <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-300" />
                <p>No active alerts</p>
                <p className="text-sm mt-2">All inventory levels are healthy</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default InventoryAlerts
