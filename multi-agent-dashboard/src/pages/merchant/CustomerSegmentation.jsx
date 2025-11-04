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
  Users, 
  Plus,
  Trash2,
  Edit,
  Target,
  DollarSign,
  ShoppingBag,
  Calendar,
  TrendingUp
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Customer Segmentation Builder
 * 
 * Create and manage customer segments:
 * - Segment builder with conditions
 * - Behavioral segmentation
 * - Demographic segmentation
 * - Purchase history segmentation
 * - Segment analytics
 * - Export segments
 */
const CustomerSegmentation = () => {
  const queryClient = useQueryClient()
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    conditions: []
  })
  const [newCondition, setNewCondition] = useState({
    field: 'total_orders',
    operator: 'greater_than',
    value: ''
  })

  // Fetch segments
  const { data: segments, isLoading } = useQuery({
    queryKey: ['customer-segments'],
    queryFn: () => api.segments.getSegments()
  })

  // Create segment mutation
  const createMutation = useMutation({
    mutationFn: (data) => api.segments.createSegment(data),
    onSuccess: () => {
      toast.success('Segment created successfully')
      queryClient.invalidateQueries(['customer-segments'])
      setIsCreating(false)
      setFormData({ name: '', description: '', conditions: [] })
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create segment')
    }
  })

  // Delete segment mutation
  const deleteMutation = useMutation({
    mutationFn: (segmentId) => api.segments.deleteSegment(segmentId),
    onSuccess: () => {
      toast.success('Segment deleted')
      queryClient.invalidateQueries(['customer-segments'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete segment')
    }
  })

  const handleAddCondition = () => {
    if (!newCondition.value) {
      toast.error('Please enter a value')
      return
    }

    setFormData({
      ...formData,
      conditions: [...formData.conditions, { ...newCondition }]
    })

    setNewCondition({
      field: 'total_orders',
      operator: 'greater_than',
      value: ''
    })
  }

  const handleRemoveCondition = (index) => {
    setFormData({
      ...formData,
      conditions: formData.conditions.filter((_, i) => i !== index)
    })
  }

  const handleCreate = () => {
    if (!formData.name || formData.conditions.length === 0) {
      toast.error('Please provide a name and at least one condition')
      return
    }

    createMutation.mutate(formData)
  }

  const handleDelete = (segmentId) => {
    if (window.confirm('Are you sure you want to delete this segment?')) {
      deleteMutation.mutate(segmentId)
    }
  }

  const getFieldLabel = (field) => {
    const labels = {
      total_orders: 'Total Orders',
      lifetime_value: 'Lifetime Value',
      avg_order_value: 'Average Order Value',
      last_order_date: 'Last Order Date',
      total_spent: 'Total Spent',
      days_since_last_order: 'Days Since Last Order',
      location: 'Location',
      signup_date: 'Signup Date'
    }
    return labels[field] || field
  }

  const getOperatorLabel = (operator) => {
    const labels = {
      greater_than: '>',
      less_than: '<',
      equal_to: '=',
      not_equal_to: '≠',
      contains: 'contains',
      not_contains: 'does not contain'
    }
    return labels[operator] || operator
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading segments...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Customer Segmentation</h1>
          <p className="text-gray-600">Create and manage customer segments</p>
        </div>
        <Dialog open={isCreating} onOpenChange={setIsCreating}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Segment
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Create Customer Segment</DialogTitle>
              <DialogDescription>Define rules to group customers</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Segment Name *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="High-Value Customers"
                />
              </div>

              <div className="space-y-2">
                <Label>Description</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Customers who have spent over $1000"
                />
              </div>

              <div className="space-y-2">
                <Label>Conditions *</Label>
                <div className="border rounded p-4 space-y-3">
                  {formData.conditions.map((condition, index) => (
                    <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                      <Badge>{getFieldLabel(condition.field)}</Badge>
                      <span className="text-sm">{getOperatorLabel(condition.operator)}</span>
                      <Badge variant="outline">{condition.value}</Badge>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleRemoveCondition(index)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}

                  <div className="grid grid-cols-4 gap-2">
                    <Select 
                      value={newCondition.field} 
                      onValueChange={(value) => setNewCondition({ ...newCondition, field: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="total_orders">Total Orders</SelectItem>
                        <SelectItem value="lifetime_value">Lifetime Value</SelectItem>
                        <SelectItem value="avg_order_value">Avg Order Value</SelectItem>
                        <SelectItem value="last_order_date">Last Order Date</SelectItem>
                        <SelectItem value="total_spent">Total Spent</SelectItem>
                        <SelectItem value="days_since_last_order">Days Since Last Order</SelectItem>
                        <SelectItem value="location">Location</SelectItem>
                        <SelectItem value="signup_date">Signup Date</SelectItem>
                      </SelectContent>
                    </Select>

                    <Select 
                      value={newCondition.operator} 
                      onValueChange={(value) => setNewCondition({ ...newCondition, operator: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="greater_than">Greater than</SelectItem>
                        <SelectItem value="less_than">Less than</SelectItem>
                        <SelectItem value="equal_to">Equal to</SelectItem>
                        <SelectItem value="not_equal_to">Not equal to</SelectItem>
                        <SelectItem value="contains">Contains</SelectItem>
                        <SelectItem value="not_contains">Does not contain</SelectItem>
                      </SelectContent>
                    </Select>

                    <Input
                      value={newCondition.value}
                      onChange={(e) => setNewCondition({ ...newCondition, value: e.target.value })}
                      placeholder="Value"
                    />

                    <Button onClick={handleAddCondition} variant="outline">
                      Add
                    </Button>
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsCreating(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Segment'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Segments Grid */}
      <div className="grid grid-cols-3 gap-6">
        {segments?.map((segment) => (
          <Card key={segment.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <Target className="w-5 h-5 text-blue-500" />
                    <span>{segment.name}</span>
                  </CardTitle>
                  {segment.description && (
                    <CardDescription className="mt-2">{segment.description}</CardDescription>
                  )}
                </div>
                <Button 
                  size="sm" 
                  variant="ghost"
                  onClick={() => handleDelete(segment.id)}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Segment Stats */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <Users className="w-4 h-4 text-gray-400" />
                      <p className="text-sm text-gray-600">Customers</p>
                    </div>
                    <p className="text-2xl font-bold">{segment.customer_count?.toLocaleString() || 0}</p>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <DollarSign className="w-4 h-4 text-gray-400" />
                      <p className="text-sm text-gray-600">Total Value</p>
                    </div>
                    <p className="text-2xl font-bold">${segment.total_value?.toLocaleString() || 0}</p>
                  </div>
                </div>

                {/* Conditions */}
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Conditions:</p>
                  <div className="space-y-1">
                    {segment.conditions?.map((condition, index) => (
                      <div key={index} className="text-sm text-gray-600 flex items-center space-x-1">
                        <Badge variant="outline" className="text-xs">
                          {getFieldLabel(condition.field)}
                        </Badge>
                        <span>{getOperatorLabel(condition.operator)}</span>
                        <span className="font-medium">{condition.value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-2 pt-2 border-t">
                  <Button size="sm" variant="outline" className="flex-1">
                    <Users className="w-4 h-4 mr-1" />
                    View Customers
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    Analytics
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {(!segments || segments.length === 0) && (
          <Card className="col-span-3">
            <CardContent className="pt-12 pb-12">
              <div className="text-center text-gray-500">
                <Target className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No segments created yet</p>
                <p className="text-sm mt-2">Create your first segment to organize customers</p>
                <Button className="mt-4" onClick={() => setIsCreating(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Segment
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Pre-built Segments */}
      <Card>
        <CardHeader>
          <CardTitle>Suggested Segments</CardTitle>
          <CardDescription>Quick-start with pre-built segments</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            {[
              { name: 'VIP Customers', icon: DollarSign, description: 'LTV > $1000', color: 'text-yellow-500' },
              { name: 'Frequent Buyers', icon: ShoppingBag, description: 'Orders > 10', color: 'text-blue-500' },
              { name: 'At Risk', icon: Calendar, description: 'No order in 90 days', color: 'text-red-500' },
              { name: 'New Customers', icon: Users, description: 'Signed up < 30 days', color: 'text-green-500' }
            ].map((preset, index) => {
              const Icon = preset.icon
              return (
                <Card key={index} className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="pt-6">
                    <Icon className={`w-8 h-8 ${preset.color} mb-3`} />
                    <h4 className="font-medium mb-1">{preset.name}</h4>
                    <p className="text-sm text-gray-600">{preset.description}</p>
                    <Button size="sm" variant="outline" className="w-full mt-3">
                      Use Template
                    </Button>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CustomerSegmentation
