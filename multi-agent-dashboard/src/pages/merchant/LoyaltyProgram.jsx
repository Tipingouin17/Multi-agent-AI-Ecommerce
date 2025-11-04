import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Label } from '@/components/ui/label'
import { 
  Gift, 
  Award,
  Star,
  TrendingUp,
  Users,
  DollarSign,
  Settings,
  Plus,
  Trash2
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Loyalty Program Management
 * 
 * Configure and manage loyalty program:
 * - Points earning rules
 * - Reward tiers
 * - Redemption options
 * - Member analytics
 * - Program settings
 */
const LoyaltyProgram = () => {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('overview')

  // Fetch loyalty program data
  const { data: program, isLoading } = useQuery({
    queryKey: ['loyalty-program'],
    queryFn: () => api.loyalty.getProgram()
  })

  // Fetch loyalty statistics
  const { data: stats } = useQuery({
    queryKey: ['loyalty-stats'],
    queryFn: () => api.loyalty.getStats()
  })

  // Update program settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: (settings) => api.loyalty.updateSettings(settings),
    onSuccess: () => {
      toast.success('Settings updated successfully')
      queryClient.invalidateQueries(['loyalty-program'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update settings')
    }
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading loyalty program...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Loyalty Program</h1>
          <p className="text-gray-600">Reward customers and build loyalty</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Program Status:</span>
          <Switch checked={program?.enabled} />
          <Badge variant={program?.enabled ? 'default' : 'secondary'}>
            {program?.enabled ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Members</p>
                <p className="text-2xl font-bold">{stats?.totalMembers?.toLocaleString() || '0'}</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-green-500" />
                  <span className="text-xs text-green-500">+{stats?.newMembersThisMonth || 0} this month</span>
                </div>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Points Issued</p>
                <p className="text-2xl font-bold">{stats?.pointsIssued?.toLocaleString() || '0'}</p>
                <p className="text-xs text-gray-400 mt-1">this month</p>
              </div>
              <Star className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Points Redeemed</p>
                <p className="text-2xl font-bold">{stats?.pointsRedeemed?.toLocaleString() || '0'}</p>
                <p className="text-xs text-gray-400 mt-1">this month</p>
              </div>
              <Gift className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Redemption Value</p>
                <p className="text-2xl font-bold">${stats?.redemptionValue?.toLocaleString() || '0'}</p>
                <p className="text-xs text-gray-400 mt-1">this month</p>
              </div>
              <DollarSign className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="earning">Earning Rules</TabsTrigger>
          <TabsTrigger value="tiers">Reward Tiers</TabsTrigger>
          <TabsTrigger value="rewards">Rewards</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview">
          <div className="grid grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Member Distribution by Tier</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {program?.tiers?.map((tier, index) => {
                    const percentage = stats?.totalMembers ? 
                      (tier.member_count / stats.totalMembers * 100) : 0
                    
                    return (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <Award className={`w-5 h-5 ${tier.color}`} />
                            <span className="font-medium">{tier.name}</span>
                          </div>
                          <span className="text-sm text-gray-600">
                            {tier.member_count} ({percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${tier.color.replace('text-', 'bg-')}`}
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Rewards</CardTitle>
                <CardDescription>Most redeemed rewards</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats?.topRewards?.map((reward, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-500 rounded flex items-center justify-center text-white font-bold">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium">{reward.name}</p>
                          <p className="text-sm text-gray-600">{reward.points} points</p>
                        </div>
                      </div>
                      <Badge>{reward.redemptions} redeemed</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {stats?.recentActivity?.map((activity, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border-b last:border-b-0">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        {activity.type === 'earned' ? (
                          <Star className="w-5 h-5 text-blue-600" />
                        ) : (
                          <Gift className="w-5 h-5 text-green-600" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium">{activity.customer_name}</p>
                        <p className="text-sm text-gray-600">{activity.description}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-medium ${activity.type === 'earned' ? 'text-blue-600' : 'text-green-600'}`}>
                        {activity.type === 'earned' ? '+' : '-'}{activity.points} points
                      </p>
                      <p className="text-xs text-gray-400">{activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Earning Rules */}
        <TabsContent value="earning">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Points Earning Rules</CardTitle>
                  <CardDescription>Configure how customers earn points</CardDescription>
                </div>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Rule
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {program?.earning_rules?.map((rule, index) => (
                  <Card key={index}>
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium">{rule.name}</h4>
                            <Switch checked={rule.enabled} />
                          </div>
                          <p className="text-sm text-gray-600 mb-3">{rule.description}</p>
                          <div className="flex items-center space-x-4 text-sm">
                            <Badge variant="outline">{rule.points} points</Badge>
                            <span className="text-gray-600">per {rule.unit}</span>
                          </div>
                        </div>
                        <Button size="sm" variant="ghost">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reward Tiers */}
        <TabsContent value="tiers">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Reward Tiers</CardTitle>
                  <CardDescription>Define membership tiers and benefits</CardDescription>
                </div>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Tier
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-6">
                {program?.tiers?.map((tier, index) => (
                  <Card key={index} className="hover:shadow-lg transition-shadow">
                    <CardContent className="pt-6">
                      <div className="text-center mb-4">
                        <Award className={`w-12 h-12 mx-auto mb-3 ${tier.color}`} />
                        <h3 className="text-xl font-bold mb-1">{tier.name}</h3>
                        <p className="text-sm text-gray-600">{tier.points_required} points required</p>
                      </div>
                      <div className="space-y-2 mb-4">
                        <p className="text-sm font-medium">Benefits:</p>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {tier.benefits?.map((benefit, i) => (
                            <li key={i} className="flex items-center space-x-2">
                              <Star className="w-3 h-3" />
                              <span>{benefit}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="pt-3 border-t">
                        <p className="text-sm text-gray-600">
                          {tier.member_count} members
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rewards */}
        <TabsContent value="rewards">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Available Rewards</CardTitle>
                  <CardDescription>Rewards customers can redeem</CardDescription>
                </div>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Reward
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-6">
                {program?.rewards?.map((reward, index) => (
                  <Card key={index} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="text-center mb-4">
                        <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-3">
                          <Gift className="w-8 h-8 text-white" />
                        </div>
                        <h4 className="font-medium mb-1">{reward.name}</h4>
                        <p className="text-sm text-gray-600 mb-3">{reward.description}</p>
                        <Badge className="text-lg">{reward.points} points</Badge>
                      </div>
                      <div className="flex items-center justify-between pt-3 border-t text-sm">
                        <span className="text-gray-600">{reward.redemptions} redeemed</span>
                        <Switch checked={reward.enabled} />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings */}
        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Program Settings</CardTitle>
              <CardDescription>Configure loyalty program parameters</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label>Program Name</Label>
                    <Input defaultValue={program?.name} />
                  </div>
                  <div className="space-y-2">
                    <Label>Points Currency Name</Label>
                    <Input defaultValue={program?.points_name} placeholder="Points" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label>Points Expiration (days)</Label>
                    <Input type="number" defaultValue={program?.points_expiration} />
                    <p className="text-sm text-gray-500">0 = never expires</p>
                  </div>
                  <div className="space-y-2">
                    <Label>Minimum Redemption Points</Label>
                    <Input type="number" defaultValue={program?.min_redemption} />
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Enable Birthday Bonus</p>
                      <p className="text-sm text-gray-600">Give bonus points on customer birthdays</p>
                    </div>
                    <Switch defaultChecked={program?.birthday_bonus_enabled} />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Enable Referral Rewards</p>
                      <p className="text-sm text-gray-600">Reward customers for referrals</p>
                    </div>
                    <Switch defaultChecked={program?.referral_rewards_enabled} />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Auto-enroll New Customers</p>
                      <p className="text-sm text-gray-600">Automatically add new customers to the program</p>
                    </div>
                    <Switch defaultChecked={program?.auto_enroll} />
                  </div>
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <Button variant="outline">Reset to Defaults</Button>
                  <Button>Save Changes</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default LoyaltyProgram
