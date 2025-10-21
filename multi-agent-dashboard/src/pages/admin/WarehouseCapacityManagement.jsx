import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  Warehouse, Users, TrendingUp, Package, Clock, 
  AlertTriangle, CheckCircle, Activity, BarChart3 
} from 'lucide-react';

/**
 * Warehouse Capacity Management Component
 * 
 * Displays and manages:
 * - Warehouse capacity utilization
 * - Workforce metrics (employees, shifts, productivity)
 * - Throughput metrics (orders/hour, units/hour)
 * - Equipment utilization
 * - Performance KPIs
 * - Capacity forecasting
 */
const WarehouseCapacityManagement = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [capacityData, setCapacityData] = useState(null);
  const [throughputData, setThroughputData] = useState(null);
  const [kpiData, setKpiData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWarehouses();
  }, []);

  useEffect(() => {
    if (selectedWarehouse) {
      fetchWarehouseData(selectedWarehouse);
    }
  }, [selectedWarehouse]);

  const fetchWarehouses = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/warehouses');
      const data = await response.json();
      setWarehouses(data);
      if (data.length > 0) {
        setSelectedWarehouse(data[0].warehouse_id);
      }
    } catch (err) {
      setError('Failed to load warehouses');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchWarehouseData = async (warehouseId) => {
    setLoading(true);
    try {
      const [capacity, throughput, kpis, forecast] = await Promise.all([
        fetch(`/api/warehouses/${warehouseId}/capacity`).then(r => r.json()),
        fetch(`/api/warehouses/${warehouseId}/throughput`).then(r => r.json()),
        fetch(`/api/warehouses/${warehouseId}/kpis`).then(r => r.json()),
        fetch(`/api/warehouses/${warehouseId}/forecast`).then(r => r.json())
      ]);
      
      setCapacityData(capacity);
      setThroughputData(throughput);
      setKpiData(kpis);
      setForecastData(forecast);
    } catch (err) {
      setError('Failed to load warehouse data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getUtilizationColor = (percentage) => {
    if (percentage >= 90) return 'text-destructive';
    if (percentage >= 75) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getUtilizationStatus = (percentage) => {
    if (percentage >= 90) return 'Critical';
    if (percentage >= 75) return 'High';
    if (percentage >= 50) return 'Moderate';
    return 'Low';
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Warehouse Capacity</h1>
            <p className="text-muted-foreground mt-1">
              Monitor capacity, workforce, and performance metrics
            </p>
          </div>
          <div className="flex gap-2">
            {warehouses.map((warehouse) => (
              <Button
                key={warehouse.warehouse_id}
                variant={selectedWarehouse === warehouse.warehouse_id ? "default" : "outline"}
                onClick={() => setSelectedWarehouse(warehouse.warehouse_id)}
              >
                {warehouse.warehouse_name}
              </Button>
            ))}
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {loading && (
          <div className="text-center py-12">
            <Activity className="w-12 h-12 mx-auto animate-spin text-primary mb-4" />
            <p className="text-muted-foreground">Loading warehouse data...</p>
          </div>
        )}

        {!loading && capacityData && (
          <>
            {/* Capacity Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="bg-card border-border">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Warehouse className="w-4 h-4" />
                    Space Utilization
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-3xl font-bold ${getUtilizationColor(capacityData.utilization_rate)}`}>
                    {capacityData.utilization_rate}%
                  </div>
                  <Progress value={capacityData.utilization_rate} className="mt-2" />
                  <p className="text-xs text-muted-foreground mt-2">
                    {capacityData.used_space_sqft?.toLocaleString()} / {capacityData.total_space_sqft?.toLocaleString()} sq ft
                  </p>
                  <Badge variant={capacityData.utilization_rate >= 90 ? "destructive" : "default"} className="mt-2">
                    {getUtilizationStatus(capacityData.utilization_rate)}
                  </Badge>
                </CardContent>
              </Card>

              <Card className="bg-card border-border">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    Workforce
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-foreground">
                    {capacityData.active_employees}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Active employees
                  </p>
                  <div className="mt-3 space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Full-time:</span>
                      <span className="font-medium">{capacityData.full_time_employees}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Part-time:</span>
                      <span className="font-medium">{capacityData.part_time_employees}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border-border">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Throughput
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-foreground">
                    {capacityData.current_orders_per_hour}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Orders per hour
                  </p>
                  <div className="mt-2">
                    <Progress 
                      value={(capacityData.current_orders_per_hour / capacityData.orders_per_hour_capacity) * 100} 
                      className="mt-2" 
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Capacity: {capacityData.orders_per_hour_capacity}/hr
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border-border">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Package className="w-4 h-4" />
                    Equipment
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-foreground">
                    {capacityData.available_equipment}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Available units
                  </p>
                  <div className="mt-3 space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Total:</span>
                      <span className="font-medium">{capacityData.total_equipment}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">In use:</span>
                      <span className="font-medium">
                        {capacityData.total_equipment - capacityData.available_equipment}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Tabs for Detailed Metrics */}
            <Tabs defaultValue="throughput" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="throughput">Throughput</TabsTrigger>
                <TabsTrigger value="kpis">Performance KPIs</TabsTrigger>
                <TabsTrigger value="forecast">Capacity Forecast</TabsTrigger>
                <TabsTrigger value="workforce">Workforce Details</TabsTrigger>
              </TabsList>

              {/* Throughput Tab */}
              <TabsContent value="throughput" className="space-y-4">
                <Card className="bg-card border-border">
                  <CardHeader>
                    <CardTitle>Throughput Metrics</CardTitle>
                    <CardDescription>Real-time processing performance</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {throughputData && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div>
                          <p className="text-sm text-muted-foreground">Orders Processed</p>
                          <p className="text-2xl font-bold text-foreground mt-1">
                            {throughputData.total_orders_processed?.toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Units Per Hour</p>
                          <p className="text-2xl font-bold text-foreground mt-1">
                            {throughputData.units_per_hour}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Accuracy Rate</p>
                          <p className="text-2xl font-bold text-green-500 mt-1">
                            {throughputData.accuracy_rate}%
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Avg Cycle Time</p>
                          <p className="text-2xl font-bold text-foreground mt-1">
                            {throughputData.avg_cycle_time_minutes}m
                          </p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* KPIs Tab */}
              <TabsContent value="kpis" className="space-y-4">
                <Card className="bg-card border-border">
                  <CardHeader>
                    <CardTitle>Performance KPIs</CardTitle>
                    <CardDescription>Key performance indicators</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {kpiData && (
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                          <div>
                            <p className="text-sm text-muted-foreground">Order Fill Rate</p>
                            <div className="flex items-center gap-2 mt-1">
                              <p className="text-2xl font-bold text-foreground">
                                {kpiData.order_fill_rate}%
                              </p>
                              <CheckCircle className="w-5 h-5 text-green-500" />
                            </div>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">On-Time Delivery</p>
                            <p className="text-2xl font-bold text-foreground mt-1">
                              {kpiData.on_time_delivery_rate}%
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Order Accuracy</p>
                            <p className="text-2xl font-bold text-foreground mt-1">
                              {kpiData.order_accuracy}%
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Picks Per Labor Hour</p>
                            <p className="text-2xl font-bold text-foreground mt-1">
                              {kpiData.picks_per_labor_hour}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Cost Per Order</p>
                            <p className="text-2xl font-bold text-foreground mt-1">
                              ${kpiData.cost_per_order}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Storage Utilization</p>
                            <p className="text-2xl font-bold text-foreground mt-1">
                              {kpiData.storage_utilization}%
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Forecast Tab */}
              <TabsContent value="forecast" className="space-y-4">
                <Card className="bg-card border-border">
                  <CardHeader>
                    <CardTitle>Capacity Forecast</CardTitle>
                    <CardDescription>Projected capacity needs and gaps</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {forecastData && (
                      <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-6">
                          <div className="space-y-3">
                            <h4 className="font-semibold text-foreground">Workforce Requirements</h4>
                            <div className="space-y-2">
                              <div className="flex justify-between">
                                <span className="text-sm text-muted-foreground">Required:</span>
                                <span className="font-medium">{forecastData.required_employees}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-sm text-muted-foreground">Current:</span>
                                <span className="font-medium">{forecastData.current_employees}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-sm text-muted-foreground">Gap:</span>
                                <span className={`font-medium ${forecastData.employee_gap > 0 ? 'text-destructive' : 'text-green-500'}`}>
                                  {forecastData.employee_gap > 0 ? '+' : ''}{forecastData.employee_gap}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="space-y-3">
                            <h4 className="font-semibold text-foreground">Equipment Requirements</h4>
                            <div className="space-y-2">
                              <div className="flex justify-between">
                                <span className="text-sm text-muted-foreground">Required:</span>
                                <span className="font-medium">{forecastData.required_equipment}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-sm text-muted-foreground">Current:</span>
                                <span className="font-medium">{forecastData.current_equipment}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-sm text-muted-foreground">Gap:</span>
                                <span className={`font-medium ${forecastData.equipment_gap > 0 ? 'text-destructive' : 'text-green-500'}`}>
                                  {forecastData.equipment_gap > 0 ? '+' : ''}{forecastData.equipment_gap}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {forecastData.recommendations && forecastData.recommendations.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-semibold text-foreground">Recommendations</h4>
                            <div className="space-y-2">
                              {forecastData.recommendations.map((rec, idx) => (
                                <Alert key={idx} className="bg-accent/50 border-border">
                                  <AlertTriangle className="w-4 h-4" />
                                  <AlertDescription>{rec}</AlertDescription>
                                </Alert>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Workforce Tab */}
              <TabsContent value="workforce" className="space-y-4">
                <Card className="bg-card border-border">
                  <CardHeader>
                    <CardTitle>Workforce Details</CardTitle>
                    <CardDescription>Employee distribution and productivity</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="p-4 border border-border rounded-lg">
                          <p className="text-sm text-muted-foreground">Total Employees</p>
                          <p className="text-2xl font-bold text-foreground mt-1">
                            {capacityData.active_employees}
                          </p>
                        </div>
                        <div className="p-4 border border-border rounded-lg">
                          <p className="text-sm text-muted-foreground">Current Shift</p>
                          <p className="text-2xl font-bold text-foreground mt-1">
                            Day
                          </p>
                        </div>
                        <div className="p-4 border border-border rounded-lg">
                          <p className="text-sm text-muted-foreground">Productivity</p>
                          <p className="text-2xl font-bold text-green-500 mt-1">
                            98%
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </div>
  );
};

export default WarehouseCapacityManagement;

