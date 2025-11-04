import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import api from '@/lib/api-enhanced'

const AccountSettings = () => {
  const queryClient = useQueryClient()
  
  const { data: user } = useQuery({
    queryKey: ['user'],
    queryFn: () => api.user.getProfile()
  })

  const [profile, setProfile] = useState({
    firstName: user?.first_name || '',
    lastName: user?.last_name || '',
    email: user?.email || '',
    phone: user?.phone || ''
  })

  const [password, setPassword] = useState({
    current: '',
    new: '',
    confirm: ''
  })

  const [preferences, setPreferences] = useState({
    emailNotifications: user?.preferences?.email_notifications ?? true,
    smsNotifications: user?.preferences?.sms_notifications ?? false,
    promotionalEmails: user?.preferences?.promotional_emails ?? true,
    orderUpdates: user?.preferences?.order_updates ?? true
  })

  const updateProfileMutation = useMutation({
    mutationFn: (data) => api.user.updateProfile(data),
    onSuccess: () => {
      toast.success('Profile updated successfully')
      queryClient.invalidateQueries(['user'])
    }
  })

  const updatePasswordMutation = useMutation({
    mutationFn: (data) => api.user.updatePassword(data),
    onSuccess: () => {
      toast.success('Password updated successfully')
      setPassword({ current: '', new: '', confirm: '' })
    },
    onError: () => {
      toast.error('Failed to update password')
    }
  })

  const updatePreferencesMutation = useMutation({
    mutationFn: (data) => api.user.updatePreferences(data),
    onSuccess: () => {
      toast.success('Preferences updated successfully')
    }
  })

  const handleProfileSubmit = (e) => {
    e.preventDefault()
    updateProfileMutation.mutate(profile)
  }

  const handlePasswordSubmit = (e) => {
    e.preventDefault()
    if (password.new !== password.confirm) {
      toast.error('Passwords do not match')
      return
    }
    if (password.new.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }
    updatePasswordMutation.mutate(password)
  }

  const handlePreferencesSubmit = (e) => {
    e.preventDefault()
    updatePreferencesMutation.mutate(preferences)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-6">Account Settings</h1>

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
            <TabsTrigger value="preferences">Preferences</TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleProfileSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>First Name</Label>
                      <Input 
                        value={profile.firstName}
                        onChange={(e) => setProfile({...profile, firstName: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Last Name</Label>
                      <Input 
                        value={profile.lastName}
                        onChange={(e) => setProfile({...profile, lastName: e.target.value})}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Email</Label>
                    <Input 
                      type="email"
                      value={profile.email}
                      onChange={(e) => setProfile({...profile, email: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Phone</Label>
                    <Input 
                      type="tel"
                      value={profile.phone}
                      onChange={(e) => setProfile({...profile, phone: e.target.value})}
                    />
                  </div>
                  <Button type="submit" disabled={updateProfileMutation.isPending}>
                    {updateProfileMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security">
            <Card>
              <CardHeader>
                <CardTitle>Change Password</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePasswordSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label>Current Password</Label>
                    <Input 
                      type="password"
                      value={password.current}
                      onChange={(e) => setPassword({...password, current: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>New Password</Label>
                    <Input 
                      type="password"
                      value={password.new}
                      onChange={(e) => setPassword({...password, new: e.target.value})}
                    />
                    <p className="text-sm text-gray-600">Must be at least 8 characters</p>
                  </div>
                  <div className="space-y-2">
                    <Label>Confirm New Password</Label>
                    <Input 
                      type="password"
                      value={password.confirm}
                      onChange={(e) => setPassword({...password, confirm: e.target.value})}
                    />
                  </div>
                  <Button type="submit" disabled={updatePasswordMutation.isPending}>
                    {updatePasswordMutation.isPending ? 'Updating...' : 'Update Password'}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="text-red-600">Danger Zone</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">Once you delete your account, there is no going back. Please be certain.</p>
                <Button variant="destructive">Delete Account</Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Preferences Tab */}
          <TabsContent value="preferences">
            <Card>
              <CardHeader>
                <CardTitle>Communication Preferences</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePreferencesSubmit} className="space-y-4">
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox 
                        id="emailNotifications"
                        checked={preferences.emailNotifications}
                        onCheckedChange={(checked) => setPreferences({...preferences, emailNotifications: checked})}
                      />
                      <Label htmlFor="emailNotifications" className="cursor-pointer">
                        <div>
                          <p className="font-medium">Email Notifications</p>
                          <p className="text-sm text-gray-600">Receive email notifications about your account</p>
                        </div>
                      </Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox 
                        id="smsNotifications"
                        checked={preferences.smsNotifications}
                        onCheckedChange={(checked) => setPreferences({...preferences, smsNotifications: checked})}
                      />
                      <Label htmlFor="smsNotifications" className="cursor-pointer">
                        <div>
                          <p className="font-medium">SMS Notifications</p>
                          <p className="text-sm text-gray-600">Receive text messages about your orders</p>
                        </div>
                      </Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox 
                        id="promotionalEmails"
                        checked={preferences.promotionalEmails}
                        onCheckedChange={(checked) => setPreferences({...preferences, promotionalEmails: checked})}
                      />
                      <Label htmlFor="promotionalEmails" className="cursor-pointer">
                        <div>
                          <p className="font-medium">Promotional Emails</p>
                          <p className="text-sm text-gray-600">Receive emails about sales and special offers</p>
                        </div>
                      </Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox 
                        id="orderUpdates"
                        checked={preferences.orderUpdates}
                        onCheckedChange={(checked) => setPreferences({...preferences, orderUpdates: checked})}
                      />
                      <Label htmlFor="orderUpdates" className="cursor-pointer">
                        <div>
                          <p className="font-medium">Order Updates</p>
                          <p className="text-sm text-gray-600">Receive updates about your order status</p>
                        </div>
                      </Label>
                    </div>
                  </div>

                  <Button type="submit" disabled={updatePreferencesMutation.isPending}>
                    {updatePreferencesMutation.isPending ? 'Saving...' : 'Save Preferences'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default AccountSettings
