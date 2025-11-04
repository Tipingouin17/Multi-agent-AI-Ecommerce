import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { 
  Star, 
  ThumbsUp,
  MessageSquare,
  CheckCircle,
  XCircle,
  Flag,
  Search,
  TrendingUp,
  Award,
  AlertTriangle
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Review & Rating Management Page
 * 
 * Manage customer reviews with:
 * - Review moderation
 * - Merchant responses
 * - Feature reviews
 * - Flag inappropriate content
 * - Review analytics
 * - Request reviews
 */
const ReviewManagement = () => {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [ratingFilter, setRatingFilter] = useState('all')
  const [selectedReview, setSelectedReview] = useState(null)
  const [responseText, setResponseText] = useState('')

  // Fetch reviews
  const { data: reviews, isLoading } = useQuery({
    queryKey: ['reviews', statusFilter, ratingFilter, searchTerm],
    queryFn: () => api.reviews.getReviews({ 
      status: statusFilter, 
      rating: ratingFilter,
      search: searchTerm 
    })
  })

  // Fetch review statistics
  const { data: stats } = useQuery({
    queryKey: ['review-stats'],
    queryFn: () => api.reviews.getStats()
  })

  // Update review status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ reviewId, status }) => 
      api.reviews.updateStatus(reviewId, status),
    onSuccess: () => {
      toast.success('Review status updated')
      queryClient.invalidateQueries(['reviews'])
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update review status')
    }
  })

  // Add merchant response mutation
  const addResponseMutation = useMutation({
    mutationFn: ({ reviewId, response }) => 
      api.reviews.addResponse(reviewId, response),
    onSuccess: () => {
      toast.success('Response added successfully')
      queryClient.invalidateQueries(['reviews'])
      setSelectedReview(null)
      setResponseText('')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to add response')
    }
  })

  // Request review mutation
  const requestReviewMutation = useMutation({
    mutationFn: (customerId) => api.reviews.requestReview(customerId),
    onSuccess: () => {
      toast.success('Review request sent')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to send review request')
    }
  })

  const handleApprove = (reviewId) => {
    updateStatusMutation.mutate({ reviewId, status: 'approved' })
  }

  const handleReject = (reviewId) => {
    updateStatusMutation.mutate({ reviewId, status: 'rejected' })
  }

  const handleFlag = (reviewId) => {
    updateStatusMutation.mutate({ reviewId, status: 'flagged' })
  }

  const handleFeature = (reviewId) => {
    updateStatusMutation.mutate({ reviewId, status: 'featured' })
  }

  const handleAddResponse = () => {
    if (!responseText.trim()) {
      toast.error('Please enter a response')
      return
    }
    addResponseMutation.mutate({ 
      reviewId: selectedReview.id, 
      response: responseText 
    })
  }

  const renderStars = (rating) => {
    return (
      <div className="flex items-center space-x-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`w-4 h-4 ${
              star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
            }`}
          />
        ))}
      </div>
    )
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'secondary', icon: AlertTriangle, label: 'Pending' },
      approved: { variant: 'default', icon: CheckCircle, label: 'Approved' },
      rejected: { variant: 'destructive', icon: XCircle, label: 'Rejected' },
      flagged: { variant: 'destructive', icon: Flag, label: 'Flagged' },
      featured: { variant: 'default', icon: Award, label: 'Featured' }
    }

    const config = statusConfig[status] || statusConfig.pending
    const Icon = config.icon

    return (
      <Badge variant={config.variant} className="flex items-center space-x-1">
        <Icon className="w-3 h-3" />
        <span>{config.label}</span>
      </Badge>
    )
  }

  const filteredReviews = reviews?.filter(review => {
    if (statusFilter !== 'all' && review.status !== statusFilter) return false
    if (ratingFilter !== 'all' && review.rating !== parseInt(ratingFilter)) return false
    if (searchTerm && !review.product_name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !review.customer_name.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading reviews...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Reviews & Ratings</h1>
          <p className="text-gray-600">Manage customer reviews and feedback</p>
        </div>
        <Button variant="outline">
          <MessageSquare className="w-4 h-4 mr-2" />
          Request Reviews
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Average Rating</p>
                <div className="flex items-center space-x-2 mt-1">
                  <p className="text-2xl font-bold">{stats?.avgRating?.toFixed(1) || '0.0'}</p>
                  {renderStars(Math.round(stats?.avgRating || 0))}
                </div>
              </div>
              <Star className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Reviews</p>
                <p className="text-2xl font-bold">{stats?.totalReviews?.toLocaleString() || '0'}</p>
                <div className="flex items-center space-x-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-green-500" />
                  <span className="text-xs text-green-500">+{stats?.newReviewsThisMonth || 0} this month</span>
                </div>
              </div>
              <MessageSquare className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending Review</p>
                <p className="text-2xl font-bold text-orange-600">
                  {stats?.pendingReviews || 0}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Response Rate</p>
                <p className="text-2xl font-bold">{stats?.responseRate?.toFixed(1) || '0.0'}%</p>
              </div>
              <ThumbsUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Rating Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Rating Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[5, 4, 3, 2, 1].map((rating) => {
              const count = stats?.ratingDistribution?.[rating] || 0
              const percentage = stats?.totalReviews ? (count / stats.totalReviews * 100) : 0
              
              return (
                <div key={rating} className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1 w-20">
                    <span className="text-sm font-medium">{rating}</span>
                    <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  </div>
                  <div className="flex-1">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-yellow-400 h-2 rounded-full" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                  <span className="text-sm text-gray-600 w-16 text-right">
                    {count} ({percentage.toFixed(0)}%)
                  </span>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search by product or customer..."
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
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="flagged">Flagged</SelectItem>
                <SelectItem value="featured">Featured</SelectItem>
              </SelectContent>
            </Select>
            <Select value={ratingFilter} onValueChange={setRatingFilter}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Ratings</SelectItem>
                <SelectItem value="5">5 Stars</SelectItem>
                <SelectItem value="4">4 Stars</SelectItem>
                <SelectItem value="3">3 Stars</SelectItem>
                <SelectItem value="2">2 Stars</SelectItem>
                <SelectItem value="1">1 Star</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Reviews List */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Reviews</CardTitle>
          <CardDescription>{filteredReviews?.length || 0} reviews found</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredReviews?.map((review) => (
              <Card key={review.id}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                        {review.customer_name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium">{review.customer_name}</h4>
                          {getStatusBadge(review.status)}
                          {review.verified_purchase && (
                            <Badge variant="outline" className="text-xs">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Verified Purchase
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center space-x-2 mb-2">
                          {renderStars(review.rating)}
                          <span className="text-sm text-gray-600">
                            {new Date(review.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-sm font-medium text-gray-700 mb-2">{review.product_name}</p>
                        {review.title && (
                          <p className="font-medium mb-1">{review.title}</p>
                        )}
                        <p className="text-sm text-gray-600 mb-2">{review.comment}</p>
                        
                        {review.merchant_response && (
                          <div className="mt-3 p-3 bg-blue-50 rounded border-l-4 border-blue-500">
                            <p className="text-sm font-medium text-blue-900 mb-1">Merchant Response</p>
                            <p className="text-sm text-blue-800">{review.merchant_response}</p>
                            <p className="text-xs text-blue-600 mt-1">
                              {new Date(review.response_date).toLocaleDateString()}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col space-y-2">
                      {review.status === 'pending' && (
                        <>
                          <Button 
                            size="sm"
                            onClick={() => handleApprove(review.id)}
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Approve
                          </Button>
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => handleReject(review.id)}
                          >
                            <XCircle className="w-4 h-4 mr-1" />
                            Reject
                          </Button>
                        </>
                      )}

                      {review.status === 'approved' && !review.merchant_response && (
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button 
                              size="sm"
                              onClick={() => setSelectedReview(review)}
                            >
                              <MessageSquare className="w-4 h-4 mr-1" />
                              Respond
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Respond to Review</DialogTitle>
                              <DialogDescription>
                                Add a public response to this review
                              </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4">
                              <div className="p-3 bg-gray-50 rounded">
                                <div className="flex items-center space-x-2 mb-2">
                                  {renderStars(review.rating)}
                                </div>
                                <p className="text-sm text-gray-600">{review.comment}</p>
                              </div>
                              <div className="space-y-2">
                                <Label>Your Response</Label>
                                <Textarea
                                  value={responseText}
                                  onChange={(e) => setResponseText(e.target.value)}
                                  placeholder="Thank you for your feedback..."
                                  rows={4}
                                />
                              </div>
                              <div className="flex justify-end space-x-2">
                                <Button variant="outline" onClick={() => setSelectedReview(null)}>
                                  Cancel
                                </Button>
                                <Button 
                                  onClick={handleAddResponse}
                                  disabled={addResponseMutation.isPending}
                                >
                                  {addResponseMutation.isPending ? 'Posting...' : 'Post Response'}
                                </Button>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      )}

                      {review.status === 'approved' && (
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleFeature(review.id)}
                        >
                          <Award className="w-4 h-4 mr-1" />
                          Feature
                        </Button>
                      )}

                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => handleFlag(review.id)}
                      >
                        <Flag className="w-4 h-4 mr-1" />
                        Flag
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {(!filteredReviews || filteredReviews.length === 0) && (
              <div className="text-center py-12 text-gray-500">
                <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No reviews found</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ReviewManagement
