import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Key, Plus, Trash2, Copy, Webhook, Eye, EyeOff } from 'lucide-react'
import api from '@/lib/api-enhanced'

const APISettings = () => {
  const queryClient = useQueryClient()
  const [isCreatingKey, setIsCreatingKey] = useState(false)
  const [isCreatingWebhook, setIsCreatingWebhook] = useState(false)
  const [showKeys, setShowKeys] = useState({})
  const [newKey, setNewKey] = useState({ name: '', permissions: [] })
  const [newWebhook, setNewWebhook] = useState({ url: '', events: [] })

  const { data: apiKeys, isLoading: loadingKeys } = useQuery({
    queryKey: ['api-keys'],
    queryFn: () => api.settings.getAPIKeys()
  })

  const { data: webhooks, isLoading: loadingWebhooks } = useQuery({
    queryKey: ['webhooks'],
    queryFn: () => api.settings.getWebhooks()
  })

  const createKeyMutation = useMutation({
    mutationFn: (data) => api.settings.createAPIKey(data),
    onSuccess: () => {
      toast.success('API key created')
      queryClient.invalidateQueries(['api-keys'])
      setIsCreatingKey(false)
    }
  })

  const deleteKeyMutation = useMutation({
    mutationFn: (id) => api.settings.deleteAPIKey(id),
    onSuccess: () => {
      toast.success('API key revoked')
      queryClient.invalidateQueries(['api-keys'])
    }
  })

  const createWebhookMutation = useMutation({
    mutationFn: (data) => api.settings.createWebhook(data),
    onSuccess: () => {
      toast.success('Webhook created')
      queryClient.invalidateQueries(['webhooks'])
      setIsCreatingWebhook(false)
    }
  })

  const deleteWebhookMutation = useMutation({
    mutationFn: (id) => api.settings.deleteWebhook(id),
    onSuccess: () => {
      toast.success('Webhook deleted')
      queryClient.invalidateQueries(['webhooks'])
    }
  })

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  if (loadingKeys || loadingWebhooks) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">API Keys & Webhooks</h1>
        <p className="text-gray-600">Manage API access and webhook integrations</p>
      </div>

      {/* API Keys Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>Manage API keys for integrations</CardDescription>
            </div>
            <Dialog open={isCreatingKey} onOpenChange={setIsCreatingKey}>
              <DialogTrigger asChild>
                <Button><Plus className="w-4 h-4 mr-2" />Create API Key</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create API Key</DialogTitle>
                  <DialogDescription>Generate a new API key for integrations</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Key Name</Label>
                    <Input value={newKey.name} onChange={(e) => setNewKey({...newKey, name: e.target.value})} placeholder="Production API" />
                  </div>
                  <div className="flex justify-end space-x-2">
                    <Button variant="outline" onClick={() => setIsCreatingKey(false)}>Cancel</Button>
                    <Button onClick={() => createKeyMutation.mutate(newKey)}>Create Key</Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {apiKeys?.map((key) => (
            <div key={key.id} className="flex items-center justify-between p-4 border rounded">
              <div className="flex-1">
                <p className="font-medium">{key.name}</p>
                <div className="flex items-center space-x-2 mt-1">
                  <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                    {showKeys[key.id] ? key.key : key.key?.substring(0, 20) + '...'}
                  </code>
                  <Button size="sm" variant="ghost" onClick={() => setShowKeys({...showKeys, [key.id]: !showKeys[key.id]})}>
                    {showKeys[key.id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => copyToClipboard(key.key)}>
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
                <p className="text-sm text-gray-600 mt-1">Created {new Date(key.created_at).toLocaleDateString()} • Last used {key.last_used || 'Never'}</p>
              </div>
              <Button size="sm" variant="destructive" onClick={() => deleteKeyMutation.mutate(key.id)}>
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          ))}
          {(!apiKeys || apiKeys.length === 0) && (
            <div className="text-center py-8 text-gray-500">
              <Key className="w-8 h-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">No API keys created</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Webhooks Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Webhooks</CardTitle>
              <CardDescription>Configure webhook endpoints for events</CardDescription>
            </div>
            <Dialog open={isCreatingWebhook} onOpenChange={setIsCreatingWebhook}>
              <DialogTrigger asChild>
                <Button><Plus className="w-4 h-4 mr-2" />Add Webhook</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Webhook</DialogTitle>
                  <DialogDescription>Configure a webhook endpoint</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Webhook URL</Label>
                    <Input value={newWebhook.url} onChange={(e) => setNewWebhook({...newWebhook, url: e.target.value})} placeholder="https://api.example.com/webhooks" />
                  </div>
                  <div className="space-y-2">
                    <Label>Events</Label>
                    <div className="space-y-2">
                      {['order.created', 'order.updated', 'product.created', 'payment.completed'].map(event => (
                        <label key={event} className="flex items-center space-x-2">
                          <input type="checkbox" />
                          <span className="text-sm">{event}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  <div className="flex justify-end space-x-2">
                    <Button variant="outline" onClick={() => setIsCreatingWebhook(false)}>Cancel</Button>
                    <Button onClick={() => createWebhookMutation.mutate(newWebhook)}>Add Webhook</Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {webhooks?.map((webhook) => (
            <div key={webhook.id} className="flex items-center justify-between p-4 border rounded">
              <div className="flex-1">
                <code className="text-sm">{webhook.url}</code>
                <div className="flex items-center space-x-2 mt-2">
                  {webhook.events?.map(event => (
                    <Badge key={event} variant="outline">{event}</Badge>
                  ))}
                </div>
                <p className="text-sm text-gray-600 mt-1">{webhook.success_count || 0} successful • {webhook.failure_count || 0} failed</p>
              </div>
              <div className="flex space-x-2">
                <Button size="sm" variant="outline">Test</Button>
                <Button size="sm" variant="destructive" onClick={() => deleteWebhookMutation.mutate(webhook.id)}>
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
          {(!webhooks || webhooks.length === 0) && (
            <div className="text-center py-8 text-gray-500">
              <Webhook className="w-8 h-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">No webhooks configured</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default APISettings
