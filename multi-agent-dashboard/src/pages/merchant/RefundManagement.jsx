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
import { Textarea } from '@/components/ui/textarea'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { 
  DollarSign, 
  CheckCircle,
  Clock,
  XCircle,
  Search,
  CreditCard,
  AlertTriangle
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Refund Management Page
 * 
 * Process and manage refunds:
 * - View refund requests
 * - Process full/partial refunds
 * - Track refund status
 * - Refund history
 * - Payment gateway integration
 * - Refund analytics
 */
const RefundManagement = () => {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedRefund, setSelectedRefund] = useState(null)
  const [refundAmount, setRefundAmount] = useState('')
  const [refundType, setRefundType] = useState('full')
  const [refundReason, setRefundReason] = useState('')

  // Fetch refunds
  const { data: refunds, isLoading } = useQuery({
    queryKey: ['refunds', statusFilter, searchTerm],
    queryFn: () => api.refunds.getRefunds({ status: statusFilter, search: searchTerm })
  })

  // Process refund mutation
  const processRefundMutation = useMutation({
    mutationFn: ({ refundId, amount, reason }) => 
      api.refunds.processRefund(refundId, { amount, reason }),
    onSuccess: () => {
      toast.success('Refund processed successfully')
      queryClient.invalidateQueries(['refunds'])
      setSelectedRefund(null)
      setRefundAmount('')
      setRefundReason('')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to process refund')
    }
  })

  const handleProcessRefund = (refund) => {
    setSelectedRefund(refund)
    setRefundAmount(refund.order_total.toString())
    setRefundType('full')
  }

  const handleConfirmRefund = () => {
    if (!refundReason.trim()) {
      toast.error('Please provide a refund reason')
      return
    }

    const amount = refundType === 'full' 
      ? selectedRefund.order_total 
      : parseFloat(refundAmount)

    if (refundType === 'partial' && (!amount || amount <= 0 || amount > selectedRefund.order_total)) {
      toast.error('Please enter a valid refund amount')
      return
    }

    processRefundMutation.mutate({
      refundId: selectedRefund.id,
      amount,
      reason: refundReason
    })
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'secondary', icon: Clock, label: 'Pending' },
      approved: { variant: 'default', icon: CheckCircle, label: 'Approved' },
      processing: { variant: 'default', icon: Clock, label: 'Processing' },
      completed: { variant: 'default', icon: CheckCircle, label: 'Completed' },
      failed: { variant: 'destructive', icon: XCircle, label: 'Failed' }
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

  const filteredRefunds = refunds?.filter(refund => {
    if (statusFilter !== 'all' && refund.status !== statusFilter) return false
    if (searchTerm && !refund.order_number.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading refunds...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Refund Management</h1>
          <p className="text-gray-600">Process and track customer refunds</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending Refunds</p>
                <p className="text-2xl font-bold">{refunds?.filter(r => r.status === 'pending').length || 0}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Processing</p>
                <p className="text-2xl font-bold">{refunds?.filter(r => r.status === 'processing').length || 0}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl font-bold">{refunds?.filter(r => r.status === 'completed').length || 0}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Refunded</p>
                <p className="text-2xl font-bold">
                  ${refunds?.filter(r => r.status === 'completed').reduce((sum, r) => sum + r.refund_amount, 0).toFixed(2) || '0.00'}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-purple-500" />
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
                  placeholder="Search by order number..."
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
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Refunds List */}
      <Card>
        <CardHeader>
          <CardTitle>Refund Requests</CardTitle>
          <CardDescription>{filteredRefunds?.length || 0} refunds found</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredRefunds?.map((refund) => (
              <Card key={refund.id}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center">
                        <CreditCard className="w-6 h-6 text-gray-400" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium">Order #{refund.order_number}</h4>
                          {getStatusBadge(refund.status)}
                        </div>
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>Customer:</strong> {refund.customer_name}
                        </p>
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>Order Total:</strong> ${refund.order_total.toFixed(2)}
                        </p>
                        {refund.refund_amount && (
                          <p className="text-sm text-gray-600 mb-1">
                            <strong>Refund Amount:</strong> ${refund.refund_amount.toFixed(2)}
                          </p>
                        )}
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>Payment Method:</strong> {refund.payment_method}
                        </p>
                        <p className="text-sm text-gray-600 mb-2">
                          <strong>Reason:</strong> {refund.reason}
                        </p>
                        <p className="text-xs text-gray-400">
                          Requested on {new Date(refund.created_at).toLocaleDateString()}
                        </p>
                        {refund.processed_at && (
                          <p className="text-xs text-gray-400">
                            Processed on {new Date(refund.processed_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col items-end space-y-2">
                      <p className="text-lg font-bold">${refund.order_total.toFixed(2)}</p>
                      
                      {refund.status === 'pending' && (
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button 
                              size="sm"
                              onClick={() => handleProcessRefund(refund)}
                            >
                              <DollarSign className="w-4 h-4 mr-1" />
                              Process Refund
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Process Refund</DialogTitle>
                              <DialogDescription>
                                Issue a refund for Order #{refund.order_number}
                              </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4">
                              <div className="space-y-2">
                                <Label>Refund Type</Label>
                                <RadioGroup value={refundType} onValueChange={setRefundType}>
                                  <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="full" id="full" />
                                    <Label htmlFor="full">Full Refund (${refund.order_total.toFixed(2)})</Label>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="partial" id="partial" />
                                    <Label htmlFor="partial">Partial Refund</Label>
                                  </div>
                                </RadioGroup>
                              </div>

                              {refundType === 'partial' && (
                                <div className="space-y-2">
                                  <Label>Refund Amount *</Label>
                                  <Input
                                    type="number"
                                    step="0.01"
                                    value={refundAmount}
                                    onChange={(e) => setRefundAmount(e.target.value)}
                                    placeholder="0.00"
                                    max={refund.order_total}
                                  />
                                  <p className="text-sm text-gray-500">
                                    Maximum: ${refund.order_total.toFixed(2)}
                                  </p>
                                </div>
                              )}

                              <div className="space-y-2">
                                <Label>Refund Reason *</Label>
                                <Textarea
                                  value={refundReason}
                                  onChange={(e) => setRefundReason(e.target.value)}
                                  placeholder="Explain the reason for this refund..."
                                  rows={3}
                                  required
                                />
                              </div>

                              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                                <div className="flex items-start space-x-2">
                                  <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                                  <div className="text-sm text-yellow-800">
                                    <p className="font-medium">Important</p>
                                    <p>This action will process the refund immediately through the payment gateway.</p>
                                  </div>
                                </div>
                              </div>

                              <div className="flex justify-end space-x-2">
                                <Button variant="outline" onClick={() => setSelectedRefund(null)}>
                                  Cancel
                                </Button>
                                <Button 
                                  onClick={handleConfirmRefund}
                                  disabled={processRefundMutation.isPending || !refundReason.trim()}
                                >
                                  {processRefundMutation.isPending ? 'Processing...' : 'Confirm Refund'}
                                </Button>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      )}

                      {refund.status === 'completed' && (
                        <Badge variant="default">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Refunded
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {(!filteredRefunds || filteredRefunds.length === 0) && (
              <div className="text-center py-12 text-gray-500">
                <DollarSign className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No refund requests found</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default RefundManagement
