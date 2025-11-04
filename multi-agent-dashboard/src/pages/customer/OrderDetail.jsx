import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Download, Package, Truck, CheckCircle, XCircle } from 'lucide-react'
import api from '@/lib/api-enhanced'

const OrderDetail = () => {
  const { orderId } = useParams()
  const queryClient = useQueryClient()

  const { data: order, isLoading } = useQuery({
    queryKey: ['order', orderId],
    queryFn: () => api.orders.getById(orderId)
  })

  const cancelMutation = useMutation({
    mutationFn: () => api.orders.cancel(orderId),
    onSuccess: () => {
      toast.success('Order cancelled successfully')
      queryClient.invalidateQueries(['order', orderId])
    }
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  const statusSteps = [
    { status: 'pending', label: 'Order Placed', icon: Package },
    { status: 'processing', label: 'Processing', icon: Package },
    { status: 'shipped', label: 'Shipped', icon: Truck },
    { status: 'delivered', label: 'Delivered', icon: CheckCircle }
  ]

  const currentStepIndex = statusSteps.findIndex(step => step.status === order?.status)

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">Order #{order?.order_number}</h1>
            <p className="text-gray-600">Placed on {new Date(order?.created_at).toLocaleDateString()}</p>
          </div>
          <div className="flex space-x-2">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Download Invoice
            </Button>
            {order?.status === 'pending' && (
              <Button variant="destructive" onClick={() => cancelMutation.mutate()}>
                Cancel Order
              </Button>
            )}
          </div>
        </div>

        {/* Order Status Timeline */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Order Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              {statusSteps.map((step, index) => (
                <div key={step.status} className="flex flex-col items-center flex-1">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    index <= currentStepIndex ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                  }`}>
                    <step.icon className="w-6 h-6" />
                  </div>
                  <span className={`mt-2 text-sm font-medium ${
                    index <= currentStepIndex ? 'text-blue-600' : 'text-gray-600'
                  }`}>
                    {step.label}
                  </span>
                  {index < statusSteps.length - 1 && (
                    <div className={`absolute w-full h-1 top-6 left-1/2 ${
                      index < currentStepIndex ? 'bg-blue-600' : 'bg-gray-200'
                    }`} style={{ width: 'calc(100% / 4)' }} />
                  )}
                </div>
              ))}
            </div>
            {order?.tracking_number && (
              <div className="mt-6 p-4 bg-blue-50 rounded">
                <p className="font-medium">Tracking Number: {order.tracking_number}</p>
                <Button variant="link" className="p-0 h-auto">Track Shipment</Button>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="grid grid-cols-3 gap-6">
          {/* Order Items */}
          <div className="col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Order Items</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {order?.items?.map((item) => (
                    <div key={item.id} className="flex items-center space-x-4 pb-4 border-b last:border-0">
                      <img src={item.image} alt={item.name} className="w-20 h-20 object-cover rounded" />
                      <div className="flex-1">
                        <Link to={`/products/${item.product_id}`} className="font-medium hover:text-blue-600">
                          {item.name}
                        </Link>
                        <p className="text-sm text-gray-600">Quantity: {item.quantity}</p>
                        <p className="text-sm text-gray-600">Price: ${item.price.toFixed(2)}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">${(item.price * item.quantity).toFixed(2)}</p>
                        <Button variant="outline" size="sm" className="mt-2">
                          Write Review
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Order Total */}
                <div className="mt-6 pt-4 border-t space-y-2">
                  <div className="flex justify-between">
                    <span>Subtotal</span>
                    <span>${order?.subtotal?.toFixed(2)}</span>
                  </div>
                  {order?.discount > 0 && (
                    <div className="flex justify-between text-green-600">
                      <span>Discount</span>
                      <span>-${order?.discount?.toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span>Shipping</span>
                    <span>${order?.shipping_cost?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tax</span>
                    <span>${order?.tax?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between font-bold text-lg pt-2 border-t">
                    <span>Total</span>
                    <span>${order?.total?.toFixed(2)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="col-span-1 space-y-6">
            {/* Shipping Address */}
            <Card>
              <CardHeader>
                <CardTitle>Shipping Address</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-medium">{order?.shipping_address?.name}</p>
                <p className="text-gray-600">{order?.shipping_address?.address1}</p>
                {order?.shipping_address?.address2 && (
                  <p className="text-gray-600">{order?.shipping_address?.address2}</p>
                )}
                <p className="text-gray-600">
                  {order?.shipping_address?.city}, {order?.shipping_address?.state} {order?.shipping_address?.zipCode}
                </p>
              </CardContent>
            </Card>

            {/* Payment Method */}
            <Card>
              <CardHeader>
                <CardTitle>Payment Method</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-medium">{order?.payment_method}</p>
                {order?.payment_details && (
                  <p className="text-gray-600">
                    {order?.payment_details?.card_brand} •••• {order?.payment_details?.last4}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Need Help?</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" className="w-full">Contact Support</Button>
                {order?.status === 'delivered' && (
                  <Button variant="outline" className="w-full">Request Return</Button>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default OrderDetail
