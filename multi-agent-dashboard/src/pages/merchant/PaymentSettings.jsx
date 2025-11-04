import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { 
  CreditCard, 
  Plus,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  EyeOff,
  TestTube
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Payment Settings
 * 
 * Configure payment gateways and methods:
 * - Add/remove payment gateways
 * - Configure API credentials
 * - Enable/disable payment methods
 * - Test payment integration
 * - Manage payout settings
 */
const PaymentSettings = () => {
  const queryClient = useQueryClient()
  const [isAdding, setIsAdding] = useState(false)
  const [showApiKey, setShowApiKey] = useState({})
  const [newGateway, setNewGateway] = useState({
    provider: 'stripe',
    api_key: '',
    api_secret: '',
    webhook_secret: '',
    test_mode: true,
    enabled: true
  })

  // Fetch payment configurations
  const { data: payments, isLoading } = useQuery({
    queryKey: ['payment-settings'],
    queryFn: () => api.settings.getPayments()
  })

  // Add payment gateway mutation
  const addMutation = useMutation({
    mutationFn: (data) => api.settings.addPaymentGateway(data),
    onSuccess: () => {
      toast.success('Payment gateway added successfully')
      queryClient.invalidateQueries(['payment-settings'])
      setIsAdding(false)
      setNewGateway({
        provider: 'stripe',
        api_key: '',
        api_secret: '',
        webhook_secret: '',
        test_mode: true,
        enabled: true
      })
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to add payment gateway')
    }
  })

  // Update payment gateway mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => api.settings.updatePaymentGateway(id, data),
    onSuccess: () => {
      toast.success('Payment gateway updated')
      queryClient.invalidateQueries(['payment-settings'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update payment gateway')
    }
  })

  // Delete payment gateway mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => api.settings.deletePaymentGateway(id),
    onSuccess: () => {
      toast.success('Payment gateway removed')
      queryClient.invalidateQueries(['payment-settings'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to remove payment gateway')
    }
  })

  // Test payment gateway mutation
  const testMutation = useMutation({
    mutationFn: (id) => api.settings.testPaymentGateway(id),
    onSuccess: () => {
      toast.success('Payment gateway test successful')
    },
    onError: (error) => {
      toast.error(error.message || 'Payment gateway test failed')
    }
  })

  const handleAdd = () => {
    if (!newGateway.api_key || !newGateway.api_secret) {
      toast.error('Please provide API credentials')
      return
    }
    addMutation.mutate(newGateway)
  }

  const handleToggle = (id, currentStatus) => {
    updateMutation.mutate({ id, data: { enabled: !currentStatus } })
  }

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to remove this payment gateway?')) {
      deleteMutation.mutate(id)
    }
  }

  const handleTest = (id) => {
    testMutation.mutate(id)
  }

  const toggleApiKeyVisibility = (id) => {
    setShowApiKey(prev => ({ ...prev, [id]: !prev[id] }))
  }

  const getProviderLogo = (provider) => {
    const logos = {
      stripe: '🔷',
      paypal: '💙',
      square: '⬛',
      authorize_net: '🟦',
      braintree: '🔵'
    }
    return logos[provider] || '💳'
  }

  const getProviderName = (provider) => {
    const names = {
      stripe: 'Stripe',
      paypal: 'PayPal',
      square: 'Square',
      authorize_net: 'Authorize.Net',
      braintree: 'Braintree'
    }
    return names[provider] || provider
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading payment settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Payment Settings</h1>
          <p className="text-gray-600">Configure payment gateways and methods</p>
        </div>
        <Dialog open={isAdding} onOpenChange={setIsAdding}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add Payment Gateway
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Add Payment Gateway</DialogTitle>
              <DialogDescription>Configure a new payment gateway for your store</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Payment Provider *</Label>
                <select
                  className="w-full p-2 border rounded"
                  value={newGateway.provider}
                  onChange={(e) => setNewGateway({ ...newGateway, provider: e.target.value })}
                >
                  <option value="stripe">Stripe</option>
                  <option value="paypal">PayPal</option>
                  <option value="square">Square</option>
                  <option value="authorize_net">Authorize.Net</option>
                  <option value="braintree">Braintree</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label>API Key / Publishable Key *</Label>
                <Input
                  value={newGateway.api_key}
                  onChange={(e) => setNewGateway({ ...newGateway, api_key: e.target.value })}
                  placeholder="pk_test_..."
                />
              </div>

              <div className="space-y-2">
                <Label>API Secret / Secret Key *</Label>
                <Input
                  type="password"
                  value={newGateway.api_secret}
                  onChange={(e) => setNewGateway({ ...newGateway, api_secret: e.target.value })}
                  placeholder="sk_test_..."
                />
              </div>

              <div className="space-y-2">
                <Label>Webhook Secret (Optional)</Label>
                <Input
                  type="password"
                  value={newGateway.webhook_secret}
                  onChange={(e) => setNewGateway({ ...newGateway, webhook_secret: e.target.value })}
                  placeholder="whsec_..."
                />
                <p className="text-sm text-gray-500">Required for webhook verification</p>
              </div>

              <div className="flex items-center justify-between p-3 border rounded">
                <div>
                  <p className="font-medium">Test Mode</p>
                  <p className="text-sm text-gray-600">Use test API keys for testing</p>
                </div>
                <Switch 
                  checked={newGateway.test_mode}
                  onCheckedChange={(checked) => setNewGateway({ ...newGateway, test_mode: checked })}
                />
              </div>

              <div className="flex items-center justify-between p-3 border rounded">
                <div>
                  <p className="font-medium">Enable Gateway</p>
                  <p className="text-sm text-gray-600">Make this gateway available at checkout</p>
                </div>
                <Switch 
                  checked={newGateway.enabled}
                  onCheckedChange={(checked) => setNewGateway({ ...newGateway, enabled: checked })}
                />
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button variant="outline" onClick={() => setIsAdding(false)}>
                  Cancel
                </Button>
                <Button onClick={handleAdd} disabled={addMutation.isPending}>
                  {addMutation.isPending ? 'Adding...' : 'Add Gateway'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Payment Gateways */}
      <div className="space-y-4">
        {payments?.map((payment) => (
          <Card key={payment.id} className="hover:shadow-md transition-shadow">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-purple-500 rounded flex items-center justify-center text-3xl">
                    {getProviderLogo(payment.provider)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-lg font-medium">{getProviderName(payment.provider)}</h3>
                      <Badge variant={payment.enabled ? 'default' : 'secondary'}>
                        {payment.enabled ? 'Active' : 'Disabled'}
                      </Badge>
                      {payment.test_mode && (
                        <Badge variant="outline">Test Mode</Badge>
                      )}
                      {payment.verified ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-4">
                      <div>
                        <Label className="text-sm text-gray-600">API Key</Label>
                        <div className="flex items-center space-x-2 mt-1">
                          <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                            {showApiKey[payment.id] 
                              ? payment.api_key 
                              : payment.api_key?.substring(0, 12) + '...'}
                          </code>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => toggleApiKeyVisibility(payment.id)}
                          >
                            {showApiKey[payment.id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </Button>
                        </div>
                      </div>

                      <div>
                        <Label className="text-sm text-gray-600">Status</Label>
                        <div className="flex items-center space-x-2 mt-1">
                          {payment.verified ? (
                            <span className="text-sm text-green-600 flex items-center space-x-1">
                              <CheckCircle className="w-4 h-4" />
                              <span>Verified</span>
                            </span>
                          ) : (
                            <span className="text-sm text-red-600 flex items-center space-x-1">
                              <XCircle className="w-4 h-4" />
                              <span>Not Verified</span>
                            </span>
                          )}
                        </div>
                      </div>

                      <div>
                        <Label className="text-sm text-gray-600">Transactions</Label>
                        <p className="text-sm font-medium mt-1">
                          {payment.transaction_count?.toLocaleString() || 0}
                        </p>
                      </div>

                      <div>
                        <Label className="text-sm text-gray-600">Total Processed</Label>
                        <p className="text-sm font-medium mt-1">
                          ${payment.total_processed?.toLocaleString() || '0.00'}
                        </p>
                      </div>
                    </div>

                    {payment.webhook_url && (
                      <div className="mt-4 p-3 bg-gray-50 rounded">
                        <Label className="text-sm text-gray-600">Webhook URL</Label>
                        <code className="text-sm block mt-1">{payment.webhook_url}</code>
                        <p className="text-xs text-gray-500 mt-1">
                          Configure this URL in your {getProviderName(payment.provider)} dashboard
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex flex-col space-y-2 ml-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">
                      {payment.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                    <Switch 
                      checked={payment.enabled}
                      onCheckedChange={() => handleToggle(payment.id, payment.enabled)}
                    />
                  </div>

                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleTest(payment.id)}
                  >
                    <TestTube className="w-4 h-4 mr-1" />
                    Test
                  </Button>

                  <Button 
                    size="sm" 
                    variant="outline"
                  >
                    Edit
                  </Button>

                  <Button 
                    size="sm" 
                    variant="destructive"
                    onClick={() => handleDelete(payment.id)}
                  >
                    <Trash2 className="w-4 h-4 mr-1" />
                    Remove
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {(!payments || payments.length === 0) && (
          <Card>
            <CardContent className="pt-12 pb-12">
              <div className="text-center text-gray-500">
                <CreditCard className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No payment gateways configured</p>
                <p className="text-sm mt-2">Add a payment gateway to start accepting payments</p>
                <Button className="mt-4" onClick={() => setIsAdding(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Payment Gateway
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Important Information */}
      <Card className="bg-yellow-50 border-yellow-200">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div>
              <p className="font-medium text-yellow-900">Important Security Information</p>
              <ul className="text-sm text-yellow-800 mt-2 space-y-1 list-disc list-inside">
                <li>Never share your API secret keys with anyone</li>
                <li>Use test mode keys during development and testing</li>
                <li>Enable webhook verification for secure payment notifications</li>
                <li>Regularly rotate your API keys for security</li>
                <li>Monitor transaction logs for suspicious activity</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Supported Payment Methods */}
      <Card>
        <CardHeader>
          <CardTitle>Supported Payment Methods</CardTitle>
          <CardDescription>Payment methods available based on your configured gateways</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            {[
              { name: 'Credit Card', icon: '💳', supported: true },
              { name: 'Debit Card', icon: '💳', supported: true },
              { name: 'PayPal', icon: '💙', supported: payments?.some(p => p.provider === 'paypal') },
              { name: 'Apple Pay', icon: '🍎', supported: payments?.some(p => p.provider === 'stripe') },
              { name: 'Google Pay', icon: 'G', supported: payments?.some(p => p.provider === 'stripe') },
              { name: 'Bank Transfer', icon: '🏦', supported: false },
              { name: 'Cryptocurrency', icon: '₿', supported: false },
              { name: 'Buy Now Pay Later', icon: '💰', supported: false }
            ].map((method, index) => (
              <Card key={index} className={method.supported ? 'border-green-200 bg-green-50' : 'border-gray-200'}>
                <CardContent className="pt-6 text-center">
                  <div className="text-3xl mb-2">{method.icon}</div>
                  <p className="text-sm font-medium">{method.name}</p>
                  <Badge 
                    variant={method.supported ? 'default' : 'secondary'} 
                    className="mt-2"
                  >
                    {method.supported ? 'Supported' : 'Not Available'}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default PaymentSettings
