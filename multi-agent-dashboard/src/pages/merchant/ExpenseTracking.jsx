import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Plus, Trash2, Edit, Download, Receipt } from 'lucide-react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '@/lib/api-enhanced'

const ExpenseTracking = () => {
  const queryClient = useQueryClient()
  const [isAdding, setIsAdding] = useState(false)
  const [newExpense, setNewExpense] = useState({
    category: '',
    amount: '',
    vendor: '',
    description: '',
    date: new Date().toISOString().split('T')[0]
  })

  const { data: expenses, isLoading } = useQuery({
    queryKey: ['expenses'],
    queryFn: () => api.financial.getExpenses()
  })

  const { data: expenseSummary } = useQuery({
    queryKey: ['expense-summary'],
    queryFn: () => api.financial.getExpenseSummary()
  })

  const addMutation = useMutation({
    mutationFn: (data) => api.financial.addExpense(data),
    onSuccess: () => {
      toast.success('Expense added')
      queryClient.invalidateQueries(['expenses'])
      setIsAdding(false)
      setNewExpense({ category: '', amount: '', vendor: '', description: '', date: new Date().toISOString().split('T')[0] })
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.financial.deleteExpense(id),
    onSuccess: () => {
      toast.success('Expense deleted')
      queryClient.invalidateQueries(['expenses'])
    }
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Expense Tracking</h1>
          <p className="text-gray-600">Manage business expenses and budgets</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Dialog open={isAdding} onOpenChange={setIsAdding}>
            <DialogTrigger asChild>
              <Button><Plus className="w-4 h-4 mr-2" />Add Expense</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Expense</DialogTitle>
                <DialogDescription>Record a business expense</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Select value={newExpense.category} onValueChange={(v) => setNewExpense({...newExpense, category: v})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="marketing">Marketing & Advertising</SelectItem>
                      <SelectItem value="software">Software & Tools</SelectItem>
                      <SelectItem value="shipping">Shipping & Fulfillment</SelectItem>
                      <SelectItem value="inventory">Inventory Purchase</SelectItem>
                      <SelectItem value="rent">Rent & Utilities</SelectItem>
                      <SelectItem value="salaries">Salaries & Wages</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Amount</Label>
                  <Input type="number" value={newExpense.amount} onChange={(e) => setNewExpense({...newExpense, amount: e.target.value})} placeholder="0.00" />
                </div>
                <div className="space-y-2">
                  <Label>Vendor/Supplier</Label>
                  <Input value={newExpense.vendor} onChange={(e) => setNewExpense({...newExpense, vendor: e.target.value})} placeholder="Company name" />
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Input value={newExpense.description} onChange={(e) => setNewExpense({...newExpense, description: e.target.value})} placeholder="Brief description" />
                </div>
                <div className="space-y-2">
                  <Label>Date</Label>
                  <Input type="date" value={newExpense.date} onChange={(e) => setNewExpense({...newExpense, date: e.target.value})} />
                </div>
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setIsAdding(false)}>Cancel</Button>
                  <Button onClick={() => addMutation.mutate(newExpense)}>Add Expense</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Total Expenses</p>
            <h3 className="text-2xl font-bold mt-1">${expenseSummary?.total?.toLocaleString() || '0'}</h3>
            <p className="text-sm text-gray-600 mt-1">This month</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Budget Remaining</p>
            <h3 className="text-2xl font-bold mt-1">${expenseSummary?.budget_remaining?.toLocaleString() || '0'}</h3>
            <p className="text-sm text-gray-600 mt-1">{expenseSummary?.budget_used || 0}% used</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Avg Daily Expense</p>
            <h3 className="text-2xl font-bold mt-1">${expenseSummary?.avg_daily || '0'}</h3>
            <p className="text-sm text-gray-600 mt-1">Per day</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-gray-600">Top Category</p>
            <h3 className="text-2xl font-bold mt-1">{expenseSummary?.top_category || 'N/A'}</h3>
            <p className="text-sm text-gray-600 mt-1">${expenseSummary?.top_category_amount || '0'}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Expense by Category */}
        <Card>
          <CardHeader>
            <CardTitle>Expenses by Category</CardTitle>
            <CardDescription>Distribution of spending</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={expenseSummary?.by_category || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: $${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {(expenseSummary?.by_category || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Monthly Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Monthly Expense Trend</CardTitle>
            <CardDescription>Spending over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={expenseSummary?.monthly_trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="amount" fill="#ef4444" name="Expenses ($)" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Expense List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Expenses</CardTitle>
          <CardDescription>Latest expense entries</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border rounded">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3 text-sm font-medium">Date</th>
                  <th className="text-left p-3 text-sm font-medium">Category</th>
                  <th className="text-left p-3 text-sm font-medium">Vendor</th>
                  <th className="text-left p-3 text-sm font-medium">Description</th>
                  <th className="text-right p-3 text-sm font-medium">Amount</th>
                  <th className="text-right p-3 text-sm font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {expenses?.map((expense) => (
                  <tr key={expense.id} className="border-t">
                    <td className="p-3">{new Date(expense.date).toLocaleDateString()}</td>
                    <td className="p-3">
                      <span className="px-2 py-1 bg-gray-100 rounded text-sm">{expense.category}</span>
                    </td>
                    <td className="p-3">{expense.vendor}</td>
                    <td className="p-3 text-gray-600">{expense.description}</td>
                    <td className="p-3 text-right font-medium">${expense.amount.toLocaleString()}</td>
                    <td className="p-3 text-right">
                      <div className="flex justify-end space-x-2">
                        <Button size="sm" variant="ghost">
                          <Receipt className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost">
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => deleteMutation.mutate(expense.id)}>
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ExpenseTracking
