import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Plus, Edit, Trash2, MapPin } from 'lucide-react'
import api from '@/lib/api-enhanced'

const AddressBook = () => {
  const queryClient = useQueryClient()
  const [isAdding, setIsAdding] = useState(false)
  const [editingAddress, setEditingAddress] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    address1: '',
    address2: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'US',
    isDefault: false
  })

  const { data: addresses, isLoading } = useQuery({
    queryKey: ['addresses'],
    queryFn: () => api.user.getAddresses()
  })

  const addMutation = useMutation({
    mutationFn: (data) => api.user.addAddress(data),
    onSuccess: () => {
      toast.success('Address added successfully')
      queryClient.invalidateQueries(['addresses'])
      setIsAdding(false)
      resetForm()
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => api.user.updateAddress(id, data),
    onSuccess: () => {
      toast.success('Address updated successfully')
      queryClient.invalidateQueries(['addresses'])
      setEditingAddress(null)
      resetForm()
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.user.deleteAddress(id),
    onSuccess: () => {
      toast.success('Address deleted successfully')
      queryClient.invalidateQueries(['addresses'])
    }
  })

  const setDefaultMutation = useMutation({
    mutationFn: (id) => api.user.setDefaultAddress(id),
    onSuccess: () => {
      toast.success('Default address updated')
      queryClient.invalidateQueries(['addresses'])
    }
  })

  const resetForm = () => {
    setFormData({
      name: '',
      address1: '',
      address2: '',
      city: '',
      state: '',
      zipCode: '',
      country: 'US',
      isDefault: false
    })
  }

  const handleEdit = (address) => {
    setEditingAddress(address)
    setFormData(address)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (editingAddress) {
      updateMutation.mutate({ id: editingAddress.id, data: formData })
    } else {
      addMutation.mutate(formData)
    }
  }

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">Address Book</h1>
          <Dialog open={isAdding} onOpenChange={setIsAdding}>
            <DialogTrigger asChild>
              <Button><Plus className="w-4 h-4 mr-2" />Add New Address</Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>{editingAddress ? 'Edit Address' : 'Add New Address'}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label>Address Line 1</Label>
                  <Input value={formData.address1} onChange={(e) => setFormData({...formData, address1: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label>Address Line 2</Label>
                  <Input value={formData.address2} onChange={(e) => setFormData({...formData, address2: e.target.value})} />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>City</Label>
                    <Input value={formData.city} onChange={(e) => setFormData({...formData, city: e.target.value})} required />
                  </div>
                  <div className="space-y-2">
                    <Label>State</Label>
                    <Input value={formData.state} onChange={(e) => setFormData({...formData, state: e.target.value})} required />
                  </div>
                  <div className="space-y-2">
                    <Label>ZIP Code</Label>
                    <Input value={formData.zipCode} onChange={(e) => setFormData({...formData, zipCode: e.target.value})} required />
                  </div>
                </div>
                <div className="flex justify-end space-x-2">
                  <Button type="button" variant="outline" onClick={() => { setIsAdding(false); setEditingAddress(null); resetForm(); }}>
                    Cancel
                  </Button>
                  <Button type="submit">{editingAddress ? 'Update' : 'Add'} Address</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {addresses?.map((address) => (
            <Card key={address.id} className={address.isDefault ? 'border-2 border-blue-500' : ''}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <MapPin className="w-5 h-5 text-gray-600" />
                    <CardTitle className="text-lg">{address.name}</CardTitle>
                  </div>
                  {address.isDefault && (
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                      Default
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700">{address.address1}</p>
                {address.address2 && <p className="text-gray-700">{address.address2}</p>}
                <p className="text-gray-700">{address.city}, {address.state} {address.zipCode}</p>
                <p className="text-gray-700">{address.country}</p>

                <div className="flex items-center space-x-2 mt-4">
                  {!address.isDefault && (
                    <Button size="sm" variant="outline" onClick={() => setDefaultMutation.mutate(address.id)}>
                      Set as Default
                    </Button>
                  )}
                  <Button size="sm" variant="outline" onClick={() => { handleEdit(address); setIsAdding(true); }}>
                    <Edit className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => deleteMutation.mutate(address.id)}>
                    <Trash2 className="w-4 h-4 mr-1 text-red-500" />
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {addresses?.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <MapPin className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">No addresses saved</h3>
              <p className="text-gray-600 mb-4">Add an address to make checkout faster</p>
              <Button onClick={() => setIsAdding(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Address
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

export default AddressBook
