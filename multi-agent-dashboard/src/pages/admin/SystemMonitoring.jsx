import { useState, useEffect } from 'react';
import { apiService } from '@/lib/api'

/**
 * System Monitoring Component
 * 
 * Provides real-time monitoring of system performance, resource usage,
 * and health metrics for the multi-agent e-commerce platform.
 */
function SystemMonitoring() {
  const [metrics, setMetrics] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [timeRange, setTimeRange] = useState('24h');
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [websocket, setWebsocket] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Load data on component mount and when time range changes
  useEffect(() => {
    loadData();
    
    // Set up auto-refresh
    let interval;
    if (autoRefresh) {
      interval = setInterval(loadData, refreshInterval * 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [timeRange, refreshInterval, autoRefresh]);

  // Set up WebSocket connection for real-time updates
  useEffect(() => {
    // Only set up WebSocket if auto-refresh is enabled
    if (!autoRefresh) return;
    
    // Handle WebSocket messages
    const handleWebSocketMessage = (data) => {
      if (data.type === 'system_update') {
        setSystemStatus(data.payload);
      } else if (data.type === 'metrics_update') {
        setMetrics(prev => {
          // Add new data point and keep only the last 100 points
          const updated = [data.payload, ...prev];
          return updated.slice(0, 100);
        });
      }
    };

    // Connect to WebSocket
    const ws = apiService.connectWebSocket(
      handleWebSocketMessage,
      (error) => console.error('WebSocket error:', error)
    );
    
    setWebsocket(ws);

    // Clean up WebSocket on unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [autoRefresh]);

  // Load data from API
  async function loadData() {
    try {
      setLoading(true);
      
      // Load system overview
      const statusData = await apiService.getSystemOverview();
      setSystemStatus(statusData);
      
      // Load performance metrics
      const metricsData = await apiService.getPerformanceMetrics(timeRange);
      setMetrics(metricsData);
      
      setError(null);
    } catch (err) {
      setError("Failed to load monitoring data: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // Toggle auto-refresh
  function toggleAutoRefresh() {
    setAutoRefresh(!autoRefresh);
  }

  // Loading state
  if (loading && !systemStatus) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">System Monitoring</h2>
          <div className="flex items-center gap-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoRefresh"
                className="h-4 w-4 text-blue-600 rounded"
                checked={autoRefresh}
                onChange={toggleAutoRefresh}
              />
              <label htmlFor="autoRefresh" className="ml-2 text-sm text-gray-700">
                Auto-refresh
              </label>
            </div>
            
            <select 
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
              className="border rounded px-2 py-1 text-sm"
              disabled={!autoRefresh}
            >
              <option value="5">Every 5s</option>
              <option value="10">Every 10s</option>
              <option value="30">Every 30s</option>
              <option value="60">Every 1m</option>
            </select>
            
            <select 
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="border rounded px-2 py-1"
            >
              <option value="1h">Last Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
            </select>
            
            <button 
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
              onClick={loadData}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Refresh'}
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
        
        {/* System Status Overview */}
        {systemStatus && (
          <div className="mb-6">
            <h3 className="text-lg font-bold mb-3">System Status</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className={`p-4 rounded ${
                systemStatus.system_status === 'healthy' ? 'bg-green-100' : 
                systemStatus.system_status === 'warning' ? 'bg-yellow-100' : 
                systemStatus.system_status === 'degraded' ? 'bg-orange-100' : 
                systemStatus.system_status === 'critical' ? 'bg-red-100' : 'bg-gray-100'
              }`}>
                <h3 className="font-bold">Overall Status</h3>
                <p className="text-2xl capitalize">{systemStatus.system_status || 'Unknown'}</p>
              </div>
              
              <div className="bg-blue-100 p-4 rounded">
                <h3 className="font-bold">Active Agents</h3>
                <p className="text-2xl">
                  {Object.values(systemStatus.agents || {}).filter(a => a.status === 'healthy').length}/
                  {Object.keys(systemStatus.agents || {}).length}
                </p>
              </div>
              
              <div className="bg-yellow-100 p-4 rounded">
                <h3 className="font-bold">Warnings</h3>
                <p className="text-2xl">
                  {Object.values(systemStatus.agents || {}).filter(a => a.status === 'warning').length}
                </p>
              </div>
              
              <div className="bg-red-100 p-4 rounded">
                <h3 className="font-bold">Active Alerts</h3>
                <p className="text-2xl">{systemStatus.active_alerts?.length || 0}</p>
              </div>
            </div>
            
            {/* System metrics summary */}
            {systemStatus.system_metrics && (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
                <div className="bg-gray-100 p-3 rounded">
                  <h3 className="text-xs font-semibold text-gray-500">CPU Usage</h3>
                  <p className="text-xl">{systemStatus.system_metrics.cpu_usage}%</p>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                    <div 
                      className={`h-1.5 rounded-full ${
                        systemStatus.system_metrics.cpu_usage > 80 ? 'bg-red-500' :
                        systemStatus.system_metrics.cpu_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${systemStatus.system_metrics.cpu_usage}%` }}
                    ></div>
                  </div>
                </div>
                <div className="bg-gray-100 p-3 rounded">
                  <h3 className="text-xs font-semibold text-gray-500">Memory Usage</h3>
                  <p className="text-xl">{systemStatus.system_metrics.memory_usage}%</p>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                    <div 
                      className={`h-1.5 rounded-full ${
                        systemStatus.system_metrics.memory_usage > 80 ? 'bg-red-500' :
                        systemStatus.system_metrics.memory_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${systemStatus.system_metrics.memory_usage}%` }}
                    ></div>
                  </div>
                </div>
                <div className="bg-gray-100 p-3 rounded">
                  <h3 className="text-xs font-semibold text-gray-500">Disk Usage</h3>
                  <p className="text-xl">{systemStatus.system_metrics.disk_usage}%</p>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                    <div 
                      className={`h-1.5 rounded-full ${
                        systemStatus.system_metrics.disk_usage > 80 ? 'bg-red-500' :
                        systemStatus.system_metrics.disk_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${systemStatus.system_metrics.disk_usage}%` }}
                    ></div>
                  </div>
                </div>
                <div className="bg-gray-100 p-3 rounded">
                  <h3 className="text-xs font-semibold text-gray-500">Response Time</h3>
                  <p className="text-xl">{systemStatus.system_metrics.response_time}ms</p>
                </div>
                <div className="bg-gray-100 p-3 rounded">
                  <h3 className="text-xs font-semibold text-gray-500">Error Rate</h3>
                  <p className="text-xl">{systemStatus.system_metrics.error_rate}%</p>
                </div>
                <div className="bg-gray-100 p-3 rounded">
                  <h3 className="text-xs font-semibold text-gray-500">Throughput</h3>
                  <p className="text-xl">{systemStatus.system_metrics.throughput}/min</p>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Performance Charts */}
        <div>
          <h3 className="text-lg font-bold mb-3">Performance Metrics</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* CPU Usage Chart */}
            <div className="border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">CPU Usage</h3>
              <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                <p className="text-gray-500">CPU Usage Chart would render here</p>
              </div>
            </div>
            
            {/* Memory Usage Chart */}
            <div className="border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">Memory Usage</h3>
              <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                <p className="text-gray-500">Memory Usage Chart would render here</p>
              </div>
            </div>
            
            {/* Response Time Chart */}
            <div className="border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">Response Time</h3>
              <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                <p className="text-gray-500">Response Time Chart would render here</p>
              </div>
            </div>
            
            {/* Throughput Chart */}
            <div className="border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">Throughput</h3>
              <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                <p className="text-gray-500">Throughput Chart would render here</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Agent Status Table */}
        {systemStatus && (
          <div>
            <h3 className="text-lg font-bold mb-3">Agent Status</h3>
            
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="py-2 px-4 text-left">Agent</th>
                    <th className="py-2 px-4 text-left">Status</th>
                    <th className="py-2 px-4 text-left">CPU</th>
                    <th className="py-2 px-4 text-left">Memory</th>
                    <th className="py-2 px-4 text-left">Response Time</th>
                    <th className="py-2 px-4 text-left">Last Heartbeat</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(systemStatus.agents || {}).map(([agentId, agent]) => (
                    <tr key={agentId} className="border-t hover:bg-gray-50">
                      <td className="py-2 px-4 font-medium">{agentId.replace(/_/g, ' ')}</td>
                      <td className="py-2 px-4">
                        <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                          agent.status === 'healthy' ? 'bg-green-500' : 
                          agent.status === 'warning' ? 'bg-yellow-500' : 
                          agent.status === 'error' ? 'bg-red-500' : 'bg-gray-500'
                        }`}></span>
                        <span className="capitalize">{agent.status}</span>
                      </td>
                      <td className="py-2 px-4">
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div 
                            className={`h-2.5 rounded-full ${
                              agent.cpu_usage > 80 ? 'bg-red-500' :
                              agent.cpu_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${agent.cpu_usage}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-500">{agent.cpu_usage}%</span>
                      </td>
                      <td className="py-2 px-4">
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div 
                            className={`h-2.5 rounded-full ${
                              agent.memory_usage > 80 ? 'bg-red-500' :
                              agent.memory_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${agent.memory_usage}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-500">{agent.memory_usage}%</span>
                      </td>
                      <td className="py-2 px-4">{agent.response_time}ms</td>
                      <td className="py-2 px-4">
                        {agent.last_heartbeat ? new Date(agent.last_heartbeat).toLocaleTimeString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* Active Alerts */}
        {systemStatus?.active_alerts?.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-bold mb-3">Active Alerts</h3>
            
            <div className="space-y-4">
              {systemStatus.active_alerts.map(alert => (
                <div 
                  key={alert.id} 
                  className={`p-4 rounded border-l-4 ${
                    alert.severity === 'critical' ? 'border-red-500 bg-red-50' :
                    alert.severity === 'high' ? 'border-orange-500 bg-orange-50' :
                    alert.severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                    'border-blue-500 bg-blue-50'
                  }`}
                >
                  <div className="flex justify-between">
                    <h3 className="font-bold">{alert.title}</h3>
                    <span className={`text-sm px-2 py-1 rounded ${
                      alert.severity === 'critical' ? 'bg-red-200 text-red-800' :
                      alert.severity === 'high' ? 'bg-orange-200 text-orange-800' :
                      alert.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                      'bg-blue-200 text-blue-800'
                    }`}>
                      {alert.severity}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                  <div className="mt-2 text-sm text-gray-500">
                    {alert.affected_agents && (
                      <span>Affected agents: {alert.affected_agents.join(', ')}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Performance Data Table */}
        {metrics.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-bold mb-3">Performance Data</h3>
            
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="py-2 px-4 text-left">Time</th>
                    <th className="py-2 px-4 text-right">CPU (%)</th>
                    <th className="py-2 px-4 text-right">Memory (%)</th>
                    <th className="py-2 px-4 text-right">Response Time (ms)</th>
                    <th className="py-2 px-4 text-right">Throughput (req/min)</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((point, index) => (
                    <tr key={index} className="border-t hover:bg-gray-50">
                      <td className="py-2 px-4">{point.time}</td>
                      <td className="py-2 px-4 text-right">{point.cpu}</td>
                      <td className="py-2 px-4 text-right">{point.memory}</td>
                      <td className="py-2 px-4 text-right">{point.response_time}</td>
                      <td className="py-2 px-4 text-right">{point.throughput}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SystemMonitoring;
