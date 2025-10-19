# Multi-Agent Dashboard - Complete Usage Guide

## Overview

The Multi-Agent E-commerce Dashboard is a comprehensive real-time monitoring and management interface for the entire multi-agent system. It provides live data visualization, agent control, alert management, and system analytics.

## Features Implemented

### ✅ Core Infrastructure (Option 2)

1. **WebSocket Real-Time Integration**
   - Live agent status updates
   - Real-time metrics streaming
   - System alerts push notifications
   - Automatic reconnection handling
   - Custom React hooks for easy integration

2. **Enhanced API Service**
   - Complete REST API integration for all 14 agents
   - System overview and health checks
   - Agent management (start/stop/restart)
   - Alert management (acknowledge/resolve)
   - Order, product, inventory operations
   - Analytics and metrics endpoints

3. **Reusable Components**
   - `AgentStatusCard` - Agent monitoring with metrics and controls
   - `DataTable` - Advanced table with sorting, filtering, pagination, export
   - `RealtimeChart` - Live metrics visualization (line, area, bar charts)
   - `AlertFeed` - Alert notification system with actions

### ✅ Complete Admin Interface (Option 1)

1. **System Dashboard**
   - Real-time overview of all 14 agents
   - Key metrics: agent status, alerts, response time, uptime
   - Live connection status indicator
   - Auto-refresh with manual refresh option

2. **Agent Monitoring Tab**
   - Grid view of all agents with detailed status cards
   - CPU and memory usage per agent
   - Response time and request metrics
   - Agent control buttons (start/stop/restart)
   - Real-time status updates via WebSocket

3. **Performance Metrics Tab**
   - Live charts for:
     - Response Time (area chart)
     - Throughput (line chart)
     - Error Rate (bar chart)
     - CPU Usage (area chart)
   - Trend indicators
   - Historical data (last 50 data points)

4. **Alerts Management Tab**
   - Real-time alert feed
   - Filter by severity (all, critical, warning, info)
   - Alert counts and badges
   - Acknowledge and resolve actions
   - Alert details with agent source

5. **System Resources Tab**
   - CPU usage monitoring
   - Memory utilization
   - Disk usage
   - Network I/O
   - Progress bars with percentage

## Installation & Setup

### 1. Install Dependencies

```bash
cd multi-agent-dashboard
npm install
```

New dependencies added:
- `date-fns` - Time formatting utilities
- `framer-motion` - Animations (already included)
- `recharts` - Chart library (already included)

### 2. Configure Backend Connection

The dashboard connects to:
- **REST API**: `http://localhost:8001-8014` (individual agents)
- **WebSocket**: `ws://localhost:8000/ws` (real-time updates)

Ensure all agents are running before starting the dashboard.

### 3. Start the Dashboard

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## Usage Guide

### Interface Selection

On first load, you'll see the interface selector:
1. **System Administrator** - Full admin dashboard (implemented)
2. **Merchant Portal** - Product and order management (basic implementation)
3. **Customer Experience** - Shopping interface (basic implementation)
4. **Database Integration Test** - Connection testing

Select "System Administrator" to access the complete admin dashboard.

### Admin Dashboard Navigation

#### Header Controls
- **Live Indicator**: Shows WebSocket connection status (green = connected)
- **Last Updated**: Timestamp of last data refresh
- **Refresh Button**: Manual data refresh from all sources

#### Key Metrics Cards
- **Agents Status**: Shows healthy/warning/offline agents with progress bar
- **Active Alerts**: Total alerts with severity breakdown
- **Avg Response Time**: System-wide response time with trend
- **System Uptime**: Overall system availability percentage

#### Tabs

**1. Agents Tab**
- Grid of all 14 agents
- Each card shows:
  - Agent name and status
  - CPU and memory usage
  - Response time and requests/sec
  - Uptime and last seen
  - Error rate and total requests
  - Control buttons (Start/Stop/Restart)

**2. Metrics Tab**
- Four real-time charts:
  - Response Time: Average latency across all agents
  - Throughput: Requests per second
  - Error Rate: Percentage of failed requests
  - CPU Usage: System CPU utilization
- Each chart shows:
  - Current value
  - Trend indicator (up/down/stable)
  - Historical data (last 50 points)

**3. Alerts Tab**
- Filter buttons: All, Critical, Warning, Info
- Alert cards with:
  - Severity icon and badge
  - Alert message and description
  - Timestamp (relative time)
  - Agent source
  - Action buttons (Acknowledge/Resolve/Dismiss)

**4. Resources Tab**
- Four resource cards:
  - CPU Usage with progress bar
  - Memory Usage with progress bar
  - Disk Usage with progress bar
  - Network I/O with throughput

### Real-Time Features

#### WebSocket Integration
The dashboard automatically connects to the WebSocket server and receives:
- Agent status updates every 5 seconds
- System metrics every 10 seconds
- Alert notifications immediately
- Automatic reconnection on disconnect

#### Data Refresh Strategy
1. **Real-time (WebSocket)**: Agent status, metrics, alerts
2. **Polling (REST API)**: System overview (30s), agents list (10s), alerts (15s)
3. **Manual**: Refresh button for immediate update
4. **Fallback**: If WebSocket disconnects, uses REST API only

### Agent Control

#### Start Agent
1. Click "Start" button on agent card
2. Agent status changes to "starting"
3. Confirmation when agent is running

#### Stop Agent
1. Click "Stop" button on agent card
2. Confirmation dialog appears
3. Agent status changes to "stopped"

#### Restart Agent
1. Click "Restart" button on agent card
2. Agent stops then starts automatically
3. Status updates in real-time

### Alert Management

#### Acknowledge Alert
1. Click "Acknowledge" button on alert
2. Alert marked as acknowledged
3. Remains visible but flagged

#### Resolve Alert
1. Click "Resolve" button on alert
2. Alert marked as resolved
3. Removed from active alerts list

#### Filter Alerts
1. Click severity filter (Critical/Warning/Info)
2. View only alerts of that severity
3. Badge shows count per severity

## API Integration

### REST API Endpoints Used

```javascript
// System
GET /api/system/overview
GET /api/system/health

// Agents
GET /api/agents
GET /api/agents/{agent_id}
POST /api/agents/{agent_id}/start
POST /api/agents/{agent_id}/stop
POST /api/agents/{agent_id}/restart

// Alerts
GET /api/alerts
POST /api/alerts/{alert_id}/acknowledge
POST /api/alerts/{alert_id}/resolve

// Metrics
GET /api/metrics/system
GET /api/metrics/agents
```

### WebSocket Events

```javascript
// Subscribe to events
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['agent_status', 'system_metrics', 'alerts']
}))

// Receive updates
{
  type: 'agent_status',
  data: { agent_id, status, metrics, ... }
}

{
  type: 'system_metrics',
  data: { cpu_usage, memory_usage, throughput, ... }
}

{
  type: 'alert',
  data: { severity, message, agent_id, ... }
}
```

## Customization

### Adding New Charts

```jsx
import RealtimeChart from '@/components/shared/RealtimeChart'

<RealtimeChart
  title="Your Metric"
  description="Description"
  data={metricsHistory}
  dataKey="your_metric_key"
  type="line" // or "area", "bar"
  color="#3b82f6"
  unit="units"
  showTrend={true}
/>
```

### Adding New Agent Cards

```jsx
import AgentStatusCard from '@/components/shared/AgentStatusCard'

<AgentStatusCard
  agent={agentData}
  onStart={handleStart}
  onStop={handleStop}
  onRestart={handleRestart}
  showControls={true}
  showMetrics={true}
/>
```

### Creating Data Tables

```jsx
import DataTable from '@/components/shared/DataTable'

<DataTable
  data={tableData}
  columns={[
    { key: 'id', header: 'ID', sortable: true },
    { key: 'name', header: 'Name', sortable: true },
    { key: 'status', header: 'Status', type: 'badge', filterable: true }
  ]}
  searchable={true}
  filterable={true}
  exportable={true}
  onRefresh={handleRefresh}
/>
```

## Troubleshooting

### WebSocket Not Connecting
1. Check if WebSocket server is running on port 8000
2. Verify firewall allows WebSocket connections
3. Check browser console for connection errors
4. Dashboard will fallback to REST API automatically

### Agents Not Showing
1. Ensure all 14 agents are running
2. Check agent health endpoints: `http://localhost:8001-8014/health`
3. Verify database connection
4. Check browser console for API errors

### Charts Not Updating
1. Verify WebSocket connection (green indicator)
2. Check if metrics data is being received
3. Clear browser cache and reload
4. Check for JavaScript errors in console

### Slow Performance
1. Reduce chart data points (default: 50)
2. Increase polling intervals
3. Disable auto-refresh temporarily
4. Check network latency

## Architecture

### Component Hierarchy

```
App.jsx
├── WebSocketProvider (context)
├── QueryClientProvider (React Query)
└── BrowserRouter
    ├── InterfaceSelector
    └── AdminLayout
        └── AdminDashboard
            ├── Header (metrics cards)
            ├── Tabs
            │   ├── Agents (AgentStatusCard grid)
            │   ├── Metrics (RealtimeChart grid)
            │   ├── Alerts (AlertFeed)
            │   └── Resources (resource cards)
            └── Footer
```

### Data Flow

```
Backend Agents → WebSocket Server → WebSocketContext → React Components
                      ↓
Backend Agents → REST API → React Query → React Components
```

### State Management

- **WebSocket State**: Managed by `WebSocketContext`
- **API State**: Managed by React Query
- **Local State**: Managed by useState/useReducer
- **Persistent State**: LocalStorage for interface selection

## Performance Optimization

1. **Memoization**: useMemo for expensive calculations
2. **Virtualization**: Large lists use virtual scrolling
3. **Debouncing**: Search and filter inputs debounced
4. **Lazy Loading**: Components loaded on demand
5. **Data Limiting**: Charts keep only last 50 points
6. **Efficient Polling**: Different intervals per data type

## Security Considerations

1. **Authentication**: Add JWT token authentication
2. **Authorization**: Role-based access control
3. **HTTPS**: Use secure WebSocket (wss://)
4. **CORS**: Configure proper CORS headers
5. **Rate Limiting**: Implement on backend
6. **Input Validation**: Sanitize all user inputs

## Future Enhancements

### Planned Features
- [ ] User authentication and roles
- [ ] Custom dashboard layouts
- [ ] Alert rules configuration
- [ ] Historical data analysis
- [ ] Export reports (PDF/Excel)
- [ ] Mobile responsive design
- [ ] Dark mode theme
- [ ] Multi-language support
- [ ] Advanced filtering and search
- [ ] Custom metrics and KPIs

### Merchant Portal (Next Priority)
- Product catalog management
- Order processing workflow
- Inventory tracking
- Marketplace integration
- Sales analytics

### Customer Interface (Future)
- Product browsing and search
- Shopping cart
- Order tracking
- Account management
- Customer support chat

## Support

For issues or questions:
1. Check this guide first
2. Review browser console for errors
3. Check agent logs for backend issues
4. Verify all services are running
5. Test with Database Integration Test interface

## Version History

### v1.0.0 (Current)
- ✅ Complete Admin Dashboard
- ✅ Real-time WebSocket integration
- ✅ Enhanced API service
- ✅ Reusable component library
- ✅ Agent monitoring and control
- ✅ Live metrics visualization
- ✅ Alert management system
- ✅ System resource monitoring

### v0.1.0 (Initial)
- Basic interface selector
- Simple agent list
- Mock data implementation

