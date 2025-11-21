#!/usr/bin/env python3
"""
Update WarehouseConfiguration.jsx with Market Master features
"""

# Read the file
with open('/home/ubuntu/Multi-agent-AI-Ecommerce/multi-agent-dashboard/src/pages/admin/WarehouseConfiguration.jsx', 'r') as f:
    content = f.read()

# Replace the Summary Cards section
old_cards = '''      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Warehouses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{warehouses.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {warehouses.filter(w => w.status === 'active').length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Capacity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {(warehouses.reduce((sum, w) => sum + w.total_capacity_sqft, 0) / 1000).toFixed(0)}K
            </div>
            <p className="text-xs text-muted-foreground mt-1">sq ft</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Workforce
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {warehouses.reduce((sum, w) => sum + w.current_employees, 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              of {warehouses.reduce((sum, w) => sum + w.max_employees, 0)} max
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Equipment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {warehouses.reduce((sum, w) => sum + w.equipment_count, 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">units total</p>
          </CardContent>
        </Card>
      </div>'''

new_cards = '''      {/* Market Master Style Metrics Dashboard */}
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
      </div>'''

content = content.replace(old_cards, new_cards)

# Write back
with open('/home/ubuntu/Multi-agent-AI-Ecommerce/multi-agent-dashboard/src/pages/admin/WarehouseConfiguration.jsx', 'w') as f:
    f.write(content)

print("✅ Warehouse UI updated successfully!")
print("   - Replaced 4 basic cards with Market Master style KPI cards")
print("   - Added colored borders, icons, and progress bars")
