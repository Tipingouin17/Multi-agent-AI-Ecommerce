import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Mail, Eye, Send, RotateCcw } from 'lucide-react'
import api from '@/lib/api-enhanced'

const EmailTemplates = () => {
  const queryClient = useQueryClient()
  const [activeTemplate, setActiveTemplate] = useState('order_confirmation')
  const [content, setContent] = useState('')

  const { data: templates, isLoading } = useQuery({
    queryKey: ['email-templates'],
    queryFn: () => api.settings.getEmailTemplates()
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, content }) => api.settings.updateEmailTemplate(id, content),
    onSuccess: () => {
      toast.success('Template saved')
      queryClient.invalidateQueries(['email-templates'])
    }
  })

  const testMutation = useMutation({
    mutationFn: (id) => api.settings.testEmailTemplate(id),
    onSuccess: () => toast.success('Test email sent')
  })

  const resetMutation = useMutation({
    mutationFn: (id) => api.settings.resetEmailTemplate(id),
    onSuccess: () => {
      toast.success('Template reset to default')
      queryClient.invalidateQueries(['email-templates'])
    }
  })

  const templateTypes = [
    { id: 'order_confirmation', name: 'Order Confirmation', description: 'Sent when an order is placed' },
    { id: 'shipping_notification', name: 'Shipping Notification', description: 'Sent when an order ships' },
    { id: 'delivery_confirmation', name: 'Delivery Confirmation', description: 'Sent when an order is delivered' },
    { id: 'password_reset', name: 'Password Reset', description: 'Sent when password reset is requested' },
    { id: 'welcome_email', name: 'Welcome Email', description: 'Sent to new customers' },
    { id: 'abandoned_cart', name: 'Abandoned Cart', description: 'Sent for abandoned carts' }
  ]

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  const currentTemplate = templates?.find(t => t.id === activeTemplate)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Email Templates</h1>
        <p className="text-gray-600">Customize transactional email templates</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Templates</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {templateTypes.map((template) => (
              <button
                key={template.id}
                onClick={() => setActiveTemplate(template.id)}
                className={`w-full text-left p-3 rounded border transition-colors ${
                  activeTemplate === template.id ? 'bg-blue-50 border-blue-500' : 'hover:bg-gray-50'
                }`}
              >
                <p className="font-medium">{template.name}</p>
                <p className="text-sm text-gray-600">{template.description}</p>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{templateTypes.find(t => t.id === activeTemplate)?.name}</CardTitle>
                <CardDescription>{templateTypes.find(t => t.id === activeTemplate)?.description}</CardDescription>
              </div>
              <div className="flex space-x-2">
                <Button size="sm" variant="outline" onClick={() => testMutation.mutate(activeTemplate)}>
                  <Send className="w-4 h-4 mr-1" />Test
                </Button>
                <Button size="sm" variant="outline" onClick={() => resetMutation.mutate(activeTemplate)}>
                  <RotateCcw className="w-4 h-4 mr-1" />Reset
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="editor">
              <TabsList>
                <TabsTrigger value="editor">Editor</TabsTrigger>
                <TabsTrigger value="preview">Preview</TabsTrigger>
                <TabsTrigger value="variables">Variables</TabsTrigger>
              </TabsList>

              <TabsContent value="editor" className="space-y-4">
                <div className="space-y-2">
                  <Label>Subject Line</Label>
                  <Textarea rows={1} defaultValue={currentTemplate?.subject} placeholder="Your Order #{{order_number}} has been confirmed" />
                </div>
                <div className="space-y-2">
                  <Label>Email Body (HTML)</Label>
                  <Textarea 
                    rows={15} 
                    defaultValue={currentTemplate?.body}
                    className="font-mono text-sm"
                    placeholder="<html>...</html>"
                  />
                </div>
                <Button onClick={() => updateMutation.mutate({ id: activeTemplate, content: currentTemplate?.body })}>
                  Save Template
                </Button>
              </TabsContent>

              <TabsContent value="preview">
                <div className="border rounded p-6 bg-white min-h-[400px]">
                  <div dangerouslySetInnerHTML={{ __html: currentTemplate?.body || '<p>No preview available</p>' }} />
                </div>
              </TabsContent>

              <TabsContent value="variables">
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">Available variables for this template:</p>
                  <div className="grid grid-cols-2 gap-2">
                    {['{{customer_name}}', '{{order_number}}', '{{order_total}}', '{{tracking_number}}', '{{store_name}}', '{{store_url}}'].map(v => (
                      <code key={v} className="text-sm bg-gray-100 px-2 py-1 rounded">{v}</code>
                    ))}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default EmailTemplates
