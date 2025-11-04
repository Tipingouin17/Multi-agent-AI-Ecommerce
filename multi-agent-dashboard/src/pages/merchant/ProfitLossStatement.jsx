import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Download, TrendingUp, TrendingDown, Calendar } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '@/lib/api-enhanced'

const ProfitLossStatement = () => {
  const [period, setPeriod] = useState('month')
  const [comparison, setComparison] = useState('previous')

  const { data: plData, isLoading } = useQuery({
    queryKey: ['profit-loss', period],
    queryFn: () => api.financial.getProfitLoss(period)
  })

  const { data: comparison Data } = useQuery({
    queryKey: ['profit-loss-comparison', period, comparison],
    queryFn: () => api.financial.getProfitLossComparison(period, comparison)
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  const LineItem = ({ label, amount, isSubtotal, isTotal, change }) => (
    <div className={`flex items-center justify-between p-3 ${isTotal ? 'bg-blue-50 border-2 border-blue-500' : isSubtotal ? 'bg-gray-50' : ''} rounded`}>
      <span className={`${isTotal || isSubtotal ? 'font-bold' : 'text-gray-700'} ${!isSubtotal && !isTotal ? 'ml-4' : ''}`}>
        {label}
      </span>
      <div className="flex items-center space-x-4">
        {change !== undefined && (
          <div className="flex items-center">
            {change >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
            )}
            <span className={`text-sm ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {Math.abs(change)}%
            </span>
          </div>
        )}
        <span className={`${isTotal || isSubtotal ? 'font-bold text-lg' : 'font-medium'} ${amount < 0 ? 'text-red-600' : ''}`}>
          ${Math.abs(amount).toLocaleString()}
        </span>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Profit & Loss Statement</h1>
          <p className="text-gray-600">Comprehensive income statement</p>
        </div>
        <div className="flex items-center space-x-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-40">
              <Calendar className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="month">This Month</SelectItem>
              <SelectItem value="quarter">This Quarter</SelectItem>
              <SelectItem value="year">This Year</SelectItem>
              <SelectItem value="ytd">Year to Date</SelectItem>
            </SelectContent>
          </Select>
          <Select value={comparison} onValueChange={setComparison}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="previous">vs Previous Period</SelectItem>
              <SelectItem value="yoy">vs Year Ago</SelectItem>
              <SelectItem value="budget">vs Budget</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* P&L Statement */}
      <Card>
        <CardHeader>
          <CardTitle>Income Statement</CardTitle>
          <CardDescription>For the period ending {plData?.period_end}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {/* Revenue Section */}
          <div className="space-y-2">
            <h3 className="font-bold text-lg mt-4 mb-2">Revenue</h3>
            <LineItem label="Gross Sales" amount={plData?.gross_sales || 0} change={plData?.gross_sales_change} />
            <LineItem label="Discounts" amount={-(plData?.discounts || 0)} />
            <LineItem label="Returns & Refunds" amount={-(plData?.returns || 0)} />
            <LineItem label="Net Sales" amount={plData?.net_sales || 0} isSubtotal change={plData?.net_sales_change} />
          </div>

          {/* Cost of Goods Sold */}
          <div className="space-y-2">
            <h3 className="font-bold text-lg mt-6 mb-2">Cost of Goods Sold</h3>
            <LineItem label="Product Costs" amount={-(plData?.product_costs || 0)} />
            <LineItem label="Shipping Costs" amount={-(plData?.shipping_costs || 0)} />
            <LineItem label="Payment Processing Fees" amount={-(plData?.payment_fees || 0)} />
            <LineItem label="Total COGS" amount={-(plData?.total_cogs || 0)} isSubtotal />
          </div>

          {/* Gross Profit */}
          <LineItem 
            label="Gross Profit" 
            amount={plData?.gross_profit || 0} 
            isSubtotal 
            change={plData?.gross_profit_change}
          />
          <div className="text-sm text-gray-600 ml-4">
            Gross Margin: {plData?.gross_margin || 0}%
          </div>

          {/* Operating Expenses */}
          <div className="space-y-2">
            <h3 className="font-bold text-lg mt-6 mb-2">Operating Expenses</h3>
            <LineItem label="Marketing & Advertising" amount={-(plData?.marketing_expenses || 0)} />
            <LineItem label="Salaries & Wages" amount={-(plData?.salaries || 0)} />
            <LineItem label="Rent & Utilities" amount={-(plData?.rent_utilities || 0)} />
            <LineItem label="Software & Tools" amount={-(plData?.software_costs || 0)} />
            <LineItem label="Other Expenses" amount={-(plData?.other_expenses || 0)} />
            <LineItem label="Total Operating Expenses" amount={-(plData?.total_operating_expenses || 0)} isSubtotal />
          </div>

          {/* Net Profit */}
          <LineItem 
            label="Net Profit (EBITDA)" 
            amount={plData?.net_profit || 0} 
            isTotal 
            change={plData?.net_profit_change}
          />
          <div className="text-sm text-gray-600 ml-4">
            Net Margin: {plData?.net_margin || 0}%
          </div>
        </CardContent>
      </Card>

      {/* Comparison Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Period Comparison</CardTitle>
          <CardDescription>Compare key metrics across periods</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={comparisonData || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="revenue" fill="#3b82f6" name="Revenue" />
              <Bar dataKey="cogs" fill="#ef4444" name="COGS" />
              <Bar dataKey="profit" fill="#10b981" name="Net Profit" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default ProfitLossStatement
