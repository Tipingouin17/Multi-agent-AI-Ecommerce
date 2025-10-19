import { useState, useEffect } from 'react';
import { apiService } from '@/lib/api'

/**
 * Alerts Management Component
 * 
 * Provides a comprehensive interface for viewing, managing, and resolving
 * system alerts from all agents.
 */
function AlertsManagement() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolution, setResolution] = useState('');
  const [resolutionInProgress, setResolutionInProgress] = useState(false);
  const [filter, setFilter] = useState('all'); // 'all', 'active', 'resolved'
  const [severityFilter, setSeverityFilter] = useState('all'); // 'all', 'critical', 'high', 'medium', 'low'

  // Load alerts on component mount
  useEffect(() => {
    loadAlerts();
    
    // Set up polling for regular updates
    const interval = setInterval(loadAlerts, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, [filter, severityFilter]);

  // Load alerts from API
  async function loadAlerts() {
    try {
      setLoading(true);
      const activeOnly = filter === 'active';
      const data = await apiService.getSystemAlerts(activeOnly);
      
      // Apply severity filter if needed
      let filteredData = data;
      if (severityFilter !== 'all') {
        filteredData = data.filter(alert => alert.severity === severityFilter);
      }
      
      setAlerts(filteredData);
      setError(null);
    } catch (err) {
      setError("Failed to load alerts: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // Handle alert resolution
  async function handleResolveAlert() {
    if (!selectedAlert || !resolution.trim()) return;
    
    try {
      setResolutionInProgress(true);
      await apiService.resolveAlert(selectedAlert.id, { resolution });
      
      // Show success message
      alert(`Alert resolved successfully`);
      
      // Refresh alerts
      loadAlerts();
      
      // Close modal
      setShowResolveModal(false);
      setSelectedAlert(null);
      setResolution('');
    } catch (err) {
      setError(`Failed to resolve alert: ${err.message}`);
    } finally {
      setResolutionInProgress(false);
    }
  }

  // Open resolve modal
  function openResolveModal(alert) {
    setSelectedAlert(alert);
    setShowResolveModal(true);
  }

  // Close resolve modal
  function closeResolveModal() {
    setShowResolveModal(false);
    setSelectedAlert(null);
    setResolution('');
  }

  // Get severity class
  function getSeverityClass(severity) {
    switch (severity) {
      case 'critical':
        return 'border-red-500 bg-red-50';
      case 'high':
        return 'border-orange-500 bg-orange-50';
      case 'medium':
        return 'border-yellow-500 bg-yellow-50';
      case 'low':
        return 'border-blue-500 bg-blue-50';
      default:
        return 'border-gray-500 bg-gray-50';
    }
  }

  // Get severity badge class
  function getSeverityBadgeClass(severity) {
    switch (severity) {
      case 'critical':
        return 'bg-red-200 text-red-800';
      case 'high':
        return 'bg-orange-200 text-orange-800';
      case 'medium':
        return 'bg-yellow-200 text-yellow-800';
      case 'low':
        return 'bg-blue-200 text-blue-800';
      default:
        return 'bg-gray-200 text-gray-800';
    }
  }

  // Loading state
  if (loading && alerts.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error && alerts.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="text-center p-6">
          <p className="text-red-500 mb-4">{error}</p>
          <button 
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            onClick={loadAlerts}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Alerts Management</h2>
          <div className="flex gap-2">
            <button 
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
              onClick={loadAlerts}
              disabled={loading}
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>
        
        {/* Display error message if any */}
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
            <p>{error}</p>
            <button 
              className="mt-2 text-sm underline"
              onClick={() => setError(null)}
            >
              Dismiss
            </button>
          </div>
        )}
        
        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              className="border rounded px-3 py-2"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">All Alerts</option>
              <option value="active">Active Only</option>
              <option value="resolved">Resolved Only</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
            <select
              className="border rounded px-3 py-2"
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
        
        {/* Alert count summary */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="bg-gray-100 p-4 rounded">
            <h3 className="font-bold">Total</h3>
            <p className="text-2xl">{alerts.length}</p>
          </div>
          <div className="bg-red-100 p-4 rounded">
            <h3 className="font-bold">Critical</h3>
            <p className="text-2xl">{alerts.filter(a => a.severity === 'critical').length}</p>
          </div>
          <div className="bg-orange-100 p-4 rounded">
            <h3 className="font-bold">High</h3>
            <p className="text-2xl">{alerts.filter(a => a.severity === 'high').length}</p>
          </div>
          <div className="bg-yellow-100 p-4 rounded">
            <h3 className="font-bold">Medium</h3>
            <p className="text-2xl">{alerts.filter(a => a.severity === 'medium').length}</p>
          </div>
          <div className="bg-blue-100 p-4 rounded">
            <h3 className="font-bold">Low</h3>
            <p className="text-2xl">{alerts.filter(a => a.severity === 'low').length}</p>
          </div>
        </div>
        
        {/* Alerts list */}
        {alerts.length > 0 ? (
          <div className="space-y-4">
            {alerts.map(alert => (
              <div 
                key={alert.id} 
                className={`p-4 rounded border-l-4 ${getSeverityClass(alert.severity)}`}
              >
                <div className="flex justify-between">
                  <h3 className="font-bold">{alert.title}</h3>
                  <span className={`text-sm px-2 py-1 rounded ${getSeverityBadgeClass(alert.severity)}`}>
                    {alert.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                <div className="mt-2 text-sm text-gray-500 flex flex-wrap gap-x-4 gap-y-1">
                  <span>Time: {new Date(alert.timestamp).toLocaleString()}</span>
                  {alert.affected_agents && (
                    <span>Affected agents: {alert.affected_agents.join(', ')}</span>
                  )}
                  <span>Status: {alert.status}</span>
                </div>
                
                {alert.status === 'active' && (
                  <div className="mt-3">
                    <button 
                      className="bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200"
                      onClick={() => openResolveModal(alert)}
                    >
                      Resolve
                    </button>
                  </div>
                )}
                
                {alert.status === 'resolved' && alert.resolution && (
                  <div className="mt-2 text-sm">
                    <p className="font-medium">Resolution:</p>
                    <p className="text-gray-600">{alert.resolution}</p>
                    <p className="text-gray-500 mt-1">
                      Resolved by {alert.resolved_by || 'System'} at {new Date(alert.resolved_at).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">No alerts found matching your filters</p>
          </div>
        )}
      </div>
      
      {/* Resolve Alert Modal */}
      {showResolveModal && selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-lg w-full">
            <div className="p-6 border-b">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold">Resolve Alert</h2>
                <button 
                  className="text-gray-500 hover:text-gray-700"
                  onClick={closeResolveModal}
                  disabled={resolutionInProgress}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6">
              <div className="mb-4">
                <h3 className="font-bold">{selectedAlert.title}</h3>
                <p className="text-sm text-gray-600">{selectedAlert.description}</p>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Resolution</label>
                <textarea
                  className="w-full border rounded px-3 py-2 h-32"
                  placeholder="Describe how this alert was resolved..."
                  value={resolution}
                  onChange={(e ) => setResolution(e.target.value)}
                  disabled={resolutionInProgress}
                ></textarea>
              </div>
            </div>
            
            <div className="p-6 border-t bg-gray-50">
              <div className="flex justify-end gap-2">
                <button 
                  className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300"
                  onClick={closeResolveModal}
                  disabled={resolutionInProgress}
                >
                  Cancel
                </button>
                <button 
                  className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
                  onClick={handleResolveAlert}
                  disabled={resolutionInProgress || !resolution.trim()}
                >
                  {resolutionInProgress ? 'Resolving...' : 'Resolve Alert'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AlertsManagement;
