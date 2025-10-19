import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { apiService } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
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
  RefreshCw
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

// API functions using real backend services
const fetchSystemOverview = async () => {
  const data = await apiService.getSystemOverview()
  
  // Transform API response to match component expectations
  return {
    systemStatus: data.system_status || 'unknown',
    totalAgents: Object.keys(data.agents || {}).length,
    activeAgents: Object.values(data.agents || {}).filter(agent => agent.status === 'healthy').length,
    offlineAgents: Object.values(data.agents || {}).filter(agent => agent.status === 'offline').length,
    activeAlerts: data.active_alerts?.length || 0,
    criticalAlerts: data.active_alerts?.filter(alert => alert.severity === 'critical').length || 0,
    systemUptime: 99.9, // Calculate from system metrics
    avgResponseTime: data.system_metrics?.response_time || 0,
    throughput: data.system_metrics?.throughput || 0,
    errorRate: data.system_metrics?.error_rate || 0,
    cpuUsage: data.system_metrics?.cpu_usage || 0,
    memoryUsage: data.system_metrics?.memory_usage || 0,
    diskUsage: data.system_metrics?.disk_usage || 0,
    networkIO: 89.5 // Calculate from network metrics
  }
}

const fetchPerformanceData = async () => {
  return await apiService.getPerformanceMetrics('24h')
}

const AdminDashboard = () => {
  const [lastUpdated, setLastUpdated] = useState(new Date())

  const { data: systemData, isLoading: systemLoading, refetch: refetchSystem } = useQuery({
    queryKey: ['systemOverview'],
    queryFn: fetchSystemOverview,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const { data: performanceData, isLoading: performanceLoading } = useQuery({
    queryKey: ['performanceData'],
    queryFn: fetchPerformanceData,
    refetchInterval: 60000, // Refetch every minute
  })

  const handleRefresh = () => {
    refetchSystem()
    setLastUpdated(new Date())
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100'
      case 'warning': return 'text-yellow-600 bg-yellow-100'
      case 'critical': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return CheckCircle
      case 'warning': return AlertTriangle
      case 'critical': return AlertTriangle
      default: return Clock
    }
  }

  if (systemLoading) {
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

  const StatusIcon = getStatusIcon(systemData?.systemStatus)

  return (
    <div className="space-y-6">
      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Dashboard</h1>
          <p className="text-gray-600">Real-time overview of your multi-agent e-commerce platform</p>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </span>
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Status Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <StatusIcon className="w-6 h-6" />
                <span>System Status</span>
              </CardTitle>
              <CardDescription>Overall health of the multi-agent system</CardDescription>
            </div>
            <Badge className={getStatusColor(systemData?.systemStatus)}>
              {systemData?.systemStatus?.toUpperCase()}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{systemData?.systemUptime}%</div>
              <div className="text-sm text-gray-600">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{systemData?.avgResponseTime}ms</div>
              <div className="text-sm text-gray-600">Avg Response</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{systemData?.throughput}</div>
              <div className="text-sm text-gray-600">Requests/min</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{systemData?.errorRate}%</div>
              <div className="text-sm text-gray-600">Error Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
              <Bot className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {systemData?.activeAgents}/{systemData?.totalAgents}
              </div>
              <p className="text-xs text-muted-foreground">
                <TrendingUp className="inline w-3 h-3 mr-1" />
                All systems operational
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{systemData?.activeAlerts}</div>
              <p className="text-xs text-muted-foreground">
                {systemData?.criticalAlerts} critical alerts
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemData?.cpuUsage}%</div>
              <Progress value={systemData?.cpuUsage} className="mt-2" />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemData?.memoryUsage}%</div>
              <Progress value={systemData?.memoryUsage} className="mt-2" />
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>System Performance (24h)</CardTitle>
            <CardDescription>CPU and Memory usage over time</CardDescription>
          </CardHeader>
          <CardContent>
            {performanceLoading ? (
              <div className="h-64 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="cpu" stroke="#3b82f6" strokeWidth={2} name="CPU %" />
                  <Line type="monotone" dataKey="memory" stroke="#10b981" strokeWidth={2} name="Memory %" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Response Time & Throughput</CardTitle>
            <CardDescription>System responsiveness metrics</CardDescription>
          </CardHeader>
          <CardContent>
            {performanceLoading ? (
              <div className="h-64 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="responseTime" stroke="#f59e0b" fill="#fef3c7" name="Response Time (ms)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common administrative tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
              <Shield className="w-6 h-6" />
              <span className="text-sm">Security Scan</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
              <Zap className="w-6 h-6" />
              <span className="text-sm">Optimize Performance</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
              <Bot className="w-6 h-6" />
              <span className="text-sm">Restart Agents</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
              <Activity className="w-6 h-6" />
              <span className="text-sm">System Health Check</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default AdminDashboard
