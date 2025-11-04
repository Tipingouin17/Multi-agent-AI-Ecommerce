import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { 
  Package, 
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Filter,
  RefreshCw,
  DollarSign,
  AlertTriangle
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Returns Management Page
 * 
 * Manage customer return requests:
 * - View all return requests
 * - Approve/reject returns
 * - Process refunds/exchanges
 * - Generate RMA numbers
 * - Track return status
 */
const ReturnsManagement = () => {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedReturn, setSelectedReturn] = useState(null)
  const [actionType, setActionType] = useState('') // approve, reject, refund, exchange
  const [actionNote, setActionNote] = useState('')

  // Fetch returns
  const { data: returns, isLoading } = useQuery({
    queryKey: ['returns', statusFilter, searchTerm],
    queryFn: () => api.returns.getReturns({ status: statusFilter, search: searchTerm })
  })

  // Process return mutation
  const processReturnMutation = useMutation({
    mutationFn: ({ returnId, action, note }) => 
      api.returns.processReturn(returnId, { action, note }),
    onSuccess: () => {
      toast.success('Return processed successfully')
      queryClient.invalidateQueries(['returns'])
      setSelectedReturn(null)
      setActionNote('')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to process return')
    }
  })

  const handleProcessReturn = (returnItem, action) => {
    setSelectedReturn(returnItem)
    setActionType(action)
  }

  const handleConfirmAction = () => {
    if (!actionNote.trim() && (actionType === 'reject')) {
      toast.error('Please provide a reason for rejection')
      return
    }

    processReturnMutation.mutate({
      returnId: selectedReturn.id,
      action: actionType,
      note: actionNote
    })
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'secondary', icon: Clock, label: 'Pending' },
      approved: { variant: 'default', icon: CheckCircle, label: 'Approved' },
      rejected: { variant: 'destructive', icon: XCircle, label: 'Rejected' },
      completed: { variant: 'default', icon: CheckCircle, label: 'Completed' },
      refunded: { variant: 'default', icon: DollarSign, label: 'Refunded' }
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

  const getReasonBadge = (reason) => {
    const colors = {
      'defective': 'bg-red-100 text-red-800',
      'wrong_item': 'bg-orange-100 text-orange-800',
      'not_as_described': 'bg-yellow-100 text-yellow-800',
      'changed_mind': 'bg-blue-100 text-blue-800',
      'other': 'bg-gray-100 text-gray-800'
    }

    return (
      <span className={`px-2 py-1 rounded text-xs ${colors[reason] || colors.other}`}>
        {reason.replace('_', ' ')}
      </span>
    )
  }

  const filteredReturns = returns?.filter(ret => {
    if (statusFilter !== 'all' && ret.status !== statusFilter) return false
    if (searchTerm && !ret.order_number.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading returns...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Returns Management</h1>
          <p className="text-gray-600">Process customer return requests</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending Returns</p>
                <p className="text-2xl font-bold">{returns?.filter(r => r.status === 'pending').length || 0}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Approved</p>
                <p className="text-2xl font-bold">{returns?.filter(r => r.status === 'approved').length || 0}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Refunded</p>
                <p className="text-2xl font-bold">${returns?.filter(r => r.status === 'refunded').reduce((sum, r) => sum + r.refund_amount, 0).toFixed(2) || '0.00'}</p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Return Rate</p>
                <p className="text-2xl font-bold">2.3%</p>
              </div>
              <RefreshCw className="w-8 h-8 text-purple-500" />
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
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="refunded">Refunded</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Returns List */}
      <Card>
        <CardHeader>
          <CardTitle>Return Requests</CardTitle>
          <CardDescription>{filteredReturns?.length || 0} returns found</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredReturns?.map((returnItem) => (
              <Card key={returnItem.id}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                        <Package className="w-8 h-8 text-gray-400" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium">Order #{returnItem.order_number}</h4>
                          {getStatusBadge(returnItem.status)}
                          {getReasonBadge(returnItem.reason)}
                        </div>
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>Customer:</strong> {returnItem.customer_name}
                        </p>
                        <p className="text-sm text-gray-600 mb-1">
                          <strong>Product:</strong> {returnItem.product_name}
                        </p>
                        <p className="text-sm text-gray-600 mb-2">
                          <strong>Reason:</strong> {returnItem.reason_description}
                        </p>
                        <p className="text-xs text-gray-400">
                          Requested on {new Date(returnItem.created_at).toLocaleDateString()}
                        </p>
                        {returnItem.rma_number && (
                          <p className="text-xs text-gray-600 mt-1">
                            <strong>RMA:</strong> {returnItem.rma_number}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col items-end space-y-2">
                      <p className="text-lg font-bold">${returnItem.refund_amount.toFixed(2)}</p>
                      
                      {returnItem.status === 'pending' && (
                        <div className="flex space-x-2">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button 
                                size="sm" 
                                onClick={() => handleProcessReturn(returnItem, 'approve')}
                              >
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Approve
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Approve Return</DialogTitle>
                                <DialogDescription>
                                  Approve this return request and generate RMA number
                                </DialogDescription>
                              </DialogHeader>
                              <div className="space-y-4">
                                <div className="space-y-2">
                                  <Label>Action Type</Label>
                                  <Select value={actionType} onValueChange={setActionType}>
                                    <SelectTrigger>
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="refund">Issue Refund</SelectItem>
                                      <SelectItem value="exchange">Process Exchange</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                                <div className="space-y-2">
                                  <Label>Notes (Optional)</Label>
                                  <Textarea
                                    value={actionNote}
                                    onChange={(e) => setActionNote(e.target.value)}
                                    placeholder="Add any notes..."
                                    rows={3}
                                  />
                                </div>
                                <div className="flex justify-end space-x-2">
                                  <Button variant="outline" onClick={() => setSelectedReturn(null)}>
                                    Cancel
                                  </Button>
                                  <Button onClick={handleConfirmAction}>
                                    Confirm Approval
                                  </Button>
                                </div>
                              </div>
                            </DialogContent>
                          </Dialog>

                          <Dialog>
                            <DialogTrigger asChild>
                              <Button 
                                size="sm" 
                                variant="destructive"
                                onClick={() => handleProcessReturn(returnItem, 'reject')}
                              >
                                <XCircle className="w-4 h-4 mr-1" />
                                Reject
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Reject Return</DialogTitle>
                                <DialogDescription>
                                  Provide a reason for rejecting this return request
                                </DialogDescription>
                              </DialogHeader>
                              <div className="space-y-4">
                                <div className="space-y-2">
                                  <Label>Rejection Reason *</Label>
                                  <Textarea
                                    value={actionNote}
                                    onChange={(e) => setActionNote(e.target.value)}
                                    placeholder="Explain why this return is being rejected..."
                                    rows={4}
                                    required
                                  />
                                </div>
                                <div className="flex justify-end space-x-2">
                                  <Button variant="outline" onClick={() => setSelectedReturn(null)}>
                                    Cancel
                                  </Button>
                                  <Button 
                                    variant="destructive" 
                                    onClick={handleConfirmAction}
                                    disabled={!actionNote.trim()}
                                  >
                                    Confirm Rejection
                                  </Button>
                                </div>
                              </div>
                            </DialogContent>
                          </Dialog>
                        </div>
                      )}

                      {returnItem.status === 'approved' && !returnItem.refunded && (
                        <Button 
                          size="sm"
                          onClick={() => {
                            handleProcessReturn(returnItem, 'refund')
                            handleConfirmAction()
                          }}
                        >
                          <DollarSign className="w-4 h-4 mr-1" />
                          Process Refund
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {(!filteredReturns || filteredReturns.length === 0) && (
              <div className="text-center py-12 text-gray-500">
                <Package className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No returns found</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ReturnsManagement
