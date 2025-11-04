import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Download, FileText, Search, Calendar } from 'lucide-react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '@/lib/api-enhanced'

const SalesReports = () => {
  const [dateRange, setDateRange] = useState('month')
  const [searchTerm, setSearchTerm] = useState('')
  const [reportType, setReportType] = useState('summary')

  const { data: salesData, isLoading } = useQuery({
    queryKey: ['sales-reports', dateRange, reportType],
    queryFn: () => api.financial.getSalesReports(dateRange, reportType)
  })

  const { data: productSales } = useQuery({
    queryKey: ['sales-by-product', dateRange],
    queryFn: () => api.financial.getSalesByProduct(dateRange)
  })

  const { data: categorySales } = useQuery({
    queryKey: ['sales-by-category', dateRange],
    queryFn: () => api.financial.getSalesByCategory(dateRange)
  })

  const exportReport = (format) => {
    api.financial.exportSalesReport(dateRange, reportType, format)
      .then(() => toast.success(`Report exported as ${format.toUpperCase()}`))
  }

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sales Reports</h1>
          <p className="text-gray-600">Detailed sales analysis and reporting</p>
        </div>
        <div className="flex items-center space-x-3">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-40">
              <Calendar className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="week">Last 7 Days</SelectItem>
              <SelectItem value="month">Last 30 Days</SelectItem>
              <SelectItem value="quarter">Last Quarter</SelectItem>
              <SelectItem value="year">Last Year</SelectItem>
              <SelectItem value="custom">Custom Range</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={() => exportReport('csv')}>
            <Download className="w-4 h-4 mr-2" />
            CSV
          </Button>
          <Button variant="outline" onClick={() => exportReport('pdf')}>
            <FileText className="w-4 h-4 mr-2" />
            PDF
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Total Sales</p>
            <h3 className="text-2xl font-bold mt-1">${salesData?.total_sales?.toLocaleString() || '0'}</h3>
            <p className="text-sm text-gray-600 mt-1">{salesData?.total_orders || 0} orders</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Average Order Value</p>
            <h3 className="text-2xl font-bold mt-1">${salesData?.avg_order_value || '0'}</h3>
            <p className="text-sm text-gray-600 mt-1">Per transaction</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Units Sold</p>
            <h3 className="text-2xl font-bold mt-1">{salesData?.units_sold?.toLocaleString() || '0'}</h3>
            <p className="text-sm text-gray-600 mt-1">Total items</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Conversion Rate</p>
            <h3 className="text-2xl font-bold mt-1">{salesData?.conversion_rate || '0'}%</h3>
            <p className="text-sm text-gray-600 mt-1">Visitors to buyers</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabbed Reports */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="products">By Product</TabsTrigger>
          <TabsTrigger value="categories">By Category</TabsTrigger>
          <TabsTrigger value="time">By Time</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Sales Trend</CardTitle>
              <CardDescription>Daily sales performance</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={salesData?.daily_sales || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="sales" stroke="#3b82f6" strokeWidth={2} name="Sales ($)" />
                  <Line type="monotone" dataKey="orders" stroke="#10b981" strokeWidth={2} name="Orders" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="products" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Sales by Product</CardTitle>
                  <CardDescription>Top selling products</CardDescription>
                </div>
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input 
                    placeholder="Search products..." 
                    className="pl-10"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={productSales?.slice(0, 10) || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="revenue" fill="#3b82f6" name="Revenue ($)" />
                  </BarChart>
                </ResponsiveContainer>

                <div className="border rounded">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="text-left p-3 text-sm font-medium">Product</th>
                        <th className="text-right p-3 text-sm font-medium">Units Sold</th>
                        <th className="text-right p-3 text-sm font-medium">Revenue</th>
                        <th className="text-right p-3 text-sm font-medium">Avg Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {productSales?.filter(p => p.name.toLowerCase().includes(searchTerm.toLowerCase())).map((product, index) => (
                        <tr key={index} className="border-t">
                          <td className="p-3">{product.name}</td>
                          <td className="p-3 text-right">{product.units_sold}</td>
                          <td className="p-3 text-right font-medium">${product.revenue.toLocaleString()}</td>
                          <td className="p-3 text-right">${product.avg_price}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="categories" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Sales by Category</CardTitle>
              <CardDescription>Revenue distribution across categories</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={categorySales || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={150} />
                  <Tooltip />
                  <Bar dataKey="revenue" fill="#10b981" name="Revenue ($)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="time" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Sales by Time Period</CardTitle>
              <CardDescription>Hourly and daily patterns</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h4 className="font-medium mb-3">Sales by Day of Week</h4>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={salesData?.by_day_of_week || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="sales" fill="#8b5cf6" name="Sales ($)" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div>
                  <h4 className="font-medium mb-3">Sales by Hour</h4>
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={salesData?.by_hour || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="hour" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="sales" stroke="#f59e0b" strokeWidth={2} name="Sales ($)" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default SalesReports
