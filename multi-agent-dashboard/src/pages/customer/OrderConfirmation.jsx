import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CheckCircle, Download, Printer } from 'lucide-react'
import api from '@/lib/api-enhanced'

const OrderConfirmation = () => {
  const { orderId } = useParams()

  const { data: order, isLoading } = useQuery({
    queryKey: ['order', orderId],
    queryFn: () => api.orders.getById(orderId)
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4">
        {/* Success Message */}
        <div className="text-center mb-8">
          <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-4" />
          <h1 className="text-3xl font-bold mb-2">Order Confirmed!</h1>
          <p className="text-gray-600">Thank you for your purchase. Your order has been received.</p>
        </div>

        {/* Order Details */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Order Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Order Number</p>
                <p className="font-bold text-lg">#{order?.order_number}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Order Date</p>
                <p className="font-medium">{new Date(order?.created_at).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Estimated Delivery</p>
                <p className="font-medium">{order?.estimated_delivery}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Payment Status</p>
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm font-medium">
                  {order?.payment_status}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Order Items */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Order Items</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {order?.items?.map((item) => (
                <div key={item.id} className="flex items-center space-x-4 pb-4 border-b last:border-0">
                  <img src={item.image} alt={item.name} className="w-20 h-20 object-cover rounded" />
                  <div className="flex-1">
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-gray-600">Quantity: {item.quantity}</p>
                  </div>
                  <span className="font-bold">${(item.price * item.quantity).toFixed(2)}</span>
                </div>
              ))}
            </div>

            {/* Order Total */}
            <div className="mt-6 pt-4 border-t space-y-2">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>${order?.subtotal?.toFixed(2)}</span>
              </div>
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

        <div className="grid grid-cols-2 gap-6 mb-6">
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
              <p className="text-gray-600">{order?.shipping_address?.country}</p>
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
                  {order?.payment_details?.card_brand} ending in {order?.payment_details?.last4}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <div className="flex justify-center space-x-4">
          <Button variant="outline">
            <Printer className="w-4 h-4 mr-2" />
            Print Receipt
          </Button>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Download Invoice
          </Button>
          <Link to="/products">
            <Button>Continue Shopping</Button>
          </Link>
        </div>

        {/* Next Steps */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>What's Next?</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-gray-600">
              <li>• You will receive an email confirmation shortly</li>
              <li>• Track your order status in your account</li>
              <li>• You'll receive a shipping notification when your order ships</li>
              <li>• Contact support if you have any questions</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default OrderConfirmation
