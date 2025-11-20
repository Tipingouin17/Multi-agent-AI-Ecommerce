/**
 * Offers Management Page
 * View and manage all special offers and promotions
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Plus, MoreVertical, Edit, Trash2, Play, Pause, BarChart3, Search } from 'lucide-react';
import { apiService } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

const Offers = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  // Load offers
  useEffect(() => {
    loadOffers();
  }, [statusFilter, typeFilter]);

  const loadOffers = async () => {
    try {
      setLoading(true);
      const params = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (typeFilter !== 'all') params.offer_type = typeFilter;
      
      const data = await apiService.getOffers(params);
      setOffers(data.offers || []);
    } catch (error) {
      console.error('Error loading offers:', error);
      toast({
        title: 'Error',
        description: 'Failed to load offers',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Filter offers by search term
  const filteredOffers = offers.filter(offer =>
    offer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    offer.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handle offer actions
  const handleActivate = async (offerId) => {
    try {
      await apiService.updateOffer(offerId, { status: 'active' });
      toast({
        title: 'Success',
        description: 'Offer activated successfully',
      });
      loadOffers();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to activate offer',
        variant: 'destructive',
      });
    }
  };

  const handlePause = async (offerId) => {
    try {
      await apiService.updateOffer(offerId, { status: 'paused' });
      toast({
        title: 'Success',
        description: 'Offer paused successfully',
      });
      loadOffers();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to pause offer',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (offerId) => {
    if (!confirm('Are you sure you want to delete this offer?')) return;
    
    try {
      await apiService.deleteOffer(offerId);
      toast({
        title: 'Success',
        description: 'Offer deleted successfully',
      });
      loadOffers();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete offer',
        variant: 'destructive',
      });
    }
  };

  // Status badge color
  const getStatusBadge = (status) => {
    const colors = {
      draft: 'secondary',
      active: 'default',
      paused: 'outline',
      expired: 'destructive',
      cancelled: 'destructive'
    };
    return (
      <Badge variant={colors[status] || 'secondary'}>
        {status}
      </Badge>
    );
  };

  // Format discount display
  const formatDiscount = (offer) => {
    if (!offer.discount_value) return '-';
    return offer.discount_type === 'percentage'
      ? `${offer.discount_value}%`
      : `$${offer.discount_value}`;
  };

  // Format date range
  const formatDateRange = (offer) => {
    if (!offer.is_scheduled) return 'Always active';
    const start = offer.start_date ? new Date(offer.start_date).toLocaleDateString() : '-';
    const end = offer.end_date ? new Date(offer.end_date).toLocaleDateString() : '-';
    return `${start} - ${end}`;
  };

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Offers & Promotions</h1>
          <p className="text-muted-foreground mt-1">
            Create and manage special offers for your products
          </p>
        </div>
        <Button onClick={() => navigate('/merchant/offers/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Create Offer
        </Button>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search offers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
              </SelectContent>
            </Select>

            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="percentage">Percentage</SelectItem>
                <SelectItem value="fixed_amount">Fixed Amount</SelectItem>
                <SelectItem value="buy_x_get_y">Buy X Get Y</SelectItem>
                <SelectItem value="bundle">Bundle</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Offers Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Offers ({filteredOffers.length})</CardTitle>
          <CardDescription>
            Manage your special offers and track their performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">Loading offers...</p>
            </div>
          ) : filteredOffers.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No offers found</p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => navigate('/merchant/offers/new')}
              >
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Offer
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Discount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Schedule</TableHead>
                  <TableHead>Usage</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOffers.map((offer) => (
                  <TableRow key={offer.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{offer.name}</div>
                        {offer.display_badge && (
                          <Badge variant="outline" className="mt-1">
                            {offer.display_badge}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="capitalize">
                      {offer.offer_type?.replace('_', ' ')}
                    </TableCell>
                    <TableCell>{formatDiscount(offer)}</TableCell>
                    <TableCell>{getStatusBadge(offer.status)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDateRange(offer)}
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {offer.current_usage_count || 0}
                        {offer.total_usage_limit && ` / ${offer.total_usage_limit}`}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => navigate(`/merchant/offers/${offer.id}/analytics`)}
                          >
                            <BarChart3 className="mr-2 h-4 w-4" />
                            View Analytics
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => navigate(`/merchant/offers/${offer.id}/edit`)}
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {offer.status === 'draft' || offer.status === 'paused' ? (
                            <DropdownMenuItem onClick={() => handleActivate(offer.id)}>
                              <Play className="mr-2 h-4 w-4" />
                              Activate
                            </DropdownMenuItem>
                          ) : offer.status === 'active' ? (
                            <DropdownMenuItem onClick={() => handlePause(offer.id)}>
                              <Pause className="mr-2 h-4 w-4" />
                              Pause
                            </DropdownMenuItem>
                          ) : null}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => handleDelete(offer.id)}
                            className="text-destructive"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Offers;
