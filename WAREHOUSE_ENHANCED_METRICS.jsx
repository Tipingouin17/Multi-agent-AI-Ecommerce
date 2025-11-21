// Replace the Summary Cards section (lines ~283-342) with this enhanced version:

{/* Market Master Style Metrics Dashboard */}
<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
  {/* Active Warehouses */}
  <Card className="border-l-4 border-l-blue-500">
    <CardHeader className="pb-2">
      <CardTitle className="text-sm font-medium text-muted-foreground flex items-center justify-between">
        Active Warehouses
        <Warehouse className="w-5 h-5 text-blue-500" />
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-3xl font-bold">{metrics.activeWarehouses}</div>
      <p className="text-xs text-muted-foreground mt-1">
        of {warehouses.length} total
      </p>
    </CardContent>
  </Card>

  {/* Total Items */}
  <Card className="border-l-4 border-l-green-500">
    <CardHeader className="pb-2">
      <CardTitle className="text-sm font-medium text-muted-foreground flex items-center justify-between">
        Total Items
        <Package className="w-5 h-5 text-green-500" />
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-3xl font-bold">{metrics.totalItems.toLocaleString()}</div>
      <p className="text-xs text-muted-foreground mt-1">
        {metrics.uniqueSkus} unique SKUs
      </p>
    </CardContent>
  </Card>

  {/* Storage Utilization */}
  <Card className="border-l-4 border-l-purple-500">
    <CardHeader className="pb-2">
      <CardTitle className="text-sm font-medium text-muted-foreground flex items-center justify-between">
        Storage Utilization
        <TrendingUp className="w-5 h-5 text-purple-500" />
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-3xl font-bold">{metrics.avgUtilization}%</div>
      <div className="mt-2">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full ${getUtilizationColor(metrics.avgUtilization)}`}
            style={{ width: `${metrics.avgUtilization}%` }}
          ></div>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Target: 70-85%
        </p>
      </div>
    </CardContent>
  </Card>

  {/* Daily Operations */}
  <Card className="border-l-4 border-l-orange-500">
    <CardHeader className="pb-2">
      <CardTitle className="text-sm font-medium text-muted-foreground flex items-center justify-between">
        Daily Operations
        <CheckCircle2 className="w-5 h-5 text-orange-500" />
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-3xl font-bold">{metrics.dailyOperations}</div>
      <p className="text-xs text-muted-foreground mt-1">
        orders fulfilled today
      </p>
    </CardContent>
  </Card>
</div>
