import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Star } from 'lucide-react'
import api from '@/lib/api-enhanced'

const CustomerReviews = () => {
  const { data: reviews, isLoading } = useQuery({
    queryKey: ['my-reviews'],
    queryFn: () => api.reviews.getMyReviews()
  })

  if (isLoading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div></div>

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-6">My Reviews</h1>

        {reviews?.length > 0 ? (
          <div className="space-y-4">
            {reviews.map((review) => (
              <Card key={review.id}>
                <CardContent className="pt-6">
                  <div className="flex items-start space-x-4">
                    <img src={review.product_image} alt={review.product_name} className="w-20 h-20 object-cover rounded" />
                    <div className="flex-1">
                      <Link to={`/products/${review.product_id}`} className="font-medium hover:text-blue-600">
                        {review.product_name}
                      </Link>
                      <div className="flex items-center mt-1">
                        {[...Array(5)].map((_, i) => (
                          <Star key={i} className={`w-4 h-4 ${i < review.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`} />
                        ))}
                        <span className="ml-2 text-sm text-gray-600">{new Date(review.created_at).toLocaleDateString()}</span>
                      </div>
                      <p className="mt-2 text-gray-700">{review.comment}</p>
                      <div className="flex space-x-2 mt-3">
                        <Button size="sm" variant="outline">Edit</Button>
                        <Button size="sm" variant="outline">Delete</Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <h3 className="text-xl font-bold mb-2">No reviews yet</h3>
              <p className="text-gray-600 mb-4">Share your experience with products you've purchased</p>
              <Link to="/account/orders"><Button>View Orders</Button></Link>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

export default CustomerReviews
