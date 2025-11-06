import React, { useState, useEffect } from 'react';
import { 
  Package, Warehouse, Clock, AlertCircle, CheckCircle, 
  TrendingUp, Activity, BarChart3, RefreshCw, Download,
  ShoppingCart, Box, MapPin, Calendar
} from 'lucide-react';
import { motion } from 'framer-motion';

const FulfillmentDashboard = () => {
  const [reservations, setReservations] = useState([]);
  const [backorders, setBackorders] = useState([]);
  const [warehouseCapacity, setWarehouseCapacity] = useState([]);
  const [backorderMetrics, setBackorderMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('reservations');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch reservations
      const reservationsRes = await fetch('http://localhost:8033/api/reservations?limit=50');
      const reservationsData = await reservationsRes.json();
      setReservations(reservationsData.reservations || []);

      // Fetch backorders
      const backordersRes = await fetch('http://localhost:8033/api/backorders?limit=50');
      const backordersData = await backordersRes.json();
      setBackorders(backordersData.backorders || []);

      // Fetch warehouse capacity
      const capacityRes = await fetch('http://localhost:8033/api/warehouses/capacity');
      const capacityData = await capacityRes.json();
      setWarehouseCapacity(capacityData.capacity || []);

      // Fetch backorder metrics
      const metricsRes = await fetch('http://localhost:8033/api/backorders/metrics');
      const metricsData = await metricsRes.json();
      setBackorderMetrics(metricsData.metrics || {});

    } catch (error) {
      console.error('Error fetching fulfillment data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'active': 'text-green-600 bg-green-50',
      'released': 'text-gray-600 bg-gray-50',
      'expired': 'text-red-600 bg-red-50',
      'fulfilled': 'text-blue-600 bg-blue-50',
      'pending': 'text-yellow-600 bg-yellow-50',
      'partially_fulfilled': 'text-orange-600 bg-orange-50',
      'cancelled': 'text-red-600 bg-red-50',
      'normal': 'text-green-600 bg-green-50',
      'high': 'text-orange-600 bg-orange-50',
      'critical': 'text-red-600 bg-red-50',
      'full': 'text-red-600 bg-red-50'
    };
    return colors[status] || 'text-gray-600 bg-gray-50';
  };

  const getReservationTypeColor = (type) => {
    const colors = {
      'soft': 'text-blue-600 bg-blue-50',
      'hard': 'text-purple-600 bg-purple-50',
      'backorder': 'text-orange-600 bg-orange-50'
    };
    return colors[type] || 'text-gray-600 bg-gray-50';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateMetrics = () => {
    const activeReservations = reservations.filter(r => r.status === 'active').length;
    const expiredReservations = reservations.filter(r => r.status === 'expired').length;
    const pendingBackorders = backorders.filter(b => b.status === 'pending').length;
    const totalCapacity = warehouseCapacity.reduce((sum, w) => sum + (w.total_capacity || 0), 0);
    const currentLoad = warehouseCapacity.reduce((sum, w) => sum + (w.current_load || 0), 0);
    const avgUtilization = totalCapacity > 0 ? ((currentLoad / totalCapacity) * 100).toFixed(1) : 0;
    
    return {
      activeReservations,
      expiredReservations,
      pendingBackorders,
      avgUtilization,
      totalCapacity,
      currentLoad
    };
  };

  const dashboardMetrics = calculateMetrics();

  if (loading && !backorderMetrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Advanced Fulfillment</h1>
          <p className="text-gray-600 mt-1">Intelligent order fulfillment and inventory allocation</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Reservations</p>
              <p className="text-2xl font-bold text-green-600 mt-1">{dashboardMetrics.activeReservations}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Backorders</p>
              <p className="text-2xl font-bold text-orange-600 mt-1">{dashboardMetrics.pendingBackorders}</p>
            </div>
            <div className="p-3 bg-orange-50 rounded-lg">
              <AlertCircle className="w-6 h-6 text-orange-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Warehouse Utilization</p>
              <p className="text-2xl font-bold text-indigo-600 mt-1">{dashboardMetrics.avgUtilization}%</p>
            </div>
            <div className="p-3 bg-indigo-50 rounded-lg">
              <BarChart3 className="w-6 h-6 text-indigo-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Expired Reservations</p>
              <p className="text-2xl font-bold text-red-600 mt-1">{dashboardMetrics.expiredReservations}</p>
            </div>
            <div className="p-3 bg-red-50 rounded-lg">
              <Clock className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Warehouse Capacity Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Warehouse className="w-5 h-5" />
          Warehouse Capacity Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {warehouseCapacity.map((warehouse) => (
            <div key={warehouse.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-gray-400" />
                  <span className="font-medium text-gray-900">Warehouse {warehouse.warehouse_id}</span>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(warehouse.status)}`}>
                  {warehouse.status}
                </span>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Current Load</span>
                  <span className="font-medium">{warehouse.current_load || 0} / {warehouse.total_capacity || 0}</span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      warehouse.utilization_percentage >= 90 ? 'bg-red-600' :
                      warehouse.utilization_percentage >= 75 ? 'bg-orange-600' :
                      'bg-green-600'
                    }`}
                    style={{ width: `${Math.min(warehouse.utilization_percentage || 0, 100)}%` }}
                  />
                </div>
                
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Utilization</span>
                  <span className="font-medium">{(warehouse.utilization_percentage || 0).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {[
              { id: 'reservations', label: 'Inventory Reservations', count: reservations.length },
              { id: 'backorders', label: 'Backorders', count: backorders.length }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
                <span className="ml-2 px-2 py-1 text-xs rounded-full bg-gray-100">
                  {tab.count}
                </span>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Reservations Tab */}
          {activeTab === 'reservations' && (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Order ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        SKU
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Warehouse
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Expires At
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reservations.map((reservation) => (
                      <tr key={reservation.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <ShoppingCart className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm font-medium text-gray-900">
                              #{reservation.order_id}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {reservation.sku}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          WH-{reservation.warehouse_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {reservation.quantity}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${getReservationTypeColor(reservation.reservation_type)}`}>
                            {reservation.reservation_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(reservation.status)}`}>
                            {reservation.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(reservation.expires_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(reservation.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Backorders Tab */}
          {activeTab === 'backorders' && (
            <div className="space-y-4">
              {/* Backorder Metrics */}
              {backorderMetrics && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-xs text-gray-600 mb-1">Total Backorders</p>
                    <p className="text-2xl font-bold text-gray-900">{backorderMetrics.total_backorders || 0}</p>
                  </div>
                  <div className="bg-yellow-50 rounded-lg p-4">
                    <p className="text-xs text-gray-600 mb-1">Pending</p>
                    <p className="text-2xl font-bold text-yellow-600">{backorderMetrics.pending || 0}</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <p className="text-xs text-gray-600 mb-1">Fulfilled</p>
                    <p className="text-2xl font-bold text-green-600">{backorderMetrics.fulfilled || 0}</p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4">
                    <p className="text-xs text-gray-600 mb-1">Avg Fulfillment Time</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {backorderMetrics.avg_fulfillment_hours ? 
                        `${Math.round(backorderMetrics.avg_fulfillment_hours)}h` : 'N/A'}
                    </p>
                  </div>
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Order ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        SKU
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Customer
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Priority
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Est. Fulfillment
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {backorders.map((backorder) => (
                      <tr key={backorder.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <Box className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm font-medium text-gray-900">
                              #{backorder.order_id}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {backorder.sku}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          Customer #{backorder.customer_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-gray-900">
                            {backorder.quantity_fulfilled || 0} / {backorder.quantity_backordered}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                              <div
                                className="bg-indigo-600 h-2 rounded-full"
                                style={{ width: `${Math.min(backorder.priority_score || 0, 100)}%` }}
                              />
                            </div>
                            <span className="text-xs text-gray-600">{backorder.priority_score || 0}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(backorder.status)}`}>
                            {backorder.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(backorder.estimated_fulfillment_date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(backorder.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Empty State */}
          {((activeTab === 'reservations' && reservations.length === 0) ||
            (activeTab === 'backorders' && backorders.length === 0)) && (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No data available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FulfillmentDashboard;
