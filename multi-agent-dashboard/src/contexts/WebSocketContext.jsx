import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react'
import { toast } from 'sonner'

const WebSocketContext = createContext(null)

export const useWebSocket = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider')
  }
  return context
}

export const WebSocketProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttemptsRef = useRef(0)
  const listenersRef = useRef(new Map())
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000

  // Get WebSocket URL from environment or default
  const getWebSocketUrl = () => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8015/ws'
    return wsUrl
  }

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }

    setConnectionStatus('connecting')
    const wsUrl = getWebSocketUrl()
    
    try {
      console.log(`Connecting to WebSocket: ${wsUrl}`)
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setConnectionStatus('connected')
        reconnectAttemptsRef.current = 0
        
        // Send initial connection message
        ws.send(JSON.stringify({
          type: 'connection',
          client_type: 'dashboard',
          timestamp: new Date().toISOString()
        }))
        
        toast.success('Connected to real-time updates')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('WebSocket message received:', data)
          setLastMessage(data)
          
          // Notify all listeners for this event type
          const eventType = data.type || data.event_type
          if (eventType && listenersRef.current.has(eventType)) {
            const listeners = listenersRef.current.get(eventType)
            listeners.forEach(callback => callback(data))
          }
          
          // Notify global listeners
          if (listenersRef.current.has('*')) {
            const globalListeners = listenersRef.current.get('*')
            globalListeners.forEach(callback => callback(data))
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.warn('WebSocket error (real-time updates unavailable):', error)
        setConnectionStatus('error')
        // Don't show error toast - WebSocket is optional
      }

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        setConnectionStatus('disconnected')
        wsRef.current = null
        
        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectDelay * reconnectAttemptsRef.current)
          
          // Silent reconnection - don't spam user with notifications
        } else {
          console.log('WebSocket connection failed - continuing without real-time updates')
          // Don't show error toast - WebSocket is optional
        }
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Error creating WebSocket connection:', error)
      setConnectionStatus('error')
    }
  }, [])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setIsConnected(false)
    setConnectionStatus('disconnected')
  }, [])

  // Send message through WebSocket
  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message)
      wsRef.current.send(messageStr)
      return true
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message)
      return false
    }
  }, [])

  // Subscribe to specific event types
  const subscribe = useCallback((eventType, callback) => {
    if (!listenersRef.current.has(eventType)) {
      listenersRef.current.set(eventType, new Set())
    }
    listenersRef.current.get(eventType).add(callback)
    
    // Return unsubscribe function
    return () => {
      const listeners = listenersRef.current.get(eventType)
      if (listeners) {
        listeners.delete(callback)
        if (listeners.size === 0) {
          listenersRef.current.delete(eventType)
        }
      }
    }
  }, [])

  // Subscribe to all events
  const subscribeAll = useCallback((callback) => {
    return subscribe('*', callback)
  }, [subscribe])

  // Connect on mount
  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  const value = {
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    subscribe,
    subscribeAll,
    connect,
    disconnect
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}

// Custom hook for agent status updates
export const useAgentStatus = (agentId = null) => {
  const [agentStatuses, setAgentStatuses] = useState({})
  const { subscribe } = useWebSocket()

  useEffect(() => {
    const unsubscribe = subscribe('agent:status', (data) => {
      if (!agentId || data.agent_id === agentId) {
        setAgentStatuses(prev => ({
          ...prev,
          [data.agent_id]: data
        }))
      }
    })

    return unsubscribe
  }, [subscribe, agentId])

  return agentId ? agentStatuses[agentId] : agentStatuses
}

// Custom hook for system alerts
export const useSystemAlerts = () => {
  const [alerts, setAlerts] = useState([])
  const { subscribe } = useWebSocket()

  useEffect(() => {
    const unsubscribe = subscribe('alert:new', (data) => {
      setAlerts(prev => [data, ...prev].slice(0, 50)) // Keep last 50 alerts
      
      // Show toast for critical alerts
      if (data.severity === 'critical') {
        toast.error(data.message, {
          duration: 10000,
          action: {
            label: 'View',
            onClick: () => console.log('View alert:', data)
          }
        })
      }
    })

    return unsubscribe
  }, [subscribe])

  return alerts
}

// Custom hook for order updates
export const useOrderUpdates = () => {
  const [orders, setOrders] = useState([])
  const { subscribe } = useWebSocket()

  useEffect(() => {
    const unsubscribeCreated = subscribe('order:created', (data) => {
      setOrders(prev => [data, ...prev])
      toast.success(`New order: ${data.order_id}`)
    })

    const unsubscribeUpdated = subscribe('order:updated', (data) => {
      setOrders(prev => prev.map(order => 
        order.order_id === data.order_id ? { ...order, ...data } : order
      ))
    })

    return () => {
      unsubscribeCreated()
      unsubscribeUpdated()
    }
  }, [subscribe])

  return orders
}

// Custom hook for inventory alerts
export const useInventoryAlerts = () => {
  const [lowStockItems, setLowStockItems] = useState([])
  const { subscribe } = useWebSocket()

  useEffect(() => {
    const unsubscribe = subscribe('inventory:low', (data) => {
      setLowStockItems(prev => {
        const exists = prev.find(item => item.product_id === data.product_id)
        if (exists) {
          return prev.map(item => 
            item.product_id === data.product_id ? data : item
          )
        }
        return [...prev, data]
      })
      
      toast.warning(`Low stock: ${data.product_name} (${data.quantity} remaining)`)
    })

    return unsubscribe
  }, [subscribe])

  return lowStockItems
}

// Custom hook for system metrics
export const useSystemMetrics = () => {
  const [metrics, setMetrics] = useState(null)
  const { subscribe } = useWebSocket()

  useEffect(() => {
    const unsubscribe = subscribe('system:metrics', (data) => {
      setMetrics(data)
    })

    return unsubscribe
  }, [subscribe])

  return metrics
}

export default WebSocketContext

