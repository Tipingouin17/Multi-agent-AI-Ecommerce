import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Mail, 
  Send,
  Pause,
  Play,
  Copy,
  Trash2,
  Search,
  Plus,
  TrendingUp,
  Users,
  MousePointer,
  DollarSign
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Campaign Management & Analytics Page
 * 
 * Manage all marketing campaigns with:
 * - Campaign list with status
 * - Performance metrics
 * - Campaign scheduling
 * - Duplicate/archive functionality
 * - Analytics dashboard
 */
const CampaignManagement = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')

  // Fetch campaigns
  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['campaigns', statusFilter, typeFilter, searchTerm],
    queryFn: () => api.campaigns.getCampaigns({ 
      status: statusFilter, 
      type: typeFilter,
      search: searchTerm 
    })
  })

  // Fetch campaign statistics
  const { data: stats } = useQuery({
    queryKey: ['campaign-stats'],
    queryFn: () => api.campaigns.getStats()
  })

  // Update campaign status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ campaignId, status }) => 
      api.campaigns.updateStatus(campaignId, status),
    onSuccess: () => {
      toast.success('Campaign status updated')
      queryClient.invalidateQueries(['campaigns'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update campaign status')
    }
  })

  // Duplicate campaign mutation
  const duplicateMutation = useMutation({
    mutationFn: (campaignId) => api.campaigns.duplicate(campaignId),
    onSuccess: () => {
      toast.success('Campaign duplicated')
      queryClient.invalidateQueries(['campaigns'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to duplicate campaign')
    }
  })

  // Delete campaign mutation
  const deleteMutation = useMutation({
    mutationFn: (campaignId) => api.campaigns.deleteCampaign(campaignId),
    onSuccess: () => {
      toast.success('Campaign deleted')
      queryClient.invalidateQueries(['campaigns'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete campaign')
    }
  })

  const handlePauseCampaign = (campaignId) => {
    updateStatusMutation.mutate({ campaignId, status: 'paused' })
  }

  const handleResumeCampaign = (campaignId) => {
    updateStatusMutation.mutate({ campaignId, status: 'active' })
  }

  const handleDuplicate = (campaignId) => {
    duplicateMutation.mutate(campaignId)
  }

  const handleDelete = (campaignId) => {
    if (window.confirm('Are you sure you want to delete this campaign?')) {
      deleteMutation.mutate(campaignId)
    }
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      draft: { variant: 'secondary', label: 'Draft' },
      scheduled: { variant: 'default', label: 'Scheduled' },
      active: { variant: 'default', label: 'Active' },
      paused: { variant: 'secondary', label: 'Paused' },
      completed: { variant: 'default', label: 'Completed' }
    }

    const config = statusConfig[status] || statusConfig.draft
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  const getTypeBadge = (type) => {
    const typeConfig = {
      email: { icon: Mail, label: 'Email' },
      sms: { icon: Send, label: 'SMS' },
      push: { icon: Send, label: 'Push' }
    }

    const config = typeConfig[type] || typeConfig.email
    const Icon = config.icon

    return (
      <Badge variant="outline" className="flex items-center space-x-1">
        <Icon className="w-3 h-3" />
        <span>{config.label}</span>
      </Badge>
    )
  }

  const filteredCampaigns = campaigns?.filter(campaign => {
    if (statusFilter !== 'all' && campaign.status !== statusFilter) return false
    if (typeFilter !== 'all' && campaign.type !== typeFilter) return false
    if (searchTerm && !campaign.name.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading campaigns...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Marketing Campaigns</h1>
          <p className="text-gray-600">Create and manage your marketing campaigns</p>
        </div>
        <Button onClick={() => navigate('/marketing/campaigns/new')}>
          <Plus className="w-4 h-4 mr-2" />
          New Campaign
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Campaigns</p>
                <p className="text-2xl font-bold">{stats?.totalCampaigns || 0}</p>
                <p className="text-xs text-gray-400 mt-1">{stats?.activeCampaigns || 0} active</p>
              </div>
              <Mail className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Open Rate</p>
                <p className="text-2xl font-bold">{stats?.avgOpenRate?.toFixed(1) || '0.0'}%</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-green-500" />
                  <span className="text-xs text-green-500">+2.3%</span>
                </div>
              </div>
              <Mail className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Click Rate</p>
                <p className="text-2xl font-bold">{stats?.avgClickRate?.toFixed(1) || '0.0'}%</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-green-500" />
                  <span className="text-xs text-green-500">+1.8%</span>
                </div>
              </div>
              <MousePointer className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Revenue</p>
                <p className="text-2xl font-bold">${stats?.totalRevenue?.toLocaleString() || '0'}</p>
                <p className="text-xs text-gray-400 mt-1">from campaigns</p>
              </div>
              <DollarSign className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search campaigns..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="email">Email</SelectItem>
                <SelectItem value="sms">SMS</SelectItem>
                <SelectItem value="push">Push Notification</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Campaigns List */}
      <Card>
        <CardHeader>
          <CardTitle>Campaigns</CardTitle>
          <CardDescription>{filteredCampaigns?.length || 0} campaigns found</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredCampaigns?.map((campaign) => (
              <Card key={campaign.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded flex items-center justify-center text-white">
                        <Mail className="w-6 h-6" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium text-lg">{campaign.name}</h4>
                          {getStatusBadge(campaign.status)}
                          {getTypeBadge(campaign.type)}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{campaign.subject}</p>
                        <div className="grid grid-cols-4 gap-4 text-sm">
                          <div>
                            <p className="text-gray-600">Recipients</p>
                            <p className="font-medium">{campaign.recipients?.toLocaleString() || 0}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">Open Rate</p>
                            <p className="font-medium">{campaign.open_rate?.toFixed(1) || '0.0'}%</p>
                          </div>
                          <div>
                            <p className="text-gray-600">Click Rate</p>
                            <p className="font-medium">{campaign.click_rate?.toFixed(1) || '0.0'}%</p>
                          </div>
                          <div>
                            <p className="text-gray-600">Revenue</p>
                            <p className="font-medium">${campaign.revenue?.toLocaleString() || '0'}</p>
                          </div>
                        </div>
                        <p className="text-xs text-gray-400 mt-2">
                          {campaign.scheduled_at 
                            ? `Scheduled for ${new Date(campaign.scheduled_at).toLocaleString()}`
                            : campaign.sent_at 
                            ? `Sent on ${new Date(campaign.sent_at).toLocaleString()}`
                            : `Created on ${new Date(campaign.created_at).toLocaleString()}`
                          }
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-col space-y-2">
                      {campaign.status === 'active' && (
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handlePauseCampaign(campaign.id)}
                        >
                          <Pause className="w-4 h-4 mr-1" />
                          Pause
                        </Button>
                      )}
                      
                      {campaign.status === 'paused' && (
                        <Button 
                          size="sm"
                          onClick={() => handleResumeCampaign(campaign.id)}
                        >
                          <Play className="w-4 h-4 mr-1" />
                          Resume
                        </Button>
                      )}

                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => navigate(`/marketing/campaigns/${campaign.id}`)}
                      >
                        View Details
                      </Button>

                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => handleDuplicate(campaign.id)}
                      >
                        <Copy className="w-4 h-4 mr-1" />
                        Duplicate
                      </Button>

                      {campaign.status === 'draft' && (
                        <Button 
                          size="sm" 
                          variant="destructive"
                          onClick={() => handleDelete(campaign.id)}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Delete
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {(!filteredCampaigns || filteredCampaigns.length === 0) && (
              <div className="text-center py-12 text-gray-500">
                <Mail className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No campaigns found</p>
                <p className="text-sm mt-2">Create your first campaign to get started</p>
                <Button className="mt-4" onClick={() => navigate('/marketing/campaigns/new')}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Campaign
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CampaignManagement
