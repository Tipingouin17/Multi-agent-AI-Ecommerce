import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Bot, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Zap,
  RefreshCw,
  Network
} from 'lucide-react';

// Agent network visualization component
const AgentNetworkDiagram = ({ agents }) => {
  const [hoveredAgent, setHoveredAgent] = useState(null);

  // Position agents in a circular layout
  const getAgentPosition = (index, total) => {
    const angle = (index / total) * 2 * Math.PI - Math.PI / 2;
    const radius = 200;
    return {
      x: 300 + radius * Math.cos(angle),
      y: 300 + radius * Math.sin(angle),
    };
  };

  const agentList = Object.entries(agents || {});

  return (
    <div className="relative w-full h-[600px] bg-gray-50 rounded-lg overflow-hidden">
      <svg width="600" height="600" className="mx-auto">
        {/* Central monitoring node */}
        <circle
          cx="300"
          cy="300"
          r="40"
          fill="#3B82F6"
          stroke="#2563EB"
          strokeWidth="3"
        />
        <text
          x="300"
          y="305"
          textAnchor="middle"
          fill="white"
          fontSize="12"
          fontWeight="bold"
        >
          AI Monitor
        </text>

        {/* Connections to agents */}
        {agentList.map(([name, data], index) => {
          const pos = getAgentPosition(index, agentList.length);
          const isHealthy = data.status === 'healthy';
          
          return (
            <g key={name}>
              {/* Connection line */}
              <line
                x1="300"
                y1="300"
                x2={pos.x}
                y2={pos.y}
                stroke={isHealthy ? '#10B981' : '#EF4444'}
                strokeWidth={hoveredAgent === name ? "3" : "1"}
                strokeDasharray={isHealthy ? "0" : "5,5"}
                opacity="0.5"
              />

              {/* Agent node */}
              <circle
                cx={pos.x}
                cy={pos.y}
                r="30"
                fill={isHealthy ? '#10B981' : '#EF4444'}
                stroke={isHealthy ? '#059669' : '#DC2626'}
                strokeWidth="2"
                className="cursor-pointer transition-all"
                onMouseEnter={() => setHoveredAgent(name)}
                onMouseLeave={() => setHoveredAgent(null)}
                style={{
                  filter: hoveredAgent === name ? 'drop-shadow(0 0 8px rgba(0,0,0,0.3))' : 'none'
                }}
              />

              {/* Agent label */}
              <text
                x={pos.x}
                y={pos.y + 50}
                textAnchor="middle"
                fontSize="11"
                fontWeight="500"
                fill="#374151"
              >
                {name}
              </text>

              {/* Status indicator */}
              <circle
                cx={pos.x + 20}
                cy={pos.y - 20}
                r="6"
                fill={isHealthy ? '#10B981' : '#EF4444'}
                stroke="white"
                strokeWidth="2"
              />
            </g>
          );
        })}

        {/* Hover tooltip */}
        {hoveredAgent && agents[hoveredAgent] && (
          <g>
            <rect
              x="50"
              y="50"
              width="200"
              height="100"
              fill="white"
              stroke="#E5E7EB"
              strokeWidth="1"
              rx="8"
              style={{ filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.1))' }}
            />
            <text x="70" y="75" fontSize="14" fontWeight="bold" fill="#111827">
              {hoveredAgent}
            </text>
            <text x="70" y="95" fontSize="12" fill="#6B7280">
              Status: {agents[hoveredAgent].status}
            </text>
            <text x="70" y="115" fontSize="12" fill="#6B7280">
              Uptime: {Math.floor(agents[hoveredAgent].uptime_seconds / 60)}m
            </text>
            <text x="70" y="135" fontSize="12" fill="#6B7280">
              Errors: {agents[hoveredAgent].error_count || 0}
            </text>
          </g>
        )}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-white p-4 rounded-lg shadow-md">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-sm text-gray-700">Healthy</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span className="text-sm text-gray-700">Error</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-gray-400"></div>
            <span className="text-sm text-gray-700">Active Connection</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-gray-400" style={{ backgroundImage: 'repeating-linear-gradient(to right, #9CA3AF 0, #9CA3AF 5px, transparent 5px, transparent 10px)' }}></div>
            <span className="text-sm text-gray-700">Inactive</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function AIMonitoringView() {
  const { data: monitoringData, isLoading, refetch } = useQuery({
    queryKey: ['ai-monitoring'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8014/system/overview');
      if (!response.ok) throw new Error('Failed to fetch monitoring data');
      return response.json();
    },
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  const agents = monitoringData?.agents || {};
  const agentList = Object.entries(agents);
  const healthyCount = agentList.filter(([_, data]) => data.status === 'healthy').length;
  const totalCount = agentList.length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Bot className="w-8 h-8 text-blue-600" />
            AI Monitoring Agent
          </h1>
          <p className="text-gray-600 mt-1">
            Real-time visualization of all agent connections and health status
          </p>
        </div>
        <Button onClick={() => refetch()} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Agents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{totalCount}</div>
            <p className="text-xs text-gray-500 mt-1">Active in system</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Healthy Agents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{healthyCount}</div>
            <p className="text-xs text-gray-500 mt-1">Operating normally</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Error Agents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{totalCount - healthyCount}</div>
            <p className="text-xs text-gray-500 mt-1">Requiring attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {totalCount > 0 ? Math.round((healthyCount / totalCount) * 100) : 0}%
            </div>
            <p className="text-xs text-gray-500 mt-1">Overall status</p>
          </CardContent>
        </Card>
      </div>

      {/* Network Visualization */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5" />
            Agent Network Topology
          </CardTitle>
          <CardDescription>
            Interactive visualization of agent connections and communication flow
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="h-[600px] flex items-center justify-center">
              <div className="text-center">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
                <p className="text-gray-600">Loading agent network...</p>
              </div>
            </div>
          ) : (
            <AgentNetworkDiagram agents={agents} />
          )}
        </CardContent>
      </Card>

      {/* Agent Details List */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Details</CardTitle>
          <CardDescription>
            Detailed status and metrics for each agent
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {agentList.map(([name, data]) => (
              <div 
                key={name}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${
                    data.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <div>
                    <h3 className="font-semibold text-gray-900">{name}</h3>
                    <p className="text-sm text-gray-600">
                      Uptime: {Math.floor(data.uptime_seconds / 60)} minutes
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <Badge variant={data.status === 'healthy' ? 'success' : 'destructive'}>
                    {data.status}
                  </Badge>
                  {data.error_count > 0 && (
                    <Badge variant="warning">
                      {data.error_count} errors
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

