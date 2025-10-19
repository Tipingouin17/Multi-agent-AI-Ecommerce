import { useState, useEffect } from 'react';
import { apiService } from '@/lib/api'

/**
 * Agent Management Component
 * 
 * Provides a comprehensive interface for monitoring and managing all agents
 * in the multi-agent e-commerce system.
 */
function AgentManagement() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionInProgress, setActionInProgress] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [agentLogs, setAgentLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);

  // Load agents on component mount
  useEffect(() => {
    loadAgents();
    
    // Set up polling for regular updates
    const interval = setInterval(loadAgents, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  // Load agent data from API
  async function loadAgents() {
    try {
      setLoading(true);
      const data = await apiService.getAgentHealth();
      setAgents(data);
      setError(null);
    } catch (err) {
      setError("Failed to load agents: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // Handle agent restart
  async function handleRestartAgent(agentId) {
    try {
      setActionInProgress(agentId);
      await apiService.restartAgent(agentId);
      
      // Show success message
      alert(`Agent ${agentId} restarted successfully`);
      
      // Refresh agent list
      loadAgents();
    } catch (err) {
      setError(`Failed to restart agent ${agentId}: ${err.message}`);
    } finally {
      setActionInProgress(null);
    }
  }

  // Handle agent stop
  async function handleStopAgent(agentId) {
    try {
      if (window.confirm(`Are you sure you want to stop agent ${agentId}?`)) {
        setActionInProgress(agentId);
        await apiService.stopAgent(agentId);
        
        // Show success message
        alert(`Agent ${agentId} stopped successfully`);
        
        // Refresh agent list
        loadAgents();
      }
    } catch (err) {
      setError(`Failed to stop agent ${agentId}: ${err.message}`);
    } finally {
      setActionInProgress(null);
    }
  }

  // Load agent logs
  async function loadAgentLogs(agentId) {
    try {
      setLogsLoading(true);
      const logs = await apiService.getAgentLogs(agentId);
      setAgentLogs(logs);
      setSelectedAgent(agents.find(a => a.agent_id === agentId));
      setShowDetails(true);
    } catch (err) {
      setError(`Failed to load logs for agent ${agentId}: ${err.message}`);
    } finally {
      setLogsLoading(false);
    }
  }

  // Close agent details modal
  function handleCloseDetails() {
    setShowDetails(false);
    setSelectedAgent(null);
    setAgentLogs([]);
  }

  // Loading state
  if (loading && agents.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error && agents.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="text-center p-6">
          <p className="text-red-500 mb-4">{error}</p>
          <button 
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            onClick={loadAgents}
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
          <h2 className="text-2xl font-bold">Agent Management</h2>
          <div className="flex gap-2">
            <button 
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
              onClick={loadAgents}
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
        
        {/* Agent status summary */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-100 p-4 rounded">
            <h3 className="font-bold">Total Agents</h3>
            <p className="text-2xl">{agents.length}</p>
          </div>
          <div className="bg-green-100 p-4 rounded">
            <h3 className="font-bold">Healthy</h3>
            <p className="text-2xl">{agents.filter(a => a.status === 'healthy').length}</p>
          </div>
          <div className="bg-yellow-100 p-4 rounded">
            <h3 className="font-bold">Warning</h3>
            <p className="text-2xl">{agents.filter(a => a.status === 'warning').length}</p>
          </div>
          <div className="bg-red-100 p-4 rounded">
            <h3 className="font-bold">Error</h3>
            <p className="text-2xl">{agents.filter(a => a.status === 'error').length}</p>
          </div>
        </div>
        
        {/* Agent cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map(agent => (
            <div key={agent.agent_id} className="border rounded-lg overflow-hidden">
              {/* Agent card header */}
              <div className={`p-4 ${
                agent.status === 'healthy' ? 'bg-green-100' : 
                agent.status === 'warning' ? 'bg-yellow-100' : 
                agent.status === 'error' ? 'bg-red-100' : 'bg-gray-100'
              }`}>
                <div className="flex justify-between items-center">
                  <h3 className="font-bold">{agent.agent_name}</h3>
                  <span className={`text-sm px-2 py-1 rounded ${
                    agent.status === 'healthy' ? 'bg-green-200 text-green-800' : 
                    agent.status === 'warning' ? 'bg-yellow-200 text-yellow-800' : 
                    agent.status === 'error' ? 'bg-red-200 text-red-800' : 'bg-gray-200 text-gray-800'
                  }`}>
                    {agent.status}
                  </span>
                </div>
              </div>
              
              {/* Agent card body */}
              <div className="p-4">
                <div className="grid grid-cols-2 gap-2 mb-4">
                  <div>
                    <div className="text-sm text-gray-500">CPU Usage</div>
                    <div className="font-medium">{agent.cpu_usage}%</div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                      <div 
                        className={`h-1.5 rounded-full ${
                          agent.cpu_usage > 80 ? 'bg-red-500' :
                          agent.cpu_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${agent.cpu_usage}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Memory Usage</div>
                    <div className="font-medium">{agent.memory_usage}%</div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                      <div 
                        className={`h-1.5 rounded-full ${
                          agent.memory_usage > 80 ? 'bg-red-500' :
                          agent.memory_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${agent.memory_usage}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Response Time</div>
                    <div className="font-medium">{agent.response_time}ms</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Last Heartbeat</div>
                    <div className="font-medium">
                      {agent.last_heartbeat ? new Date(agent.last_heartbeat).toLocaleTimeString() : 'N/A'}
                    </div>
                  </div>
                </div>
                
                {/* Agent action buttons */}
                <div className="flex gap-2">
                  <button 
                    className="flex-1 bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200"
                    onClick={() => loadAgentLogs(agent.agent_id)}
                    disabled={actionInProgress === agent.agent_id}
                  >
                    Details
                  </button>
                  <button 
                    className="flex-1 bg-green-100 text-green-700 px-3 py-1 rounded hover:bg-green-200"
                    onClick={() => handleRestartAgent(agent.agent_id)}
                    disabled={actionInProgress === agent.agent_id}
                  >
                    {actionInProgress === agent.agent_id ? 'Working...' : 'Restart'}
                  </button>
                  <button 
                    className="flex-1 bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200"
                    onClick={() => handleStopAgent(agent.agent_id)}
                    disabled={actionInProgress === agent.agent_id}
                  >
                    Stop
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Agent Details Modal */}
      {showDetails && selectedAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="p-6 border-b">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">{selectedAgent.agent_name} Details</h2>
                <button 
                  className="text-gray-500 hover:text-gray-700"
                  onClick={handleCloseDetails}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 120px )' }}>
              {/* Agent Details */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <h3 className="font-bold mb-2">Agent Information</h3>
                  <table className="w-full">
                    <tbody>
                      <tr>
                        <td className="py-1 text-gray-500">ID:</td>
                        <td>{selectedAgent.agent_id}</td>
                      </tr>
                      <tr>
                        <td className="py-1 text-gray-500">Status:</td>
                        <td>
                          <span className={`px-2 py-0.5 rounded text-sm ${
                            selectedAgent.status === 'healthy' ? 'bg-green-200 text-green-800' : 
                            selectedAgent.status === 'warning' ? 'bg-yellow-200 text-yellow-800' : 
                            'bg-red-200 text-red-800'
                          }`}>
                            {selectedAgent.status}
                          </span>
                        </td>
                      </tr>
                      <tr>
                        <td className="py-1 text-gray-500">Last Heartbeat:</td>
                        <td>{selectedAgent.last_heartbeat ? new Date(selectedAgent.last_heartbeat).toLocaleString() : 'N/A'}</td>
                      </tr>
                      <tr>
                        <td className="py-1 text-gray-500">Version:</td>
                        <td>{selectedAgent.version || 'N/A'}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                
                <div>
                  <h3 className="font-bold mb-2">Performance Metrics</h3>
                  <table className="w-full">
                    <tbody>
                      <tr>
                        <td className="py-1 text-gray-500">CPU Usage:</td>
                        <td>{selectedAgent.cpu_usage}%</td>
                      </tr>
                      <tr>
                        <td className="py-1 text-gray-500">Memory Usage:</td>
                        <td>{selectedAgent.memory_usage}%</td>
                      </tr>
                      <tr>
                        <td className="py-1 text-gray-500">Response Time:</td>
                        <td>{selectedAgent.response_time}ms</td>
                      </tr>
                      <tr>
                        <td className="py-1 text-gray-500">Active Tasks:</td>
                        <td>{selectedAgent.active_tasks || 0}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              
              {/* Agent Logs */}
              <div>
                <h3 className="font-bold mb-2">Recent Logs</h3>
                {logsLoading ? (
                  <div className="flex items-center justify-center h-40">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  </div>
                ) : agentLogs.length > 0 ? (
                  <div className="bg-gray-100 rounded p-4 max-h-96 overflow-y-auto font-mono text-sm">
                    {agentLogs.map((log, index) => (
                      <div 
                        key={index} 
                        className={`py-1 ${
                          log.level === 'ERROR' ? 'text-red-600' :
                          log.level === 'WARNING' ? 'text-yellow-600' :
                          log.level === 'INFO' ? 'text-blue-600' : ''
                        }`}
                      >
                        <span className="text-gray-500">[{new Date(log.timestamp).toLocaleTimeString()}]</span> {log.message}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No logs available</p>
                )}
              </div>
            </div>
            
            <div className="p-6 border-t bg-gray-50">
              <div className="flex justify-end gap-2">
                <button 
                  className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300"
                  onClick={handleCloseDetails}
                >
                  Close
                </button>
                <button 
                  className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                  onClick={() => loadAgentLogs(selectedAgent.agent_id)}
                  disabled={logsLoading}
                >
                  {logsLoading ? 'Loading...' : 'Refresh Logs'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AgentManagement;
