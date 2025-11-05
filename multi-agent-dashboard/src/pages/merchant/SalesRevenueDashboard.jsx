import React, { useState, useEffect } from 'react'
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
  TrendingUp,
  TrendingDown,
  DollarSign,
  ShoppingCart,
  Users,
  Package,
  Calendar,
  Download,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react'
import api from '@/lib/api-enhanced'

const SalesRevenueDashboard = () => {
  const [timeRange, setTimeRange] = useState('30d') // 7d, 30d, 90d, 1y
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Fetch sales overview data
  const { data: salesOverview, isLoading: loadingOverview, refetch: refetchOverview } = useQuery({
    queryKey: ['salesOverview', timeRange],
    queryFn: () => api.analytics.getSalesOverview({ timeRange }),
    refetchInterval: 60000, // Refresh every minute
  })

  // Fetch sales trends data
  const { data: salesTrends, isLoading: loadingTrends } = useQuery({
    queryKey: ['salesTrends', timeRange],
    queryFn: () => api.analytics.getSalesTrends({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch revenue breakdown
  const { data: revenueBreakdown, isLoading: loadingBreakdown } = useQuery({
    queryKey: ['revenueBreakdown', timeRange],
    queryFn: () => api.analytics.getRevenueBreakdown({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch top products
  const { data: topProducts, isLoading: loadingProducts } = useQuery({
    queryKey: ['topProducts', timeRange],
    queryFn: () => api.analytics.getTopProducts({ timeRange, limit: 10 }),
    refetchInterval: 60000,
  })

  const handleRefresh = () => {
    refetchOverview()
    setLastUpdated(new Date())
  }

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting sales data...')
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

  // Calculate trend indicator
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

  // Colors for charts
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Sales & Revenue</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track your sales performance and revenue metrics
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
          <Button variant="outline" size="sm" onClick={handleExport}>
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
          title="Total Revenue"
          value={formatCurrency(salesOverview?.totalRevenue || 0)}
          change={salesOverview?.revenueChange || 0}
          icon={DollarSign}
          loading={loadingOverview}
        />
        <KPICard
          title="Total Orders"
          value={(salesOverview?.totalOrders || 0).toLocaleString()}
          change={salesOverview?.ordersChange || 0}
          icon={ShoppingCart}
          loading={loadingOverview}
        />
        <KPICard
          title="Average Order Value"
          value={formatCurrency(salesOverview?.averageOrderValue || 0)}
          change={salesOverview?.aovChange || 0}
          icon={Package}
          loading={loadingOverview}
        />
        <KPICard
          title="Total Customers"
          value={(salesOverview?.totalCustomers || 0).toLocaleString()}
          change={salesOverview?.customersChange || 0}
          icon={Users}
          loading={loadingOverview}
        />
      </div>

      {/* Sales Trends Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Sales Trends</CardTitle>
          <CardDescription>Revenue and orders over time</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingTrends ? (
            <div className="h-80 flex items-center justify-center">
              <div className="text-gray-500">Loading chart data...</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={salesTrends || []}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
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
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                  formatter={(value) => formatCurrency(value)}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorRevenue)"
                  name="Revenue"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue by Category</CardTitle>
            <CardDescription>Revenue distribution across product categories</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingBreakdown ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={256}>
                <PieChart>
                  <Pie
                    data={revenueBreakdown || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {(revenueBreakdown || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Top Products */}
        <Card>
          <CardHeader>
            <CardTitle>Top Products</CardTitle>
            <CardDescription>Best selling products by revenue</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingProducts ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <div className="space-y-4">
                {(topProducts || []).map((product, index) => (
                  <div key={product.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-50 text-blue-600 font-semibold text-sm">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{product.name}</p>
                        <p className="text-sm text-gray-500">{product.units} units sold</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">{formatCurrency(product.revenue)}</p>
                      <p className="text-sm text-gray-500">{formatPercentage(product.growth)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default SalesRevenueDashboard
