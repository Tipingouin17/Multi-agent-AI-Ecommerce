import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  TrendingUp, 
  TrendingDown,
  DollarSign,
  ShoppingCart,
  Eye,
  Package,
  BarChart3,
  Download
} from 'lucide-react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '@/lib/api-enhanced'

/**
 * Product Analytics Page
 * 
 * Comprehensive analytics for product performance:
 * - Sales trends
 * - Conversion rates
 * - Top performers
 * - Inventory turnover
 * - Revenue by product
 * - View/cart/purchase funnel
 */
const ProductAnalytics = () => {
  const [timeRange, setTimeRange] = useState('30d') // 7d, 30d, 90d, 1y
  const [selectedCategory, setSelectedCategory] = useState('all')

  // Fetch analytics data
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['product-analytics', timeRange, selectedCategory],
    queryFn: () => api.analytics.getProductAnalytics({ timeRange, category: selectedCategory })
  })

  // Fetch categories
  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.product.getCategories()
  })

  const handleExportData = () => {
    // Export analytics data to CSV
    const csvData = analytics?.topProducts?.map(p => ({
      name: p.name,
      revenue: p.revenue,
      units_sold: p.units_sold,
      conversion_rate: p.conversion_rate
    }))
    
    // Convert to CSV and download
    const csv = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `product-analytics-${timeRange}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Product Analytics</h1>
          <p className="text-gray-600">Analyze product performance and sales trends</p>
        </div>
        <div className="flex items-center space-x-2">
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {categories.map(cat => (
                <SelectItem key={cat.id} value={cat.id.toString()}>
                  {cat.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="1y">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={handleExportData}>
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
                <p className="text-2xl font-bold">${analytics?.totalRevenue?.toLocaleString() || '0'}</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-500">+12.5%</span>
                </div>
              </div>
              <DollarSign className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Units Sold</p>
                <p className="text-2xl font-bold">{analytics?.unitsSold?.toLocaleString() || '0'}</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-500">+8.3%</span>
                </div>
              </div>
              <Package className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg. Conversion</p>
                <p className="text-2xl font-bold">{analytics?.avgConversion?.toFixed(1) || '0'}%</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingDown className="w-4 h-4 text-red-500" />
                  <span className="text-sm text-red-500">-2.1%</span>
                </div>
              </div>
              <ShoppingCart className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Product Views</p>
                <p className="text-2xl font-bold">{analytics?.totalViews?.toLocaleString() || '0'}</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-500">+15.7%</span>
                </div>
              </div>
              <Eye className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="revenue" className="space-y-6">
        <TabsList>
          <TabsTrigger value="revenue">Revenue Trends</TabsTrigger>
          <TabsTrigger value="top-products">Top Products</TabsTrigger>
          <TabsTrigger value="category">By Category</TabsTrigger>
          <TabsTrigger value="funnel">Conversion Funnel</TabsTrigger>
        </TabsList>

        {/* Revenue Trends */}
        <TabsContent value="revenue">
          <Card>
            <CardHeader>
              <CardTitle>Revenue Over Time</CardTitle>
              <CardDescription>Daily revenue for the selected period</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={analytics?.revenueTimeSeries || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} name="Revenue ($)" />
                  <Line type="monotone" dataKey="units" stroke="#10b981" strokeWidth={2} name="Units Sold" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Top Products */}
        <TabsContent value="top-products">
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Products</CardTitle>
              <CardDescription>Best sellers by revenue</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics?.topProducts?.slice(0, 10).map((product, index) => (
                  <div key={product.id} className="flex items-center space-x-4">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center font-bold text-blue-600">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{product.name}</p>
                      <p className="text-sm text-gray-600">{product.units_sold} units sold</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold">${product.revenue.toLocaleString()}</p>
                      <Badge variant={product.trend === 'up' ? 'default' : 'secondary'}>
                        {product.conversion_rate}% conversion
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* By Category */}
        <TabsContent value="category">
          <div className="grid grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Revenue by Category</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={analytics?.categoryRevenue || []}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {analytics?.categoryRevenue?.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Category Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analytics?.categoryRevenue || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" name="Revenue ($)" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Conversion Funnel */}
        <TabsContent value="funnel">
          <Card>
            <CardHeader>
              <CardTitle>Product Conversion Funnel</CardTitle>
              <CardDescription>Track customer journey from view to purchase</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="relative">
                  <div className="flex items-center space-x-4">
                    <div className="w-full bg-blue-100 h-16 flex items-center justify-between px-6 rounded">
                      <div>
                        <p className="font-medium">Product Views</p>
                        <p className="text-2xl font-bold">{analytics?.funnel?.views?.toLocaleString() || '0'}</p>
                      </div>
                      <Badge>100%</Badge>
                    </div>
                  </div>
                </div>

                <div className="relative">
                  <div className="flex items-center space-x-4">
                    <div className="w-3/4 bg-green-100 h-16 flex items-center justify-between px-6 rounded">
                      <div>
                        <p className="font-medium">Added to Cart</p>
                        <p className="text-2xl font-bold">{analytics?.funnel?.addedToCart?.toLocaleString() || '0'}</p>
                      </div>
                      <Badge>{((analytics?.funnel?.addedToCart / analytics?.funnel?.views) * 100).toFixed(1)}%</Badge>
                    </div>
                  </div>
                </div>

                <div className="relative">
                  <div className="flex items-center space-x-4">
                    <div className="w-1/2 bg-orange-100 h-16 flex items-center justify-between px-6 rounded">
                      <div>
                        <p className="font-medium">Initiated Checkout</p>
                        <p className="text-2xl font-bold">{analytics?.funnel?.checkout?.toLocaleString() || '0'}</p>
                      </div>
                      <Badge>{((analytics?.funnel?.checkout / analytics?.funnel?.views) * 100).toFixed(1)}%</Badge>
                    </div>
                  </div>
                </div>

                <div className="relative">
                  <div className="flex items-center space-x-4">
                    <div className="w-1/3 bg-purple-100 h-16 flex items-center justify-between px-6 rounded">
                      <div>
                        <p className="font-medium">Completed Purchase</p>
                        <p className="text-2xl font-bold">{analytics?.funnel?.purchased?.toLocaleString() || '0'}</p>
                      </div>
                      <Badge>{((analytics?.funnel?.purchased / analytics?.funnel?.views) * 100).toFixed(1)}%</Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default ProductAnalytics
