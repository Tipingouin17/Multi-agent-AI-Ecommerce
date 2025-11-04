import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tantml:invoke>
<parameter name="toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Store, 
  Globe,
  Mail,
  Phone,
  MapPin,
  Upload,
  Save,
  AlertCircle
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Store Settings (General)
 * 
 * Configure basic store information:
 * - Store identity (name, logo, tagline)
 * - Contact information
 * - Regional settings (currency, timezone, language)
 * - Store status
 * - SEO settings
 * - Social media links
 */
const StoreSettings = () => {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('general')
  const [logoFile, setLogoFile] = useState(null)
  const [logoPreview, setLogoPreview] = useState(null)

  // Fetch store settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ['store-settings'],
    queryFn: () => api.settings.getGeneral()
  })

  const [formData, setFormData] = useState(settings || {
    store_name: '',
    tagline: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    currency: 'USD',
    timezone: 'America/New_York',
    language: 'en',
    store_status: 'active',
    meta_description: '',
    facebook_url: '',
    twitter_url: '',
    instagram_url: '',
    linkedin_url: ''
  })

  // Update settings mutation
  const updateMutation = useMutation({
    mutationFn: (data) => api.settings.updateGeneral(data),
    onSuccess: () => {
      toast.success('Settings saved successfully')
      queryClient.invalidateQueries(['store-settings'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to save settings')
    }
  })

  // Upload logo mutation
  const uploadLogoMutation = useMutation({
    mutationFn: (file) => api.settings.uploadLogo(file),
    onSuccess: (data) => {
      toast.success('Logo uploaded successfully')
      queryClient.invalidateQueries(['store-settings'])
      setLogoFile(null)
      setLogoPreview(null)
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to upload logo')
    }
  })

  const handleLogoChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setLogoFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setLogoPreview(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleLogoUpload = () => {
    if (logoFile) {
      uploadLogoMutation.mutate(logoFile)
    }
  }

  const handleSave = () => {
    updateMutation.mutate(formData)
  }

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Store Settings</h1>
          <p className="text-gray-600">Configure your store information and preferences</p>
        </div>
        <Button onClick={handleSave} disabled={updateMutation.isPending}>
          <Save className="w-4 h-4 mr-2" />
          {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="contact">Contact</TabsTrigger>
          <TabsTrigger value="regional">Regional</TabsTrigger>
          <TabsTrigger value="seo">SEO & Social</TabsTrigger>
        </TabsList>

        {/* General Tab */}
        <TabsContent value="general">
          <div className="grid grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Store Identity</CardTitle>
                <CardDescription>Basic information about your store</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Store Name *</Label>
                  <Input
                    value={formData.store_name}
                    onChange={(e) => handleChange('store_name', e.target.value)}
                    placeholder="My Awesome Store"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Tagline</Label>
                  <Input
                    value={formData.tagline}
                    onChange={(e) => handleChange('tagline', e.target.value)}
                    placeholder="Quality products at great prices"
                  />
                  <p className="text-sm text-gray-500">A short description of your store</p>
                </div>

                <div className="space-y-2">
                  <Label>Store Status</Label>
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="font-medium">Store Active</p>
                      <p className="text-sm text-gray-600">
                        {formData.store_status === 'active' 
                          ? 'Your store is live and accepting orders' 
                          : 'Your store is in maintenance mode'}
                      </p>
                    </div>
                    <Switch 
                      checked={formData.store_status === 'active'}
                      onCheckedChange={(checked) => 
                        handleChange('store_status', checked ? 'active' : 'maintenance')
                      }
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Store Logo</CardTitle>
                <CardDescription>Upload your store logo</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-center w-full">
                  <label className="flex flex-col items-center justify-center w-full h-48 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                    {logoPreview || settings?.logo_url ? (
                      <img 
                        src={logoPreview || settings?.logo_url} 
                        alt="Logo preview" 
                        className="max-h-40 object-contain"
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <Upload className="w-10 h-10 mb-3 text-gray-400" />
                        <p className="mb-2 text-sm text-gray-500">
                          <span className="font-semibold">Click to upload</span> or drag and drop
                        </p>
                        <p className="text-xs text-gray-500">PNG, JPG or SVG (MAX. 2MB)</p>
                      </div>
                    )}
                    <input 
                      type="file" 
                      className="hidden" 
                      accept="image/*"
                      onChange={handleLogoChange}
                    />
                  </label>
                </div>

                {logoFile && (
                  <div className="flex space-x-2">
                    <Button onClick={handleLogoUpload} className="flex-1">
                      Upload Logo
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setLogoFile(null)
                        setLogoPreview(null)
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                )}

                {settings?.logo_url && !logoFile && (
                  <Button variant="outline" className="w-full">
                    Remove Current Logo
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Contact Tab */}
        <TabsContent value="contact">
          <Card>
            <CardHeader>
              <CardTitle>Contact Information</CardTitle>
              <CardDescription>How customers can reach you</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Email Address *</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleChange('email', e.target.value)}
                      placeholder="hello@mystore.com"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Phone Number</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => handleChange('phone', e.target.value)}
                      placeholder="+1 (555) 123-4567"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="col-span-2 space-y-2">
                  <Label>Street Address</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      value={formData.address}
                      onChange={(e) => handleChange('address', e.target.value)}
                      placeholder="123 Main Street"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>City</Label>
                  <Input
                    value={formData.city}
                    onChange={(e) => handleChange('city', e.target.value)}
                    placeholder="New York"
                  />
                </div>

                <div className="space-y-2">
                  <Label>State/Province</Label>
                  <Input
                    value={formData.state}
                    onChange={(e) => handleChange('state', e.target.value)}
                    placeholder="NY"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Postal Code</Label>
                  <Input
                    value={formData.postal_code}
                    onChange={(e) => handleChange('postal_code', e.target.value)}
                    placeholder="10001"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Country</Label>
                  <Select value={formData.country} onValueChange={(value) => handleChange('country', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select country" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="US">United States</SelectItem>
                      <SelectItem value="CA">Canada</SelectItem>
                      <SelectItem value="GB">United Kingdom</SelectItem>
                      <SelectItem value="AU">Australia</SelectItem>
                      <SelectItem value="DE">Germany</SelectItem>
                      <SelectItem value="FR">France</SelectItem>
                      <SelectItem value="ES">Spain</SelectItem>
                      <SelectItem value="IT">Italy</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Regional Tab */}
        <TabsContent value="regional">
          <Card>
            <CardHeader>
              <CardTitle>Regional Settings</CardTitle>
              <CardDescription>Configure currency, timezone, and language</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Currency *</Label>
                  <Select value={formData.currency} onValueChange={(value) => handleChange('currency', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="USD">USD - US Dollar</SelectItem>
                      <SelectItem value="EUR">EUR - Euro</SelectItem>
                      <SelectItem value="GBP">GBP - British Pound</SelectItem>
                      <SelectItem value="CAD">CAD - Canadian Dollar</SelectItem>
                      <SelectItem value="AUD">AUD - Australian Dollar</SelectItem>
                      <SelectItem value="JPY">JPY - Japanese Yen</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-gray-500">Default currency for your store</p>
                </div>

                <div className="space-y-2">
                  <Label>Timezone *</Label>
                  <Select value={formData.timezone} onValueChange={(value) => handleChange('timezone', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="America/New_York">Eastern Time (ET)</SelectItem>
                      <SelectItem value="America/Chicago">Central Time (CT)</SelectItem>
                      <SelectItem value="America/Denver">Mountain Time (MT)</SelectItem>
                      <SelectItem value="America/Los_Angeles">Pacific Time (PT)</SelectItem>
                      <SelectItem value="Europe/London">London (GMT)</SelectItem>
                      <SelectItem value="Europe/Paris">Paris (CET)</SelectItem>
                      <SelectItem value="Asia/Tokyo">Tokyo (JST)</SelectItem>
                      <SelectItem value="Australia/Sydney">Sydney (AEST)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-gray-500">Used for order timestamps and scheduling</p>
                </div>

                <div className="space-y-2">
                  <Label>Language *</Label>
                  <Select value={formData.language} onValueChange={(value) => handleChange('language', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                      <SelectItem value="it">Italian</SelectItem>
                      <SelectItem value="pt">Portuguese</SelectItem>
                      <SelectItem value="ja">Japanese</SelectItem>
                      <SelectItem value="zh">Chinese</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-gray-500">Default language for your store</p>
                </div>

                <div className="col-span-2 p-4 bg-blue-50 border border-blue-200 rounded flex items-start space-x-3">
                  <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-blue-900">Regional Settings Impact</p>
                    <p className="text-sm text-blue-800 mt-1">
                      Changing these settings will affect how prices, dates, and times are displayed 
                      throughout your store. Existing orders will not be affected.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SEO & Social Tab */}
        <TabsContent value="seo">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>SEO Settings</CardTitle>
                <CardDescription>Optimize your store for search engines</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Meta Description</Label>
                  <Textarea
                    value={formData.meta_description}
                    onChange={(e) => handleChange('meta_description', e.target.value)}
                    placeholder="A brief description of your store for search engines"
                    rows={3}
                    maxLength={160}
                  />
                  <p className="text-sm text-gray-500">
                    {formData.meta_description?.length || 0}/160 characters
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Social Media Links</CardTitle>
                <CardDescription>Connect your social media profiles</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Facebook</Label>
                    <div className="relative">
                      <Globe className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        value={formData.facebook_url}
                        onChange={(e) => handleChange('facebook_url', e.target.value)}
                        placeholder="https://facebook.com/yourstore"
                        className="pl-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Twitter</Label>
                    <div className="relative">
                      <Globe className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        value={formData.twitter_url}
                        onChange={(e) => handleChange('twitter_url', e.target.value)}
                        placeholder="https://twitter.com/yourstore"
                        className="pl-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Instagram</Label>
                    <div className="relative">
                      <Globe className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        value={formData.instagram_url}
                        onChange={(e) => handleChange('instagram_url', e.target.value)}
                        placeholder="https://instagram.com/yourstore"
                        className="pl-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>LinkedIn</Label>
                    <div className="relative">
                      <Globe className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        value={formData.linkedin_url}
                        onChange={(e) => handleChange('linkedin_url', e.target.value)}
                        placeholder="https://linkedin.com/company/yourstore"
                        className="pl-10"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Save Button (Footer) */}
      <div className="flex justify-end pt-4 border-t">
        <Button onClick={handleSave} disabled={updateMutation.isPending} size="lg">
          <Save className="w-4 h-4 mr-2" />
          {updateMutation.isPending ? 'Saving Changes...' : 'Save All Changes'}
        </Button>
      </div>
    </div>
  )
}

export default StoreSettings
