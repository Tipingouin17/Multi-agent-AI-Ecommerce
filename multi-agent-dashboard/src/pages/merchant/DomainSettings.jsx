import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Globe, Plus, CheckCircle, XCircle, Shield, Trash2 } from 'lucide-react'
import api from '@/lib/api-enhanced'

const DomainSettings = () => {
  const queryClient = useQueryClient()
  const [isAdding, setIsAdding] = useState(false)
  const [newDomain, setNewDomain] = useState('')

  const { data: domains, isLoading } = useQuery({
    queryKey: ['domains'],
    queryFn: () => api.settings.getDomains()
  })

  const addMutation = useMutation({
    mutationFn: (domain) => api.settings.addDomain(domain),
    onSuccess: () => {
      toast.success('Domain added')
      queryClient.invalidateQueries(['domains'])
      setIsAdding(false)
      setNewDomain('')
    }
  })

  const verifyMutation = useMutation({
    mutationFn: (id) => api.settings.verifyDomain(id),
    onSuccess: () => {
      toast.success('Domain verified')
      queryClient.invalidateQueries(['domains'])
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.settings.deleteDomain(id),
    onSuccess: () => {
      toast.success('Domain removed')
      queryClient.invalidateQueries(['domains'])
    }
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Domain & SSL</h1>
          <p className="text-gray-600">Manage custom domains and SSL certificates</p>
        </div>
        <Dialog open={isAdding} onOpenChange={setIsAdding}>
          <DialogTrigger asChild>
            <Button><Plus className="w-4 h-4 mr-2" />Add Domain</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Custom Domain</DialogTitle>
              <DialogDescription>Connect your own domain to your store</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Domain Name</Label>
                <Input value={newDomain} onChange={(e) => setNewDomain(e.target.value)} placeholder="www.mystore.com" />
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsAdding(false)}>Cancel</Button>
                <Button onClick={() => addMutation.mutate(newDomain)}>Add Domain</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="space-y-4">
        {domains?.map((domain) => (
          <Card key={domain.id}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <Globe className="w-8 h-8 text-blue-500" />
                  <div>
                    <h3 className="font-medium">{domain.name}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      {domain.verified ? (
                        <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Verified</Badge>
                      ) : (
                        <Badge variant="secondary"><XCircle className="w-3 h-3 mr-1" />Not Verified</Badge>
                      )}
                      {domain.ssl_enabled && (
                        <Badge className="bg-blue-500"><Shield className="w-3 h-3 mr-1" />SSL Active</Badge>
                      )}
                      {domain.primary && <Badge>Primary</Badge>}
                    </div>
                  </div>
                </div>
                <div className="flex space-x-2">
                  {!domain.verified && (
                    <Button size="sm" onClick={() => verifyMutation.mutate(domain.id)}>Verify</Button>
                  )}
                  <Button size="sm" variant="destructive" onClick={() => deleteMutation.mutate(domain.id)}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              {!domain.verified && (
                <div className="mt-4 p-4 bg-gray-50 rounded">
                  <p className="text-sm font-medium mb-2">DNS Configuration</p>
                  <code className="text-xs block">A Record: @ → 192.0.2.1</code>
                  <code className="text-xs block">CNAME: www → mystore.platform.com</code>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
        {(!domains || domains.length === 0) && (
          <Card>
            <CardContent className="pt-12 pb-12 text-center text-gray-500">
              <Globe className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No custom domains configured</p>
              <Button className="mt-4" onClick={() => setIsAdding(true)}><Plus className="w-4 h-4 mr-2" />Add Domain</Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

export default DomainSettings
