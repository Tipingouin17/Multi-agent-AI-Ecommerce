import { useState, useEffect } from 'react';
import { 
  Package, AlertTriangle, TrendingUp, ShoppingCart, 
  CheckCircle, Clock, XCircle, RefreshCw, Plus, Download 
} from 'lucide-react';
import { motion } from 'framer-motion';

const ReplenishmentDashboard = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending');
  const [priorityFilter, setPriorityFilter] = useState('all');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [filter, priorityFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch recommendations
      let url = `http://localhost:8032/api/replenishment/recommendations?status=${filter}`;
      if (priorityFilter !== 'all') {
        url += `&priority=${priorityFilter}`;
      }
      const recsRes = await fetch(url);
      const recsData = await recsRes.json();
      setRecommendations(recsData.data || []);

      // Fetch purchase orders
      const posRes = await fetch('http://localhost:8032/api/purchase-orders');
      const posData = await posRes.json();
      setPurchaseOrders(posData.data || []);

      // Fetch stats
      const statsRes = await fetch('http://localhost:8032/api/replenishment/stats');
      const statsData = await statsRes.json();
      setStats(statsData.data || {});

    } catch (error) {
      console.error('Error fetching replenishment data:', error);
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8032/api/replenishment/analyze', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        alert(`Analysis complete! Found ${data.data.total_recommendations} products needing replenishment.`);
        fetchData();
      }
    } catch (error) {
      console.error('Error running analysis:', error);
      alert('Failed to run analysis');
    } finally {
      setLoading(false);
    }
  };

  const createPurchaseOrder = async (recommendations) => {
    try {
      // Group recommendations by vendor (for now, use a default vendor)
      const items = recommendations.map(rec => ({
        product_id: rec.product_id,
        quantity: rec.recommended_quantity,
        unit_cost: 10.00 // This should come from product cost
      }));

      const response = await fetch('http://localhost:8032/api/purchase-orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vendor_id: 1, // This should be selected by user
          items: items,
          expected_delivery_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          notes: 'Auto-generated from replenishment recommendations'
        })
      });

      const data = await response.json();
      
      if (data.success) {
        alert(`Purchase order ${data.data.po_number} created successfully!`);
        fetchData();
      }
    } catch (error) {
      console.error('Error creating purchase order:', error);
      alert('Failed to create purchase order');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-blue-600 bg-blue-50';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'critical': return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'high': return <TrendingUp className="w-5 h-5 text-orange-600" />;
      default: return <Package className="w-5 h-5 text-yellow-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'delivered': return 'text-green-600 bg-green-50';
      case 'in_transit': return 'text-blue-600 bg-blue-50';
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      case 'cancelled': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading && !stats) {
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
          <h1 className="text-3xl font-bold text-gray-900">Inventory Replenishment</h1>
          <p className="text-gray-600 mt-1">Automated inventory replenishment and purchase order management</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={runAnalysis}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            Run Analysis
          </button>
          <button
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Plus className="w-5 h-5" />
            New PO
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl shadow-sm p-6 border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Products Monitored</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {stats.products_monitored || 0}
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
            className="bg-white rounded-xl shadow-sm p-6 border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Critical Items</p>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {stats.pending_recommendations?.critical || 0}
                </p>
              </div>
              <div className="p-3 bg-red-50 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl shadow-sm p-6 border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">High Priority</p>
                <p className="text-2xl font-bold text-orange-600 mt-1">
                  {stats.pending_recommendations?.high || 0}
                </p>
              </div>
              <div className="p-3 bg-orange-50 rounded-lg">
                <TrendingUp className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl shadow-sm p-6 border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Pending</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {stats.pending_recommendations?.total || 0}
                </p>
              </div>
              <div className="p-3 bg-yellow-50 rounded-lg">
                <ShoppingCart className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Recommendations Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900">Replenishment Recommendations</h2>
            <div className="flex gap-3">
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="all">All Priorities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="pending">Pending</option>
                <option value="po_created">PO Created</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Priority
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SKU
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Stock
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reorder Point
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Recommended Qty
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reason
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recommendations.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-8 text-center text-gray-500">
                    No recommendations found. Run analysis to generate recommendations.
                  </td>
                </tr>
              ) : (
                recommendations.map((rec) => (
                  <tr key={rec.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getPriorityIcon(rec.priority)}
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(rec.priority)}`}>
                          {rec.priority}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{rec.product_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{rec.sku}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{rec.current_stock}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{rec.reorder_point}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-bold text-indigo-600">{rec.recommended_quantity}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{rec.reason.replace(/_/g, ' ')}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {rec.status === 'pending' && (
                        <button
                          onClick={() => createPurchaseOrder([rec])}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          Create PO
                        </button>
                      )}
                      {rec.po_id && (
                        <span className="text-green-600">PO #{rec.po_id}</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Purchase Orders Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Recent Purchase Orders</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  PO Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Order Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expected Delivery
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {purchaseOrders.slice(0, 10).map((po) => (
                <tr key={po.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{po.po_number}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(po.status)}`}>
                      {po.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      {po.order_date ? new Date(po.order_date).toLocaleDateString() : '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      {po.expected_delivery_date ? new Date(po.expected_delivery_date).toLocaleDateString() : '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {po.currency} {po.total_amount.toFixed(2)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-indigo-600 hover:text-indigo-900 mr-3">
                      View
                    </button>
                    <button className="text-gray-600 hover:text-gray-900">
                      <Download className="w-4 h-4 inline" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ReplenishmentDashboard;
