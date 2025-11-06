import React, { useState, useEffect } from 'react';
import { 
  Package, Truck, CheckCircle, AlertTriangle, Clock, 
  XCircle, TrendingUp, Activity, FileText, MapPin,
  Search, Filter, RefreshCw, Download, Eye, Edit
} from 'lucide-react';
import { motion } from 'framer-motion';

const InboundManagementDashboard = () => {
  const [shipments, setShipments] = useState([]);
  const [putawayTasks, setPutawayTasks] = useState([]);
  const [inspections, setInspections] = useState([]);
  const [discrepancies, setDiscrepancies] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('shipments');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedShipment, setSelectedShipment] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [statusFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch shipments
      const shipmentsUrl = statusFilter === 'all' 
        ? 'http://localhost:8032/api/inbound/shipments?limit=50'
        : `http://localhost:8032/api/inbound/shipments?status=${statusFilter}&limit=50`;
      const shipmentsRes = await fetch(shipmentsUrl);
      const shipmentsData = await shipmentsRes.json();
      setShipments(shipmentsData.shipments || []);

      // Fetch putaway tasks
      const tasksRes = await fetch('http://localhost:8032/api/inbound/putaway-tasks?limit=50');
      const tasksData = await tasksRes.json();
      setPutawayTasks(tasksData.tasks || []);

      // Fetch inspections
      const inspectionsRes = await fetch('http://localhost:8032/api/inbound/inspections?limit=50');
      const inspectionsData = await inspectionsRes.json();
      setInspections(inspectionsData.inspections || []);

      // Fetch discrepancies
      const discrepanciesRes = await fetch('http://localhost:8032/api/inbound/discrepancies?limit=50');
      const discrepanciesData = await discrepanciesRes.json();
      setDiscrepancies(discrepanciesData.discrepancies || []);

      // Fetch metrics
      const metricsRes = await fetch('http://localhost:8032/api/inbound/metrics');
      const metricsData = await metricsRes.json();
      setMetrics(metricsData.summary || {});

    } catch (error) {
      console.error('Error fetching inbound data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'expected': 'text-blue-600 bg-blue-50',
      'in_transit': 'text-purple-600 bg-purple-50',
      'arrived': 'text-yellow-600 bg-yellow-50',
      'receiving': 'text-orange-600 bg-orange-50',
      'completed': 'text-green-600 bg-green-50',
      'cancelled': 'text-red-600 bg-red-50',
      'pending': 'text-gray-600 bg-gray-50',
      'in_progress': 'text-blue-600 bg-blue-50',
      'passed': 'text-green-600 bg-green-50',
      'failed': 'text-red-600 bg-red-50',
      'open': 'text-red-600 bg-red-50',
      'resolved': 'text-green-600 bg-green-50'
    };
    return colors[status] || 'text-gray-600 bg-gray-50';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'expected': <Clock className="w-4 h-4" />,
      'in_transit': <Truck className="w-4 h-4" />,
      'arrived': <MapPin className="w-4 h-4" />,
      'receiving': <Activity className="w-4 h-4" />,
      'completed': <CheckCircle className="w-4 h-4" />,
      'cancelled': <XCircle className="w-4 h-4" />,
      'pending': <Clock className="w-4 h-4" />,
      'passed': <CheckCircle className="w-4 h-4" />,
      'failed': <AlertTriangle className="w-4 h-4" />,
      'open': <AlertTriangle className="w-4 h-4" />
    };
    return icons[status] || <FileText className="w-4 h-4" />;
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
    const totalShipments = shipments.length;
    const completedShipments = shipments.filter(s => s.status === 'completed').length;
    const pendingTasks = putawayTasks.filter(t => t.status === 'pending').length;
    const openDiscrepancies = discrepancies.filter(d => d.resolution_status === 'open').length;
    
    return {
      totalShipments,
      completedShipments,
      pendingTasks,
      openDiscrepancies,
      completionRate: totalShipments > 0 ? ((completedShipments / totalShipments) * 100).toFixed(1) : 0
    };
  };

  const dashboardMetrics = calculateMetrics();

  if (loading && !metrics) {
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
          <h1 className="text-3xl font-bold text-gray-900">Inbound Management</h1>
          <p className="text-gray-600 mt-1">Receiving, quality control, and putaway operations</p>
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Shipments</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{dashboardMetrics.totalShipments}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <Package className="w-6 h-6 text-blue-600" />
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
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-green-600 mt-1">{dashboardMetrics.completedShipments}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
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
              <p className="text-sm text-gray-600">Pending Tasks</p>
              <p className="text-2xl font-bold text-orange-600 mt-1">{dashboardMetrics.pendingTasks}</p>
            </div>
            <div className="p-3 bg-orange-50 rounded-lg">
              <Clock className="w-6 h-6 text-orange-600" />
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
              <p className="text-sm text-gray-600">Discrepancies</p>
              <p className="text-2xl font-bold text-red-600 mt-1">{dashboardMetrics.openDiscrepancies}</p>
            </div>
            <div className="p-3 bg-red-50 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Completion Rate</p>
              <p className="text-2xl font-bold text-indigo-600 mt-1">{dashboardMetrics.completionRate}%</p>
            </div>
            <div className="p-3 bg-indigo-50 rounded-lg">
              <TrendingUp className="w-6 h-6 text-indigo-600" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {[
              { id: 'shipments', label: 'Shipments', count: shipments.length },
              { id: 'putaway', label: 'Putaway Tasks', count: putawayTasks.length },
              { id: 'inspections', label: 'Quality Inspections', count: inspections.length },
              { id: 'discrepancies', label: 'Discrepancies', count: discrepancies.length }
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
          {/* Shipments Tab */}
          {activeTab === 'shipments' && (
            <div className="space-y-4">
              {/* Filters */}
              <div className="flex gap-4 items-center">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                      type="text"
                      placeholder="Search shipments..."
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="all">All Status</option>
                  <option value="expected">Expected</option>
                  <option value="in_transit">In Transit</option>
                  <option value="arrived">Arrived</option>
                  <option value="receiving">Receiving</option>
                  <option value="completed">Completed</option>
                </select>
              </div>

              {/* Shipments Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Shipment #
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Carrier
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Expected Arrival
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Items
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Progress
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {shipments.map((shipment) => (
                      <tr key={shipment.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <Package className="w-5 h-5 text-gray-400 mr-2" />
                            <span className="text-sm font-medium text-gray-900">
                              {shipment.shipment_number}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(shipment.status)}`}>
                            {getStatusIcon(shipment.status)}
                            {shipment.status?.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {shipment.carrier || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(shipment.expected_arrival_date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {shipment.received_items || 0} / {shipment.total_items || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-indigo-600 h-2 rounded-full"
                                style={{
                                  width: `${shipment.total_items > 0 ? (shipment.received_items / shipment.total_items) * 100 : 0}%`
                                }}
                              />
                            </div>
                            <span className="text-xs text-gray-600">
                              {shipment.total_items > 0 ? Math.round((shipment.received_items / shipment.total_items) * 100) : 0}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => setSelectedShipment(shipment)}
                            className="text-indigo-600 hover:text-indigo-900 mr-3"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Putaway Tasks Tab */}
          {activeTab === 'putaway' && (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Task #
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        SKU
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        From Location
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        To Location
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Priority
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {putawayTasks.map((task) => (
                      <tr key={task.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {task.task_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {task.sku}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {task.quantity}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {task.from_location || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {task.to_location || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                            {getStatusIcon(task.status)}
                            {task.status?.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded ${
                            task.priority === 'high' ? 'bg-red-100 text-red-800' :
                            task.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {task.priority}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Quality Inspections Tab */}
          {activeTab === 'inspections' && (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Inspection #
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        SKU
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sample Size
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Passed
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Failed
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {inspections.map((inspection) => (
                      <tr key={inspection.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {inspection.inspection_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {inspection.sku}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {inspection.inspection_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {inspection.sample_size || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                          {inspection.passed_count || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                          {inspection.failed_count || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(inspection.status)}`}>
                            {getStatusIcon(inspection.status)}
                            {inspection.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Discrepancies Tab */}
          {activeTab === 'discrepancies' && (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Shipment #
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        SKU
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Expected
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actual
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Variance
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {discrepancies.map((discrepancy) => (
                      <tr key={discrepancy.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {discrepancy.shipment_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {discrepancy.sku}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {discrepancy.discrepancy_type?.replace('_', ' ')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {discrepancy.expected_quantity}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {discrepancy.actual_quantity}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-medium ${
                            discrepancy.variance > 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {discrepancy.variance > 0 ? '+' : ''}{discrepancy.variance}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(discrepancy.resolution_status)}`}>
                            {getStatusIcon(discrepancy.resolution_status)}
                            {discrepancy.resolution_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(discrepancy.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Empty State */}
          {((activeTab === 'shipments' && shipments.length === 0) ||
            (activeTab === 'putaway' && putawayTasks.length === 0) ||
            (activeTab === 'inspections' && inspections.length === 0) ||
            (activeTab === 'discrepancies' && discrepancies.length === 0)) && (
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

export default InboundManagementDashboard;
