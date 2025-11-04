import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { 
  User, 
  Mail,
  Phone,
  MapPin,
  ShoppingBag,
  DollarSign,
  Calendar,
  MessageSquare,
  Gift,
  Ban,
  ArrowLeft,
  Edit,
  Star,
  TrendingUp,
  Package
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Customer Profile Detail Page
 * 
 * Comprehensive customer profile with:
 * - Customer information
 * - Purchase history
 * - Lifetime value metrics
 * - Communication timeline
 * - Loyalty points
 * - Notes and tags
 * - Quick actions
 */
const CustomerProfile = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [noteText, setNoteText] = useState('')
  const [isAddingNote, setIsAddingNote] = useState(false)

  // Fetch customer details
  const { data: customer, isLoading } = useQuery({
    queryKey: ['customer', id],
    queryFn: () => api.customers.getCustomer(id)
  })

  // Fetch customer orders
  const { data: orders } = useQuery({
    queryKey: ['customer-orders', id],
    queryFn: () => api.customers.getCustomerOrders(id)
  })

  // Fetch customer communications
  const { data: communications } = useQuery({
    queryKey: ['customer-communications', id],
    queryFn: () => api.customers.getCustomerCommunications(id)
  })

  // Add note mutation
  const addNoteMutation = useMutation({
    mutationFn: (note) => api.customers.addNote(id, note),
    onSuccess: () => {
      toast.success('Note added successfully')
      queryClient.invalidateQueries(['customer-communications', id])
      setNoteText('')
      setIsAddingNote(false)
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to add note')
    }
  })

  // Send email mutation
  const sendEmailMutation = useMutation({
    mutationFn: () => api.customers.sendEmail(id),
    onSuccess: () => {
      toast.success('Email sent successfully')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to send email')
    }
  })

  const handleAddNote = () => {
    if (!noteText.trim()) {
      toast.error('Please enter a note')
      return
    }
    addNoteMutation.mutate(noteText)
  }

  const handleSendEmail = () => {
    sendEmailMutation.mutate()
  }

  const getOrderStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'secondary', label: 'Pending' },
      processing: { variant: 'default', label: 'Processing' },
      shipped: { variant: 'default', label: 'Shipped' },
      delivered: { variant: 'default', label: 'Delivered' },
      cancelled: { variant: 'destructive', label: 'Cancelled' }
    }

    const config = statusConfig[status] || statusConfig.pending
    
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading customer profile...</p>
        </div>
      </div>
    )
  }

  if (!customer) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <User className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-600">Customer not found</p>
          <Button className="mt-4" onClick={() => navigate('/customers')}>
            Back to Customers
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" onClick={() => navigate('/customers')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{customer.name}</h1>
            <p className="text-gray-600">{customer.email}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleSendEmail}>
            <Mail className="w-4 h-4 mr-2" />
            Send Email
          </Button>
          <Button variant="outline">
            <Edit className="w-4 h-4 mr-2" />
            Edit Profile
          </Button>
          <Button variant="destructive" size="sm">
            <Ban className="w-4 h-4 mr-2" />
            Ban Customer
          </Button>
        </div>
      </div>

      {/* Customer Info Cards */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Lifetime Value</p>
                <p className="text-2xl font-bold text-green-600">${customer.lifetime_value.toLocaleString()}</p>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Orders</p>
                <p className="text-2xl font-bold">{customer.total_orders}</p>
              </div>
              <ShoppingBag className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Order Value</p>
                <p className="text-2xl font-bold">${customer.avg_order_value.toFixed(2)}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Loyalty Points</p>
                <p className="text-2xl font-bold">{customer.loyalty_points || 0}</p>
              </div>
              <Gift className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Customer Details */}
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Customer Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-3">
              <User className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Full Name</p>
                <p className="font-medium">{customer.name}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Mail className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Email</p>
                <p className="font-medium">{customer.email}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Phone className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Phone</p>
                <p className="font-medium">{customer.phone || 'Not provided'}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <MapPin className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Location</p>
                <p className="font-medium">{customer.city}, {customer.state} {customer.zip}</p>
                <p className="text-sm text-gray-500">{customer.country}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Calendar className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Member Since</p>
                <p className="font-medium">{new Date(customer.created_at).toLocaleDateString()}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Star className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Segment</p>
                <Badge className="mt-1">{customer.segment}</Badge>
              </div>
            </div>

            {customer.tags && customer.tags.length > 0 && (
              <div>
                <p className="text-sm text-gray-600 mb-2">Tags</p>
                <div className="flex flex-wrap gap-2">
                  {customer.tags.map((tag, index) => (
                    <Badge key={index} variant="outline">{tag}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Main Content */}
        <div className="col-span-2">
          <Tabs defaultValue="orders" className="space-y-6">
            <TabsList>
              <TabsTrigger value="orders">Order History</TabsTrigger>
              <TabsTrigger value="communications">Communications</TabsTrigger>
              <TabsTrigger value="addresses">Addresses</TabsTrigger>
            </TabsList>

            {/* Order History */}
            <TabsContent value="orders">
              <Card>
                <CardHeader>
                  <CardTitle>Purchase History</CardTitle>
                  <CardDescription>{orders?.length || 0} orders</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {orders?.map((order) => (
                      <Card key={order.id} className="hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => navigate(`/orders/${order.id}`)}>
                        <CardContent className="pt-6">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-4">
                              <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center">
                                <Package className="w-6 h-6 text-gray-400" />
                              </div>
                              <div>
                                <div className="flex items-center space-x-2 mb-2">
                                  <h4 className="font-medium">Order #{order.order_number}</h4>
                                  {getOrderStatusBadge(order.status)}
                                </div>
                                <p className="text-sm text-gray-600 mb-1">
                                  {order.items_count} items
                                </p>
                                <p className="text-xs text-gray-400">
                                  {new Date(order.created_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-bold">${order.total.toFixed(2)}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}

                    {(!orders || orders.length === 0) && (
                      <div className="text-center py-12 text-gray-500">
                        <ShoppingBag className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                        <p>No orders yet</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Communications */}
            <TabsContent value="communications">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Communication Timeline</CardTitle>
                      <CardDescription>Notes, emails, and interactions</CardDescription>
                    </div>
                    <Dialog open={isAddingNote} onOpenChange={setIsAddingNote}>
                      <DialogTrigger asChild>
                        <Button size="sm">
                          <MessageSquare className="w-4 h-4 mr-2" />
                          Add Note
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Add Customer Note</DialogTitle>
                          <DialogDescription>
                            Add a note about this customer
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div className="space-y-2">
                            <Label>Note</Label>
                            <Textarea
                              value={noteText}
                              onChange={(e) => setNoteText(e.target.value)}
                              placeholder="Enter your note here..."
                              rows={4}
                            />
                          </div>
                          <div className="flex justify-end space-x-2">
                            <Button variant="outline" onClick={() => setIsAddingNote(false)}>
                              Cancel
                            </Button>
                            <Button 
                              onClick={handleAddNote}
                              disabled={addNoteMutation.isPending}
                            >
                              {addNoteMutation.isPending ? 'Adding...' : 'Add Note'}
                            </Button>
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {communications?.map((comm, index) => (
                      <div key={index} className="flex items-start space-x-4 pb-4 border-b last:border-b-0">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <MessageSquare className="w-5 h-5 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <p className="font-medium">{comm.type}</p>
                            <Badge variant="outline" className="text-xs">{comm.channel}</Badge>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{comm.message}</p>
                          <p className="text-xs text-gray-400">
                            {comm.author} • {new Date(comm.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}

                    {(!communications || communications.length === 0) && (
                      <div className="text-center py-12 text-gray-500">
                        <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                        <p>No communications yet</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Addresses */}
            <TabsContent value="addresses">
              <Card>
                <CardHeader>
                  <CardTitle>Saved Addresses</CardTitle>
                  <CardDescription>Customer shipping and billing addresses</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {customer.addresses?.map((address, index) => (
                      <Card key={index}>
                        <CardContent className="pt-6">
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center space-x-2 mb-2">
                                <MapPin className="w-4 h-4 text-gray-400" />
                                <h4 className="font-medium">{address.type}</h4>
                                {address.is_default && <Badge variant="default">Default</Badge>}
                              </div>
                              <p className="text-sm text-gray-600">{address.street}</p>
                              <p className="text-sm text-gray-600">
                                {address.city}, {address.state} {address.zip}
                              </p>
                              <p className="text-sm text-gray-600">{address.country}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}

                    {(!customer.addresses || customer.addresses.length === 0) && (
                      <div className="text-center py-12 text-gray-500">
                        <MapPin className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                        <p>No saved addresses</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}

export default CustomerProfile
