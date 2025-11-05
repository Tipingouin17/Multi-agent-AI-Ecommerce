import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Users,
  MousePointer,
  RefreshCw,
  Download,
  ArrowUpRight,
  ArrowDownRight,
  Megaphone,
  Tag
} from 'lucide-react'
import api from '@/lib/api-enhanced'

const MarketingAnalyticsDashboard = () => {
  const [timeRange, setTimeRange] = useState('30d')
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Fetch marketing overview
  const { data: marketingOverview, isLoading: loadingOverview, refetch } = useQuery({
    queryKey: ['marketingOverview', timeRange],
    queryFn: () => api.analytics.getMarketingOverview({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch campaign performance
  const { data: campaigns, isLoading: loadingCampaigns } = useQuery({
    queryKey: ['campaignPerformance', timeRange],
    queryFn: () => api.analytics.getCampaignPerformance({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch traffic sources
  const { data: trafficSources, isLoading: loadingTraffic } = useQuery({
    queryKey: ['trafficSources', timeRange],
    queryFn: () => api.analytics.getTrafficSources({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch promotion effectiveness
  const { data: promotions, isLoading: loadingPromotions } = useQuery({
    queryKey: ['promotionEffectiveness', timeRange],
    queryFn: () => api.analytics.getPromotionEffectiveness({ timeRange }),
    refetchInterval: 60000,
  })

  // Fetch conversion by channel
  const { data: channelConversion, isLoading: loadingChannels } = useQuery({
    queryKey: ['channelConversion', timeRange],
    queryFn: () => api.analytics.getChannelConversion({ timeRange }),
    refetchInterval: 60000,
  })

  const handleRefresh = () => {
    refetch()
    setLastUpdated(new Date())
  }

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Format percentage
  const formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
  }

  // Get trend indicator
  const getTrendIndicator = (value) => {
    if (value > 0) {
      return {
        icon: <ArrowUpRight className="w-4 h-4" />,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
      }
    } else if (value < 0) {
      return {
        icon: <ArrowDownRight className="w-4 h-4" />,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
      }
    }
    return {
      icon: null,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
    }
  }

  // KPI Card Component
  const KPICard = ({ title, value, change, icon: Icon, loading }) => {
    const trend = getTrendIndicator(change)
    
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <div className="mt-2 flex items-baseline gap-2">
                <p className="text-3xl font-bold text-gray-900">
                  {loading ? '...' : value}
                </p>
                {change !== undefined && (
                  <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${trend.bgColor}`}>
                    {trend.icon}
                    <span className={`text-sm font-medium ${trend.color}`}>
                      {formatPercentage(change)}
                    </span>
                  </div>
                )}
              </div>
              <p className="mt-1 text-xs text-gray-500">vs. previous period</p>
            </div>
            <div className="ml-4">
              <div className="p-3 bg-purple-50 rounded-lg">
                <Icon className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Channel colors
  const CHANNEL_COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#6b7280']

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Marketing Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track campaign performance and optimize marketing spend
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-gray-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Time Range Selector */}
      <Tabs value={timeRange} onValueChange={setTimeRange}>
        <TabsList>
          <TabsTrigger value="7d">Last 7 Days</TabsTrigger>
          <TabsTrigger value="30d">Last 30 Days</TabsTrigger>
          <TabsTrigger value="90d">Last 90 Days</TabsTrigger>
          <TabsTrigger value="1y">Last Year</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Marketing Spend"
          value={formatCurrency(marketingOverview?.totalSpend || 0)}
          change={marketingOverview?.spendChange || 0}
          icon={DollarSign}
          loading={loadingOverview}
        />
        <KPICard
          title="ROAS"
          value={`${(marketingOverview?.roas || 0).toFixed(2)}x`}
          change={marketingOverview?.roasChange || 0}
          icon={TrendingUp}
          loading={loadingOverview}
        />
        <KPICard
          title="Conversions"
          value={marketingOverview?.conversions?.toLocaleString() || '0'}
          change={marketingOverview?.conversionsChange || 0}
          icon={Target}
          loading={loadingOverview}
        />
        <KPICard
          title="Cost per Acquisition"
          value={formatCurrency(marketingOverview?.cpa || 0)}
          change={marketingOverview?.cpaChange || 0}
          icon={Users}
          loading={loadingOverview}
        />
      </div>

      {/* Campaign Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Campaign Performance</CardTitle>
          <CardDescription>Active campaigns and their effectiveness</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingCampaigns ? (
            <div className="h-80 flex items-center justify-center">
              <div className="text-gray-500">Loading campaign data...</div>
            </div>
          ) : (
            <div className="space-y-4">
              {(campaigns || []).map((campaign, index) => (
                <div key={campaign.id} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <Megaphone className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{campaign.name}</h3>
                        <p className="text-sm text-gray-500">{campaign.channel}</p>
                      </div>
                    </div>
                    <Badge variant={campaign.status === 'active' ? 'default' : 'secondary'}>
                      {campaign.status}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-5 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Spend</p>
                      <p className="font-semibold text-gray-900">{formatCurrency(campaign.spend)}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Revenue</p>
                      <p className="font-semibold text-gray-900">{formatCurrency(campaign.revenue)}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">ROAS</p>
                      <p className={`font-semibold ${campaign.roas >= 3 ? 'text-green-600' : campaign.roas >= 2 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {campaign.roas.toFixed(2)}x
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Conversions</p>
                      <p className="font-semibold text-gray-900">{campaign.conversions}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">CPA</p>
                      <p className="font-semibold text-gray-900">{formatCurrency(campaign.cpa)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Traffic Sources */}
        <Card>
          <CardHeader>
            <CardTitle>Traffic Sources</CardTitle>
            <CardDescription>Where your visitors come from</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingTraffic ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <div className="space-y-4">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={trafficSources || []}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {(trafficSources || []).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={CHANNEL_COLORS[index % CHANNEL_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2">
                  {(trafficSources || []).map((source, index) => (
                    <div key={source.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: CHANNEL_COLORS[index % CHANNEL_COLORS.length] }}
                        />
                        <span className="text-sm font-medium text-gray-900">{source.name}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-gray-900">{source.value.toLocaleString()}</p>
                        <p className="text-xs text-gray-500">visitors</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Channel Conversion Rates */}
        <Card>
          <CardHeader>
            <CardTitle>Conversion by Channel</CardTitle>
            <CardDescription>Conversion rates across marketing channels</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingChannels ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={256}>
                <BarChart data={channelConversion || []} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    type="number"
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <YAxis 
                    type="category"
                    dataKey="channel"
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                    width={100}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }}
                    formatter={(value) => `${value.toFixed(2)}%`}
                  />
                  <Bar dataKey="conversionRate" fill="#8b5cf6" name="Conversion Rate" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Promotion Effectiveness */}
      <Card>
        <CardHeader>
          <CardTitle>Promotion Effectiveness</CardTitle>
          <CardDescription>Active promotions and their impact on sales</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingPromotions ? (
            <div className="h-64 flex items-center justify-center">
              <div className="text-gray-500">Loading data...</div>
            </div>
          ) : (
            <div className="space-y-4">
              {(promotions || []).map((promo) => (
                <div key={promo.id} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-orange-100 rounded-lg">
                        <Tag className="w-5 h-5 text-orange-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{promo.name}</h3>
                        <p className="text-sm text-gray-500">{promo.code}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant={promo.active ? 'default' : 'secondary'}>
                        {promo.active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Discount</p>
                      <p className="font-semibold text-gray-900">{promo.discount}%</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Uses</p>
                      <p className="font-semibold text-gray-900">{promo.uses}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Revenue</p>
                      <p className="font-semibold text-gray-900">{formatCurrency(promo.revenue)}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">ROI</p>
                      <p className={`font-semibold ${promo.roi >= 200 ? 'text-green-600' : promo.roi >= 100 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {promo.roi.toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Marketing Spend Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Marketing Spend vs Revenue</CardTitle>
          <CardDescription>Track ROI over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={256}>
            <AreaChart data={marketingOverview?.spendTrend || []}>
              <defs>
                <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis 
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
                formatter={(value) => formatCurrency(value)}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="spend"
                stroke="#ef4444"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorSpend)"
                name="Marketing Spend"
              />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#10b981"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorRevenue)"
                name="Revenue Generated"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Click-Through Rate</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {(marketingOverview?.ctr || 0).toFixed(2)}%
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {formatPercentage(marketingOverview?.ctrChange || 0)} vs. last period
                </p>
              </div>
              <MousePointer className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Email Open Rate</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {(marketingOverview?.emailOpenRate || 0).toFixed(1)}%
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {marketingOverview?.emailsSent?.toLocaleString() || 0} emails sent
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Social Engagement</p>
                <p className="mt-2 text-2xl font-bold text-gray-900">
                  {(marketingOverview?.socialEngagement || 0).toFixed(1)}%
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {marketingOverview?.socialReach?.toLocaleString() || 0} reach
                </p>
              </div>
              <Users className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Marketing Optimization</CardTitle>
          <CardDescription>Recommended actions to improve ROI</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline" className="justify-start">
              <Megaphone className="w-4 h-4 mr-2" />
              Create New Campaign
            </Button>
            <Button variant="outline" className="justify-start">
              <Tag className="w-4 h-4 mr-2" />
              Launch Promotion
            </Button>
            <Button variant="outline" className="justify-start">
              <Target className="w-4 h-4 mr-2" />
              Optimize Low-Performing Campaigns
            </Button>
            <Button variant="outline" className="justify-start">
              <TrendingUp className="w-4 h-4 mr-2" />
              Analyze Best Channels
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default MarketingAnalyticsDashboard
