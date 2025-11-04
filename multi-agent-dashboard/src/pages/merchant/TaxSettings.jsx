import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Receipt, Plus, Trash2, Edit, Calculator } from 'lucide-react'
import api from '@/lib/api-enhanced'

const TaxSettings = () => {
  const queryClient = useQueryClient()
  const [isAdding, setIsAdding] = useState(false)
  const [newTax, setNewTax] = useState({
    name: '',
    country: 'US',
    state: '',
    rate: '',
    tax_type: 'sales_tax',
    inclusive: false,
    enabled: true
  })

  const { data: taxes, isLoading } = useQuery({
    queryKey: ['tax-settings'],
    queryFn: () => api.settings.getTaxes()
  })

  const addMutation = useMutation({
    mutationFn: (data) => api.settings.addTaxRule(data),
    onSuccess: () => {
      toast.success('Tax rule added')
      queryClient.invalidateQueries(['tax-settings'])
      setIsAdding(false)
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.settings.deleteTaxRule(id),
    onSuccess: () => {
      toast.success('Tax rule deleted')
      queryClient.invalidateQueries(['tax-settings'])
    }
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tax Configuration</h1>
          <p className="text-gray-600">Manage tax rules and rates</p>
        </div>
        <Dialog open={isAdding} onOpenChange={setIsAdding}>
          <DialogTrigger asChild>
            <Button><Plus className="w-4 h-4 mr-2" />Add Tax Rule</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Tax Rule</DialogTitle>
              <DialogDescription>Configure a new tax rule</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Rule Name *</Label>
                <Input value={newTax.name} onChange={(e) => setNewTax({...newTax, name: e.target.value})} placeholder="US Sales Tax" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Country *</Label>
                  <Select value={newTax.country} onValueChange={(value) => setNewTax({...newTax, country: value})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="US">United States</SelectItem>
                      <SelectItem value="CA">Canada</SelectItem>
                      <SelectItem value="GB">United Kingdom</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>State/Province</Label>
                  <Input value={newTax.state} onChange={(e) => setNewTax({...newTax, state: e.target.value})} placeholder="CA" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Tax Rate (%) *</Label>
                  <Input type="number" step="0.01" value={newTax.rate} onChange={(e) => setNewTax({...newTax, rate: e.target.value})} placeholder="8.5" />
                </div>
                <div className="space-y-2">
                  <Label>Tax Type</Label>
                  <Select value={newTax.tax_type} onValueChange={(value) => setNewTax({...newTax, tax_type: value})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sales_tax">Sales Tax</SelectItem>
                      <SelectItem value="vat">VAT</SelectItem>
                      <SelectItem value="gst">GST</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex items-center justify-between p-3 border rounded">
                <div>
                  <p className="font-medium">Tax Inclusive Pricing</p>
                  <p className="text-sm text-gray-600">Tax is included in product prices</p>
                </div>
                <Switch checked={newTax.inclusive} onCheckedChange={(checked) => setNewTax({...newTax, inclusive: checked})} />
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsAdding(false)}>Cancel</Button>
                <Button onClick={() => addMutation.mutate(newTax)}>Add Rule</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="space-y-4">
        {taxes?.map((tax) => (
          <Card key={tax.id}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <Receipt className="w-8 h-8 text-blue-500" />
                  <div>
                    <h3 className="font-medium">{tax.name}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge>{tax.rate}%</Badge>
                      <Badge variant="outline">{tax.tax_type}</Badge>
                      <span className="text-sm text-gray-600">{tax.country} {tax.state && `• ${tax.state}`}</span>
                      {tax.inclusive && <Badge variant="secondary">Inclusive</Badge>}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch checked={tax.enabled} />
                  <Button size="sm" variant="outline"><Edit className="w-4 h-4" /></Button>
                  <Button size="sm" variant="destructive" onClick={() => deleteMutation.mutate(tax.id)}><Trash2 className="w-4 h-4" /></Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        {(!taxes || taxes.length === 0) && (
          <Card>
            <CardContent className="pt-12 pb-12 text-center text-gray-500">
              <Calculator className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No tax rules configured</p>
              <Button className="mt-4" onClick={() => setIsAdding(true)}><Plus className="w-4 h-4 mr-2" />Add Tax Rule</Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

export default TaxSettings
