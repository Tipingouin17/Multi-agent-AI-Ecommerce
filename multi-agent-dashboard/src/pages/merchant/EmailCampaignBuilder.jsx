import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Mail, 
  Users,
  Eye,
  Send,
  Save,
  ArrowLeft,
  Image,
  Type,
  Layout
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Email Campaign Builder
 * 
 * Create and design email campaigns:
 * - Campaign setup
 * - Email content editor
 * - Audience selection
 * - Preview and test
 * - Schedule or send
 */
const EmailCampaignBuilder = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('setup')
  
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    from_name: '',
    from_email: '',
    reply_to: '',
    preview_text: '',
    content: '',
    audience: 'all',
    segment_id: '',
    schedule_type: 'now',
    schedule_date: ''
  })

  // Create campaign mutation
  const createMutation = useMutation({
    mutationFn: (data) => api.campaigns.createCampaign(data),
    onSuccess: () => {
      toast.success('Campaign created successfully')
      queryClient.invalidateQueries(['campaigns'])
      navigate('/marketing/campaigns')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create campaign')
    }
  })

  // Send test email mutation
  const sendTestMutation = useMutation({
    mutationFn: (email) => api.campaigns.sendTest(email, formData),
    onSuccess: () => {
      toast.success('Test email sent')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to send test email')
    }
  })

  const handleSaveDraft = () => {
    createMutation.mutate({ ...formData, status: 'draft' })
  }

  const handleSchedule = () => {
    if (formData.schedule_type === 'later' && !formData.schedule_date) {
      toast.error('Please select a schedule date')
      return
    }
    createMutation.mutate({ ...formData, status: 'scheduled' })
  }

  const handleSendNow = () => {
    if (!formData.name || !formData.subject || !formData.content) {
      toast.error('Please fill in all required fields')
      return
    }
    createMutation.mutate({ ...formData, status: 'sending' })
  }

  const handleSendTest = () => {
    const email = prompt('Enter email address for test:')
    if (email) {
      sendTestMutation.mutate(email)
    }
  }

  const insertTemplate = (template) => {
    const templates = {
      welcome: `<h1>Welcome to Our Store!</h1>
<p>Thank you for joining us. Here's a special discount code just for you:</p>
<div style="background: #f3f4f6; padding: 20px; text-align: center; margin: 20px 0;">
  <h2 style="color: #3b82f6;">WELCOME10</h2>
  <p>10% off your first order</p>
</div>
<p>Start shopping now and discover our amazing products!</p>`,
      
      promotion: `<h1>Special Offer Inside!</h1>
<p>Don't miss out on our limited-time promotion:</p>
<div style="background: #3b82f6; color: white; padding: 30px; text-align: center; margin: 20px 0;">
  <h2>50% OFF</h2>
  <p>All Products</p>
  <a href="#" style="background: white; color: #3b82f6; padding: 10px 30px; text-decoration: none; display: inline-block; margin-top: 10px;">Shop Now</a>
</div>`,
      
      abandoned_cart: `<h1>You Left Something Behind!</h1>
<p>We noticed you left items in your cart. Complete your purchase now:</p>
<div style="border: 1px solid #e5e7eb; padding: 20px; margin: 20px 0;">
  <h3>Your Cart Items</h3>
  <p>Product Name - $XX.XX</p>
</div>
<a href="#" style="background: #3b82f6; color: white; padding: 15px 40px; text-decoration: none; display: inline-block;">Complete Purchase</a>`,
      
      newsletter: `<h1>Monthly Newsletter</h1>
<h2>What's New This Month</h2>
<p>Check out our latest products, blog posts, and company updates:</p>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
  <div style="border: 1px solid #e5e7eb; padding: 15px;">
    <h3>New Product Launch</h3>
    <p>Description of the new product...</p>
  </div>
  <div style="border: 1px solid #e5e7eb; padding: 15px;">
    <h3>Blog Post</h3>
    <p>Latest article from our blog...</p>
  </div>
</div>`
    }
    
    setFormData({ ...formData, content: templates[template] || '' })
    toast.success('Template inserted')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" onClick={() => navigate('/marketing/campaigns')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Create Email Campaign</h1>
            <p className="text-gray-600">Design and send email campaigns to your customers</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleSaveDraft}>
            <Save className="w-4 h-4 mr-2" />
            Save Draft
          </Button>
          <Button variant="outline" onClick={handleSendTest}>
            <Eye className="w-4 h-4 mr-2" />
            Send Test
          </Button>
          <Button onClick={handleSendNow}>
            <Send className="w-4 h-4 mr-2" />
            Send Now
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-3 gap-6">
        {/* Editor */}
        <div className="col-span-2">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="setup">Setup</TabsTrigger>
              <TabsTrigger value="design">Design</TabsTrigger>
              <TabsTrigger value="audience">Audience</TabsTrigger>
              <TabsTrigger value="schedule">Schedule</TabsTrigger>
            </TabsList>

            {/* Setup Tab */}
            <TabsContent value="setup">
              <Card>
                <CardHeader>
                  <CardTitle>Campaign Setup</CardTitle>
                  <CardDescription>Basic campaign information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Campaign Name *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Summer Sale 2025"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Email Subject *</Label>
                    <Input
                      value={formData.subject}
                      onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                      placeholder="Don't miss our summer sale!"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Preview Text</Label>
                    <Input
                      value={formData.preview_text}
                      onChange={(e) => setFormData({ ...formData, preview_text: e.target.value })}
                      placeholder="Up to 50% off on selected items"
                    />
                    <p className="text-sm text-gray-500">Shown in email client preview</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>From Name</Label>
                      <Input
                        value={formData.from_name}
                        onChange={(e) => setFormData({ ...formData, from_name: e.target.value })}
                        placeholder="Your Store"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>From Email</Label>
                      <Input
                        type="email"
                        value={formData.from_email}
                        onChange={(e) => setFormData({ ...formData, from_email: e.target.value })}
                        placeholder="hello@yourstore.com"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Reply-To Email</Label>
                    <Input
                      type="email"
                      value={formData.reply_to}
                      onChange={(e) => setFormData({ ...formData, reply_to: e.target.value })}
                      placeholder="support@yourstore.com"
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Design Tab */}
            <TabsContent value="design">
              <Card>
                <CardHeader>
                  <CardTitle>Email Content</CardTitle>
                  <CardDescription>Design your email content</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Email Templates</Label>
                    <div className="grid grid-cols-2 gap-2">
                      <Button variant="outline" onClick={() => insertTemplate('welcome')}>
                        <Layout className="w-4 h-4 mr-2" />
                        Welcome Email
                      </Button>
                      <Button variant="outline" onClick={() => insertTemplate('promotion')}>
                        <Layout className="w-4 h-4 mr-2" />
                        Promotion
                      </Button>
                      <Button variant="outline" onClick={() => insertTemplate('abandoned_cart')}>
                        <Layout className="w-4 h-4 mr-2" />
                        Abandoned Cart
                      </Button>
                      <Button variant="outline" onClick={() => insertTemplate('newsletter')}>
                        <Layout className="w-4 h-4 mr-2" />
                        Newsletter
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Email Content (HTML) *</Label>
                    <Textarea
                      value={formData.content}
                      onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                      placeholder="Enter your email HTML here..."
                      rows={15}
                      className="font-mono text-sm"
                    />
                    <p className="text-sm text-gray-500">
                      Use HTML to design your email. You can insert templates above.
                    </p>
                  </div>

                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm">
                      <Image className="w-4 h-4 mr-2" />
                      Insert Image
                    </Button>
                    <Button variant="outline" size="sm">
                      <Type className="w-4 h-4 mr-2" />
                      Insert Text Block
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Audience Tab */}
            <TabsContent value="audience">
              <Card>
                <CardHeader>
                  <CardTitle>Select Audience</CardTitle>
                  <CardDescription>Choose who will receive this campaign</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Audience Type</Label>
                    <Select value={formData.audience} onValueChange={(value) => setFormData({ ...formData, audience: value })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Customers</SelectItem>
                        <SelectItem value="segment">Customer Segment</SelectItem>
                        <SelectItem value="subscribers">Newsletter Subscribers</SelectItem>
                        <SelectItem value="vip">VIP Customers</SelectItem>
                        <SelectItem value="inactive">Inactive Customers</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.audience === 'segment' && (
                    <div className="space-y-2">
                      <Label>Select Segment</Label>
                      <Select value={formData.segment_id} onValueChange={(value) => setFormData({ ...formData, segment_id: value })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Choose a segment" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">High-Value Customers</SelectItem>
                          <SelectItem value="2">Frequent Buyers</SelectItem>
                          <SelectItem value="3">At Risk</SelectItem>
                          <SelectItem value="4">New Customers</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  <Card className="bg-blue-50 border-blue-200">
                    <CardContent className="pt-6">
                      <div className="flex items-center space-x-3">
                        <Users className="w-8 h-8 text-blue-600" />
                        <div>
                          <p className="font-medium text-blue-900">Estimated Recipients</p>
                          <p className="text-2xl font-bold text-blue-600">12,450</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Schedule Tab */}
            <TabsContent value="schedule">
              <Card>
                <CardHeader>
                  <CardTitle>Schedule Campaign</CardTitle>
                  <CardDescription>Choose when to send your campaign</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Send Time</Label>
                    <Select value={formData.schedule_type} onValueChange={(value) => setFormData({ ...formData, schedule_type: value })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="now">Send Immediately</SelectItem>
                        <SelectItem value="later">Schedule for Later</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.schedule_type === 'later' && (
                    <div className="space-y-2">
                      <Label>Schedule Date & Time</Label>
                      <Input
                        type="datetime-local"
                        value={formData.schedule_date}
                        onChange={(e) => setFormData({ ...formData, schedule_date: e.target.value })}
                      />
                    </div>
                  )}

                  <Card className="bg-green-50 border-green-200">
                    <CardContent className="pt-6">
                      <div className="space-y-2">
                        <h4 className="font-medium text-green-900">Best Time to Send</h4>
                        <p className="text-sm text-green-800">
                          Based on your audience's engagement patterns, we recommend sending on 
                          <strong> Tuesday at 10:00 AM</strong> for optimal open rates.
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="flex justify-end space-x-2 pt-4">
                    <Button variant="outline" onClick={handleSaveDraft}>
                      Save as Draft
                    </Button>
                    {formData.schedule_type === 'later' ? (
                      <Button onClick={handleSchedule}>
                        Schedule Campaign
                      </Button>
                    ) : (
                      <Button onClick={handleSendNow}>
                        <Send className="w-4 h-4 mr-2" />
                        Send Now
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Preview */}
        <div className="col-span-1">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle>Email Preview</CardTitle>
              <CardDescription>How your email will look</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-lg overflow-hidden">
                {/* Email Header */}
                <div className="bg-gray-100 p-3 border-b text-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{formData.from_name || 'Your Store'}</span>
                    <span className="text-gray-500">now</span>
                  </div>
                  <div className="text-gray-600">{formData.from_email || 'hello@yourstore.com'}</div>
                  <div className="font-medium mt-2">{formData.subject || 'Email Subject'}</div>
                  {formData.preview_text && (
                    <div className="text-gray-500 text-xs mt-1">{formData.preview_text}</div>
                  )}
                </div>

                {/* Email Body */}
                <div className="p-4 bg-white min-h-[400px]">
                  {formData.content ? (
                    <div dangerouslySetInnerHTML={{ __html: formData.content }} />
                  ) : (
                    <div className="text-center text-gray-400 py-12">
                      <Mail className="w-12 h-12 mx-auto mb-4" />
                      <p>Email content will appear here</p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default EmailCampaignBuilder
