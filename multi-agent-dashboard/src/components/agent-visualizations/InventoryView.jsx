import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Warehouse, 
  Package, 
  TrendingDown, 
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  MapPin,
  BarChart3,
  RefreshCw
} from 'lucide-react';

// Warehouse floor plan visualization
const WarehouseFloorPlan = ({ warehouse }) => {
  const [hoveredZone, setHoveredZone] = useState(null);

  // Define warehouse zones
  const zones = [
    { id: 'A1', x: 50, y: 50, width: 150, height: 100, stock: 85, capacity: 100, name: 'Electronics' },
    { id: 'A2', x: 220, y: 50, width: 150, height: 100, stock: 92, capacity: 100, name: 'Clothing' },
    { id: 'A3', x: 390, y: 50, width: 150, height: 100, stock: 45, capacity: 100, name: 'Home & Garden' },
    { id: 'B1', x: 50, y: 170, width: 150, height: 100, stock: 78, capacity: 100, name: 'Sports' },
    { id: 'B2', x: 220, y: 170, width: 150, height: 100, stock: 95, capacity: 100, name: 'Books' },
    { id: 'B3', x: 390, y: 170, width: 150, height: 100, stock: 38, capacity: 100, name: 'Toys' },
    { id: 'C1', x: 50, y: 290, width: 150, height: 100, stock: 88, capacity: 100, name: 'Beauty' },
    { id: 'C2', x: 220, y: 290, width: 150, height: 100, stock: 67, capacity: 100, name: 'Food' },
    { id: 'C3', x: 390, y: 290, width: 150, height: 100, stock: 15, capacity: 100, name: 'Automotive' },
  ];

  const getZoneColor = (stock, capacity) => {
    const percentage = (stock / capacity) * 100;
    if (percentage >= 80) return '#EF4444'; // Red - almost full
    if (percentage >= 60) return '#F59E0B'; // Orange - moderate
    if (percentage >= 30) return '#10B981'; // Green - good
    return '#3B82F6'; // Blue - low stock
  };

  return (
    <div className="relative w-full h-[450px] bg-gray-100 rounded-lg overflow-hidden">
      <svg width="600" height="450" className="mx-auto">
        {/* Warehouse outline */}
        <rect x="30" y="30" width="540" height="390" fill="none" stroke="#9CA3AF" strokeWidth="3" />
        
        {/* Loading dock */}
        <rect x="30" y="420" width="540" height="20" fill="#6B7280" />
        <text x="300" y="435" textAnchor="middle" fontSize="12" fill="white" fontWeight="bold">
          Loading Dock
        </text>

        {/* Warehouse zones */}
        {zones.map((zone) => {
          const fillColor = getZoneColor(zone.stock, zone.capacity);
          const isHovered = hoveredZone === zone.id;
          
          return (
            <g key={zone.id}>
              <rect
                x={zone.x}
                y={zone.y}
                width={zone.width}
                height={zone.height}
                fill={fillColor}
                fillOpacity={isHovered ? 0.8 : 0.6}
                stroke={isHovered ? '#111827' : '#6B7280'}
                strokeWidth={isHovered ? 3 : 1}
                className="cursor-pointer transition-all"
                onMouseEnter={() => setHoveredZone(zone.id)}
                onMouseLeave={() => setHoveredZone(null)}
              />
              
              {/* Zone label */}
              <text
                x={zone.x + zone.width / 2}
                y={zone.y + 30}
                textAnchor="middle"
                fontSize="16"
                fontWeight="bold"
                fill="white"
              >
                {zone.id}
              </text>
              
              {/* Zone name */}
              <text
                x={zone.x + zone.width / 2}
                y={zone.y + 50}
                textAnchor="middle"
                fontSize="11"
                fill="white"
              >
                {zone.name}
              </text>
              
              {/* Stock level */}
              <text
                x={zone.x + zone.width / 2}
                y={zone.y + 70}
                textAnchor="middle"
                fontSize="13"
                fontWeight="bold"
                fill="white"
              >
                {zone.stock}/{zone.capacity}
              </text>
              
              {/* Percentage bar */}
              <rect
                x={zone.x + 20}
                y={zone.y + 80}
                width={zone.width - 40}
                height="8"
                fill="white"
                fillOpacity="0.3"
                rx="4"
              />
              <rect
                x={zone.x + 20}
                y={zone.y + 80}
                width={(zone.width - 40) * (zone.stock / zone.capacity)}
                height="8"
                fill="white"
                rx="4"
              />
            </g>
          );
        })}

        {/* Hover tooltip */}
        {hoveredZone && zones.find(z => z.id === hoveredZone) && (
          <g>
            <rect
              x="450"
              y="50"
              width="140"
              height="90"
              fill="white"
              stroke="#E5E7EB"
              strokeWidth="1"
              rx="8"
              style={{ filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.1))' }}
            />
            <text x="470" y="70" fontSize="12" fontWeight="bold" fill="#111827">
              Zone {hoveredZone}
            </text>
            <text x="470" y="90" fontSize="11" fill="#6B7280">
              {zones.find(z => z.id === hoveredZone).name}
            </text>
            <text x="470" y="110" fontSize="11" fill="#6B7280">
              Stock: {zones.find(z => z.id === hoveredZone).stock}
            </text>
            <text x="470" y="130" fontSize="11" fill="#6B7280">
              Capacity: {zones.find(z => z.id === hoveredZone).capacity}
            </text>
          </g>
        )}
      </svg>

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-md">
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#EF4444' }}></div>
            <span className="text-gray-700">80-100% Full</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#F59E0B' }}></div>
            <span className="text-gray-700">60-80% Full</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10B981' }}></div>
            <span className="text-gray-700">30-60% Full</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#3B82F6' }}></div>
            <span className="text-gray-700">&lt;30% Full</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Stock alerts component
const StockAlerts = ({ alerts }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-orange-600" />
          Stock Alerts
        </CardTitle>
        <CardDescription>
          Items requiring immediate attention
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {alerts.map((alert, idx) => (
            <div 
              key={idx}
              className="flex items-center justify-between p-3 bg-orange-50 border border-orange-200 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                <div>
                  <p className="font-semibold text-gray-900">{alert.product}</p>
                  <p className="text-sm text-gray-600">
                    Only {alert.stock} units left in {alert.warehouse}
                  </p>
                </div>
              </div>
              <Badge variant="warning">Low Stock</Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default function InventoryView() {
  const [selectedWarehouse, setSelectedWarehouse] = useState('Paris');

  const warehouses = [
    { name: 'Paris', location: 'France', totalStock: 8547, capacity: 10000, utilization: 85 },
    { name: 'Lyon', location: 'France', totalStock: 6234, capacity: 8000, utilization: 78 },
    { name: 'Marseille', location: 'France', totalStock: 4521, capacity: 6000, utilization: 75 },
  ];

  const stockAlerts = [
    { product: 'iPhone 15 Pro', stock: 5, warehouse: 'Paris', sku: 'ELEC-001' },
    { product: 'Samsung Galaxy S24', stock: 3, warehouse: 'Lyon', sku: 'ELEC-002' },
    { product: 'Nike Air Max', stock: 8, warehouse: 'Paris', sku: 'SHOE-015' },
  ];

  const topProducts = [
    { name: 'iPhone 15 Pro', stock: 245, trend: 'up', change: '+12%' },
    { name: 'Samsung Galaxy S24', stock: 189, trend: 'up', change: '+8%' },
    { name: 'MacBook Pro M3', stock: 156, trend: 'down', change: '-5%' },
    { name: 'Sony WH-1000XM5', stock: 342, trend: 'up', change: '+15%' },
    { name: 'iPad Air', stock: 278, trend: 'down', change: '-3%' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Warehouse className="w-8 h-8 text-blue-600" />
            Inventory Agent
          </h1>
          <p className="text-gray-600 mt-1">
            Real-time warehouse visualization and stock level monitoring
          </p>
        </div>
        <Button variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Warehouse Selection */}
      <div className="flex gap-2">
        {warehouses.map((wh) => (
          <Button
            key={wh.name}
            variant={selectedWarehouse === wh.name ? 'default' : 'outline'}
            onClick={() => setSelectedWarehouse(wh.name)}
            className="flex items-center gap-2"
          >
            <MapPin className="w-4 h-4" />
            {wh.name}
          </Button>
        ))}
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Stock
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {warehouses.find(w => w.name === selectedWarehouse)?.totalStock.toLocaleString()}
            </div>
            <p className="text-xs text-gray-500 mt-1">Units in warehouse</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Capacity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {warehouses.find(w => w.name === selectedWarehouse)?.capacity.toLocaleString()}
            </div>
            <p className="text-xs text-gray-500 mt-1">Maximum capacity</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Utilization
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {warehouses.find(w => w.name === selectedWarehouse)?.utilization}%
            </div>
            <p className="text-xs text-gray-500 mt-1">Space used</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Low Stock Items
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{stockAlerts.length}</div>
            <p className="text-xs text-gray-500 mt-1">Need reorder</p>
          </CardContent>
        </Card>
      </div>

      {/* Warehouse Floor Plan */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Warehouse className="w-5 h-5" />
            Warehouse Floor Plan - {selectedWarehouse}
          </CardTitle>
          <CardDescription>
            Interactive visualization of stock levels by zone
          </CardDescription>
        </CardHeader>
        <CardContent>
          <WarehouseFloorPlan warehouse={selectedWarehouse} />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stock Alerts */}
        <StockAlerts alerts={stockAlerts} />

        {/* Top Products */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Top Products
            </CardTitle>
            <CardDescription>
              Most stocked items with trend analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topProducts.map((product, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{product.name}</p>
                    <p className="text-sm text-gray-600">{product.stock} units</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {product.trend === 'up' ? (
                      <TrendingUp className="w-5 h-5 text-green-600" />
                    ) : (
                      <TrendingDown className="w-5 h-5 text-red-600" />
                    )}
                    <span className={`text-sm font-semibold ${
                      product.trend === 'up' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {product.change}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

