import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  PieChart,
  BarChart3,
  Download,
  Calendar
} from 'lucide-react'
import { LineChart, Line, BarChart, Bar, PieChart as RePieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '@/lib/api-enhanced'

const FinancialDashboard = () => {
  const [period, setPeriod] = useState('month')

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['financial-dashboard', period],
    queryFn: () => api.financial.getDashboard(period)
  })

  const { data: revenueData } = useQuery({
    queryKey: ['financial-revenue', period],
    queryFn: () => api.financial.getRevenue(period)
  })

  const { data: profitLoss } = useQuery({
    queryKey: ['financial-profit-loss', period],
    queryFn: () => api.financial.getProfitLoss(period)
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Financial Dashboard</h1>
          <p className="text-gray-600">Comprehensive financial overview and insights</p>
        </div>
        <div className="flex items-center space-x-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-40">
              <Calendar className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="week">This Week</SelectItem>
              <SelectItem value="month">This Month</SelectItem>
              <SelectItem value="quarter">This Quarter</SelectItem>
              <SelectItem value="year">This Year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Revenue</p>
                <h3 className="text-2xl font-bold mt-1">${metrics?.revenue?.toLocaleString() || '0'}</h3>
                <div className="flex items-center mt-2">
                  {metrics?.revenue_change >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                  )}
                  <span className={`text-sm ${metrics?.revenue_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {Math.abs(metrics?.revenue_change || 0)}% vs last period
                  </span>
                </div>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Net Profit</p>
                <h3 className="text-2xl font-bold mt-1">${metrics?.profit?.toLocaleString() || '0'}</h3>
                <div className="flex items-center mt-2">
                  {metrics?.profit_change >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                  )}
                  <span className={`text-sm ${metrics?.profit_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {Math.abs(metrics?.profit_change || 0)}% vs last period
                  </span>
                </div>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Profit Margin</p>
                <h3 className="text-2xl font-bold mt-1">{metrics?.profit_margin || '0'}%</h3>
                <div className="flex items-center mt-2">
                  <span className="text-sm text-gray-600">
                    Target: 30%
                  </span>
                </div>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                <PieChart className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Expenses</p>
                <h3 className="text-2xl font-bold mt-1">${metrics?.expenses?.toLocaleString() || '0'}</h3>
                <div className="flex items-center mt-2">
                  <span className="text-sm text-gray-600">
                    {metrics?.expense_ratio || '0'}% of revenue
                  </span>
                </div>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Trend</CardTitle>
          <CardDescription>Daily revenue over the selected period</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={revenueData?.daily || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} name="Revenue" />
              <Line type="monotone" dataKey="profit" stroke="#10b981" strokeWidth={2} name="Profit" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-6">
        {/* Revenue by Channel */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue by Channel</CardTitle>
            <CardDescription>Distribution of revenue sources</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <RePieChart>
                <Pie
                  data={metrics?.revenue_by_channel || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: $${entry.value.toLocaleString()}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {(metrics?.revenue_by_channel || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </RePieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Top Products */}
        <Card>
          <CardHeader>
            <CardTitle>Top Revenue Products</CardTitle>
            <CardDescription>Best performing products by revenue</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={metrics?.top_products || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="revenue" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Profit & Loss Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Profit & Loss Summary</CardTitle>
          <CardDescription>Income statement for the selected period</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <span className="font-medium">Gross Revenue</span>
              <span className="font-bold text-lg">${profitLoss?.gross_revenue?.toLocaleString() || '0'}</span>
            </div>
            <div className="flex items-center justify-between p-3">
              <span className="text-gray-600">- Returns & Refunds</span>
              <span className="text-red-600">-${profitLoss?.returns?.toLocaleString() || '0'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded">
              <span className="font-medium">Net Revenue</span>
              <span className="font-bold">${profitLoss?.net_revenue?.toLocaleString() || '0'}</span>
            </div>
            <div className="flex items-center justify-between p-3">
              <span className="text-gray-600">- Cost of Goods Sold</span>
              <span className="text-red-600">-${profitLoss?.cogs?.toLocaleString() || '0'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded">
              <span className="font-medium">Gross Profit</span>
              <span className="font-bold text-green-600">${profitLoss?.gross_profit?.toLocaleString() || '0'}</span>
            </div>
            <div className="flex items-center justify-between p-3">
              <span className="text-gray-600">- Operating Expenses</span>
              <span className="text-red-600">-${profitLoss?.operating_expenses?.toLocaleString() || '0'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-100 rounded border-2 border-green-500">
              <span className="font-bold text-lg">Net Profit</span>
              <span className="font-bold text-lg text-green-600">${profitLoss?.net_profit?.toLocaleString() || '0'}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default FinancialDashboard
