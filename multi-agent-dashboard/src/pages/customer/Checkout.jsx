import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Checkbox } from '@/components/ui/checkbox'
import { Check, CreditCard, Truck, Package } from 'lucide-react'
import api from '@/lib/api-enhanced'

const Checkout = () => {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [shippingAddress, setShippingAddress] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    address1: '',
    address2: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'US'
  })
  const [shippingMethod, setShippingMethod] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('credit_card')
  const [paymentInfo, setPaymentInfo] = useState({
    cardNumber: '',
    cardName: '',
    expiryDate: '',
    cvv: ''
  })
  const [couponCode, setCouponCode] = useState('')
  const [agreedToTerms, setAgreedToTerms] = useState(false)

  const { data: cart } = useQuery({
    queryKey: ['cart'],
    queryFn: () => api.cart.getCart()
  })

  const { data: shippingMethods } = useQuery({
    queryKey: ['shipping-methods', shippingAddress.zipCode],
    queryFn: () => api.shipping.getMethods(shippingAddress.zipCode),
    enabled: !!shippingAddress.zipCode && shippingAddress.zipCode.length >= 5
  })

  const applyCouponMutation = useMutation({
    mutationFn: (code) => api.cart.applyCoupon(code),
    onSuccess: () => {
      toast.success('Coupon applied successfully')
    },
    onError: () => {
      toast.error('Invalid coupon code')
    }
  })

  const placeOrderMutation = useMutation({
    mutationFn: (orderData) => api.orders.create(orderData),
    onSuccess: (data) => {
      toast.success('Order placed successfully!')
      navigate(`/order-confirmation/${data.order_id}`)
    },
    onError: () => {
      toast.error('Failed to place order')
    }
  })

  const handleNextStep = () => {
    if (currentStep === 1) {
      // Validate shipping address
      if (!shippingAddress.firstName || !shippingAddress.lastName || !shippingAddress.email || 
          !shippingAddress.address1 || !shippingAddress.city || !shippingAddress.state || !shippingAddress.zipCode) {
        toast.error('Please fill in all required fields')
        return
      }
    } else if (currentStep === 2) {
      // Validate shipping method
      if (!shippingMethod) {
        toast.error('Please select a shipping method')
        return
      }
    }
    setCurrentStep(currentStep + 1)
  }

  const handlePlaceOrder = () => {
    if (!agreedToTerms) {
      toast.error('Please agree to the terms and conditions')
      return
    }

    if (paymentMethod === 'credit_card') {
      if (!paymentInfo.cardNumber || !paymentInfo.cardName || !paymentInfo.expiryDate || !paymentInfo.cvv) {
        toast.error('Please fill in all payment information')
        return
      }
    }

    const orderData = {
      shipping_address: shippingAddress,
      shipping_method: shippingMethod,
      payment_method: paymentMethod,
      payment_info: paymentMethod === 'credit_card' ? paymentInfo : null,
      coupon_code: couponCode,
      items: cart?.items || []
    }

    placeOrderMutation.mutate(orderData)
  }

  const steps = [
    { number: 1, title: 'Shipping', icon: Truck },
    { number: 2, title: 'Delivery', icon: Package },
    { number: 3, title: 'Payment', icon: CreditCard }
  ]

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    currentStep >= step.number ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                  }`}>
                    {currentStep > step.number ? (
                      <Check className="w-6 h-6" />
                    ) : (
                      <step.icon className="w-6 h-6" />
                    )}
                  </div>
                  <span className={`mt-2 text-sm font-medium ${
                    currentStep >= step.number ? 'text-blue-600' : 'text-gray-600'
                  }`}>
                    {step.title}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-24 h-1 mx-4 ${
                    currentStep > step.number ? 'bg-blue-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="col-span-2 space-y-6">
            {/* Step 1: Shipping Address */}
            {currentStep === 1 && (
              <Card>
                <CardHeader>
                  <CardTitle>Shipping Address</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>First Name *</Label>
                      <Input 
                        value={shippingAddress.firstName}
                        onChange={(e) => setShippingAddress({...shippingAddress, firstName: e.target.value})}
                        placeholder="John"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Last Name *</Label>
                      <Input 
                        value={shippingAddress.lastName}
                        onChange={(e) => setShippingAddress({...shippingAddress, lastName: e.target.value})}
                        placeholder="Doe"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Email *</Label>
                    <Input 
                      type="email"
                      value={shippingAddress.email}
                      onChange={(e) => setShippingAddress({...shippingAddress, email: e.target.value})}
                      placeholder="john@example.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Phone *</Label>
                    <Input 
                      type="tel"
                      value={shippingAddress.phone}
                      onChange={(e) => setShippingAddress({...shippingAddress, phone: e.target.value})}
                      placeholder="(555) 123-4567"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Address Line 1 *</Label>
                    <Input 
                      value={shippingAddress.address1}
                      onChange={(e) => setShippingAddress({...shippingAddress, address1: e.target.value})}
                      placeholder="123 Main St"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Address Line 2</Label>
                    <Input 
                      value={shippingAddress.address2}
                      onChange={(e) => setShippingAddress({...shippingAddress, address2: e.target.value})}
                      placeholder="Apt 4B"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>City *</Label>
                      <Input 
                        value={shippingAddress.city}
                        onChange={(e) => setShippingAddress({...shippingAddress, city: e.target.value})}
                        placeholder="New York"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>State *</Label>
                      <Input 
                        value={shippingAddress.state}
                        onChange={(e) => setShippingAddress({...shippingAddress, state: e.target.value})}
                        placeholder="NY"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>ZIP Code *</Label>
                      <Input 
                        value={shippingAddress.zipCode}
                        onChange={(e) => setShippingAddress({...shippingAddress, zipCode: e.target.value})}
                        placeholder="10001"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end pt-4">
                    <Button onClick={handleNextStep}>Continue to Delivery</Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Step 2: Shipping Method */}
            {currentStep === 2 && (
              <Card>
                <CardHeader>
                  <CardTitle>Delivery Method</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <RadioGroup value={shippingMethod} onValueChange={setShippingMethod}>
                    {shippingMethods?.map((method) => (
                      <div key={method.id} className="flex items-center justify-between p-4 border rounded cursor-pointer hover:bg-gray-50">
                        <div className="flex items-center space-x-3">
                          <RadioGroupItem value={method.id} id={method.id} />
                          <Label htmlFor={method.id} className="cursor-pointer">
                            <div>
                              <p className="font-medium">{method.name}</p>
                              <p className="text-sm text-gray-600">{method.description}</p>
                              <p className="text-sm text-gray-600">Estimated delivery: {method.estimated_days} days</p>
                            </div>
                          </Label>
                        </div>
                        <span className="font-bold">${method.cost.toFixed(2)}</span>
                      </div>
                    ))}
                  </RadioGroup>
                  <div className="flex justify-between pt-4">
                    <Button variant="outline" onClick={() => setCurrentStep(1)}>Back</Button>
                    <Button onClick={handleNextStep}>Continue to Payment</Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Step 3: Payment */}
            {currentStep === 3 && (
              <Card>
                <CardHeader>
                  <CardTitle>Payment Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <RadioGroup value={paymentMethod} onValueChange={setPaymentMethod}>
                    <div className="flex items-center space-x-2 p-3 border rounded">
                      <RadioGroupItem value="credit_card" id="credit_card" />
                      <Label htmlFor="credit_card" className="cursor-pointer">Credit Card</Label>
                    </div>
                    <div className="flex items-center space-x-2 p-3 border rounded">
                      <RadioGroupItem value="paypal" id="paypal" />
                      <Label htmlFor="paypal" className="cursor-pointer">PayPal</Label>
                    </div>
                  </RadioGroup>

                  {paymentMethod === 'credit_card' && (
                    <div className="space-y-4 mt-4">
                      <div className="space-y-2">
                        <Label>Card Number *</Label>
                        <Input 
                          value={paymentInfo.cardNumber}
                          onChange={(e) => setPaymentInfo({...paymentInfo, cardNumber: e.target.value})}
                          placeholder="1234 5678 9012 3456"
                          maxLength={19}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Cardholder Name *</Label>
                        <Input 
                          value={paymentInfo.cardName}
                          onChange={(e) => setPaymentInfo({...paymentInfo, cardName: e.target.value})}
                          placeholder="John Doe"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Expiry Date *</Label>
                          <Input 
                            value={paymentInfo.expiryDate}
                            onChange={(e) => setPaymentInfo({...paymentInfo, expiryDate: e.target.value})}
                            placeholder="MM/YY"
                            maxLength={5}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>CVV *</Label>
                          <Input 
                            value={paymentInfo.cvv}
                            onChange={(e) => setPaymentInfo({...paymentInfo, cvv: e.target.value})}
                            placeholder="123"
                            maxLength={4}
                            type="password"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center space-x-2 pt-4">
                    <Checkbox 
                      id="terms" 
                      checked={agreedToTerms}
                      onCheckedChange={setAgreedToTerms}
                    />
                    <Label htmlFor="terms" className="text-sm cursor-pointer">
                      I agree to the <a href="/terms" className="text-blue-600 hover:underline">Terms and Conditions</a>
                    </Label>
                  </div>

                  <div className="flex justify-between pt-4">
                    <Button variant="outline" onClick={() => setCurrentStep(2)}>Back</Button>
                    <Button onClick={handlePlaceOrder} disabled={placeOrderMutation.isPending}>
                      {placeOrderMutation.isPending ? 'Processing...' : 'Place Order'}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Order Summary Sidebar */}
          <div className="col-span-1">
            <Card className="sticky top-4">
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Cart Items */}
                <div className="space-y-3">
                  {cart?.items?.map((item) => (
                    <div key={item.id} className="flex items-center space-x-3">
                      <img src={item.image} alt={item.name} className="w-16 h-16 object-cover rounded" />
                      <div className="flex-1">
                        <p className="font-medium text-sm">{item.name}</p>
                        <p className="text-sm text-gray-600">Qty: {item.quantity}</p>
                      </div>
                      <span className="font-medium">${(item.price * item.quantity).toFixed(2)}</span>
                    </div>
                  ))}
                </div>

                {/* Coupon Code */}
                <div className="pt-4 border-t">
                  <div className="flex space-x-2">
                    <Input 
                      value={couponCode}
                      onChange={(e) => setCouponCode(e.target.value)}
                      placeholder="Coupon code"
                    />
                    <Button 
                      variant="outline" 
                      onClick={() => applyCouponMutation.mutate(couponCode)}
                      disabled={!couponCode}
                    >
                      Apply
                    </Button>
                  </div>
                </div>

                {/* Totals */}
                <div className="space-y-2 pt-4 border-t">
                  <div className="flex justify-between">
                    <span>Subtotal</span>
                    <span>${cart?.subtotal?.toFixed(2) || '0.00'}</span>
                  </div>
                  {cart?.discount > 0 && (
                    <div className="flex justify-between text-green-600">
                      <span>Discount</span>
                      <span>-${cart?.discount?.toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span>Shipping</span>
                    <span>
                      {shippingMethod && shippingMethods 
                        ? `$${shippingMethods.find(m => m.id === shippingMethod)?.cost.toFixed(2)}` 
                        : 'Calculated at next step'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tax</span>
                    <span>${cart?.tax?.toFixed(2) || '0.00'}</span>
                  </div>
                  <div className="flex justify-between font-bold text-lg pt-2 border-t">
                    <span>Total</span>
                    <span>${cart?.total?.toFixed(2) || '0.00'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Checkout
