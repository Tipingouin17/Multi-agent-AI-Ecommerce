import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  XCircle,
  Play,
  Square,
  RotateCw,
  TrendingUp,
  TrendingDown,
  Cpu,
  MemoryStick
} from 'lucide-react'
import { motion } from 'framer-motion'

const AgentStatusCard = ({ 
  agent, 
  onStart, 
  onStop, 
  onRestart,
  showControls = true,
  showMetrics = true,
  compact = false
}) => {
  if (!agent) return null

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'running':
        return 'text-green-600 bg-green-100 border-green-200'
      case 'warning':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200'
      case 'critical':
      case 'error':
        return 'text-red-600 bg-red-100 border-red-200'
      case 'offline':
      case 'stopped':
        return 'text-gray-600 bg-gray-100 border-gray-200'
      default:
        return 'text-blue-600 bg-blue-100 border-blue-200'
    }
  }

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'running':
        return CheckCircle
      case 'warning':
        return AlertTriangle
      case 'critical':
      case 'error':
        return XCircle
      case 'offline':
      case 'stopped':
        return Clock
      default:
        return Activity
    }
  }

  const StatusIcon = getStatusIcon(agent.status)
  const statusColor = getStatusColor(agent.status)

  const formatUptime = (seconds) => {
    if (!seconds) return 'N/A'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }

  const formatLastSeen = (timestamp) => {
    if (!timestamp) return 'Never'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = Math.floor((now - date) / 1000)
    
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return date.toLocaleDateString()
  }

  if (compact) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <StatusIcon className={`w-5 h-5 ${statusColor.split(' ')[0]}`} />
                <div>
                  <h3 className="font-semibold text-sm">{agent.name || agent.agent_id}</h3>
                  <p className="text-xs text-gray-500">{formatLastSeen(agent.last_heartbeat)}</p>
                </div>
              </div>
              <Badge className={statusColor}>
                {agent.status}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <StatusIcon className={`w-6 h-6 ${statusColor.split(' ')[0]}`} />
              <div>
                <CardTitle className="text-lg">{agent.name || agent.agent_id}</CardTitle>
                <CardDescription>{agent.description || 'Multi-agent system component'}</CardDescription>
              </div>
            </div>
            <Badge className={statusColor}>
              {agent.status}
            </Badge>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Metrics */}
          {showMetrics && agent.metrics && (
            <div className="grid grid-cols-2 gap-4">
              {/* CPU Usage */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center space-x-1 text-gray-600">
                    <Cpu className="w-4 h-4" />
                    <span>CPU</span>
                  </span>
                  <span className="font-semibold">{agent.metrics.cpu_usage?.toFixed(1) || 0}%</span>
                </div>
                <Progress value={agent.metrics.cpu_usage || 0} className="h-2" />
              </div>

              {/* Memory Usage */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center space-x-1 text-gray-600">
                    <MemoryStick className="w-4 h-4" />
                    <span>Memory</span>
                  </span>
                  <span className="font-semibold">{agent.metrics.memory_usage?.toFixed(1) || 0}%</span>
                </div>
                <Progress value={agent.metrics.memory_usage || 0} className="h-2" />
              </div>

              {/* Response Time */}
              <div className="text-center p-2 bg-gray-50 rounded">
                <div className="text-2xl font-bold text-gray-900">
                  {agent.metrics.response_time?.toFixed(0) || 0}ms
                </div>
                <div className="text-xs text-gray-600">Avg Response</div>
              </div>

              {/* Requests per Second */}
              <div className="text-center p-2 bg-gray-50 rounded">
                <div className="text-2xl font-bold text-gray-900">
                  {agent.metrics.requests_per_second?.toFixed(1) || 0}
                </div>
                <div className="text-xs text-gray-600">Req/sec</div>
              </div>
            </div>
          )}

          {/* Status Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Uptime:</span>
              <span className="ml-2 font-semibold">{formatUptime(agent.uptime)}</span>
            </div>
            <div>
              <span className="text-gray-600">Last Seen:</span>
              <span className="ml-2 font-semibold">{formatLastSeen(agent.last_heartbeat)}</span>
            </div>
            {agent.metrics?.error_rate !== undefined && (
              <>
                <div>
                  <span className="text-gray-600">Error Rate:</span>
                  <span className="ml-2 font-semibold">{agent.metrics.error_rate.toFixed(2)}%</span>
                </div>
                <div>
                  <span className="text-gray-600">Total Requests:</span>
                  <span className="ml-2 font-semibold">{agent.metrics.total_requests || 0}</span>
                </div>
              </>
            )}
          </div>

          {/* Controls */}
          {showControls && (
            <div className="flex items-center space-x-2 pt-4 border-t">
              <Button
                size="sm"
                variant="outline"
                onClick={() => onStart?.(agent.agent_id)}
                disabled={agent.status === 'running' || agent.status === 'healthy'}
                className="flex-1"
              >
                <Play className="w-4 h-4 mr-1" />
                Start
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onStop?.(agent.agent_id)}
                disabled={agent.status === 'stopped' || agent.status === 'offline'}
                className="flex-1"
              >
                <Square className="w-4 h-4 mr-1" />
                Stop
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onRestart?.(agent.agent_id)}
                className="flex-1"
              >
                <RotateCw className="w-4 h-4 mr-1" />
                Restart
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default AgentStatusCard

