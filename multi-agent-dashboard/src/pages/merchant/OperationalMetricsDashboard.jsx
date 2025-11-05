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
  Clock,
  Package,
  Truck,
  RefreshCw,
  Download,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react'
import api from '@/lib/api-enhanced'

const OperationalMetricsDashboard = () => {
  const [timeRange, setTimeRange] = useState('30d')
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Fetch operational overview
  const { data: operationalOverview, isLoading: loadingOverview, refetch } = useQuery({
    queryKey: ['operationalOverview', timeRange],
    queryFn: () => api.analytics.getOperationalOverview({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch fulfillment metrics
  const { data: fulfillment, isLoading: loadingFulfillment } = useQuery({
    queryKey: ['fulfillmentMetrics', timeRange],
    queryFn: () => api.analytics.getFulfillmentMetrics({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch shipping performance
  const { data: shipping, isLoading: loadingShipping } = useQuery({
    queryKey: ['shippingPerformance', timeRange],
    queryFn: () => api.analytics.getShippingPerformance({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch return metrics
  const { data: returns, isLoading: loadingReturns } = useQuery({
    queryKey: ['returnMetrics', timeRange],
    queryFn: () => api.analytics.getReturnMetrics({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch warehouse efficiency
  const { data: warehouse, isLoading: loadingWarehouse } = useQuery({
    queryKey: ['warehouseEfficiency', timeRange],
    queryFn: () => api.analytics.getWarehouseEfficiency({ timeRange }),
    refetchInterval: 60000,
  })

  const handleRefresh = () => {
    refetch()
    setLastUpdated(new Date())
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
  const KPICard = ({ title, value, change, icon: Icon, loading, unit = '' }) => {
    const trend = getTrendIndicator(change)
    
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <div className="mt-2 flex items-baseline gap-2">
                <p className="text-3xl font-bold text-gray-900">
                  {loading ? '...' : `${value}${unit}`}
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
              <div className="p-3 bg-indigo-50 rounded-lg">
                <Icon className="w-6 h-6 text-indigo-600" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Operational Metrics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor fulfillment, shipping, and warehouse performance
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
          title="Avg Fulfillment Time"
          value={(operationalOverview?.avgFulfillmentTime || 0).toFixed(1)}
          change={operationalOverview?.fulfillmentTimeChange || 0}
          icon={Clock}
          loading={loadingOverview}
          unit="h"
        />
        <KPICard
          title="On-Time Delivery Rate"
          value={(operationalOverview?.onTimeDeliveryRate || 0).toFixed(1)}
          change={operationalOverview?.deliveryRateChange || 0}
          icon={Truck}
          loading={loadingOverview}
          unit="%"
        />
        <KPICard
          title="Return Rate"
          value={(operationalOverview?.returnRate || 0).toFixed(1)}
          change={operationalOverview?.returnRateChange || 0}
          icon={Package}
          loading={loadingOverview}
          unit="%"
        />
        <KPICard
          title="Warehouse Efficiency"
          value={(operationalOverview?.warehouseEfficiency || 0).toFixed(0)}
          change={operationalOverview?.efficiencyChange || 0}
          icon={TrendingUp}
          loading={loadingOverview}
          unit="%"
        />
      </div>

      {/* Fulfillment Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Fulfillment Performance</CardTitle>
          <CardDescription>Order processing and fulfillment metrics over time</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingFulfillment ? (
            <div className="h-80 flex items-center justify-center">
              <div className="text-gray-500">Loading chart data...</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={fulfillment || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="date" 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `${value}h`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                  formatter={(value) => `${value.toFixed(1)}h`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avgFulfillmentTime"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ fill: '#6366f1', r: 4 }}
                  name="Avg Fulfillment Time"
                />
                <Line
                  type="monotone"
                  dataKey="targetTime"
                  stroke="#94a3b8"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Target Time"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Shipping Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Shipping Performance</CardTitle>
            <CardDescription>Delivery metrics by carrier</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingShipping ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <div className="space-y-4">
                {(shipping || []).map((carrier) => (
                  <div key={carrier.name} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Truck className="w-5 h-5 text-indigo-600" />
                        <h3 className="font-semibold text-gray-900">{carrier.name}</h3>
                      </div>
                      <Badge variant={carrier.onTimeRate >= 95 ? 'default' : carrier.onTimeRate >= 85 ? 'secondary' : 'destructive'}>
                        {carrier.onTimeRate.toFixed(1)}% On-Time
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Shipments</p>
                        <p className="font-semibold text-gray-900">{carrier.shipments.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Avg Transit</p>
                        <p className="font-semibold text-gray-900">{carrier.avgTransitTime.toFixed(1)} days</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Issues</p>
                        <p className={`font-semibold ${carrier.issues === 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {carrier.issues}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Return Analysis */}
        <Card>
          <CardHeader>
            <CardTitle>Return Analysis</CardTitle>
            <CardDescription>Return reasons and trends</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingReturns ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={256}>
                <BarChart data={returns || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    type="number"
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                  />
                  <YAxis 
                    type="category"
                    dataKey="reason"
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                    width={120}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="count" fill="#ef4444" name="Returns" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Warehouse Efficiency */}
      <Card>
        <CardHeader>
          <CardTitle>Warehouse Efficiency</CardTitle>
          <CardDescription>Warehouse operations and productivity metrics</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingWarehouse ? (
            <div className="h-64 flex items-center justify-center">
              <div className="text-gray-500">Loading data...</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {(warehouse || []).map((wh) => (
                <Card key={wh.id} className="border-2">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">{wh.name}</h3>
                      <Badge variant={wh.efficiency >= 90 ? 'default' : wh.efficiency >= 75 ? 'secondary' : 'destructive'}>
                        {wh.efficiency}%
                      </Badge>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Orders Processed</span>
                        <span className="font-medium">{wh.ordersProcessed.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg Pick Time</span>
                        <span className="font-medium">{wh.avgPickTime.toFixed(1)} min</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Accuracy Rate</span>
                        <span className={`font-medium ${wh.accuracyRate >= 99 ? 'text-green-600' : 'text-yellow-600'}`}>
                          {wh.accuracyRate.toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Utilization</span>
                        <span className="font-medium">{wh.utilization.toFixed(0)}%</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Order Status Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Order Status Distribution</CardTitle>
          <CardDescription>Current order pipeline</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">Pending</span>
              </div>
              <p className="text-2xl font-bold text-blue-900">
                {operationalOverview?.orderStatus?.pending || 0}
              </p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="flex items-center gap-2 mb-2">
                <Package className="w-5 h-5 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-900">Processing</span>
              </div>
              <p className="text-2xl font-bold text-yellow-900">
                {operationalOverview?.orderStatus?.processing || 0}
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <Truck className="w-5 h-5 text-purple-600" />
                <span className="text-sm font-medium text-purple-900">Shipped</span>
              </div>
              <p className="text-2xl font-bold text-purple-900">
                {operationalOverview?.orderStatus?.shipped || 0}
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-green-900">Delivered</span>
              </div>
              <p className="text-2xl font-bold text-green-900">
                {operationalOverview?.orderStatus?.delivered || 0}
              </p>
            </div>
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center gap-2 mb-2">
                <XCircle className="w-5 h-5 text-red-600" />
                <span className="text-sm font-medium text-red-900">Issues</span>
              </div>
              <p className="text-2xl font-bold text-red-900">
                {operationalOverview?.orderStatus?.issues || 0}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Alerts</CardTitle>
          <CardDescription>Issues requiring attention</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {(operationalOverview?.alerts || []).map((alert, index) => (
              <div 
                key={index} 
                className={`p-4 rounded-lg border ${
                  alert.severity === 'high' ? 'bg-red-50 border-red-200' :
                  alert.severity === 'medium' ? 'bg-yellow-50 border-yellow-200' :
                  'bg-blue-50 border-blue-200'
                }`}
              >
                <div className="flex items-start gap-3">
                  <AlertTriangle className={`w-5 h-5 mt-0.5 ${
                    alert.severity === 'high' ? 'text-red-600' :
                    alert.severity === 'medium' ? 'text-yellow-600' :
                    'text-blue-600'
                  }`} />
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900">{alert.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                  </div>
                  <Badge variant={alert.severity === 'high' ? 'destructive' : 'secondary'}>
                    {alert.severity}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Operational Actions</CardTitle>
          <CardDescription>Quick access to common operations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline" className="justify-start">
              <Package className="w-4 h-4 mr-2" />
              Process Pending Orders
            </Button>
            <Button variant="outline" className="justify-start">
              <Truck className="w-4 h-4 mr-2" />
              Schedule Shipments
            </Button>
            <Button variant="outline" className="justify-start">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Review Issues
            </Button>
            <Button variant="outline" className="justify-start">
              <TrendingUp className="w-4 h-4 mr-2" />
              Optimize Warehouse
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default OperationalMetricsDashboard
