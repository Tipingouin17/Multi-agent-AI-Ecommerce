import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import {
  Users,
  UserPlus,
  UserMinus,
  DollarSign,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Download,
  ArrowUpRight,
  ArrowDownRight,
  Target
} from 'lucide-react'
import api from '@/lib/api-enhanced'

const CustomerAnalyticsDashboard = () => {
  const [timeRange, setTimeRange] = useState('30d')
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Fetch customer overview
  const { data: customerOverview, isLoading: loadingOverview, refetch } = useQuery({
    queryKey: ['customerOverview', timeRange],
    queryFn: () => api.analytics.getCustomerOverview({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch customer acquisition
  const { data: acquisition, isLoading: loadingAcquisition } = useQuery({
    queryKey: ['customerAcquisition', timeRange],
    queryFn: () => api.analytics.getCustomerAcquisition({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch customer retention
  const { data: retention, isLoading: loadingRetention } = useQuery({
    queryKey: ['customerRetention', timeRange],
    queryFn: () => api.analytics.getCustomerRetention({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch customer segmentation
  const { data: segmentation, isLoading: loadingSegmentation } = useQuery({
    queryKey: ['customerSegmentation'],
    queryFn: () => api.analytics.getCustomerSegmentation(),
    refetchInterval: 60000,
  })

  // Fetch customer lifetime value
  const { data: clvData, isLoading: loadingCLV } = useQuery({
    queryKey: ['customerLifetimeValue', timeRange],
    queryFn: () => api.analytics.getCustomerLifetimeValue({ timeRange }),
    refetchInterval: 60000,
  })

  const handleRefresh = () => {
    refetch()
    setLastUpdated(new Date())
  }

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Format percentage
  const formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
  }

  // Get trend indicator
  const getTrendIndicator = (value) => {
    if (value > 0) {
      return {
        icon: <ArrowUpRight className="w-4 h-4" />,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
      }
    } else if (value < 0) {
      return {
        icon: <ArrowDownRight className="w-4 h-4" />,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
      }
    }
    return {
      icon: null,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
    }
  }

  // KPI Card Component
  const KPICard = ({ title, value, change, icon: Icon, loading }) => {
    const trend = getTrendIndicator(change)
    
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <div className="mt-2 flex items-baseline gap-2">
                <p className="text-3xl font-bold text-gray-900">
                  {loading ? '...' : value}
                </p>
                {change !== undefined && (
                  <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${trend.bgColor}`}>
                    {trend.icon}
                    <span className={`text-sm font-medium ${trend.color}`}>
                      {formatPercentage(change)}
                    </span>
                  </div>
                )}
              </div>
              <p className="mt-1 text-xs text-gray-500">vs. previous period</p>
            </div>
            <div className="ml-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <Icon className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Segment colors
  const SEGMENT_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Customer Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Understand your customers and optimize acquisition & retention
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-gray-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Time Range Selector */}
      <Tabs value={timeRange} onValueChange={setTimeRange}>
        <TabsList>
          <TabsTrigger value="7d">Last 7 Days</TabsTrigger>
          <TabsTrigger value="30d">Last 30 Days</TabsTrigger>
          <TabsTrigger value="90d">Last 90 Days</TabsTrigger>
          <TabsTrigger value="1y">Last Year</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Customers"
          value={customerOverview?.totalCustomers?.toLocaleString() || '0'}
          change={customerOverview?.customerGrowth || 0}
          icon={Users}
          loading={loadingOverview}
        />
        <KPICard
          title="New Customers"
          value={customerOverview?.newCustomers?.toLocaleString() || '0'}
          change={customerOverview?.newCustomerGrowth || 0}
          icon={UserPlus}
          loading={loadingOverview}
        />
        <KPICard
          title="Customer Lifetime Value"
          value={formatCurrency(customerOverview?.avgCLV || 0)}
          change={customerOverview?.clvChange || 0}
          icon={DollarSign}
          loading={loadingOverview}
        />
        <KPICard
          title="Retention Rate"
          value={`${(customerOverview?.retentionRate || 0).toFixed(1)}%`}
          change={customerOverview?.retentionChange || 0}
          icon={Target}
          loading={loadingOverview}
        />
      </div>

      {/* Customer Acquisition Trends */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Acquisition Trends</CardTitle>
          <CardDescription>New customers over time with acquisition channels</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingAcquisition ? (
            <div className="h-80 flex items-center justify-center">
              <div className="text-gray-500">Loading chart data...</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={acquisition || []}>
                <defs>
                  <linearGradient id="colorNewCustomers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="date" 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="newCustomers"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorNewCustomers)"
                  name="New Customers"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Customer Segmentation */}
        <Card>
          <CardHeader>
            <CardTitle>Customer Segmentation</CardTitle>
            <CardDescription>Customers by value tier</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingSegmentation ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <div className="space-y-4">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={segmentation || []}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {(segmentation || []).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={SEGMENT_COLORS[index % SEGMENT_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2">
                  {(segmentation || []).map((segment, index) => (
                    <div key={segment.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: SEGMENT_COLORS[index % SEGMENT_COLORS.length] }}
                        />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{segment.name}</p>
                          <p className="text-xs text-gray-500">{segment.description}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-gray-900">{segment.value}</p>
                        <p className="text-xs text-gray-500">customers</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Retention Rate Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Customer Retention</CardTitle>
            <CardDescription>Retention rate over time</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingRetention ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={256}>
                <LineChart data={retention || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                  />
                  <YAxis 
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }}
                    formatter={(value) => `${value.toFixed(1)}%`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="retentionRate"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={{ fill: '#10b981', r: 4 }}
                    name="Retention Rate"
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Customer Lifetime Value Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Lifetime Value Distribution</CardTitle>
          <CardDescription>CLV by customer cohort</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingCLV ? (
            <div className="h-64 flex items-center justify-center">
              <div className="text-gray-500">Loading data...</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={256}>
              <BarChart data={clvData || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="cohort" 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                  formatter={(value) => formatCurrency(value)}
                />
                <Bar dataKey="avgCLV" fill="#3b82f6" name="Avg CLV" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Churn Rate</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {(customerOverview?.churnRate || 0).toFixed(1)}%
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {customerOverview?.churnedCustomers || 0} customers lost
                </p>
              </div>
              <UserMinus className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Orders per Customer</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {(customerOverview?.avgOrdersPerCustomer || 0).toFixed(1)}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {formatPercentage(customerOverview?.ordersPerCustomerChange || 0)} vs. last period
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Customer Acquisition Cost</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {formatCurrency(customerOverview?.cac || 0)}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  CAC/CLV Ratio: {(customerOverview?.cacClvRatio || 0).toFixed(2)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Insights</CardTitle>
          <CardDescription>Actionable insights and recommendations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline" className="justify-start">
              <Users className="w-4 h-4 mr-2" />
              View High-Value Customers
            </Button>
            <Button variant="outline" className="justify-start">
              <UserMinus className="w-4 h-4 mr-2" />
              Identify At-Risk Customers
            </Button>
            <Button variant="outline" className="justify-start">
              <Target className="w-4 h-4 mr-2" />
              Create Retention Campaign
            </Button>
            <Button variant="outline" className="justify-start">
              <TrendingUp className="w-4 h-4 mr-2" />
              Analyze Customer Behavior
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CustomerAnalyticsDashboard
