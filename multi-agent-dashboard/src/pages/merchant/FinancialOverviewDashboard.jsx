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
  DollarSign,
  TrendingUp,
  TrendingDown,
  CreditCard,
  PieChart as PieChartIcon,
  RefreshCw,
  Download,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react'
import api from '@/lib/api-enhanced'

const FinancialOverviewDashboard = () => {
  const [timeRange, setTimeRange] = useState('30d')
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Fetch financial overview
  const { data: financialOverview, isLoading: loadingOverview, refetch } = useQuery({
    queryKey: ['financialOverview', timeRange],
    queryFn: () => api.analytics.getFinancialOverview({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch revenue vs expenses
  const { data: revenueExpenses, isLoading: loadingRevenueExpenses } = useQuery({
    queryKey: ['revenueExpenses', timeRange],
    queryFn: () => api.analytics.getRevenueExpenses({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch profit margins
  const { data: profitMargins, isLoading: loadingMargins } = useQuery({
    queryKey: ['profitMargins', timeRange],
    queryFn: () => api.analytics.getProfitMargins({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch payment methods breakdown
  const { data: paymentMethods, isLoading: loadingPayments } = useQuery({
    queryKey: ['paymentMethodsBreakdown', timeRange],
    queryFn: () => api.analytics.getPaymentMethodsBreakdown({ timeRange }),
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

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Financial Overview</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor your financial performance and profitability
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
          title="Total Revenue"
          value={formatCurrency(financialOverview?.totalRevenue || 0)}
          change={financialOverview?.revenueChange || 0}
          icon={DollarSign}
          loading={loadingOverview}
        />
        <KPICard
          title="Net Profit"
          value={formatCurrency(financialOverview?.netProfit || 0)}
          change={financialOverview?.profitChange || 0}
          icon={TrendingUp}
          loading={loadingOverview}
        />
        <KPICard
          title="Total Expenses"
          value={formatCurrency(financialOverview?.totalExpenses || 0)}
          change={financialOverview?.expensesChange || 0}
          icon={CreditCard}
          loading={loadingOverview}
        />
        <KPICard
          title="Profit Margin"
          value={`${(financialOverview?.profitMargin || 0).toFixed(1)}%`}
          change={financialOverview?.marginChange || 0}
          icon={PieChartIcon}
          loading={loadingOverview}
        />
      </div>

      {/* Revenue vs Expenses */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue vs Expenses</CardTitle>
          <CardDescription>Compare revenue and expenses over time</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingRevenueExpenses ? (
            <div className="h-80 flex items-center justify-center">
              <div className="text-gray-500">Loading chart data...</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={revenueExpenses || []}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
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
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorRevenue)"
                  name="Revenue"
                />
                <Area
                  type="monotone"
                  dataKey="expenses"
                  stroke="#ef4444"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorExpenses)"
                  name="Expenses"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profit Margins Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Profit Margin Trend</CardTitle>
            <CardDescription>Gross and net profit margins over time</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingMargins ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={256}>
                <LineChart data={profitMargins || []}>
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
                    dataKey="grossMargin"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6', r: 4 }}
                    name="Gross Margin"
                  />
                  <Line
                    type="monotone"
                    dataKey="netMargin"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={{ fill: '#10b981', r: 4 }}
                    name="Net Margin"
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Payment Methods Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Payment Methods</CardTitle>
            <CardDescription>Revenue by payment method</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingPayments ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={256}>
                <BarChart data={paymentMethods || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="method" 
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
                  <Bar dataKey="amount" fill="#3b82f6" name="Revenue" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Financial Metrics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Cost of Goods Sold</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {formatCurrency(financialOverview?.cogs || 0)}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {((financialOverview?.cogs / financialOverview?.totalRevenue) * 100 || 0).toFixed(1)}% of revenue
                </p>
              </div>
              <TrendingDown className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Operating Expenses</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {formatCurrency(financialOverview?.operatingExpenses || 0)}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {((financialOverview?.operatingExpenses / financialOverview?.totalRevenue) * 100 || 0).toFixed(1)}% of revenue
                </p>
              </div>
              <CreditCard className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">EBITDA</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {formatCurrency(financialOverview?.ebitda || 0)}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {((financialOverview?.ebitda / financialOverview?.totalRevenue) * 100 || 0).toFixed(1)}% margin
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Financial Reports</CardTitle>
          <CardDescription>Access detailed financial reports</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="justify-start">
              <Download className="w-4 h-4 mr-2" />
              Profit & Loss Statement
            </Button>
            <Button variant="outline" className="justify-start">
              <Download className="w-4 h-4 mr-2" />
              Cash Flow Statement
            </Button>
            <Button variant="outline" className="justify-start">
              <Download className="w-4 h-4 mr-2" />
              Balance Sheet
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default FinancialOverviewDashboard
