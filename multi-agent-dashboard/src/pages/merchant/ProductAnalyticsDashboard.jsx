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
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts'
import {
  Package,
  TrendingUp,
  TrendingDown,
  ShoppingCart,
  Eye,
  RefreshCw,
  Download,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  Star
} from 'lucide-react'
import api from '@/lib/api-enhanced'

const ProductAnalyticsDashboard = () => {
  const [timeRange, setTimeRange] = useState('30d')
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Fetch product overview
  const { data: productOverview, isLoading: loadingOverview, refetch } = useQuery({
    queryKey: ['productOverview', timeRange],
    queryFn: () => api.analytics.getProductOverview({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch product performance
  const { data: performance, isLoading: loadingPerformance } = useQuery({
    queryKey: ['productPerformance', timeRange],
    queryFn: () => api.analytics.getProductPerformance({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch category performance
  const { data: categoryPerf, isLoading: loadingCategory } = useQuery({
    queryKey: ['categoryPerformance', timeRange],
    queryFn: () => api.analytics.getCategoryPerformance({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch conversion funnel
  const { data: conversionFunnel, isLoading: loadingFunnel } = useQuery({
    queryKey: ['conversionFunnel', timeRange],
    queryFn: () => api.analytics.getConversionFunnel({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch product lifecycle
  const { data: lifecycle, isLoading: loadingLifecycle } = useQuery({
    queryKey: ['productLifecycle'],
    queryFn: () => api.analytics.getProductLifecycle(),
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

  // Get lifecycle stage color
  const getLifecycleColor = (stage) => {
    const colors = {
      'Introduction': '#3b82f6',
      'Growth': '#10b981',
      'Maturity': '#f59e0b',
      'Decline': '#ef4444'
    }
    return colors[stage] || '#6b7280'
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Product Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track product performance and optimize your catalog
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
          title="Total Products"
          value={productOverview?.totalProducts?.toLocaleString() || '0'}
          change={productOverview?.productGrowth || 0}
          icon={Package}
          loading={loadingOverview}
        />
        <KPICard
          title="Product Views"
          value={productOverview?.totalViews?.toLocaleString() || '0'}
          change={productOverview?.viewsGrowth || 0}
          icon={Eye}
          loading={loadingOverview}
        />
        <KPICard
          title="Conversion Rate"
          value={`${(productOverview?.conversionRate || 0).toFixed(1)}%`}
          change={productOverview?.conversionChange || 0}
          icon={ShoppingCart}
          loading={loadingOverview}
        />
        <KPICard
          title="Avg Product Rating"
          value={(productOverview?.avgRating || 0).toFixed(1)}
          change={productOverview?.ratingChange || 0}
          icon={Star}
          loading={loadingOverview}
        />
      </div>

      {/* Product Performance Matrix */}
      <Card>
        <CardHeader>
          <CardTitle>Product Performance Matrix</CardTitle>
          <CardDescription>Revenue vs. Units Sold (bubble size = profit margin)</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingPerformance ? (
            <div className="h-80 flex items-center justify-center">
              <div className="text-gray-500">Loading chart data...</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  type="number" 
                  dataKey="units" 
                  name="Units Sold" 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  type="number" 
                  dataKey="revenue" 
                  name="Revenue" 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <ZAxis type="number" dataKey="margin" range={[50, 400]} name="Margin" />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                  formatter={(value, name) => {
                    if (name === 'Revenue') return formatCurrency(value)
                    if (name === 'Margin') return `${value}%`
                    return value
                  }}
                />
                <Legend />
                <Scatter 
                  name="Products" 
                  data={performance || []} 
                  fill="#3b82f6"
                />
              </ScatterChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Category Performance</CardTitle>
            <CardDescription>Revenue by product category</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingCategory ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={256}>
                <BarChart data={categoryPerf || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    type="number"
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                  />
                  <YAxis 
                    type="category"
                    dataKey="category"
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                    width={100}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }}
                    formatter={(value) => formatCurrency(value)}
                  />
                  <Bar dataKey="revenue" fill="#3b82f6" name="Revenue" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Conversion Funnel */}
        <Card>
          <CardHeader>
            <CardTitle>Conversion Funnel</CardTitle>
            <CardDescription>From product view to purchase</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingFunnel ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <div className="space-y-3">
                {(conversionFunnel || []).map((stage, index) => {
                  const percentage = (stage.count / (conversionFunnel[0]?.count || 1)) * 100
                  return (
                    <div key={stage.stage} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">{stage.stage}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-gray-900">
                            {stage.count.toLocaleString()}
                          </span>
                          <span className="text-xs text-gray-500">
                            ({percentage.toFixed(1)}%)
                          </span>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div 
                          className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      {index < (conversionFunnel || []).length - 1 && (
                        <div className="flex items-center justify-end text-xs text-gray-500">
                          Drop-off: {((1 - (conversionFunnel[index + 1]?.count || 0) / stage.count) * 100).toFixed(1)}%
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Product Lifecycle */}
      <Card>
        <CardHeader>
          <CardTitle>Product Lifecycle Analysis</CardTitle>
          <CardDescription>Products by lifecycle stage</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingLifecycle ? (
            <div className="h-64 flex items-center justify-center">
              <div className="text-gray-500">Loading data...</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {(lifecycle || []).map((stage) => (
                <Card key={stage.stage} className="border-2" style={{ borderColor: getLifecycleColor(stage.stage) }}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold" style={{ color: getLifecycleColor(stage.stage) }}>
                        {stage.stage}
                      </h3>
                      <Badge variant="outline" style={{ borderColor: getLifecycleColor(stage.stage), color: getLifecycleColor(stage.stage) }}>
                        {stage.count}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Revenue</span>
                        <span className="font-medium">{formatCurrency(stage.revenue)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg Age</span>
                        <span className="font-medium">{stage.avgAge} days</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Growth</span>
                        <span className={`font-medium ${stage.growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatPercentage(stage.growth)}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top & Bottom Performers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top Performers</CardTitle>
            <CardDescription>Best selling products this period</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(productOverview?.topProducts || []).map((product, index) => (
                <div key={product.id} className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-8 h-8 bg-green-600 text-white rounded-full font-bold text-sm">
                      {index + 1}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{product.name}</p>
                      <p className="text-xs text-gray-500">{product.category}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-gray-900">{formatCurrency(product.revenue)}</p>
                    <p className="text-xs text-green-600">{product.units} units</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Needs Attention</CardTitle>
            <CardDescription>Products requiring action</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(productOverview?.lowPerformers || []).map((product, index) => (
                <div key={product.id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{product.name}</p>
                      <p className="text-xs text-gray-500">{product.issue}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-red-600">{formatPercentage(product.decline)}</p>
                    <p className="text-xs text-gray-500">vs. last period</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Time to First Sale</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {productOverview?.avgTimeToFirstSale || 0} days
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  For new products
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Out of Stock Rate</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {(productOverview?.outOfStockRate || 0).toFixed(1)}%
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {productOverview?.outOfStockCount || 0} products affected
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Return Rate</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {(productOverview?.returnRate || 0).toFixed(1)}%
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {formatPercentage(productOverview?.returnRateChange || 0)} vs. last period
                </p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Product Optimization</CardTitle>
          <CardDescription>Recommended actions to improve performance</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline" className="justify-start">
              <Package className="w-4 h-4 mr-2" />
              Review Low Performers
            </Button>
            <Button variant="outline" className="justify-start">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Restock Out of Stock Items
            </Button>
            <Button variant="outline" className="justify-start">
              <TrendingUp className="w-4 h-4 mr-2" />
              Optimize Product Descriptions
            </Button>
            <Button variant="outline" className="justify-start">
              <Star className="w-4 h-4 mr-2" />
              Improve Low-Rated Products
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ProductAnalyticsDashboard
