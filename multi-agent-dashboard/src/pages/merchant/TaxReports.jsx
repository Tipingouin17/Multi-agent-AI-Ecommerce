import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Download, FileText, Calendar } from 'lucide-react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '@/lib/api-enhanced'

const TaxReports = () => {
  const [period, setPeriod] = useState('quarter')
  const [jurisdiction, setJurisdiction] = useState('all')

  const { data: taxData, isLoading } = useQuery({
    queryKey: ['tax-reports', period, jurisdiction],
    queryFn: () => api.financial.getTaxReports(period, jurisdiction)
  })

  const { data: taxLiability } = useQuery({
    queryKey: ['tax-liability', period],
    queryFn: () => api.financial.getTaxLiability(period)
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tax Reports</h1>
          <p className="text-gray-600">Sales tax reporting and compliance</p>
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
            </SelectContent>
          </Select>
          <Select value={jurisdiction} onValueChange={setJurisdiction}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Jurisdictions</SelectItem>
              <SelectItem value="federal">Federal</SelectItem>
              <SelectItem value="state">State</SelectItem>
              <SelectItem value="local">Local</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Total Tax Collected</p>
            <h3 className="text-2xl font-bold mt-1">${taxData?.total_collected?.toLocaleString() || '0'}</h3>
            <p className="text-sm text-gray-600 mt-1">This period</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Tax Liability</p>
            <h3 className="text-2xl font-bold mt-1">${taxLiability?.total?.toLocaleString() || '0'}</h3>
            <p className="text-sm text-gray-600 mt-1">Amount owed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Tax Remitted</p>
            <h3 className="text-2xl font-bold mt-1">${taxData?.remitted?.toLocaleString() || '0'}</h3>
            <p className="text-sm text-gray-600 mt-1">Already paid</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Effective Tax Rate</p>
            <h3 className="text-2xl font-bold mt-1">{taxData?.effective_rate || '0'}%</h3>
            <p className="text-sm text-gray-600 mt-1">Average rate</p>
          </CardContent>
        </Card>
      </div>

      {/* Tax Collection Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Tax Collection Trend</CardTitle>
          <CardDescription>Monthly tax collected over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={taxData?.monthly_trend || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="collected" stroke="#3b82f6" strokeWidth={2} name="Tax Collected ($)" />
              <Line type="monotone" dataKey="remitted" stroke="#10b981" strokeWidth={2} name="Tax Remitted ($)" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Tax by Jurisdiction */}
      <Card>
        <CardHeader>
          <CardTitle>Tax by Jurisdiction</CardTitle>
          <CardDescription>Breakdown of tax collected by location</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={taxData?.by_jurisdiction || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="jurisdiction" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="collected" fill="#8b5cf6" name="Tax Collected ($)" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Detailed Tax Table */}
      <Card>
        <CardHeader>
          <CardTitle>Tax Details by Jurisdiction</CardTitle>
          <CardDescription>Comprehensive tax breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border rounded">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3 text-sm font-medium">Jurisdiction</th>
                  <th className="text-right p-3 text-sm font-medium">Tax Rate</th>
                  <th className="text-right p-3 text-sm font-medium">Taxable Sales</th>
                  <th className="text-right p-3 text-sm font-medium">Tax Collected</th>
                  <th className="text-right p-3 text-sm font-medium">Tax Remitted</th>
                  <th className="text-right p-3 text-sm font-medium">Balance Due</th>
                </tr>
              </thead>
              <tbody>
                {taxData?.details?.map((item, index) => (
                  <tr key={index} className="border-t">
                    <td className="p-3 font-medium">{item.jurisdiction}</td>
                    <td className="p-3 text-right">{item.rate}%</td>
                    <td className="p-3 text-right">${item.taxable_sales.toLocaleString()}</td>
                    <td className="p-3 text-right font-medium">${item.collected.toLocaleString()}</td>
                    <td className="p-3 text-right text-green-600">${item.remitted.toLocaleString()}</td>
                    <td className="p-3 text-right">
                      <span className={`font-bold ${item.balance_due > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        ${item.balance_due.toLocaleString()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-50 border-t-2">
                <tr>
                  <td className="p-3 font-bold">Total</td>
                  <td className="p-3"></td>
                  <td className="p-3 text-right font-bold">${taxData?.total_taxable_sales?.toLocaleString() || '0'}</td>
                  <td className="p-3 text-right font-bold">${taxData?.total_collected?.toLocaleString() || '0'}</td>
                  <td className="p-3 text-right font-bold text-green-600">${taxData?.total_remitted?.toLocaleString() || '0'}</td>
                  <td className="p-3 text-right font-bold text-red-600">${taxData?.total_balance_due?.toLocaleString() || '0'}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Tax Filing Reminders */}
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Tax Filings</CardTitle>
          <CardDescription>Important tax deadlines</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {taxData?.upcoming_filings?.map((filing, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded">
                <div>
                  <p className="font-medium">{filing.jurisdiction} - {filing.period}</p>
                  <p className="text-sm text-gray-600">Due: {new Date(filing.due_date).toLocaleDateString()}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold">${filing.amount.toLocaleString()}</p>
                  <Button size="sm" className="mt-2">
                    <FileText className="w-4 h-4 mr-1" />
                    File Return
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default TaxReports
