import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
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
  Package,
  Clock,
  CheckCircle,
  XCircle,
  Truck,
  AlertTriangle,
  TrendingUp,
  RefreshCw,
  Download,
  Filter
} from 'lucide-react'
import api from '@/lib/api-enhanced'

const OrderManagementDashboard = () => {
  const [timeRange, setTimeRange] = useState('30d')
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Fetch order metrics
  const { data: orderMetrics, isLoading: loadingMetrics, refetch } = useQuery({
    queryKey: ['orderMetrics', timeRange],
    queryFn: () => api.analytics.getOrderMetrics({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch order status distribution
  const { data: statusDistribution, isLoading: loadingStatus } = useQuery({
    queryKey: ['orderStatusDistribution', timeRange],
    queryFn: () => api.analytics.getOrderStatusDistribution({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch order trends
  const { data: orderTrends, isLoading: loadingTrends } = useQuery({
    queryKey: ['orderTrends', timeRange],
    queryFn: () => api.analytics.getOrderTrends({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch fulfillment metrics
  const { data: fulfillmentMetrics, isLoading: loadingFulfillment } = useQuery({
    queryKey: ['fulfillmentMetrics', timeRange],
    queryFn: () => api.analytics.getFulfillmentMetrics({ timeRange }),
    refetchInterval: 60000,
  })

  const handleRefresh = () => {
    refetch()
    setLastUpdated(new Date())
  }

  // Status colors
  const STATUS_COLORS = {
    pending: '#f59e0b',
    processing: '#3b82f6',
    shipped: '#8b5cf6',
    delivered: '#10b981',
    cancelled: '#ef4444',
    returned: '#6b7280',
  }

  // KPI Card Component
  const KPICard = ({ title, value, subtitle, icon: Icon, color, loading }) => {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {loading ? '...' : value}
              </p>
              <p className="mt-1 text-xs text-gray-500">{subtitle}</p>
            </div>
            <div className="ml-4">
              <div className={`p-3 ${color} rounded-lg`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Format time
  const formatTime = (hours) => {
    if (hours < 1) return `${Math.round(hours * 60)}m`
    if (hours < 24) return `${hours.toFixed(1)}h`
    return `${(hours / 24).toFixed(1)}d`
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Order Management</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor order processing and fulfillment performance
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
        </TabsList>
      </Tabs>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Orders"
          value={(orderMetrics?.totalOrders || 0).toLocaleString()}
          subtitle={`${orderMetrics?.orderGrowth || 0}% vs. previous period`}
          icon={Package}
          color="bg-blue-500"
          loading={loadingMetrics}
        />
        <KPICard
          title="Pending Orders"
          value={(orderMetrics?.pendingOrders || 0).toLocaleString()}
          subtitle="Awaiting processing"
          icon={Clock}
          color="bg-orange-500"
          loading={loadingMetrics}
        />
        <KPICard
          title="Avg. Fulfillment Time"
          value={formatTime(orderMetrics?.avgFulfillmentTime || 0)}
          subtitle={`${orderMetrics?.fulfillmentImprovement || 0}% faster`}
          icon={Truck}
          color="bg-purple-500"
          loading={loadingMetrics}
        />
        <KPICard
          title="Order Success Rate"
          value={`${(orderMetrics?.successRate || 0).toFixed(1)}%`}
          subtitle="Delivered successfully"
          icon={CheckCircle}
          color="bg-green-500"
          loading={loadingMetrics}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Order Status Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Order Status Distribution</CardTitle>
            <CardDescription>Current orders by status</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingStatus ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={256}>
                <PieChart>
                  <Pie
                    data={statusDistribution || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {(statusDistribution || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.status] || '#6b7280'} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Fulfillment Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Fulfillment Performance</CardTitle>
            <CardDescription>Average time by stage</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingFulfillment ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <div className="space-y-4">
                {(fulfillmentMetrics?.stages || []).map((stage) => (
                  <div key={stage.name} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">{stage.name}</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {formatTime(stage.avgTime)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${(stage.avgTime / fulfillmentMetrics.maxTime) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Order Trends */}
      <Card>
        <CardHeader>
          <CardTitle>Order Volume Trends</CardTitle>
          <CardDescription>Daily order volume over time</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingTrends ? (
            <div className="h-80 flex items-center justify-center">
              <div className="text-gray-500">Loading chart data...</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={orderTrends || []}>
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
                <Bar dataKey="orders" fill="#3b82f6" name="Total Orders" />
                <Bar dataKey="delivered" fill="#10b981" name="Delivered" />
                <Bar dataKey="cancelled" fill="#ef4444" name="Cancelled" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common order management tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="justify-start">
              <AlertTriangle className="w-4 h-4 mr-2" />
              View Pending Orders ({orderMetrics?.pendingOrders || 0})
            </Button>
            <Button variant="outline" className="justify-start">
              <Clock className="w-4 h-4 mr-2" />
              Process Delayed Orders ({orderMetrics?.delayedOrders || 0})
            </Button>
            <Button variant="outline" className="justify-start">
              <XCircle className="w-4 h-4 mr-2" />
              Review Cancellations ({orderMetrics?.recentCancellations || 0})
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default OrderManagementDashboard
