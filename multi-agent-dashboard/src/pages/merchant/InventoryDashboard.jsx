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
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts'
import {
  Package,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Warehouse,
  RefreshCw,
  Download,
  AlertCircle,
  CheckCircle2
} from 'lucide-react'
import api from '@/lib/api-enhanced'

const InventoryDashboard = () => {
  const [timeRange, setTimeRange] = useState('30d')
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Fetch inventory overview
  const { data: inventoryOverview, isLoading: loadingOverview, refetch } = useQuery({
    queryKey: ['inventoryOverview'],
    queryFn: () => api.analytics.getInventoryOverview(),
    refetchInterval: 60000,
  })

  // Fetch low stock items
  const { data: lowStockItems, isLoading: loadingLowStock } = useQuery({
    queryKey: ['lowStockItems'],
    queryFn: () => api.analytics.getLowStockItems({ limit: 10 }),
    refetchInterval: 60000,
  })

  // Fetch inventory turnover
  const { data: inventoryTurnover, isLoading: loadingTurnover } = useQuery({
    queryKey: ['inventoryTurnover', timeRange],
    queryFn: () => api.analytics.getInventoryTurnover({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch warehouse distribution
  const { data: warehouseDistribution, isLoading: loadingWarehouse } = useQuery({
    queryKey: ['warehouseDistribution'],
    queryFn: () => api.analytics.getWarehouseDistribution(),
    refetchInterval: 60000,
  })

  const handleRefresh = () => {
    refetch()
    setLastUpdated(new Date())
  }

  // KPI Card Component
  const KPICard = ({ title, value, subtitle, icon: Icon, color, alert, loading }) => {
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
              {alert && (
                <div className="mt-2">
                  <Badge variant="destructive" className="text-xs">
                    <AlertTriangle className="w-3 h-3 mr-1" />
                    {alert}
                  </Badge>
                </div>
              )}
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

  // Calculate stock status color
  const getStockStatusColor = (stockLevel) => {
    if (stockLevel < 20) return '#ef4444' // red
    if (stockLevel < 50) return '#f59e0b' // orange
    return '#10b981' // green
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inventory Management</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor stock levels and inventory performance
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
          title="Total SKUs"
          value={(inventoryOverview?.totalSKUs || 0).toLocaleString()}
          subtitle={`${inventoryOverview?.activeSKUs || 0} active`}
          icon={Package}
          color="bg-blue-500"
          loading={loadingOverview}
        />
        <KPICard
          title="Total Stock Value"
          value={`$${((inventoryOverview?.totalValue || 0) / 1000).toFixed(0)}k`}
          subtitle={`${inventoryOverview?.valueChange || 0}% vs. last month`}
          icon={TrendingUp}
          color="bg-green-500"
          loading={loadingOverview}
        />
        <KPICard
          title="Low Stock Items"
          value={(inventoryOverview?.lowStockCount || 0).toLocaleString()}
          subtitle="Requires attention"
          icon={AlertTriangle}
          color="bg-orange-500"
          alert={inventoryOverview?.lowStockCount > 0 ? "Action needed" : null}
          loading={loadingOverview}
        />
        <KPICard
          title="Out of Stock"
          value={(inventoryOverview?.outOfStockCount || 0).toLocaleString()}
          subtitle="Products unavailable"
          icon={AlertCircle}
          color="bg-red-500"
          alert={inventoryOverview?.outOfStockCount > 0 ? "Critical" : null}
          loading={loadingOverview}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Low Stock Alert */}
        <Card>
          <CardHeader>
            <CardTitle>Low Stock Alerts</CardTitle>
            <CardDescription>Products requiring restock</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingLowStock ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <div className="space-y-3">
                {(lowStockItems || []).map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{item.name}</p>
                      <p className="text-sm text-gray-500">SKU: {item.sku}</p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2">
                        <div className="text-right">
                          <p className="font-semibold text-gray-900">{item.currentStock} units</p>
                          <p className="text-xs text-gray-500">Min: {item.minStock}</p>
                        </div>
                        <div 
                          className="w-2 h-12 rounded-full"
                          style={{ backgroundColor: getStockStatusColor((item.currentStock / item.minStock) * 100) }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
                {(!lowStockItems || lowStockItems.length === 0) && (
                  <div className="text-center py-8 text-gray-500">
                    <CheckCircle2 className="w-12 h-12 mx-auto mb-2 text-green-500" />
                    <p>All products are well stocked!</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Warehouse Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Warehouse Distribution</CardTitle>
            <CardDescription>Stock across warehouses</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingWarehouse ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={256}>
                <BarChart data={warehouseDistribution || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <YAxis type="category" dataKey="name" stroke="#6b7280" style={{ fontSize: '12px' }} width={100} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="stock" fill="#3b82f6" name="Stock Units">
                    {(warehouseDistribution || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.utilization > 90 ? '#ef4444' : '#3b82f6'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Inventory Turnover */}
      <Card>
        <CardHeader>
          <CardTitle>Inventory Turnover Rate</CardTitle>
          <CardDescription>How quickly inventory is sold and replaced</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingTurnover ? (
            <div className="h-80 flex items-center justify-center">
              <div className="text-gray-500">Loading chart data...</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={inventoryTurnover || []}>
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
                <Line
                  type="monotone"
                  dataKey="turnoverRate"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  name="Turnover Rate"
                />
                <Line
                  type="monotone"
                  dataKey="daysToSell"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: '#10b981', r: 4 }}
                  name="Days to Sell"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Inventory Health Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg. Turnover Rate</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {(inventoryOverview?.avgTurnoverRate || 0).toFixed(1)}x
                </p>
                <p className="mt-1 text-xs text-gray-500">per year</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg. Days in Stock</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {(inventoryOverview?.avgDaysInStock || 0).toFixed(0)}
                </p>
                <p className="mt-1 text-xs text-gray-500">days</p>
              </div>
              <Package className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Dead Stock</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {(inventoryOverview?.deadStockCount || 0).toLocaleString()}
                </p>
                <p className="mt-1 text-xs text-gray-500">items (90+ days)</p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common inventory management tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="justify-start">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Restock Low Items ({inventoryOverview?.lowStockCount || 0})
            </Button>
            <Button variant="outline" className="justify-start">
              <Package className="w-4 h-4 mr-2" />
              Review Dead Stock ({inventoryOverview?.deadStockCount || 0})
            </Button>
            <Button variant="outline" className="justify-start">
              <Warehouse className="w-4 h-4 mr-2" />
              Optimize Warehouse
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default InventoryDashboard
