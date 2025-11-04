import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Heart, ShoppingCart, Trash2, Share2 } from 'lucide-react'
import api from '@/lib/api-enhanced'

const Wishlist = () => {
  const queryClient = useQueryClient()

  const { data: wishlist, isLoading } = useQuery({
    queryKey: ['wishlist'],
    queryFn: () => api.wishlist.get()
  })

  const removeMutation = useMutation({
    mutationFn: (productId) => api.wishlist.remove(productId),
    onSuccess: () => {
      toast.success('Removed from wishlist')
      queryClient.invalidateQueries(['wishlist'])
    }
  })

  const addToCartMutation = useMutation({
    mutationFn: (productId) => api.cart.add({ productId, quantity: 1 }),
    onSuccess: () => {
      toast.success('Added to cart')
      queryClient.invalidateQueries(['cart'])
    }
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold">My Wishlist</h1>
            <p className="text-gray-600">{wishlist?.items?.length || 0} items</p>
          </div>
        </div>

        {wishlist?.items?.length > 0 ? (
          <div className="grid grid-cols-4 gap-6">
            {wishlist.items.map((item) => (
              <Card key={item.id}>
                <Link to={`/products/${item.product_id}`}>
                  <img src={item.image} alt={item.name} className="w-full h-48 object-cover rounded-t" />
                </Link>
                <CardContent className="pt-4">
                  <h3 className="font-medium mb-2">{item.name}</h3>
                  <span className="text-lg font-bold">${item.price.toFixed(2)}</span>
                  <Button className="w-full mt-2" size="sm" onClick={() => addToCartMutation.mutate(item.product_id)}>
                    Add to Cart
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <Heart className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">Your wishlist is empty</h3>
              <Link to="/products"><Button>Start Shopping</Button></Link>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

export default Wishlist
