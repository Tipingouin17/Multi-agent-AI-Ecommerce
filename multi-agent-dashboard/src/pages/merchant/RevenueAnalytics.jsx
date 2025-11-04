import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { LineChart, Line, BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, DollarSign, Users, ShoppingCart } from 'lucide-react'
import api from '@/lib/api-enhanced'

const RevenueAnalytics = () => {
  const [period, setPeriod] = useState('year')

  const { data: analytics, isLoading } = useQuery({
    queryKey: ['revenue-analytics', period],
    queryFn: () => api.financial.getRevenueAnalytics(period)
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Revenue Analytics</h1>
          <p className="text-gray-600">Deep insights into revenue sources and trends</p>
        </div>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="month">Last Month</SelectItem>
            <SelectItem value="quarter">Last Quarter</SelectItem>
            <SelectItem value="year">Last Year</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Revenue</p>
                <h3 className="text-2xl font-bold mt-1">${analytics?.total_revenue?.toLocaleString() || '0'}</h3>
              </div>
              <DollarSign className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Growth Rate</p>
                <h3 className="text-2xl font-bold mt-1">{analytics?.growth_rate || '0'}%</h3>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Customer LTV</p>
                <h3 className="text-2xl font-bold mt-1">${analytics?.avg_ltv || '0'}</h3>
              </div>
              <Users className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Repeat Rate</p>
                <h3 className="text-2xl font-bold mt-1">{analytics?.repeat_rate || '0'}%</h3>
              </div>
              <ShoppingCart className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Trend & Forecast</CardTitle>
          <CardDescription>Historical revenue with projected growth</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={analytics?.revenue_trend || []}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="actual" stroke="#3b82f6" fillOpacity={1} fill="url(#colorRevenue)" name="Actual Revenue" />
              <Area type="monotone" dataKey="forecast" stroke="#10b981" strokeDasharray="5 5" fill="none" name="Forecast" />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-6">
        {/* Revenue by Channel */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue by Channel</CardTitle>
            <CardDescription>Distribution across sales channels</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analytics?.by_channel || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.percentage}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {(analytics?.by_channel || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Revenue by Product Line */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue by Product Line</CardTitle>
            <CardDescription>Top performing product categories</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics?.by_product_line || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={120} />
                <Tooltip />
                <Bar dataKey="revenue" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Geographic Revenue */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue by Region</CardTitle>
          <CardDescription>Geographic distribution of sales</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics?.by_region || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="revenue" fill="#8b5cf6" name="Revenue ($)" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Customer Cohort Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Cohort Revenue</CardTitle>
          <CardDescription>Revenue contribution by customer acquisition cohort</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analytics?.cohort_revenue || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="cohort" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="month1" stroke="#3b82f6" name="Month 1" />
              <Line type="monotone" dataKey="month3" stroke="#10b981" name="Month 3" />
              <Line type="monotone" dataKey="month6" stroke="#f59e0b" name="Month 6" />
              <Line type="monotone" dataKey="month12" stroke="#ef4444" name="Month 12" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default RevenueAnalytics
