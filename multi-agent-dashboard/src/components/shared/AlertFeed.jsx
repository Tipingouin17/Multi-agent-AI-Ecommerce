import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  AlertTriangle, 
  Info, 
  XCircle, 
  CheckCircle, 
  Bell,
  BellOff,
  X,
  Check,
  Eye
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { formatDistanceToNow } from 'date-fns'

const AlertFeed = ({ 
  alerts = [], 
  onAcknowledge,
  onResolve,
  onDismiss,
  maxHeight = 600,
  showActions = true,
  compact = false
}) => {
  const [filter, setFilter] = useState('all') // 'all', 'critical', 'warning', 'info'

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return XCircle
      case 'warning':
        return AlertTriangle
      case 'info':
        return Info
      default:
        return Bell
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'text-red-600 bg-red-100 border-red-200'
      case 'warning':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200'
      case 'info':
        return 'text-blue-600 bg-blue-100 border-blue-200'
      default:
        return 'text-gray-600 bg-gray-100 border-gray-200'
    }
  }

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'all') return true
    return alert.severity?.toLowerCase() === filter
  })

  const alertCounts = {
    all: alerts.length,
    critical: alerts.filter(a => a.severity?.toLowerCase() === 'critical').length,
    warning: alerts.filter(a => a.severity?.toLowerCase() === 'warning').length,
    info: alerts.filter(a => a.severity?.toLowerCase() === 'info').length
  }

  const formatTime = (timestamp) => {
    if (!timestamp) return 'Unknown time'
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true })
    } catch {
      return 'Unknown time'
    }
  }

  if (compact) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center space-x-2">
              <Bell className="w-5 h-5" />
              <span>Alerts</span>
            </CardTitle>
            <Badge variant="secondary">{alerts.length}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px]">
            <div className="space-y-2">
              {filteredAlerts.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <BellOff className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                  <p>No alerts</p>
                </div>
              ) : (
                filteredAlerts.map((alert) => {
                  const SeverityIcon = getSeverityIcon(alert.severity)
                  return (
                    <div
                      key={alert.id || alert.alert_id}
                      className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                    >
                      <SeverityIcon className={`w-5 h-5 mt-0.5 ${getSeverityColor(alert.severity).split(' ')[0]}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {alert.message || alert.title}
                        </p>
                        <p className="text-xs text-gray-500">{formatTime(alert.timestamp || alert.created_at)}</p>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Bell className="w-6 h-6" />
              <span>System Alerts</span>
            </CardTitle>
            <CardDescription>Real-time system notifications and alerts</CardDescription>
          </div>
          <Badge variant="secondary" className="text-lg px-3 py-1">
            {alerts.length}
          </Badge>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center space-x-2 mt-4">
          {[
            { key: 'all', label: 'All', count: alertCounts.all },
            { key: 'critical', label: 'Critical', count: alertCounts.critical },
            { key: 'warning', label: 'Warning', count: alertCounts.warning },
            { key: 'info', label: 'Info', count: alertCounts.info }
          ].map(({ key, label, count }) => (
            <Button
              key={key}
              variant={filter === key ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(key)}
              className="flex items-center space-x-1"
            >
              <span>{label}</span>
              {count > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {count}
                </Badge>
              )}
            </Button>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        <ScrollArea style={{ height: maxHeight }}>
          <AnimatePresence>
            {filteredAlerts.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center py-12 text-gray-500"
              >
                <BellOff className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p className="text-lg font-medium">No {filter !== 'all' ? filter : ''} alerts</p>
                <p className="text-sm">All systems operating normally</p>
              </motion.div>
            ) : (
              <div className="space-y-3">
                {filteredAlerts.map((alert, index) => {
                  const SeverityIcon = getSeverityIcon(alert.severity)
                  const severityColor = getSeverityColor(alert.severity)

                  return (
                    <motion.div
                      key={alert.id || alert.alert_id || index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.2, delay: index * 0.05 }}
                      className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start space-x-4">
                        {/* Icon */}
                        <div className={`p-2 rounded-full ${severityColor}`}>
                          <SeverityIcon className="w-5 h-5" />
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h4 className="text-sm font-semibold text-gray-900">
                                {alert.title || alert.message}
                              </h4>
                              {alert.description && (
                                <p className="text-sm text-gray-600 mt-1">
                                  {alert.description}
                                </p>
                              )}
                              <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                                <span>{formatTime(alert.timestamp || alert.created_at)}</span>
                                {alert.agent_id && (
                                  <>
                                    <span>•</span>
                                    <span className="font-medium">{alert.agent_id}</span>
                                  </>
                                )}
                                {alert.source && (
                                  <>
                                    <span>•</span>
                                    <span>{alert.source}</span>
                                  </>
                                )}
                              </div>
                            </div>

                            <Badge className={severityColor}>
                              {alert.severity}
                            </Badge>
                          </div>

                          {/* Actions */}
                          {showActions && (
                            <div className="flex items-center space-x-2 mt-3">
                              {!alert.acknowledged && onAcknowledge && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => onAcknowledge(alert.id || alert.alert_id)}
                                  className="text-xs"
                                >
                                  <Eye className="w-3 h-3 mr-1" />
                                  Acknowledge
                                </Button>
                              )}
                              {!alert.resolved && onResolve && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => onResolve(alert.id || alert.alert_id)}
                                  className="text-xs"
                                >
                                  <Check className="w-3 h-3 mr-1" />
                                  Resolve
                                </Button>
                              )}
                              {onDismiss && (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => onDismiss(alert.id || alert.alert_id)}
                                  className="text-xs"
                                >
                                  <X className="w-3 h-3" />
                                </Button>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            )}
          </AnimatePresence>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

export default AlertFeed

