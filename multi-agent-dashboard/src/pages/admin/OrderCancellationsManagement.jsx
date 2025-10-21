import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { 
  XCircle, CheckCircle, Clock, DollarSign, 
  FileText, AlertTriangle, User 
} from 'lucide-react';

/**
 * Order Cancellations Management Component
 * 
 * Manages order cancellation requests:
 * - View pending cancellation requests
 * - Approve or reject cancellations
 * - Track refund status
 * - View cancellation history
 */
const OrderCancellationsManagement = () => {
  const [cancellations, setCancellations] = useState([]);
  const [selectedCancellation, setSelectedCancellation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [showReviewDialog, setShowReviewDialog] = useState(false);

  useEffect(() => {
    fetchCancellations();
  }, []);

  const fetchCancellations = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/orders/cancellations');
      const data = await response.json();
      setCancellations(data);
    } catch (err) {
      setError('Failed to load cancellation requests');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReviewCancellation = async (requestId, approved) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/orders/cancellations/${requestId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved,
          reviewed_by: 'admin-001', // In real app, get from auth context
          review_notes: reviewNotes
        })
      });

      if (response.ok) {
        await fetchCancellations();
        setShowReviewDialog(false);
        setReviewNotes('');
        setSelectedCancellation(null);
      }
    } catch (err) {
      setError('Failed to process cancellation review');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'secondary', icon: Clock, label: 'Pending' },
      approved: { variant: 'default', icon: CheckCircle, label: 'Approved' },
      rejected: { variant: 'destructive', icon: XCircle, label: 'Rejected' },
      completed: { variant: 'outline', icon: CheckCircle, label: 'Completed' }
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1 w-fit">
        <Icon className="w-3 h-3" />
        {config.label}
      </Badge>
    );
  };

  const getReasonLabel = (reason) => {
    const reasons = {
      customer_request: 'Customer Request',
      out_of_stock: 'Out of Stock',
      payment_failed: 'Payment Failed',
      fraud_detected: 'Fraud Detected',
      shipping_delay: 'Shipping Delay',
      wrong_item: 'Wrong Item Ordered',
      other: 'Other'
    };
    return reasons[reason] || reason;
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Order Cancellations</h1>
            <p className="text-muted-foreground mt-1">
              Review and manage order cancellation requests
            </p>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Pending Requests</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-500">
                {cancellations.filter(c => c.status === 'pending').length}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Awaiting review
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Approved Today</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-500">
                {cancellations.filter(c => 
                  c.status === 'approved' && 
                  new Date(c.reviewed_at).toDateString() === new Date().toDateString()
                ).length}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Last 24 hours
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Total Refunds</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                ${cancellations
                  .filter(c => c.status === 'approved')
                  .reduce((sum, c) => sum + (c.refund_amount || 0), 0)
                  .toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Processed refunds
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Rejection Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                {cancellations.length > 0
                  ? Math.round((cancellations.filter(c => c.status === 'rejected').length / cancellations.length) * 100)
                  : 0}%
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Of all requests
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Cancellations List */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle>Cancellation Requests</CardTitle>
            <CardDescription>
              {cancellations.length} total requests
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading && <p className="text-muted-foreground">Loading cancellations...</p>}

            {!loading && cancellations.length === 0 && (
              <div className="text-center py-12">
                <CheckCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No cancellation requests</p>
              </div>
            )}

            {!loading && cancellations.length > 0 && (
              <div className="space-y-4">
                {cancellations.map((cancellation) => (
                  <div
                    key={cancellation.request_id}
                    className="p-4 border border-border rounded-lg hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 space-y-3">
                        {/* Header */}
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-foreground">
                            Order #{cancellation.order_id}
                          </h3>
                          {getStatusBadge(cancellation.status)}
                        </div>

                        {/* Details */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <p className="text-muted-foreground">Reason</p>
                            <p className="font-medium text-foreground">
                              {getReasonLabel(cancellation.reason)}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Requested By</p>
                            <p className="font-medium text-foreground flex items-center gap-1">
                              <User className="w-3 h-3" />
                              {cancellation.requested_by}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Refund Amount</p>
                            <p className="font-medium text-foreground flex items-center gap-1">
                              <DollarSign className="w-3 h-3" />
                              ${cancellation.refund_amount}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Requested At</p>
                            <p className="font-medium text-foreground flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(cancellation.requested_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>

                        {/* Reason Details */}
                        {cancellation.reason_details && (
                          <div className="p-3 bg-muted/50 rounded-md">
                            <p className="text-sm text-muted-foreground mb-1">Details:</p>
                            <p className="text-sm text-foreground">{cancellation.reason_details}</p>
                          </div>
                        )}

                        {/* Review Info */}
                        {cancellation.reviewed_at && (
                          <div className="text-sm text-muted-foreground">
                            <p>
                              Reviewed by {cancellation.reviewed_by} on{' '}
                              {new Date(cancellation.reviewed_at).toLocaleString()}
                            </p>
                            {cancellation.review_notes && (
                              <p className="mt-1 italic">"{cancellation.review_notes}"</p>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      {cancellation.status === 'pending' && (
                        <div className="flex gap-2 ml-4">
                          <Dialog open={showReviewDialog && selectedCancellation?.request_id === cancellation.request_id}>
                            <DialogTrigger asChild>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setSelectedCancellation(cancellation);
                                  setShowReviewDialog(true);
                                }}
                              >
                                <FileText className="w-4 h-4 mr-1" />
                                Review
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="bg-card border-border">
                              <DialogHeader>
                                <DialogTitle>Review Cancellation Request</DialogTitle>
                                <DialogDescription>
                                  Order #{cancellation.order_id} - ${cancellation.refund_amount}
                                </DialogDescription>
                              </DialogHeader>
                              <div className="space-y-4 py-4">
                                <div className="space-y-2">
                                  <Label htmlFor="review_notes">Review Notes</Label>
                                  <Textarea
                                    id="review_notes"
                                    value={reviewNotes}
                                    onChange={(e) => setReviewNotes(e.target.value)}
                                    placeholder="Enter review notes..."
                                    className="bg-background border-input"
                                  />
                                </div>
                                <div className="flex gap-2 justify-end">
                                  <Button
                                    variant="outline"
                                    onClick={() => {
                                      setShowReviewDialog(false);
                                      setReviewNotes('');
                                      setSelectedCancellation(null);
                                    }}
                                  >
                                    Cancel
                                  </Button>
                                  <Button
                                    variant="destructive"
                                    onClick={() => handleReviewCancellation(cancellation.request_id, false)}
                                    disabled={loading}
                                  >
                                    <XCircle className="w-4 h-4 mr-1" />
                                    Reject
                                  </Button>
                                  <Button
                                    onClick={() => handleReviewCancellation(cancellation.request_id, true)}
                                    disabled={loading}
                                  >
                                    <CheckCircle className="w-4 h-4 mr-1" />
                                    Approve
                                  </Button>
                                </div>
                              </div>
                            </DialogContent>
                          </Dialog>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default OrderCancellationsManagement;

