import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@/tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Bell, Mail, MessageSquare, Smartphone, Save } from 'lucide-react'
import api from '@/lib/api-enhanced'

const NotificationSettings = () => {
  const queryClient = useQueryClient()
  const [settings, setSettings] = useState({
    new_order_email: true,
    new_order_sms: false,
    low_inventory_email: true,
    low_inventory_sms: false,
    customer_inquiry_email: true,
    payment_issue_email: true,
    system_alert_email: true
  })

  const { data, isLoading } = useQuery({
    queryKey: ['notification-settings'],
    queryFn: () => api.settings.getNotifications()
  })

  const updateMutation = useMutation({
    mutationFn: (data) => api.settings.updateNotifications(data),
    onSuccess: () => toast.success('Notification settings saved')
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  const notificationGroups = [
    {
      title: 'Order Notifications',
      description: 'Get notified about new orders and order updates',
      items: [
        { key: 'new_order_email', label: 'New Order (Email)', icon: Mail },
        { key: 'new_order_sms', label: 'New Order (SMS)', icon: MessageSquare }
      ]
    },
    {
      title: 'Inventory Alerts',
      description: 'Get notified about inventory levels',
      items: [
        { key: 'low_inventory_email', label: 'Low Inventory (Email)', icon: Mail },
        { key: 'low_inventory_sms', label: 'Low Inventory (SMS)', icon: MessageSquare }
      ]
    },
    {
      title: 'Customer Communications',
      description: 'Get notified about customer inquiries',
      items: [
        { key: 'customer_inquiry_email', label: 'Customer Inquiry (Email)', icon: Mail }
      ]
    },
    {
      title: 'System Alerts',
      description: 'Get notified about system issues',
      items: [
        { key: 'payment_issue_email', label: 'Payment Issues (Email)', icon: Mail },
        { key: 'system_alert_email', label: 'System Alerts (Email)', icon: Mail }
      ]
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Notification Settings</h1>
          <p className="text-gray-600">Manage how you receive notifications</p>
        </div>
        <Button onClick={() => updateMutation.mutate(settings)}>
          <Save className="w-4 h-4 mr-2" />Save Settings
        </Button>
      </div>

      <div className="space-y-6">
        {notificationGroups.map((group, index) => (
          <Card key={index}>
            <CardHeader>
              <CardTitle>{group.title}</CardTitle>
              <CardDescription>{group.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {group.items.map((item) => (
                <div key={item.key} className="flex items-center justify-between p-3 border rounded">
                  <div className="flex items-center space-x-3">
                    <item.icon className="w-5 h-5 text-gray-600" />
                    <Label>{item.label}</Label>
                  </div>
                  <Switch 
                    checked={settings[item.key]}
                    onCheckedChange={(checked) => setSettings({...settings, [item.key]: checked})}
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default NotificationSettings
