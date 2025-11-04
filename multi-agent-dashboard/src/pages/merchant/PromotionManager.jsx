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
  Tag, 
  Percent,
  DollarSign,
  Gift,
  TrendingUp,
  Calendar,
  Users,
  Search,
  Plus,
  Copy,
  Trash2,
  BarChart
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Discount & Promotion Manager Page
 * 
 * Create and manage promotions:
 * - Discount codes
 * - Percentage/fixed discounts
 * - BOGO offers
 * - Free shipping
 * - Usage tracking
 * - Performance analytics
 */
const PromotionManager = () => {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [isCreating, setIsCreating] = useState(false)
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    type: 'percentage',
    value: '',
    min_purchase: '',
    max_uses: '',
    start_date: '',
    end_date: '',
    description: ''
  })

  // Fetch promotions
  const { data: promotions, isLoading } = useQuery({
    queryKey: ['promotions', statusFilter, typeFilter, searchTerm],
    queryFn: () => api.promotions.getPromotions({ 
      status: statusFilter, 
      type: typeFilter,
      search: searchTerm 
    })
  })

  // Fetch promotion statistics
  const { data: stats } = useQuery({
    queryKey: ['promotion-stats'],
    queryFn: () => api.promotions.getStats()
  })

  // Create promotion mutation
  const createMutation = useMutation({
    mutationFn: (data) => api.promotions.createPromotion(data),
    onSuccess: () => {
      toast.success('Promotion created successfully')
      queryClient.invalidateQueries(['promotions'])
      setIsCreating(false)
      setFormData({
        name: '',
        code: '',
        type: 'percentage',
        value: '',
        min_purchase: '',
        max_uses: '',
        start_date: '',
        end_date: '',
        description: ''
      })
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create promotion')
    }
  })

  // Delete promotion mutation
  const deleteMutation = useMutation({
    mutationFn: (promotionId) => api.promotions.deletePromotion(promotionId),
    onSuccess: () => {
      toast.success('Promotion deleted')
      queryClient.invalidateQueries(['promotions'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete promotion')
    }
  })

  const handleCreate = () => {
    if (!formData.name || !formData.code || !formData.value) {
      toast.error('Please fill in all required fields')
      return
    }

    createMutation.mutate(formData)
  }

  const handleDelete = (promotionId) => {
    if (window.confirm('Are you sure you want to delete this promotion?')) {
      deleteMutation.mutate(promotionId)
    }
  }

  const generateCode = () => {
    const code = 'PROMO' + Math.random().toString(36).substring(2, 8).toUpperCase()
    setFormData({ ...formData, code })
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { variant: 'default', label: 'Active' },
      scheduled: { variant: 'secondary', label: 'Scheduled' },
      expired: { variant: 'destructive', label: 'Expired' },
      paused: { variant: 'secondary', label: 'Paused' }
    }

    const config = statusConfig[status] || statusConfig.active
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  const getTypeBadge = (type) => {
    const typeConfig = {
      percentage: { icon: Percent, label: 'Percentage Off', color: 'bg-blue-100 text-blue-800' },
      fixed: { icon: DollarSign, label: 'Fixed Amount', color: 'bg-green-100 text-green-800' },
      bogo: { icon: Gift, label: 'BOGO', color: 'bg-purple-100 text-purple-800' },
      free_shipping: { icon: Tag, label: 'Free Shipping', color: 'bg-orange-100 text-orange-800' }
    }

    const config = typeConfig[type] || typeConfig.percentage
    const Icon = config.icon

    return (
      <Badge className={config.color}>
        <Icon className="w-3 h-3 mr-1" />
        {config.label}
      </Badge>
    )
  }

  const filteredPromotions = promotions?.filter(promo => {
    if (statusFilter !== 'all' && promo.status !== statusFilter) return false
    if (typeFilter !== 'all' && promo.type !== typeFilter) return false
    if (searchTerm && !promo.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !promo.code.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading promotions...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Promotions & Discounts</h1>
          <p className="text-gray-600">Create and manage discount codes and offers</p>
        </div>
        <Dialog open={isCreating} onOpenChange={setIsCreating}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Promotion
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create Promotion</DialogTitle>
              <DialogDescription>Set up a new discount or promotion</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Promotion Name *</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Summer Sale 2025"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Discount Code *</Label>
                  <div className="flex space-x-2">
                    <Input
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                      placeholder="SUMMER25"
                    />
                    <Button type="button" variant="outline" onClick={generateCode}>
                      Generate
                    </Button>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Discount Type *</Label>
                <RadioGroup value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value })}>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="percentage" id="percentage" />
                    <Label htmlFor="percentage">Percentage Off</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="fixed" id="fixed" />
                    <Label htmlFor="fixed">Fixed Amount Off</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="bogo" id="bogo" />
                    <Label htmlFor="bogo">Buy One Get One</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="free_shipping" id="free_shipping" />
                    <Label htmlFor="free_shipping">Free Shipping</Label>
                  </div>
                </RadioGroup>
              </div>

              {formData.type !== 'free_shipping' && (
                <div className="space-y-2">
                  <Label>Discount Value *</Label>
                  <Input
                    type="number"
                    value={formData.value}
                    onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                    placeholder={formData.type === 'percentage' ? '25' : '10.00'}
                  />
                  <p className="text-sm text-gray-500">
                    {formData.type === 'percentage' ? 'Enter percentage (e.g., 25 for 25% off)' : 'Enter amount (e.g., 10.00 for $10 off)'}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Minimum Purchase</Label>
                  <Input
                    type="number"
                    value={formData.min_purchase}
                    onChange={(e) => setFormData({ ...formData, min_purchase: e.target.value })}
                    placeholder="0.00"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Max Uses</Label>
                  <Input
                    type="number"
                    value={formData.max_uses}
                    onChange={(e) => setFormData({ ...formData, max_uses: e.target.value })}
                    placeholder="Unlimited"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Start Date *</Label>
                  <Input
                    type="datetime-local"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>End Date</Label>
                  <Input
                    type="datetime-local"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe this promotion..."
                  rows={3}
                />
              </div>

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsCreating(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Promotion'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Promotions</p>
                <p className="text-2xl font-bold">{stats?.activePromotions || 0}</p>
              </div>
              <Tag className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Uses</p>
                <p className="text-2xl font-bold">{stats?.totalUses?.toLocaleString() || '0'}</p>
                <p className="text-xs text-gray-400 mt-1">this month</p>
              </div>
              <Users className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Discount</p>
                <p className="text-2xl font-bold">${stats?.totalDiscount?.toLocaleString() || '0'}</p>
                <p className="text-xs text-gray-400 mt-1">given</p>
              </div>
              <DollarSign className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Conversion Rate</p>
                <p className="text-2xl font-bold">{stats?.conversionRate?.toFixed(1) || '0.0'}%</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-green-500" />
                  <span className="text-xs text-green-500">+3.2%</span>
                </div>
              </div>
              <BarChart className="w-8 h-8 text-orange-500" />
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
                  placeholder="Search by name or code..."
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
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="percentage">Percentage Off</SelectItem>
                <SelectItem value="fixed">Fixed Amount</SelectItem>
                <SelectItem value="bogo">BOGO</SelectItem>
                <SelectItem value="free_shipping">Free Shipping</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Promotions List */}
      <Card>
        <CardHeader>
          <CardTitle>Promotions</CardTitle>
          <CardDescription>{filteredPromotions?.length || 0} promotions found</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredPromotions?.map((promo) => (
              <Card key={promo.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-500 rounded flex items-center justify-center text-white font-bold">
                        <Tag className="w-6 h-6" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium text-lg">{promo.name}</h4>
                          {getStatusBadge(promo.status)}
                          {getTypeBadge(promo.type)}
                        </div>
                        <div className="flex items-center space-x-4 mb-2">
                          <Badge variant="outline" className="font-mono text-lg">
                            {promo.code}
                          </Badge>
                          <Button size="sm" variant="ghost" onClick={() => {
                            navigator.clipboard.writeText(promo.code)
                            toast.success('Code copied to clipboard')
                          }}>
                            <Copy className="w-3 h-3" />
                          </Button>
                        </div>
                        {promo.description && (
                          <p className="text-sm text-gray-600 mb-2">{promo.description}</p>
                        )}
                        <div className="grid grid-cols-4 gap-4 text-sm">
                          <div>
                            <p className="text-gray-600">Uses</p>
                            <p className="font-medium">{promo.uses} / {promo.max_uses || '∞'}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">Discount Given</p>
                            <p className="font-medium">${promo.total_discount?.toLocaleString() || '0'}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">Start Date</p>
                            <p className="font-medium">{new Date(promo.start_date).toLocaleDateString()}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">End Date</p>
                            <p className="font-medium">
                              {promo.end_date ? new Date(promo.end_date).toLocaleDateString() : 'No expiry'}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col space-y-2">
                      <Button size="sm" variant="outline">
                        <BarChart className="w-4 h-4 mr-1" />
                        Analytics
                      </Button>
                      <Button 
                        size="sm" 
                        variant="destructive"
                        onClick={() => handleDelete(promo.id)}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {(!filteredPromotions || filteredPromotions.length === 0) && (
              <div className="text-center py-12 text-gray-500">
                <Tag className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No promotions found</p>
                <p className="text-sm mt-2">Create your first promotion to boost sales</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default PromotionManager
