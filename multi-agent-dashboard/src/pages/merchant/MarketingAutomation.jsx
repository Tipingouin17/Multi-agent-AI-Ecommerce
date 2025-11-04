import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { 
  Workflow, 
  Play,
  Pause,
  Copy,
  Trash2,
  Plus,
  Mail,
  ShoppingCart,
  UserPlus,
  Calendar,
  TrendingUp,
  Users,
  Send
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Marketing Automation Workflows
 * 
 * Create and manage automated marketing workflows:
 * - Pre-built workflow templates
 * - Workflow activation/deactivation
 * - Performance tracking
 * - Trigger-based automation
 */
const MarketingAutomation = () => {
  const queryClient = useQueryClient()

  // Fetch workflows
  const { data: workflows, isLoading } = useQuery({
    queryKey: ['marketing-workflows'],
    queryFn: () => api.automation.getWorkflows()
  })

  // Fetch workflow statistics
  const { data: stats } = useQuery({
    queryKey: ['automation-stats'],
    queryFn: () => api.automation.getStats()
  })

  // Toggle workflow status mutation
  const toggleMutation = useMutation({
    mutationFn: ({ workflowId, enabled }) => 
      api.automation.updateWorkflow(workflowId, { enabled }),
    onSuccess: () => {
      toast.success('Workflow status updated')
      queryClient.invalidateQueries(['marketing-workflows'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update workflow')
    }
  })

  // Duplicate workflow mutation
  const duplicateMutation = useMutation({
    mutationFn: (workflowId) => api.automation.duplicateWorkflow(workflowId),
    onSuccess: () => {
      toast.success('Workflow duplicated')
      queryClient.invalidateQueries(['marketing-workflows'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to duplicate workflow')
    }
  })

  // Delete workflow mutation
  const deleteMutation = useMutation({
    mutationFn: (workflowId) => api.automation.deleteWorkflow(workflowId),
    onSuccess: () => {
      toast.success('Workflow deleted')
      queryClient.invalidateQueries(['marketing-workflows'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete workflow')
    }
  })

  const handleToggle = (workflowId, currentStatus) => {
    toggleMutation.mutate({ workflowId, enabled: !currentStatus })
  }

  const handleDuplicate = (workflowId) => {
    duplicateMutation.mutate(workflowId)
  }

  const handleDelete = (workflowId) => {
    if (window.confirm('Are you sure you want to delete this workflow?')) {
      deleteMutation.mutate(workflowId)
    }
  }

  const getWorkflowIcon = (type) => {
    const icons = {
      welcome: UserPlus,
      abandoned_cart: ShoppingCart,
      win_back: Calendar,
      birthday: Calendar,
      post_purchase: Mail,
      review_request: Mail
    }
    return icons[type] || Workflow
  }

  const workflowTemplates = [
    {
      name: 'Welcome Series',
      description: 'Send a series of emails to new subscribers',
      icon: UserPlus,
      color: 'text-blue-500',
      trigger: 'New subscriber',
      steps: 3
    },
    {
      name: 'Abandoned Cart Recovery',
      description: 'Remind customers about items left in cart',
      icon: ShoppingCart,
      color: 'text-orange-500',
      trigger: 'Cart abandoned',
      steps: 3
    },
    {
      name: 'Win-Back Campaign',
      description: 'Re-engage inactive customers',
      icon: Calendar,
      color: 'text-purple-500',
      trigger: 'No purchase in 90 days',
      steps: 2
    },
    {
      name: 'Birthday Rewards',
      description: 'Send birthday discounts to customers',
      icon: Calendar,
      color: 'text-pink-500',
      trigger: 'Customer birthday',
      steps: 1
    },
    {
      name: 'Post-Purchase Follow-up',
      description: 'Thank customers and request feedback',
      icon: Mail,
      color: 'text-green-500',
      trigger: 'Order delivered',
      steps: 2
    },
    {
      name: 'Review Request',
      description: 'Ask customers to review their purchase',
      icon: Mail,
      color: 'text-yellow-500',
      trigger: '7 days after delivery',
      steps: 1
    }
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading workflows...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Marketing Automation</h1>
          <p className="text-gray-600">Create automated workflows to engage customers</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Create Workflow
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Workflows</p>
                <p className="text-2xl font-bold">{stats?.activeWorkflows || 0}</p>
              </div>
              <Workflow className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Emails Sent</p>
                <p className="text-2xl font-bold">{stats?.emailsSent?.toLocaleString() || '0'}</p>
                <p className="text-xs text-gray-400 mt-1">this month</p>
              </div>
              <Send className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Conversion Rate</p>
                <p className="text-2xl font-bold">{stats?.conversionRate?.toFixed(1) || '0.0'}%</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-green-500" />
                  <span className="text-xs text-green-500">+2.4%</span>
                </div>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Revenue Generated</p>
                <p className="text-2xl font-bold">${stats?.revenue?.toLocaleString() || '0'}</p>
                <p className="text-xs text-gray-400 mt-1">from automation</p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Workflows */}
      <Card>
        <CardHeader>
          <CardTitle>Active Workflows</CardTitle>
          <CardDescription>{workflows?.length || 0} workflows configured</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {workflows?.map((workflow) => {
              const Icon = getWorkflowIcon(workflow.type)
              
              return (
                <Card key={workflow.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4 flex-1">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded flex items-center justify-center text-white">
                          <Icon className="w-6 h-6" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium text-lg">{workflow.name}</h4>
                            <Badge variant={workflow.enabled ? 'default' : 'secondary'}>
                              {workflow.enabled ? 'Active' : 'Paused'}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600 mb-3">{workflow.description}</p>
                          
                          <div className="grid grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-gray-600">Trigger</p>
                              <p className="font-medium">{workflow.trigger}</p>
                            </div>
                            <div>
                              <p className="text-gray-600">Emails Sent</p>
                              <p className="font-medium">{workflow.emails_sent?.toLocaleString() || 0}</p>
                            </div>
                            <div>
                              <p className="text-gray-600">Open Rate</p>
                              <p className="font-medium">{workflow.open_rate?.toFixed(1) || '0.0'}%</p>
                            </div>
                            <div>
                              <p className="text-gray-600">Conversion Rate</p>
                              <p className="font-medium">{workflow.conversion_rate?.toFixed(1) || '0.0'}%</p>
                            </div>
                          </div>

                          {/* Workflow Steps Preview */}
                          <div className="mt-3 flex items-center space-x-2">
                            <span className="text-xs text-gray-500">Steps:</span>
                            {workflow.steps?.map((step, index) => (
                              <div key={index} className="flex items-center">
                                <Badge variant="outline" className="text-xs">
                                  {step.delay ? `Wait ${step.delay}` : step.action}
                                </Badge>
                                {index < workflow.steps.length - 1 && (
                                  <span className="mx-1 text-gray-400">→</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-col space-y-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">
                            {workflow.enabled ? 'Active' : 'Paused'}
                          </span>
                          <Switch 
                            checked={workflow.enabled}
                            onCheckedChange={() => handleToggle(workflow.id, workflow.enabled)}
                          />
                        </div>
                        
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleDuplicate(workflow.id)}
                        >
                          <Copy className="w-4 h-4 mr-1" />
                          Duplicate
                        </Button>

                        <Button 
                          size="sm" 
                          variant="outline"
                        >
                          Edit
                        </Button>

                        <Button 
                          size="sm" 
                          variant="destructive"
                          onClick={() => handleDelete(workflow.id)}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}

            {(!workflows || workflows.length === 0) && (
              <div className="text-center py-12 text-gray-500">
                <Workflow className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No workflows created yet</p>
                <p className="text-sm mt-2">Start with a template below</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Workflow Templates */}
      <Card>
        <CardHeader>
          <CardTitle>Workflow Templates</CardTitle>
          <CardDescription>Quick-start with pre-built automation workflows</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-6">
            {workflowTemplates.map((template, index) => {
              const Icon = template.icon
              
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow cursor-pointer">
                  <CardContent className="pt-6">
                    <Icon className={`w-10 h-10 ${template.color} mb-4`} />
                    <h4 className="font-medium text-lg mb-2">{template.name}</h4>
                    <p className="text-sm text-gray-600 mb-4">{template.description}</p>
                    
                    <div className="space-y-2 mb-4 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Trigger:</span>
                        <Badge variant="outline">{template.trigger}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Steps:</span>
                        <span className="font-medium">{template.steps}</span>
                      </div>
                    </div>

                    <Button className="w-full" size="sm">
                      <Plus className="w-4 h-4 mr-2" />
                      Use Template
                    </Button>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default MarketingAutomation
