import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Bot,
  Server,
  Zap,
  Shield,
  RefreshCw,
  Database,
  Cpu,
  HardDrive,
  Network
} from 'lucide-react'
import { formatDateTime, formatRelativeTime } from '@/utils/dateFormatter'

// Import our new components
import { useWebSocket, useAgentStatus, useSystemAlerts, useSystemMetrics } from '@/contexts/WebSocketContext'
import api from '@/lib/api-enhanced'
import AgentStatusCard from '@/components/shared/AgentStatusCard'
import RealtimeChart from '@/components/shared/RealtimeChart'
import AlertFeed from '@/components/shared/AlertFeed'

const AdminDashboard = () => {
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [performanceHistory, setPerformanceHistory] = useState([])

  // WebSocket integration
  const { isConnected, connectionStatus } = useWebSocket()
  const agentStatuses = useAgentStatus()
  const systemAlerts = useSystemAlerts()
  const systemMetrics = useSystemMetrics()

  // Fetch system overview
  const { data: systemData, isLoading, refetch } = useQuery({
    queryKey: ['systemOverview'],
    queryFn: api.system.getOverview,
    refetchInterval: 30000,
  })

  // Fetch agents
  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: api.agent.getAllAgents,
    refetchInterval: 10000,
  })

  // Fetch alerts
  const { data: alertsData } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => api.alert.getAlerts({ status: 'active', limit: 50 }),
    refetchInterval: 15000,
  })
  const alerts = alertsData?.alerts || []

  // Update performance history from WebSocket
  useEffect(() => {
    if (systemMetrics) {
      setPerformanceHistory(prev => {
        const newData = [...prev, {
          timestamp: new Date().toISOString(),
          cpu: systemMetrics.cpu_usage || 0,
          memory: systemMetrics.memory_usage || 0,
          throughput: systemMetrics.throughput || 0,
          responseTime: systemMetrics.response_time || 0
        }]
        // Keep last 50 data points
        return newData.slice(-50)
      })
    }
  }, [systemMetrics])

  const handleRefresh = () => {
    refetch()
    setLastUpdated(new Date())
  }

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await api.alert.acknowledgeAlert(alertId)
      refetch()
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
    }
  }

  const handleResolveAlert = async (alertId) => {
    try {
      await api.alert.resolveAlert(alertId, 'Resolved from dashboard')
      refetch()
    } catch (error) {
      console.error('Failed to resolve alert:', error)
    }
  }

  const handleAgentAction = async (action, agentId) => {
    try {
      switch (action) {
        case 'start':
          await api.agent.startAgent(agentId)
          break
        case 'stop':
          await api.agent.stopAgent(agentId)
          break
        case 'restart':
          await api.agent.restartAgent(agentId)
          break
      }
      refetch()
    } catch (error) {
      console.error(`Failed to ${action} agent:`, error)
    }
  }

  // Calculate statistics
  const stats = {
    totalAgents: Object.keys(agents || {}).length || 14,
    healthyAgents: Object.values(agents || {}).filter(a => a.status === 'healthy').length,
    warningAgents: Object.values(agents || {}).filter(a => a.status === 'warning').length,
    criticalAgents: Object.values(agents || {}).filter(a => a.status === 'critical' || a.status === 'error').length,
    offlineAgents: Object.values(agents || {}).filter(a => a.status === 'offline' || a.status === 'stopped').length,
    activeAlerts: (alerts.length || 0) + systemAlerts.length,
    criticalAlerts: (alerts.filter(a => a.severity === 'critical').length || 0) + 
                    systemAlerts.filter(a => a.severity === 'critical').length,
    systemUptime: systemData?.system_uptime || 99.9,
    avgResponseTime: systemMetrics?.response_time || systemData?.avg_response_time || 0,
    throughput: systemMetrics?.throughput || systemData?.throughput || 0,
    errorRate: systemMetrics?.error_rate || systemData?.error_rate || 0,
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-full"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Dashboard</h1>
          <p className="text-gray-600">Real-time overview of your multi-agent e-commerce platform</p>
        </div>
        <div className="flex items-center space-x-4">
          {/* WebSocket Status */}
          <Badge variant={isConnected ? 'default' : 'destructive'} className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span>{isConnected ? 'Live' : 'Disconnected'}</span>
          </Badge>
          
          <span className="text-sm text-gray-500">
            Last updated: {formatDateTime(lastUpdated)}
          </span>
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Agents */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center space-x-2">
                <Bot className="w-4 h-4" />
                <span>Total Agents</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.totalAgents}</div>
              <div className="flex items-center space-x-4 mt-2 text-sm">
                <span className="text-green-600 flex items-center">
                  <CheckCircle className="w-4 h-4 mr-1" />
                  {stats.healthyAgents} healthy
                </span>
                {stats.criticalAgents > 0 && (
                  <span className="text-red-600 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-1" />
                    {stats.criticalAgents} critical
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Active Alerts */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4" />
                <span>Active Alerts</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.activeAlerts}</div>
              <div className="flex items-center space-x-2 mt-2">
                {stats.criticalAlerts > 0 && (
                  <Badge variant="destructive">{stats.criticalAlerts} critical</Badge>
                )}
                <span className="text-sm text-gray-600">
                  {stats.activeAlerts - stats.criticalAlerts} warnings
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* System Uptime */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center space-x-2">
                <Server className="w-4 h-4" />
                <span>System Uptime</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.systemUptime.toFixed(2)}%</div>
              <Progress value={stats.systemUptime} className="mt-2" />
            </CardContent>
          </Card>
        </motion.div>

        {/* Avg Response Time */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center space-x-2">
                <Zap className="w-4 h-4" />
                <span>Avg Response Time</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.avgResponseTime.toFixed(0)}ms</div>
              <div className="flex items-center space-x-1 mt-2 text-sm text-gray-600">
                {stats.avgResponseTime < 100 ? (
                  <>
                    <TrendingDown className="w-4 h-4 text-green-600" />
                    <span className="text-green-600">Excellent</span>
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-4 h-4 text-yellow-600" />
                    <span className="text-yellow-600">Moderate</span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="agents" className="space-y-6">
        <TabsList>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.values(agents || {}).map((agent, index) => (
              <motion.div
                key={agent.agent_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <AgentStatusCard
                  agent={agentStatuses[agent.agent_id] || agent}
                  onStart={(id) => handleAgentAction('start', id)}
                  onStop={(id) => handleAgentAction('stop', id)}
                  onRestart={(id) => handleAgentAction('restart', id)}
                  showControls={true}
                  showMetrics={true}
                />
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RealtimeChart
              title="CPU Usage"
              description="System CPU utilization over time"
              data={performanceHistory}
              dataKey="cpu"
              type="area"
              color="#3b82f6"
              unit="%"
              height={250}
            />
            <RealtimeChart
              title="Memory Usage"
              description="System memory utilization over time"
              data={performanceHistory}
              dataKey="memory"
              type="area"
              color="#10b981"
              unit="%"
              height={250}
            />
            <RealtimeChart
              title="Throughput"
              description="Requests processed per second"
              data={performanceHistory}
              dataKey="throughput"
              type="line"
              color="#8b5cf6"
              unit=" req/s"
              height={250}
            />
            <RealtimeChart
              title="Response Time"
              description="Average response time in milliseconds"
              data={performanceHistory}
              dataKey="responseTime"
              type="line"
              color="#f59e0b"
              unit="ms"
              height={250}
            />
          </div>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-6">
          <AlertFeed
            alerts={[...(alerts || []), ...systemAlerts]}
            onAcknowledge={handleAcknowledgeAlert}
            onResolve={handleResolveAlert}
            maxHeight={600}
            showActions={true}
          />
        </TabsContent>

        {/* System Tab */}
        <TabsContent value="system" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* System Resources */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Cpu className="w-5 h-5" />
                  <span>CPU</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{systemMetrics?.cpu_usage?.toFixed(1) || 0}%</div>
                <Progress value={systemMetrics?.cpu_usage || 0} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <HardDrive className="w-5 h-5" />
                  <span>Memory</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{systemMetrics?.memory_usage?.toFixed(1) || 0}%</div>
                <Progress value={systemMetrics?.memory_usage || 0} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="w-5 h-5" />
                  <span>Disk</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{systemMetrics?.disk_usage?.toFixed(1) || 0}%</div>
                <Progress value={systemMetrics?.disk_usage || 0} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Network className="w-5 h-5" />
                  <span>Network</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{systemMetrics?.network_io?.toFixed(1) || 0} MB/s</div>
                <div className="text-sm text-gray-600 mt-2">I/O throughput</div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AdminDashboard

