import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Truck, 
  MapPin, 
  Clock, 
  DollarSign, 
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Brain,
  Sparkles
} from 'lucide-react';

// AI Decision Explanation Component
const AIDecisionCard = ({ decision }) => {
  if (!decision) return null;

  return (
    <Card className="bg-gradient-to-br from-purple-50 to-blue-50 border-purple-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-purple-900">
          <Brain className="w-5 h-5" />
          AI Decision Analysis
        </CardTitle>
        <CardDescription>
          How the AI selected the optimal carrier
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">On-Time Delivery</span>
            <span className="text-sm font-bold text-purple-700">{decision.onTimeScore}%</span>
          </div>
          <Progress value={decision.onTimeScore} className="h-2" />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Cost Efficiency</span>
            <span className="text-sm font-bold text-purple-700">{decision.costScore}%</span>
          </div>
          <Progress value={decision.costScore} className="h-2" />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Service Quality</span>
            <span className="text-sm font-bold text-purple-700">{decision.qualityScore}%</span>
          </div>
          <Progress value={decision.qualityScore} className="h-2" />
        </div>

        <div className="mt-4 p-3 bg-white rounded-lg border border-purple-200">
          <p className="text-sm text-gray-700">
            <Sparkles className="w-4 h-4 inline mr-1 text-purple-600" />
            <strong>AI Reasoning:</strong> {decision.reasoning}
          </p>
        </div>

        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Clock className="w-4 h-4" />
          <span>Decision made in {decision.processingTime}ms</span>
        </div>
      </CardContent>
    </Card>
  );
};

// Carrier Comparison Table
const CarrierComparison = ({ carriers, selectedCarrier }) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 font-semibold text-gray-700">Carrier</th>
            <th className="text-left py-3 px-4 font-semibold text-gray-700">Price</th>
            <th className="text-left py-3 px-4 font-semibold text-gray-700">Delivery Time</th>
            <th className="text-left py-3 px-4 font-semibold text-gray-700">On-Time Rate</th>
            <th className="text-left py-3 px-4 font-semibold text-gray-700">Service Level</th>
            <th className="text-left py-3 px-4 font-semibold text-gray-700">AI Score</th>
          </tr>
        </thead>
        <tbody>
          {carriers.map((carrier) => {
            const isSelected = carrier.name === selectedCarrier;
            return (
              <tr 
                key={carrier.name}
                className={`border-b border-gray-100 ${
                  isSelected ? 'bg-green-50' : 'hover:bg-gray-50'
                }`}
              >
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-green-600" />}
                    <span className={`font-medium ${isSelected ? 'text-green-900' : 'text-gray-900'}`}>
                      {carrier.name}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <span className="font-semibold text-gray-900">€{carrier.price.toFixed(2)}</span>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-1 text-gray-700">
                    <Clock className="w-4 h-4" />
                    {carrier.deliveryDays} days
                  </div>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <Progress value={carrier.onTimeRate} className="h-2 w-20" />
                    <span className="text-sm text-gray-600">{carrier.onTimeRate}%</span>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <Badge variant={carrier.serviceLevel === 'Express' ? 'default' : 'secondary'}>
                    {carrier.serviceLevel}
                  </Badge>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <div className="text-2xl font-bold text-purple-600">{carrier.aiScore}</div>
                    <TrendingUp className="w-4 h-4 text-purple-600" />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

// Interactive Map Component (simplified visualization)
const DeliveryMap = ({ origin, destination, selectedCarrier }) => {
  return (
    <div className="relative w-full h-[400px] bg-gradient-to-br from-blue-50 to-green-50 rounded-lg overflow-hidden border-2 border-gray-200">
      <svg width="100%" height="100%" viewBox="0 0 800 400">
        {/* Map background */}
        <rect width="800" height="400" fill="url(#mapGradient)" />
        <defs>
          <linearGradient id="mapGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#EFF6FF" />
            <stop offset="100%" stopColor="#ECFDF5" />
          </linearGradient>
        </defs>

        {/* Route line */}
        <line
          x1="150"
          y1="200"
          x2="650"
          y2="200"
          stroke="#3B82F6"
          strokeWidth="3"
          strokeDasharray="10,5"
          opacity="0.6"
        />

        {/* Origin marker */}
        <g>
          <circle cx="150" cy="200" r="30" fill="#10B981" stroke="#059669" strokeWidth="3" />
          <MapPin x="135" y="185" className="w-8 h-8 text-white" />
          <text x="150" y="250" textAnchor="middle" fontSize="14" fontWeight="bold" fill="#374151">
            {origin}
          </text>
        </g>

        {/* Destination marker */}
        <g>
          <circle cx="650" cy="200" r="30" fill="#EF4444" stroke="#DC2626" strokeWidth="3" />
          <MapPin x="635" y="185" className="w-8 h-8 text-white" />
          <text x="650" y="250" textAnchor="middle" fontSize="14" fontWeight="bold" fill="#374151">
            {destination}
          </text>
        </g>

        {/* Carrier truck (animated) */}
        <g className="animate-pulse">
          <circle cx="400" cy="200" r="25" fill="#8B5CF6" stroke="#7C3AED" strokeWidth="2" />
          <Truck x="385" y="185" className="w-8 h-8 text-white" />
          <text x="400" y="235" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#6B21A8">
            {selectedCarrier}
          </text>
        </g>

        {/* Distance indicator */}
        <g>
          <rect x="350" y="160" width="100" height="25" fill="white" stroke="#E5E7EB" strokeWidth="1" rx="4" />
          <text x="400" y="177" textAnchor="middle" fontSize="12" fill="#374151">
            ~500 km
          </text>
        </g>
      </svg>

      {/* Map legend */}
      <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-md">
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-gray-700">Origin</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-gray-700">Destination</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span className="text-gray-700">Carrier</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function CarrierSelectionView() {
  const [selectedShipment, setSelectedShipment] = useState(null);

  // Mock data - replace with actual API call
  const mockData = {
    carriers: [
      { name: 'Colis Privé', price: 8.50, deliveryDays: 2, onTimeRate: 94, serviceLevel: 'Standard', aiScore: 92 },
      { name: 'UPS', price: 12.30, deliveryDays: 1, onTimeRate: 98, serviceLevel: 'Express', aiScore: 89 },
      { name: 'Chronopost', price: 15.00, deliveryDays: 1, onTimeRate: 97, serviceLevel: 'Express', aiScore: 85 },
      { name: 'Colissimo', price: 7.80, deliveryDays: 3, onTimeRate: 91, serviceLevel: 'Economy', aiScore: 78 },
    ],
    selectedCarrier: 'Colis Privé',
    decision: {
      onTimeScore: 94,
      costScore: 88,
      qualityScore: 92,
      reasoning: 'Colis Privé offers the best balance between cost (€8.50) and on-time delivery rate (94%). While UPS has a higher on-time rate, the 45% price premium doesn\'t justify the marginal improvement for this standard shipment.',
      processingTime: 127,
    },
    origin: 'Paris',
    destination: 'Lyon',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Truck className="w-8 h-8 text-blue-600" />
            Carrier Selection Agent
          </h1>
          <p className="text-gray-600 mt-1">
            AI-powered optimal carrier selection with real-time decision visualization
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Selected Carrier
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{mockData.selectedCarrier}</div>
            <p className="text-xs text-gray-500 mt-1">AI recommended</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Estimated Cost
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              €{mockData.carriers.find(c => c.name === mockData.selectedCarrier)?.price.toFixed(2)}
            </div>
            <p className="text-xs text-gray-500 mt-1">Best value</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Delivery Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {mockData.carriers.find(c => c.name === mockData.selectedCarrier)?.deliveryDays} days
            </div>
            <p className="text-xs text-gray-500 mt-1">Estimated</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              On-Time Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {mockData.carriers.find(c => c.name === mockData.selectedCarrier)?.onTimeRate}%
            </div>
            <p className="text-xs text-gray-500 mt-1">Historical</p>
          </CardContent>
        </Card>
      </div>

      {/* Delivery Route Map */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Delivery Route Visualization
          </CardTitle>
          <CardDescription>
            Interactive map showing origin, destination, and selected carrier
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DeliveryMap 
            origin={mockData.origin}
            destination={mockData.destination}
            selectedCarrier={mockData.selectedCarrier}
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Carrier Comparison */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Carrier Comparison</CardTitle>
              <CardDescription>
                All available carriers ranked by AI decision score
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CarrierComparison 
                carriers={mockData.carriers}
                selectedCarrier={mockData.selectedCarrier}
              />
            </CardContent>
          </Card>
        </div>

        {/* AI Decision Analysis */}
        <div>
          <AIDecisionCard decision={mockData.decision} />
        </div>
      </div>

      {/* Package Details */}
      <Card>
        <CardHeader>
          <CardTitle>Package Details</CardTitle>
          <CardDescription>
            Factors considered in carrier selection
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">Weight</p>
              <p className="text-lg font-semibold text-gray-900">2.5 kg</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Dimensions</p>
              <p className="text-lg font-semibold text-gray-900">30×20×15 cm</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Fragile</p>
              <p className="text-lg font-semibold text-gray-900">No</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Dangerous Goods</p>
              <p className="text-lg font-semibold text-gray-900">No</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

