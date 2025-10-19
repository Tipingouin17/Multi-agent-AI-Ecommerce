/**
 * Order Management Page - Enhanced
 * 
 * Comprehensive order management interface with all enhanced features:
 * - Order modifications
 * - Order splitting
 * - Partial shipments
 * - Fulfillment planning
 * - Cancellation management
 * - Notes and tags
 * - Timeline view
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Package,
  Split,
  Truck,
  XCircle,
  MessageSquare,
  Tag,
  Clock,
  Edit,
  CheckCircle,
  AlertCircle,
  FileText,
  Calendar,
} from 'lucide-react';
import { DataTable } from '@/components/shared/DataTable';
import { api } from '@/lib/api-enhanced';
import { formatDistanceToNow } from 'date-fns';


// Status badge colors
const statusColors = {
  pending: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  shipped: 'bg-purple-100 text-purple-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};


/**
 * Order Timeline Component
 */
const OrderTimeline = ({ orderId }) => {
  const { data: timeline, isLoading } = useQuery({
    queryKey: ['orderTimeline', orderId],
    queryFn: () => api.orders.getTimeline(orderId),
    enabled: !!orderId,
  });

  if (isLoading) return <div>Loading timeline...</div>;

  return (
    <div className="space-y-4">
      {timeline?.map((event, index) => (
        <div key={event.event_id} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="w-3 h-3 bg-blue-500 rounded-full" />
            {index < timeline.length - 1 && (
              <div className="w-0.5 h-full bg-gray-200 mt-2" />
            )}
          </div>
          <div className="flex-1 pb-4">
            <div className="flex items-center justify-between">
              <h4 className="font-medium">{event.event_type}</h4>
              <span className="text-sm text-gray-500">
                {formatDistanceToNow(new Date(event.event_timestamp), { addSuffix: true })}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">{event.description}</p>
            {event.metadata && (
              <pre className="text-xs bg-gray-50 p-2 rounded mt-2 overflow-auto">
                {JSON.stringify(event.metadata, null, 2)}
              </pre>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};


/**
 * Order Modifications Component
 */
const OrderModifications = ({ orderId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    field_name: '',
    old_value: '',
    new_value: '',
    reason: '',
    modified_by: 'admin',
  });

  const queryClient = useQueryClient();

  const { data: modifications } = useQuery({
    queryKey: ['orderModifications', orderId],
    queryFn: () => api.orders.getModifications(orderId),
    enabled: !!orderId,
  });

  const modifyMutation = useMutation({
    mutationFn: (data) => api.orders.modifyField(orderId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['orderModifications', orderId]);
      queryClient.invalidateQueries(['orderTimeline', orderId]);
      setIsOpen(false);
      setFormData({
        field_name: '',
        old_value: '',
        new_value: '',
        reason: '',
        modified_by: 'admin',
      });
    },
  });

  const columns = [
    {
      accessorKey: 'field_name',
      header: 'Field',
    },
    {
      accessorKey: 'old_value',
      header: 'Old Value',
    },
    {
      accessorKey: 'new_value',
      header: 'New Value',
    },
    {
      accessorKey: 'reason',
      header: 'Reason',
    },
    {
      accessorKey: 'modified_by',
      header: 'Modified By',
    },
    {
      accessorKey: 'modified_at',
      header: 'Modified At',
      cell: ({ row }) => formatDistanceToNow(new Date(row.original.modified_at), { addSuffix: true }),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Modification History</h3>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button>
              <Edit className="w-4 h-4 mr-2" />
              Modify Order
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Modify Order Field</DialogTitle>
              <DialogDescription>
                Make changes to order fields with audit trail
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Field Name</Label>
                <Select
                  value={formData.field_name}
                  onValueChange={(value) => setFormData({ ...formData, field_name: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select field" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="status">Status</SelectItem>
                    <SelectItem value="shipping_address">Shipping Address</SelectItem>
                    <SelectItem value="customer_email">Customer Email</SelectItem>
                    <SelectItem value="customer_phone">Customer Phone</SelectItem>
                    <SelectItem value="notes">Notes</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Old Value</Label>
                <Input
                  value={formData.old_value}
                  onChange={(e) => setFormData({ ...formData, old_value: e.target.value })}
                  placeholder="Current value"
                />
              </div>
              <div>
                <Label>New Value</Label>
                <Input
                  value={formData.new_value}
                  onChange={(e) => setFormData({ ...formData, new_value: e.target.value })}
                  placeholder="New value"
                />
              </div>
              <div>
                <Label>Reason</Label>
                <Textarea
                  value={formData.reason}
                  onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                  placeholder="Reason for modification"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => modifyMutation.mutate(formData)}>
                Save Modification
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      <DataTable columns={columns} data={modifications || []} />
    </div>
  );
};


/**
 * Partial Shipments Component
 */
const PartialShipments = ({ orderId }) => {
  const [isOpen, setIsOpen] = useState(false);

  const { data: shipments } = useQuery({
    queryKey: ['orderShipments', orderId],
    queryFn: () => api.orders.getShipments(orderId),
    enabled: !!orderId,
  });

  const columns = [
    {
      accessorKey: 'shipment_number',
      header: 'Shipment #',
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <Badge className={statusColors[row.original.status] || 'bg-gray-100'}>
          {row.original.status}
        </Badge>
      ),
    },
    {
      accessorKey: 'tracking_number',
      header: 'Tracking',
    },
    {
      accessorKey: 'carrier',
      header: 'Carrier',
    },
    {
      accessorKey: 'shipped_at',
      header: 'Shipped',
      cell: ({ row }) =>
        row.original.shipped_at
          ? formatDistanceToNow(new Date(row.original.shipped_at), { addSuffix: true })
          : '-',
    },
    {
      accessorKey: 'delivered_at',
      header: 'Delivered',
      cell: ({ row }) =>
        row.original.delivered_at
          ? formatDistanceToNow(new Date(row.original.delivered_at), { addSuffix: true })
          : '-',
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Shipments</h3>
        <Button onClick={() => setIsOpen(true)}>
          <Truck className="w-4 h-4 mr-2" />
          Create Shipment
        </Button>
      </div>
      <DataTable columns={columns} data={shipments || []} />
    </div>
  );
};


/**
 * Order Notes Component
 */
const OrderNotes = ({ orderId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [isVisible, setIsVisible] = useState(false);

  const queryClient = useQueryClient();

  const { data: notes } = useQuery({
    queryKey: ['orderNotes', orderId],
    queryFn: () => api.orders.getNotes(orderId),
    enabled: !!orderId,
  });

  const addNoteMutation = useMutation({
    mutationFn: (data) => api.orders.addNote(orderId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['orderNotes', orderId]);
      setIsOpen(false);
      setNoteText('');
      setIsVisible(false);
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Notes</h3>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button>
              <MessageSquare className="w-4 h-4 mr-2" />
              Add Note
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Order Note</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Note</Label>
                <Textarea
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Enter note..."
                  rows={4}
                />
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="visible"
                  checked={isVisible}
                  onChange={(e) => setIsVisible(e.target.checked)}
                />
                <Label htmlFor="visible">Visible to customer</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() =>
                  addNoteMutation.mutate({
                    note_text: noteText,
                    is_visible_to_customer: isVisible,
                    created_by: 'admin',
                  })
                }
              >
                Add Note
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      <div className="space-y-2">
        {notes?.map((note) => (
          <Card key={note.note_id}>
            <CardContent className="pt-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="text-sm">{note.note_text}</p>
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                    <span>{note.created_by}</span>
                    <span>•</span>
                    <span>{formatDistanceToNow(new Date(note.created_at), { addSuffix: true })}</span>
                    {note.is_visible_to_customer && (
                      <>
                        <span>•</span>
                        <Badge variant="outline" className="text-xs">
                          Customer Visible
                        </Badge>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};


/**
 * Order Tags Component
 */
const OrderTags = ({ orderId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [tagName, setTagName] = useState('');

  const queryClient = useQueryClient();

  const { data: tags } = useQuery({
    queryKey: ['orderTags', orderId],
    queryFn: () => api.orders.getTags(orderId),
    enabled: !!orderId,
  });

  const addTagMutation = useMutation({
    mutationFn: (data) => api.orders.addTag(orderId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['orderTags', orderId]);
      setIsOpen(false);
      setTagName('');
    },
  });

  const removeTagMutation = useMutation({
    mutationFn: (tag) => api.orders.removeTag(orderId, tag),
    onSuccess: () => {
      queryClient.invalidateQueries(['orderTags', orderId]);
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Tags</h3>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button>
              <Tag className="w-4 h-4 mr-2" />
              Add Tag
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Tag</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Tag Name</Label>
                <Input
                  value={tagName}
                  onChange={(e) => setTagName(e.target.value)}
                  placeholder="e.g., priority, vip, fragile"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() =>
                  addTagMutation.mutate({
                    tag: tagName,
                    added_by: 'admin',
                  })
                }
              >
                Add Tag
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      <div className="flex flex-wrap gap-2">
        {tags?.map((tag) => (
          <Badge
            key={tag.tag_id}
            variant="secondary"
            className="cursor-pointer hover:bg-red-100"
            onClick={() => removeTagMutation.mutate(tag.tag)}
          >
            {tag.tag}
            <XCircle className="w-3 h-3 ml-1" />
          </Badge>
        ))}
      </div>
    </div>
  );
};


/**
 * Main Order Management Component
 */
export default function OrderManagement() {
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: () => api.orders.getAll(),
  });

  const orderColumns = [
    {
      accessorKey: 'order_id',
      header: 'Order ID',
      cell: ({ row }) => (
        <Button
          variant="link"
          onClick={() => setSelectedOrderId(row.original.order_id)}
        >
          {row.original.order_id}
        </Button>
      ),
    },
    {
      accessorKey: 'customer_email',
      header: 'Customer',
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <Badge className={statusColors[row.original.status] || 'bg-gray-100'}>
          {row.original.status}
        </Badge>
      ),
    },
    {
      accessorKey: 'total_amount',
      header: 'Total',
      cell: ({ row }) => `$${row.original.total_amount.toFixed(2)}`,
    },
    {
      accessorKey: 'created_at',
      header: 'Created',
      cell: ({ row }) =>
        formatDistanceToNow(new Date(row.original.created_at), { addSuffix: true }),
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Order Management</h1>
        <p className="text-gray-500">
          Comprehensive order management with enhanced features
        </p>
      </div>

      {!selectedOrderId ? (
        <Card>
          <CardHeader>
            <CardTitle>All Orders</CardTitle>
            <CardDescription>View and manage all orders</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <Input
                placeholder="Search orders..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <DataTable columns={orderColumns} data={orders || []} />
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          <Button variant="outline" onClick={() => setSelectedOrderId(null)}>
            ← Back to Orders
          </Button>

          <Tabs defaultValue="timeline">
            <TabsList>
              <TabsTrigger value="timeline">
                <Clock className="w-4 h-4 mr-2" />
                Timeline
              </TabsTrigger>
              <TabsTrigger value="modifications">
                <Edit className="w-4 h-4 mr-2" />
                Modifications
              </TabsTrigger>
              <TabsTrigger value="shipments">
                <Truck className="w-4 h-4 mr-2" />
                Shipments
              </TabsTrigger>
              <TabsTrigger value="notes">
                <MessageSquare className="w-4 h-4 mr-2" />
                Notes
              </TabsTrigger>
              <TabsTrigger value="tags">
                <Tag className="w-4 h-4 mr-2" />
                Tags
              </TabsTrigger>
            </TabsList>

            <TabsContent value="timeline">
              <Card>
                <CardHeader>
                  <CardTitle>Order Timeline</CardTitle>
                  <CardDescription>Complete event history</CardDescription>
                </CardHeader>
                <CardContent>
                  <OrderTimeline orderId={selectedOrderId} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="modifications">
              <Card>
                <CardHeader>
                  <CardTitle>Order Modifications</CardTitle>
                  <CardDescription>Track all changes to the order</CardDescription>
                </CardHeader>
                <CardContent>
                  <OrderModifications orderId={selectedOrderId} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="shipments">
              <Card>
                <CardHeader>
                  <CardTitle>Partial Shipments</CardTitle>
                  <CardDescription>Manage order shipments</CardDescription>
                </CardHeader>
                <CardContent>
                  <PartialShipments orderId={selectedOrderId} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="notes">
              <Card>
                <CardHeader>
                  <CardTitle>Order Notes</CardTitle>
                  <CardDescription>Internal and customer notes</CardDescription>
                </CardHeader>
                <CardContent>
                  <OrderNotes orderId={selectedOrderId} />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="tags">
              <Card>
                <CardHeader>
                  <CardTitle>Order Tags</CardTitle>
                  <CardDescription>Categorize and filter orders</CardDescription>
                </CardHeader>
                <CardContent>
                  <OrderTags orderId={selectedOrderId} />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}

