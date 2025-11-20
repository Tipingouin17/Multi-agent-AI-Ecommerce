import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, Filter, TrendingUp, DollarSign, Eye, MousePointer } from 'lucide-react'
import { apiService } from '../../lib/api'

const Campaigns = () => {
  const navigate = useNavigate()
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    fetchCampaigns()
  }, [statusFilter])

  const fetchCampaigns = async () => {
    try {
      setLoading(true)
      const params = {}
      if (statusFilter !== 'all') {
        params.status = statusFilter
      }
      const data = await apiService.getCampaigns(params)
      setCampaigns(data.campaigns || [])
    } catch (error) {
      console.error('Failed to fetch campaigns:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (campaignId) => {
    if (!confirm('Are you sure you want to delete this campaign?')) return
    
    try {
      await apiService.deleteCampaign(campaignId)
      fetchCampaigns()
    } catch (error) {
      console.error('Failed to delete campaign:', error)
      alert('Failed to delete campaign')
    }
  }

  const getStatusBadge = (status) => {
    const statusColors = {
      active: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-blue-100 text-blue-800',
      draft: 'bg-gray-100 text-gray-800'
    }
    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${statusColors[status] || statusColors.draft}`}>
        {status}
      </span>
    )
  }

  const getPlatformBadge = (platform) => {
    const platformColors = {
      google: 'bg-blue-100 text-blue-800',
      facebook: 'bg-indigo-100 text-indigo-800',
      instagram: 'bg-pink-100 text-pink-800',
      amazon: 'bg-orange-100 text-orange-800',
      tiktok: 'bg-gray-100 text-gray-800'
    }
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded ${platformColors[platform] || 'bg-gray-100 text-gray-800'}`}>
        {platform}
      </span>
    )
  }

  const filteredCampaigns = campaigns.filter(campaign =>
    campaign.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    campaign.platform.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Advertising Campaigns</h1>
          <p className="text-gray-600 mt-1">Manage your advertising campaigns across platforms</p>
        </div>
        <button
          onClick={() => navigate('/merchant/campaigns/new')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={20} />
          New Campaign
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Campaigns</p>
              <p className="text-2xl font-bold text-gray-900">
                {campaigns.filter(c => c.status === 'active').length}
              </p>
            </div>
            <TrendingUp className="text-green-500" size={24} />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Spend</p>
              <p className="text-2xl font-bold text-gray-900">
                ${campaigns.reduce((sum, c) => sum + (c.total_spent || 0), 0).toFixed(2)}
              </p>
            </div>
            <DollarSign className="text-blue-500" size={24} />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Impressions</p>
              <p className="text-2xl font-bold text-gray-900">
                {campaigns.reduce((sum, c) => sum + (c.impressions || 0), 0).toLocaleString()}
              </p>
            </div>
            <Eye className="text-purple-500" size={24} />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Clicks</p>
              <p className="text-2xl font-bold text-gray-900">
                {campaigns.reduce((sum, c) => sum + (c.clicks || 0), 0).toLocaleString()}
              </p>
            </div>
            <MousePointer className="text-orange-500" size={24} />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search campaigns..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="completed">Completed</option>
              <option value="draft">Draft</option>
            </select>
          </div>
        </div>
      </div>

      {/* Campaigns List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading campaigns...</p>
          </div>
        ) : filteredCampaigns.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-600">No campaigns found</p>
            <button
              onClick={() => navigate('/merchant/campaigns/new')}
              className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
            >
              Create your first campaign
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Campaign
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Platform
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Budget
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Spent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Performance
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredCampaigns.map((campaign) => (
                  <tr key={campaign.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{campaign.name}</div>
                        <div className="text-sm text-gray-500">ID: {campaign.id}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {getPlatformBadge(campaign.platform)}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(campaign.status)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      ${campaign.daily_budget ? `${campaign.daily_budget}/day` : `${campaign.total_budget} total`}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      ${(campaign.total_spent || 0).toFixed(2)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="text-gray-900">{(campaign.impressions || 0).toLocaleString()} impressions</div>
                        <div className="text-gray-500">{(campaign.clicks || 0).toLocaleString()} clicks ({campaign.ctr || 0}% CTR)</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right text-sm font-medium">
                      <button
                        onClick={() => navigate(`/merchant/campaigns/${campaign.id}`)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        View
                      </button>
                      <button
                        onClick={() => handleDelete(campaign.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default Campaigns
