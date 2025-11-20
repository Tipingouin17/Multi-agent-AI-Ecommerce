import { useState, useEffect } from 'react';
import { apiService } from '@/lib/api'

/**
 * System Configuration Component
 * 
 * Provides an interface for viewing and modifying system-wide configuration
 * settings for the multi-agent e-commerce platform.
 */
function SystemConfiguration() {
  const [config, setConfig] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [activeSection, setActiveSection] = useState('general'); // 'general', 'agents', 'integrations', 'notifications'
  const [unsavedChanges, setUnsavedChanges] = useState(false);
  const [originalConfig, setOriginalConfig] = useState({});

  // Load configuration on component mount
  useEffect(() => {
    loadConfiguration();
  }, []);

  // Load configuration from API
  async function loadConfiguration() {
    try {
      setLoading(true);
      const data = await apiService.getSystemConfiguration();
      
      // Provide default configuration if API returns empty
      const defaultConfig = {
        general: {
          systemName: 'Multi-Agent E-Commerce Platform',
          environment: 'development',
          logLevel: 'info',
          maintenanceMode: false,
          debugMode: true
        },
        agents: {
          maxConcurrentAgents: 10,
          agentTimeout: 30,
          autoRestart: true,
          healthCheckInterval: 60
        },
        integrations: {
          enableMarketplaces: true,
          enablePaymentGateways: true,
          enableShippingCarriers: true
        },
        notifications: {
          enableEmail: true,
          enableSMS: false,
          enablePush: false
        }
      };
      
      const finalConfig = Object.keys(data).length > 0 ? data : defaultConfig;
      setConfig(finalConfig);
      setOriginalConfig(JSON.parse(JSON.stringify(finalConfig))); // Deep copy
      setError(null);
      setUnsavedChanges(false);
    } catch (err) {
      setError("Failed to load configuration: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // Save configuration
  async function saveConfiguration() {
    try {
      setSaving(true);
      await apiService.updateSystemConfiguration(config);
      setOriginalConfig(JSON.parse(JSON.stringify(config))); // Deep copy
      setUnsavedChanges(false);
      alert('Configuration saved successfully');
    } catch (err) {
      setError("Failed to save configuration: " + err.message);
      console.error(err);
    } finally {
      setSaving(false);
    }
  }

  // Handle input change
  function handleInputChange(section, key, value) {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
    setUnsavedChanges(true);
  }

  // Handle checkbox change
  function handleCheckboxChange(section, key) {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: !prev[section][key]
      }
    }));
    setUnsavedChanges(true);
  }

  // Reset configuration
  function handleReset() {
    if (window.confirm('Are you sure you want to reset all changes?')) {
      setConfig(JSON.parse(JSON.stringify(originalConfig))); // Deep copy
      setUnsavedChanges(false);
    }
  }

  // Loading state
  if (loading && Object.keys(config).length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error && Object.keys(config).length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="text-center p-6">
          <p className="text-red-500 mb-4">{error}</p>
          <button 
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            onClick={loadConfiguration}
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
          <h2 className="text-2xl font-bold">System Configuration</h2>
          <div className="flex gap-2">
            <button 
              className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400"
              onClick={handleReset}
              disabled={!unsavedChanges || saving}
            >
              Reset
            </button>
            <button 
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
              onClick={saveConfiguration}
              disabled={!unsavedChanges || saving}
            >
              {saving ? 'Saving...' : 'Save Changes'}
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
        
        {/* Unsaved changes warning */}
        {unsavedChanges && (
          <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
            <p>You have unsaved changes. Click "Save Changes" to apply them.</p>
          </div>
        )}
        
        {/* Configuration sections */}
        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar */}
          <div className="md:w-1/4">
            <div className="bg-gray-100 p-4 rounded">
              <h3 className="font-bold mb-3">Configuration Sections</h3>
              <nav className="space-y-1">
                <button
                  className={`w-full text-left px-3 py-2 rounded ${
                    activeSection === 'general' 
                      ? 'bg-blue-500 text-white' 
                      : 'hover:bg-gray-200'
                  }`}
                  onClick={() => setActiveSection('general')}
                >
                  General Settings
                </button>
                <button
                  className={`w-full text-left px-3 py-2 rounded ${
                    activeSection === 'agents' 
                      ? 'bg-blue-500 text-white' 
                      : 'hover:bg-gray-200'
                  }`}
                  onClick={() => setActiveSection('agents')}
                >
                  Agent Configuration
                </button>
                <button
                  className={`w-full text-left px-3 py-2 rounded ${
                    activeSection === 'integrations' 
                      ? 'bg-blue-500 text-white' 
                      : 'hover:bg-gray-200'
                  }`}
                  onClick={() => setActiveSection('integrations')}
                >
                  External Integrations
                </button>
                <button
                  className={`w-full text-left px-3 py-2 rounded ${
                    activeSection === 'notifications' 
                      ? 'bg-blue-500 text-white' 
                      : 'hover:bg-gray-200'
                  }`}
                  onClick={() => setActiveSection('notifications')}
                >
                  Notifications
                </button>
              </nav>
            </div>
          </div>
          
          {/* Main content */}
          <div className="md:w-3/4">
            {/* General Settings */}
            {activeSection === 'general' && config.general && (
              <div>
                <h3 className="text-lg font-bold mb-4">General Settings</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      System Name
                    </label>
                    <input
                      type="text"
                      className="w-full border rounded px-3 py-2"
                      value={config.general.systemName || ''}
                      onChange={(e) => handleInputChange('general', 'systemName', e.target.value)}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Environment
                    </label>
                    <select
                      className="w-full border rounded px-3 py-2"
                      value={config.general.environment || 'development'}
                      onChange={(e) => handleInputChange('general', 'environment', e.target.value)}
                    >
                      <option value="development">Development</option>
                      <option value="staging">Staging</option>
                      <option value="production">Production</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Log Level
                    </label>
                    <select
                      className="w-full border rounded px-3 py-2"
                      value={config.general.logLevel || 'info'}
                      onChange={(e) => handleInputChange('general', 'logLevel', e.target.value)}
                    >
                      <option value="debug">Debug</option>
                      <option value="info">Info</option>
                      <option value="warn">Warning</option>
                      <option value="error">Error</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="enableDebugMode"
                      className="h-4 w-4 text-blue-600 rounded"
                      checked={config.general.debugMode || false}
                      onChange={() => handleCheckboxChange('general', 'debugMode')}
                    />
                    <label htmlFor="enableDebugMode" className="ml-2 text-sm text-gray-700">
                      Enable Debug Mode
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="enableMetrics"
                      className="h-4 w-4 text-blue-600 rounded"
                      checked={config.general.enableMetrics || false}
                      onChange={() => handleCheckboxChange('general', 'enableMetrics')}
                    />
                    <label htmlFor="enableMetrics" className="ml-2 text-sm text-gray-700">
                      Enable Performance Metrics
                    </label>
                  </div>
                </div>
              </div>
            )}
            
            {/* Agent Configuration */}
            {activeSection === 'agents' && config.agents && (
              <div>
                <h3 className="text-lg font-bold mb-4">Agent Configuration</h3>
                
                <div className="space-y-6">
                  {Object.entries(config.agents).map(([agentId, agentConfig]) => (
                    <div key={agentId} className="border rounded p-4">
                      <h4 className="font-bold mb-2">{agentConfig.name || agentId}</h4>
                      
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Port
                          </label>
                          <input
                            type="number"
                            className="border rounded px-3 py-2"
                            value={agentConfig.port || ''}
                            onChange={(e) => handleInputChange('agents', agentId, {
                              ...agentConfig,
                              port: parseInt(e.target.value)
                            })}
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Max Concurrent Tasks
                          </label>
                          <input
                            type="number"
                            className="border rounded px-3 py-2"
                            value={agentConfig.maxConcurrentTasks || ''}
                            onChange={(e) => handleInputChange('agents', agentId, {
                              ...agentConfig,
                              maxConcurrentTasks: parseInt(e.target.value)
                            })}
                          />
                        </div>
                        
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            id={`${agentId}-enabled`}
                            className="h-4 w-4 text-blue-600 rounded"
                            checked={agentConfig.enabled !== false} // Default to true if undefined
                            onChange={() => handleInputChange('agents', agentId, {
                              ...agentConfig,
                              enabled: !agentConfig.enabled
                            })}
                          />
                          <label htmlFor={`${agentId}-enabled`} className="ml-2 text-sm text-gray-700">
                            Enabled
                          </label>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* External Integrations */}
            {activeSection === 'integrations' && config.integrations && (
              <div>
                <h3 className="text-lg font-bold mb-4">External Integrations</h3>
                
                <div className="space-y-6">
                  {/* API Keys */}
                  <div className="border rounded p-4">
                    <h4 className="font-bold mb-2">API Keys</h4>
                    
                    <div className="space-y-3">
                      {Object.entries(config.integrations.apiKeys || {}).map(([service, key]) => (
                        <div key={service}>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            {service}
                          </label>
                          <input
                            type="password"
                            className="w-full border rounded px-3 py-2"
                            value={key || ''}
                            onChange={(e) => handleInputChange('integrations', 'apiKeys', {
                              ...config.integrations.apiKeys,
                              [service]: e.target.value
                            })}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Marketplace Connections */}
                  <div className="border rounded p-4">
                    <h4 className="font-bold mb-2">Marketplace Connections</h4>
                    
                    <div className="space-y-3">
                      {Object.entries(config.integrations.marketplaces || {}).map(([marketplace, settings]) => (
                        <div key={marketplace} className="border-t pt-3 first:border-t-0 first:pt-0">
                          <h5 className="font-medium mb-2">{marketplace}</h5>
                          
                          <div className="space-y-2">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                API URL
                              </label>
                              <input
                                type="text"
                                className="w-full border rounded px-3 py-2"
                                value={settings.apiUrl || ''}
                                onChange={(e) => handleInputChange('integrations', 'marketplaces', {
                                  ...config.integrations.marketplaces,
                                  [marketplace]: {
                                    ...settings,
                                    apiUrl: e.target.value
                                  }
                                })}
                              />
                            </div>
                            
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                id={`${marketplace}-enabled`}
                                className="h-4 w-4 text-blue-600 rounded"
                                checked={settings.enabled !== false} // Default to true if undefined
                                onChange={() => handleInputChange('integrations', 'marketplaces', {
                                  ...config.integrations.marketplaces,
                                  [marketplace]: {
                                    ...settings,
                                    enabled: !settings.enabled
                                  }
                                })}
                              />
                              <label htmlFor={`${marketplace}-enabled`} className="ml-2 text-sm text-gray-700">
                                Enabled
                              </label>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Notifications */}
            {activeSection === 'notifications' && config.notifications && (
              <div>
                <h3 className="text-lg font-bold mb-4">Notifications</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="enableEmailNotifications"
                      className="h-4 w-4 text-blue-600 rounded"
                      checked={config.notifications.email?.enabled || false}
                      onChange={() => handleInputChange('notifications', 'email', {
                        ...config.notifications.email,
                        enabled: !config.notifications.email?.enabled
                      })}
                    />
                    <label htmlFor="enableEmailNotifications" className="ml-2 text-sm text-gray-700">
                      Enable Email Notifications
                    </label>
                  </div>
                  
                  {config.notifications.email?.enabled && (
                    <div className="ml-6 space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          SMTP Server
                        </label>
                        <input
                          type="text"
                          className="w-full border rounded px-3 py-2"
                          value={config.notifications.email.smtpServer || ''}
                          onChange={(e) => handleInputChange('notifications', 'email', {
                            ...config.notifications.email,
                            smtpServer: e.target.value
                          })}
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          SMTP Port
                        </label>
                        <input
                          type="number"
                          className="w-full border rounded px-3 py-2"
                          value={config.notifications.email.smtpPort || ''}
                          onChange={(e) => handleInputChange('notifications', 'email', {
                            ...config.notifications.email,
                            smtpPort: parseInt(e.target.value)
                          })}
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          From Email
                        </label>
                        <input
                          type="email"
                          className="w-full border rounded px-3 py-2"
                          value={config.notifications.email.fromEmail || ''}
                          onChange={(e) => handleInputChange('notifications', 'email', {
                            ...config.notifications.email,
                            fromEmail: e.target.value
                          })}
                        />
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center mt-4">
                    <input
                      type="checkbox"
                      id="enableSlackNotifications"
                      className="h-4 w-4 text-blue-600 rounded"
                      checked={config.notifications.slack?.enabled || false}
                      onChange={() => handleInputChange('notifications', 'slack', {
                        ...config.notifications.slack,
                        enabled: !config.notifications.slack?.enabled
                      })}
                    />
                    <label htmlFor="enableSlackNotifications" className="ml-2 text-sm text-gray-700">
                      Enable Slack Notifications
                    </label>
                  </div>
                  
                  {config.notifications.slack?.enabled && (
                    <div className="ml-6">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Webhook URL
                      </label>
                      <input
                        type="text"
                        className="w-full border rounded px-3 py-2"
                        value={config.notifications.slack.webhookUrl || ''}
                        onChange={(e) => handleInputChange('notifications', 'slack', {
                          ...config.notifications.slack,
                          webhookUrl: e.target.value
                        })}
                      />
                    </div>
                  )}
                  
                  <h4 className="font-bold mt-6 mb-2">Notification Events</h4>
                  
                  <div className="space-y-2">
                    {Object.entries(config.notifications.events || {}).map(([event, enabled]) => (
                      <div key={event} className="flex items-center">
                        <input
                          type="checkbox"
                          id={`event-${event}`}
                          className="h-4 w-4 text-blue-600 rounded"
                          checked={enabled}
                          onChange={() => handleInputChange('notifications', 'events', {
                            ...config.notifications.events,
                            [event]: !enabled
                          })}
                        />
                        <label htmlFor={`event-${event}`} className="ml-2 text-sm text-gray-700">
                          {event.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SystemConfiguration;
