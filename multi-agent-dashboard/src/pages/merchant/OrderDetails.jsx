import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { 
  ArrowLeft, 
  Package, 
  Truck,
  CheckCircle,
  XCircle,
  Clock,
  MapPin,
  User,
  Mail,
  Phone,
  CreditCard,
  FileText,
  MessageSquare
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Order Details Page
 * 
 * Comprehensive view of a single order with:
 * - Order information and status
 * - Customer details
 * - Product items
 * - Payment information
 * - Shipping details
 * - Order timeline
 * - Actions (fulfill, cancel, refund)
 */
const OrderDetails = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [note, setNote] = useState('')

  // Fetch order data
  const { data: order, isLoading } = useQuery({
    queryKey: ['order', id],
    queryFn: () => api.order.getOrder(id)
  })

  // Update order status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ status }) => api.order.updateOrderStatus(id, status),
    onSuccess: () => {
      toast.success('Order status updated')
      queryClient.invalidateQueries(['order', id])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update order status')
    }
  })

  // Add note mutation
  const addNoteMutation = useMutation({
    mutationFn: (noteText) => api.order.addOrderNote(id, noteText),
    onSuccess: () => {
      toast.success('Note added')
      setNote('')
      queryClient.invalidateQueries(['order', id])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to add note')
    }
  })

  // Create shipment mutation
  const createShipmentMutation = useMutation({
    mutationFn: () => api.order.createShipment(id),
    onSuccess: () => {
      toast.success('Shipment created')
      queryClient.invalidateQueries(['order', id])
      navigate(`/orders/${id}/fulfill`)
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create shipment')
    }
  })

  const handleStatusChange = (status) => {
    if (window.confirm(`Are you sure you want to change the order status to ${status}?`)) {
      updateStatusMutation.mutate({ status })
    }
  }

  const handleAddNote = () => {
    if (note.trim()) {
      addNoteMutation.mutate(note)
    }
  }

  const handleFulfillOrder = () => {
    createShipmentMutation.mutate()
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'secondary', icon: Clock },
      processing: { variant: 'default', icon: Package },
      shipped: { variant: 'default', icon: Truck },
      delivered: { variant: 'default', icon: CheckCircle },
      cancelled: { variant: 'destructive', icon: XCircle }
    }

    const config = statusConfig[status] || statusConfig.pending
    const Icon = config.icon

    return (
      <Badge variant={config.variant} className="flex items-center space-x-1">
        <Icon className="w-3 h-3" />
        <span className="capitalize">{status}</span>
      </Badge>
    )
  }

  if (isLoading) {
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
          <Button variant="ghost" size="sm" onClick={() => navigate('/orders')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Orders
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Order #{order.order_number}</h1>
            <p className="text-gray-600">
              Placed on {new Date(order.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusBadge(order.status)}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Column - Order Details */}
        <div className="col-span-2 space-y-6">
          {/* Order Items */}
          <Card>
            <CardHeader>
              <CardTitle>Order Items</CardTitle>
              <CardDescription>{order.items?.length || 0} items</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {order.items?.map((item, index) => (
                  <div key={index} className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                      <Package className="w-8 h-8 text-gray-400" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">{item.product_name}</h4>
                      <p className="text-sm text-gray-600">SKU: {item.sku}</p>
                      <p className="text-sm text-gray-600">Quantity: {item.quantity}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">${item.price}</p>
                      <p className="text-sm text-gray-600">
                        Total: ${(item.price * item.quantity).toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              
              <Separator className="my-4" />
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>${order.subtotal?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Shipping</span>
                  <span>${order.shipping_cost?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tax</span>
                  <span>${order.tax_amount?.toFixed(2) || '0.00'}</span>
                </div>
                <Separator />
                <div className="flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>${order.total_amount?.toFixed(2) || '0.00'}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Order Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {order.timeline?.map((event, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <div className="flex-1">
                      <p className="font-medium">{event.title}</p>
                      <p className="text-sm text-gray-600">{event.description}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(event.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Notes */}
          <Card>
            <CardHeader>
              <CardTitle>Order Notes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Add a note about this order..."
                  rows={3}
                />
                <Button onClick={handleAddNote} disabled={!note.trim()}>
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Add Note
                </Button>
              </div>

              {order.notes?.length > 0 && (
                <div className="space-y-3 mt-4">
                  {order.notes.map((note, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded">
                      <p className="text-sm">{note.content}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {note.author} • {new Date(note.created_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Customer & Actions */}
        <div className="space-y-6">
          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {order.status === 'pending' && (
                <>
                  <Button 
                    className="w-full" 
                    onClick={handleFulfillOrder}
                    disabled={createShipmentMutation.isPending}
                  >
                    <Package className="w-4 h-4 mr-2" />
                    Fulfill Order
                  </Button>
                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={() => handleStatusChange('cancelled')}
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Cancel Order
                  </Button>
                </>
              )}
              
              {order.status === 'processing' && (
                <Button 
                  className="w-full"
                  onClick={() => navigate(`/orders/${id}/ship`)}
                >
                  <Truck className="w-4 h-4 mr-2" />
                  Create Shipment
                </Button>
              )}

              <Button variant="outline" className="w-full">
                <FileText className="w-4 h-4 mr-2" />
                Print Invoice
              </Button>
              
              <Button variant="outline" className="w-full">
                <FileText className="w-4 h-4 mr-2" />
                Print Packing Slip
              </Button>
            </CardContent>
          </Card>

          {/* Customer Information */}
          <Card>
            <CardHeader>
              <CardTitle>Customer</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-2">
                <User className="w-4 h-4 text-gray-400" />
                <span>{order.customer_name}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Mail className="w-4 h-4 text-gray-400" />
                <span className="text-sm">{order.customer_email}</span>
              </div>
              {order.customer_phone && (
                <div className="flex items-center space-x-2">
                  <Phone className="w-4 h-4 text-gray-400" />
                  <span className="text-sm">{order.customer_phone}</span>
                </div>
              )}
              <Button variant="link" className="p-0 h-auto">
                View customer profile
              </Button>
            </CardContent>
          </Card>

          {/* Shipping Address */}
          <Card>
            <CardHeader>
              <CardTitle>Shipping Address</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-start space-x-2">
                <MapPin className="w-4 h-4 text-gray-400 mt-1" />
                <div className="text-sm">
                  <p>{order.shipping_address?.street}</p>
                  <p>
                    {order.shipping_address?.city}, {order.shipping_address?.state}{' '}
                    {order.shipping_address?.zip}
                  </p>
                  <p>{order.shipping_address?.country}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Payment Information */}
          <Card>
            <CardHeader>
              <CardTitle>Payment</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CreditCard className="w-4 h-4 text-gray-400" />
                  <span className="text-sm">{order.payment_method}</span>
                </div>
                <Badge variant={order.payment_status === 'paid' ? 'default' : 'secondary'}>
                  {order.payment_status}
                </Badge>
              </div>
              {order.transaction_id && (
                <p className="text-xs text-gray-600">
                  Transaction ID: {order.transaction_id}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default OrderDetails
