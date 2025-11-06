import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, BarChart3, RefreshCw, Play, AlertCircle, CheckCircle,
  Calendar, Target, Activity, Zap
} from 'lucide-react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';

const ForecastingDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [productId, setProductId] = useState('1');
  const [horizonDays, setHorizonDays] = useState('30');
  const [modelType, setModelType] = useState('ensemble');

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8037/api/forecasting/dashboard');
      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateForecast = async () => {
    try {
      setGenerating(true);
      const response = await fetch('http://localhost:8037/api/forecasting/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: parseInt(productId),
          horizon_days: parseInt(horizonDays),
          model_type: modelType
        })
      });
      const data = await response.json();
      
      if (data.success) {
        setForecastData(data);
        await fetchDashboard();
      }
    } catch (error) {
      console.error('Error generating forecast:', error);
    } finally {
      setGenerating(false);
    }
  };

  // Prepare chart data
  const chartData = forecastData?.forecast?.map(f => ({
    date: new Date(f.forecast_date).toLocaleDateString(),
    forecast: Math.round(f.forecast_value),
    lower: Math.round(f.lower_bound),
    upper: Math.round(f.upper_bound)
  })) || [];

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const summary = dashboardData?.summary || {};
  const models = dashboardData?.models || [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">ML-Based Demand Forecasting</h1>
          <p className="text-gray-600 mt-1">Predict future demand with machine learning models</p>
        </div>
        <button
          onClick={fetchDashboard}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Products Forecasted</p>
              <p className="text-2xl font-bold text-indigo-600 mt-1">
                {summary.products_with_forecasts || 0}
              </p>
            </div>
            <div className="p-3 bg-indigo-50 rounded-lg">
              <Target className="w-6 h-6 text-indigo-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Forecasts</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {summary.total_forecasts || 0}
              </p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <BarChart3 className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Forecast Value</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {summary.avg_forecast_value ? Math.round(summary.avg_forecast_value) : 0}
              </p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Models</p>
              <p className="text-2xl font-bold text-purple-600 mt-1">
                {models.length || 3}
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <Activity className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Forecast Generator */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-indigo-600" />
          Generate New Forecast
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Product ID
            </label>
            <input
              type="number"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Enter product ID"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Forecast Horizon (Days)
            </label>
            <select
              value={horizonDays}
              onChange={(e) => setHorizonDays(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="7">7 Days</option>
              <option value="14">14 Days</option>
              <option value="30">30 Days</option>
              <option value="60">60 Days</option>
              <option value="90">90 Days</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model Type
            </label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="arima">ARIMA (Fast)</option>
              <option value="prophet">Prophet (Seasonal)</option>
              <option value="ensemble">Ensemble (Best)</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={generateForecast}
              disabled={generating}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {generating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Generate Forecast
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Forecast Results */}
      {forecastData && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-600" />
              Forecast Results - Product {forecastData.product_id}
            </h3>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <CheckCircle className="w-4 h-4 text-green-600" />
              Model: {forecastData.model_type.toUpperCase()}
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Total Forecast</p>
              <p className="text-xl font-bold text-gray-900 mt-1">
                {Math.round(forecastData.summary.total_forecast).toLocaleString()} units
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Daily Average</p>
              <p className="text-xl font-bold text-gray-900 mt-1">
                {Math.round(forecastData.summary.avg_daily_forecast)} units
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Min Forecast</p>
              <p className="text-xl font-bold text-gray-900 mt-1">
                {Math.round(forecastData.summary.min_forecast)} units
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Max Forecast</p>
              <p className="text-xl font-bold text-gray-900 mt-1">
                {Math.round(forecastData.summary.max_forecast)} units
              </p>
            </div>
          </div>

          {/* Forecast Chart */}
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="upper"
                  stackId="1"
                  stroke="#93c5fd"
                  fill="#dbeafe"
                  name="Upper Bound"
                />
                <Area
                  type="monotone"
                  dataKey="forecast"
                  stackId="2"
                  stroke="#4f46e5"
                  fill="#818cf8"
                  name="Forecast"
                />
                <Area
                  type="monotone"
                  dataKey="lower"
                  stackId="3"
                  stroke="#93c5fd"
                  fill="#dbeafe"
                  name="Lower Bound"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Model Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-600" />
          Available Models
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 border-2 border-indigo-200 rounded-lg">
            <h4 className="font-semibold text-indigo-600 mb-2">ARIMA</h4>
            <p className="text-sm text-gray-600 mb-2">
              AutoRegressive Integrated Moving Average
            </p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>✓ Fast computation</li>
              <li>✓ Good for stable trends</li>
              <li>✓ Simple interpretation</li>
            </ul>
          </div>

          <div className="p-4 border-2 border-blue-200 rounded-lg">
            <h4 className="font-semibold text-blue-600 mb-2">Prophet</h4>
            <p className="text-sm text-gray-600 mb-2">
              Facebook's Time Series Model
            </p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>✓ Seasonal patterns</li>
              <li>✓ Holiday effects</li>
              <li>✓ Robust to outliers</li>
            </ul>
          </div>

          <div className="p-4 border-2 border-green-200 rounded-lg bg-green-50">
            <h4 className="font-semibold text-green-600 mb-2">Ensemble ⭐</h4>
            <p className="text-sm text-gray-600 mb-2">
              Combined ARIMA + Prophet
            </p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>✓ Best accuracy</li>
              <li>✓ Balanced approach</li>
              <li>✓ Recommended</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          ML models automatically detect trends and seasonal patterns in your historical sales data.
          Ensemble model combines multiple algorithms for the most accurate predictions.
        </p>
      </div>
    </div>
  );
};

export default ForecastingDashboard;
