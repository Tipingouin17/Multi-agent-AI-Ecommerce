import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const RealtimeChart = ({
  title,
  description,
  data = [],
  dataKey,
  xAxisKey = 'timestamp',
  type = 'line', // 'line', 'area', 'bar'
  color = '#3b82f6',
  height = 300,
  showTrend = true,
  showLegend = false,
  maxDataPoints = 50,
  unit = '',
  formatValue,
  className = ''
}) => {
  const [chartData, setChartData] = useState(data)
  const [trend, setTrend] = useState(null)

  useEffect(() => {
    // Keep only the last maxDataPoints
    const newData = data.slice(-maxDataPoints)
    setChartData(newData)

    // Calculate trend
    if (newData.length >= 2 && showTrend) {
      const recent = newData.slice(-5)
      const older = newData.slice(-10, -5)
      
      if (recent.length > 0 && older.length > 0) {
        const recentAvg = recent.reduce((sum, d) => sum + (d[dataKey] || 0), 0) / recent.length
        const olderAvg = older.reduce((sum, d) => sum + (d[dataKey] || 0), 0) / older.length
        
        const change = ((recentAvg - olderAvg) / olderAvg) * 100
        
        if (Math.abs(change) < 1) {
          setTrend({ direction: 'stable', value: 0 })
        } else if (change > 0) {
          setTrend({ direction: 'up', value: change })
        } else {
          setTrend({ direction: 'down', value: Math.abs(change) })
        }
      }
    }
  }, [data, dataKey, maxDataPoints, showTrend])

  const formatXAxis = (value) => {
    const date = new Date(value)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const formatYAxis = (value) => {
    if (formatValue) return formatValue(value)
    return `${value}${unit}`
  }

  const formatTooltipValue = (value) => {
    if (formatValue) return formatValue(value)
    return `${value}${unit}`
  }

  const getTrendIcon = () => {
    if (!trend) return null
    
    switch (trend.direction) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-600" />
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-600" />
      case 'stable':
        return <Minus className="w-4 h-4 text-gray-600" />
      default:
        return null
    }
  }

  const getTrendColor = () => {
    if (!trend) return 'text-gray-600'
    
    switch (trend.direction) {
      case 'up':
        return 'text-green-600'
      case 'down':
        return 'text-red-600'
      case 'stable':
        return 'text-gray-600'
      default:
        return 'text-gray-600'
    }
  }

  const renderChart = () => {
    const commonProps = {
      data: chartData,
      margin: { top: 5, right: 5, left: 0, bottom: 5 }
    }

    const axisProps = {
      xAxis: {
        dataKey: xAxisKey,
        tickFormatter: formatXAxis,
        stroke: '#9ca3af',
        fontSize: 12
      },
      yAxis: {
        tickFormatter: formatYAxis,
        stroke: '#9ca3af',
        fontSize: 12
      }
    }

    switch (type) {
      case 'area':
        return (
          <AreaChart {...commonProps}>
            <defs>
              <linearGradient id={`gradient-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.8}/>
                <stop offset="95%" stopColor={color} stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis {...axisProps.xAxis} />
            <YAxis {...axisProps.yAxis} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '6px' }}
              formatter={formatTooltipValue}
              labelFormatter={formatXAxis}
            />
            {showLegend && <Legend />}
            <Area 
              type="monotone" 
              dataKey={dataKey} 
              stroke={color} 
              fill={`url(#gradient-${dataKey})`}
              strokeWidth={2}
            />
          </AreaChart>
        )
      
      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis {...axisProps.xAxis} />
            <YAxis {...axisProps.yAxis} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '6px' }}
              formatter={formatTooltipValue}
              labelFormatter={formatXAxis}
            />
            {showLegend && <Legend />}
            <Bar dataKey={dataKey} fill={color} radius={[4, 4, 0, 0]} />
          </BarChart>
        )
      
      case 'line':
      default:
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis {...axisProps.xAxis} />
            <YAxis {...axisProps.yAxis} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '6px' }}
              formatter={formatTooltipValue}
              labelFormatter={formatXAxis}
            />
            {showLegend && <Legend />}
            <Line 
              type="monotone" 
              dataKey={dataKey} 
              stroke={color} 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        )
    }
  }

  const currentValue = chartData.length > 0 ? chartData[chartData.length - 1][dataKey] : 0

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          {showTrend && trend && (
            <div className="flex items-center space-x-2">
              {getTrendIcon()}
              <span className={`text-sm font-semibold ${getTrendColor()}`}>
                {trend.value.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
        <div className="mt-2">
          <div className="text-3xl font-bold">{formatTooltipValue(currentValue)}</div>
          <div className="text-sm text-gray-500">Current value</div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          {renderChart()}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

export default RealtimeChart

