import React, { useState, useEffect } from 'react';
import { 
  Package, RefreshCw, CheckCircle, XCircle, Clock, 
  DollarSign, TrendingUp, AlertCircle, Search, Filter
} from 'lucide-react';
import { motion } from 'framer-motion';

const RMADashboard = () => {
  const [rmaRequests, setRmaRequests] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch RMA requests
      const requestsRes = await fetch('http://localhost:8035/api/rma/requests');
      const requestsData = await requestsRes.json();
      setRmaRequests(requestsData.requests || []);

      // Fetch metrics
      const metricsRes = await fetch('http://localhost:8035/api/rma/metrics');
      const metricsData = await metricsRes.json();
      setMetrics(metricsData.metrics || {});

    } catch (error) {
      console.error('Error fetching RMA data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'requested': 'text-yellow-600 bg-yellow-50',
      'approved': 'text-blue-600 bg-blue-50',
      'rejected': 'text-red-600 bg-red-50',
      'label_sent': 'text-purple-600 bg-purple-50',
      'in_transit': 'text-indigo-600 bg-indigo-50',
      'received': 'text-cyan-600 bg-cyan-50',
      'inspecting': 'text-orange-600 bg-orange-50',
      'inspected': 'text-teal-600 bg-teal-50',
      'refund_pending': 'text-amber-600 bg-amber-50',
      'refund_processed': 'text-green-600 bg-green-50',
      'completed': 'text-green-600 bg-green-50',
      'closed': 'text-gray-600 bg-gray-50'
    };
    return colors[status] || 'text-gray-600 bg-gray-50';
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

  const filteredRequests = rmaRequests.filter(req => {
    const matchesTab = activeTab === 'all' || req.status === activeTab;
    const matchesSearch = !searchTerm || 
      req.rma_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      req.order_id.toString().includes(searchTerm);
    return matchesTab && matchesSearch;
  });

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
          <h1 className="text-3xl font-bold text-gray-900">RMA Management</h1>
          <p className="text-gray-600 mt-1">Return Merchandise Authorization workflow</p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
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
              <p className="text-sm text-gray-600">Total Requests</p>
              <p className="text-2xl font-bold text-indigo-600 mt-1">
                {metrics?.total_requests || 0}
              </p>
            </div>
            <div className="p-3 bg-indigo-50 rounded-lg">
              <Package className="w-6 h-6 text-indigo-600" />
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
              <p className="text-sm text-gray-600">Pending Approval</p>
              <p className="text-2xl font-bold text-yellow-600 mt-1">
                {metrics?.status_distribution?.requested || 0}
              </p>
            </div>
            <div className="p-3 bg-yellow-50 rounded-lg">
              <Clock className="w-6 h-6 text-yellow-600" />
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
              <p className="text-sm text-gray-600">Total Refunds</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                ${metrics?.total_refunds?.toLocaleString() || '0'}
              </p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <DollarSign className="w-6 h-6 text-green-600" />
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
              <p className="text-sm text-gray-600">Avg Processing Time</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {metrics?.average_processing_days?.toFixed(1) || '0'} days
              </p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <TrendingUp className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search by RMA number or Order ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Status Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px overflow-x-auto">
            {[
              { id: 'all', label: 'All', count: rmaRequests.length },
              { id: 'requested', label: 'Requested', count: metrics?.status_distribution?.requested || 0 },
              { id: 'approved', label: 'Approved', count: metrics?.status_distribution?.approved || 0 },
              { id: 'received', label: 'Received', count: metrics?.status_distribution?.received || 0 },
              { id: 'refund_processed', label: 'Refunded', count: metrics?.status_distribution?.refund_processed || 0 }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
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

        {/* RMA Requests Table */}
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    RMA Number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Order ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reason
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Requested
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Eligible
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRequests.map((request) => (
                  <tr key={request.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-indigo-600">
                        {request.rma_number}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      #{request.order_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      #{request.customer_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {request.return_reason.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                        {request.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(request.requested_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {request.is_eligible ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredRequests.length === 0 && (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No RMA requests found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RMADashboard;
