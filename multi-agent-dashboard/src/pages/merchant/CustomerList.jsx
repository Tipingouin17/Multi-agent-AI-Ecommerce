import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Users, 
  DollarSign,
  ShoppingBag,
  TrendingUp,
  Search,
  Mail,
  Download,
  Filter,
  Eye,
  Tag
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Customer List & Management Page
 * 
 * Comprehensive customer directory with:
 * - Search and filtering
 * - Customer segmentation
 * - Lifetime value tracking
 * - Purchase history overview
 * - Bulk operations
 * - Export functionality
 */
const CustomerList = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [segmentFilter, setSegmentFilter] = useState('all')
  const [sortBy, setSortBy] = useState('ltv_desc')
  const [selectedCustomers, setSelectedCustomers] = useState([])

  // Fetch customers
  const { data: customersData, isLoading } = useQuery({
    queryKey: ['customers', searchTerm, segmentFilter, sortBy],
    queryFn: () => api.customers.getCustomers({ 
      search: searchTerm, 
      segment: segmentFilter,
      sort: sortBy 
    })
  })

  // Fetch customer statistics
  const { data: stats } = useQuery({
    queryKey: ['customer-stats'],
    queryFn: () => api.customers.getStats()
  })

  // Export customers mutation
  const exportMutation = useMutation({
    mutationFn: () => api.customers.exportCustomers(selectedCustomers),
    onSuccess: (data) => {
      // Create download link
      const url = window.URL.createObjectURL(new Blob([data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `customers-${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
      toast.success('Customers exported successfully')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to export customers')
    }
  })

  // Bulk email mutation
  const bulkEmailMutation = useMutation({
    mutationFn: (customerIds) => api.customers.sendBulkEmail(customerIds),
    onSuccess: () => {
      toast.success('Email campaign created')
      setSelectedCustomers([])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create email campaign')
    }
  })

  const handleSelectCustomer = (customerId) => {
    setSelectedCustomers(prev => 
      prev.includes(customerId) 
        ? prev.filter(id => id !== customerId)
        : [...prev, customerId]
    )
  }

  const handleSelectAll = () => {
    if (selectedCustomers.length === customersData?.customers?.length) {
      setSelectedCustomers([])
    } else {
      setSelectedCustomers(customersData?.customers?.map(c => c.id) || [])
    }
  }

  const handleViewProfile = (customerId) => {
    navigate(`/customers/${customerId}`)
  }

  const handleExport = () => {
    if (selectedCustomers.length === 0) {
      toast.error('Please select customers to export')
      return
    }
    exportMutation.mutate()
  }

  const handleBulkEmail = () => {
    if (selectedCustomers.length === 0) {
      toast.error('Please select customers to email')
      return
    }
    bulkEmailMutation.mutate(selectedCustomers)
  }

  const getSegmentBadge = (segment) => {
    const segmentConfig = {
      vip: { variant: 'default', label: 'VIP', color: 'bg-purple-100 text-purple-800' },
      loyal: { variant: 'default', label: 'Loyal', color: 'bg-blue-100 text-blue-800' },
      at_risk: { variant: 'destructive', label: 'At Risk', color: 'bg-red-100 text-red-800' },
      new: { variant: 'default', label: 'New', color: 'bg-green-100 text-green-800' },
      inactive: { variant: 'secondary', label: 'Inactive', color: 'bg-gray-100 text-gray-800' }
    }

    const config = segmentConfig[segment] || segmentConfig.new
    
    return (
      <Badge className={config.color}>
        {config.label}
      </Badge>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading customers...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Customers</h1>
          <p className="text-gray-600">Manage your customer relationships</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleBulkEmail} disabled={selectedCustomers.length === 0}>
            <Mail className="w-4 h-4 mr-2" />
            Email Selected ({selectedCustomers.length})
          </Button>
          <Button variant="outline" onClick={handleExport} disabled={selectedCustomers.length === 0}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Customers</p>
                <p className="text-2xl font-bold">{stats?.totalCustomers?.toLocaleString() || '0'}</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-500">+{stats?.newCustomersThisMonth || 0} this month</span>
                </div>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Lifetime Value</p>
                <p className="text-2xl font-bold">${stats?.avgLifetimeValue?.toFixed(2) || '0.00'}</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-500">+8.2%</span>
                </div>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Orders</p>
                <p className="text-2xl font-bold">{stats?.avgOrders?.toFixed(1) || '0.0'}</p>
                <p className="text-sm text-gray-600 mt-1">per customer</p>
              </div>
              <ShoppingBag className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Retention Rate</p>
                <p className="text-2xl font-bold">{stats?.retentionRate?.toFixed(1) || '0.0'}%</p>
                <p className="text-sm text-gray-600 mt-1">90-day</p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-500" />
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
                  placeholder="Search by name, email, or phone..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={segmentFilter} onValueChange={setSegmentFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All Segments" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Segments</SelectItem>
                <SelectItem value="vip">VIP</SelectItem>
                <SelectItem value="loyal">Loyal</SelectItem>
                <SelectItem value="at_risk">At Risk</SelectItem>
                <SelectItem value="new">New</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ltv_desc">Lifetime Value (High to Low)</SelectItem>
                <SelectItem value="ltv_asc">Lifetime Value (Low to High)</SelectItem>
                <SelectItem value="orders_desc">Most Orders</SelectItem>
                <SelectItem value="recent">Recently Active</SelectItem>
                <SelectItem value="name_asc">Name (A-Z)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Customer List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Customer Directory</CardTitle>
              <CardDescription>{customersData?.customers?.length || 0} customers found</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={handleSelectAll}>
              {selectedCustomers.length === customersData?.customers?.length ? 'Deselect All' : 'Select All'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {customersData?.customers?.map((customer) => (
              <Card key={customer.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-start space-x-4">
                    <input
                      type="checkbox"
                      checked={selectedCustomers.includes(customer.id)}
                      onChange={() => handleSelectCustomer(customer.id)}
                      className="mt-1"
                    />
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      {customer.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-medium text-lg">{customer.name}</h4>
                        {getSegmentBadge(customer.segment)}
                        {customer.tags?.map((tag, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            <Tag className="w-3 h-3 mr-1" />
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm text-gray-600">
                        <p><strong>Email:</strong> {customer.email}</p>
                        <p><strong>Phone:</strong> {customer.phone || 'N/A'}</p>
                        <p><strong>Location:</strong> {customer.city}, {customer.state}</p>
                        <p><strong>Member Since:</strong> {new Date(customer.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="mb-3">
                        <p className="text-sm text-gray-600">Lifetime Value</p>
                        <p className="text-2xl font-bold text-green-600">${customer.lifetime_value.toLocaleString()}</p>
                      </div>
                      <div className="mb-3">
                        <p className="text-sm text-gray-600">Total Orders</p>
                        <p className="text-lg font-semibold">{customer.total_orders}</p>
                      </div>
                      <p className="text-xs text-gray-400">
                        Last order: {customer.last_order_date ? new Date(customer.last_order_date).toLocaleDateString() : 'Never'}
                      </p>
                    </div>
                    <div className="flex flex-col space-y-2">
                      <Button 
                        size="sm" 
                        onClick={() => handleViewProfile(customer.id)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        View Profile
                      </Button>
                      <Button size="sm" variant="outline">
                        <Mail className="w-4 h-4 mr-1" />
                        Email
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {(!customersData?.customers || customersData.customers.length === 0) && (
              <div className="text-center py-12 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No customers found</p>
                <p className="text-sm mt-2">Try adjusting your search or filters</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CustomerList
