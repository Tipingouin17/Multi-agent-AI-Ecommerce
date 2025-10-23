import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Truck, 
  MapPin, 
  Clock, 
  DollarSign, 
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Brain,
  Sparkles,
  RefreshCw,
  Loader2
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
            <span className="text-sm font-bold text-purple-700">{decision.onTimeScore || 0}%</span>
          </div>
          <Progress value={decision.onTimeScore || 0} className="h-2" />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Cost Efficiency</span>
            <span className="text-sm font-bold text-purple-700">{decision.costScore || 0}%</span>
          </div>
          <Progress value={decision.costScore || 0} className="h-2" />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Service Quality</span>
            <span className="text-sm font-bold text-purple-700">{decision.qualityScore || 0}%</span>
          </div>
          <Progress value={decision.qualityScore || 0} className="h-2" />
        </div>

        <div className="pt-4 border-t border-purple-200">
          <div className="flex items-start gap-2">
            <Sparkles className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-gray-700">
              {decision.reasoning || 'AI analysis in progress...'}
            </p>
          </div>
        </div>

        {decision.factors && decision.factors.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-900">Key Factors:</h4>
            <ul className="space-y-1">
              {decision.factors.map((factor, index) => (
                <li key={index} className="flex items-center gap-2 text-sm text-gray-700">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  {factor}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Carrier Comparison Component
const CarrierComparison = ({ carriers, selectedCarrier }) => {
  if (!carriers || carriers.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Truck className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No carriers available</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {carriers.map((carrier) => {
        const isSelected = carrier.name === selectedCarrier;
        return (
          <div
            key={carrier.id || carrier.name}
            className={`p-4 rounded-lg border-2 transition-all ${
              isSelected
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Truck className={`w-5 h-5 ${isSelected ? 'text-blue-600' : 'text-gray-600'}`} />
                <span className="font-semibold text-gray-900">{carrier.name}</span>
                {isSelected && (
                  <Badge className="bg-blue-600">Selected</Badge>
                )}
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-gray-900">
                  €{carrier.price?.toFixed(2) || '0.00'}
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <span className="text-gray-500">Delivery:</span>
                <span className="ml-1 font-medium">{carrier.deliveryDays || 'N/A'} days</span>
              </div>
              <div>
                <span className="text-gray-500">On-Time:</span>
                <span className="ml-1 font-medium">{carrier.onTimeRate || 0}%</span>
              </div>
              <div>
                <span className="text-gray-500">Service:</span>
                <span className="ml-1 font-medium">{carrier.serviceLevel || 'Standard'}</span>
              </div>
            </div>

            {carrier.aiScore && (
              <div className="mt-2 pt-2 border-t border-gray-200">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">AI Score:</span>
                  <span className="font-semibold text-purple-600">{carrier.aiScore}/100</span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// Delivery Map Component (Placeholder - can be enhanced with real map library)
const DeliveryMap = ({ origin, destination, selectedCarrier }) => {
  if (!origin || !destination) {
    return (
      <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
        <div className="text-center text-gray-500">
          <MapPin className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>Route information unavailable</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-64 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg p-4 flex flex-col justify-between">
      <div className="flex items-start gap-2">
        <MapPin className="w-5 h-5 text-blue-600 flex-shrink-0" />
        <div>
          <div className="text-sm font-semibold text-gray-900">Origin</div>
          <div className="text-sm text-gray-700">{origin.address || 'Unknown'}</div>
        </div>
      </div>
      
      <div className="flex items-center justify-center">
        <div className="text-center">
          <Truck className="w-8 h-8 mx-auto text-blue-600 mb-1" />
          <div className="text-xs text-gray-600">{selectedCarrier || 'No carrier selected'}</div>
        </div>
      </div>
      
      <div className="flex items-start gap-2">
        <MapPin className="w-5 h-5 text-purple-600 flex-shrink-0" />
        <div>
          <div className="text-sm font-semibold text-gray-900">Destination</div>
          <div className="text-sm text-gray-700">{destination.address || 'Unknown'}</div>
        </div>
      </div>
    </div>
  );
};

// Error Display Component
const ErrorDisplay = ({ error, onRetry }) => (
  <Alert variant="destructive" className="mb-4">
    <AlertCircle className="h-4 w-4" />
    <AlertDescription className="ml-2">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-semibold">Failed to load carrier data</p>
          <p className="text-sm mt-1">{error?.message || 'Database connection error'}</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="ml-4"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </Button>
      </div>
    </AlertDescription>
  </Alert>
);

// Loading Skeleton Component
const LoadingSkeleton = () => (
  <div className="space-y-4">
    <div className="flex items-center justify-center py-8">
      <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      <span className="ml-2 text-gray-600">Loading carrier data from database...</span>
    </div>
  </div>
);

// Main Component
const CarrierSelectionView = ({ shipmentId }) => {
  const [selectedShipment, setSelectedShipment] = useState(null);

  // Fetch shipment data from Transport Agent API
  const { data: shipmentData, isLoading, error, refetch } = useQuery({
    queryKey: ['shipment', shipmentId],
    queryFn: async () => {
      if (!shipmentId) {
        throw new Error('No shipment ID provided');
      }

      const response = await fetch(`http://localhost:8006/api/shipments/${shipmentId}`);
      
      if (!response.ok) {
        throw new Error(`Transport Agent API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      return data;
    },
    enabled: !!shipmentId,
    retry: 2,
    staleTime: 30000, // 30 seconds
  });

  // Fetch available carriers from Transport Agent API
  const { data: carriersData, isLoading: carriersLoading, error: carriersError } = useQuery({
    queryKey: ['carriers'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8006/api/carriers');
      
      if (!response.ok) {
        throw new Error(`Transport Agent API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      return data;
    },
    retry: 2,
    staleTime: 60000, // 1 minute
  });

  // Handle loading state
  if (isLoading || carriersLoading) {
    return <LoadingSkeleton />;
  }

  // Handle error state
  if (error || carriersError) {
    return (
      <ErrorDisplay 
        error={error || carriersError} 
        onRetry={() => {
          refetch();
        }} 
      />
    );
  }

  // Handle no data state
  if (!shipmentData && !carriersData) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No shipment or carrier data available. Please ensure the Transport Agent is running and connected to the database.
        </AlertDescription>
      </Alert>
    );
  }

  const carriers = carriersData?.carriers || [];
  const selectedCarrier = shipmentData?.selectedCarrier || shipmentData?.carrier_name || null;
  const origin = shipmentData?.origin || null;
  const destination = shipmentData?.destination || null;
  const decision = shipmentData?.aiDecision || shipmentData?.decision || null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Carrier Selection</h2>
          <p className="text-sm text-gray-600 mt-1">
            AI-powered carrier optimization for shipment {shipmentId || 'N/A'}
          </p>
        </div>
        <Button onClick={() => refetch()} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Selected Carrier</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{selectedCarrier || 'Not selected'}</div>
            <p className="text-xs text-gray-500 mt-1">AI recommended</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Shipping Cost</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              €{carriers.find(c => c.name === selectedCarrier)?.price?.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-gray-500 mt-1">Best value</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Delivery Time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {carriers.find(c => c.name === selectedCarrier)?.deliveryDays || 'N/A'} days
            </div>
            <p className="text-xs text-gray-500 mt-1">Estimated</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>On-Time Rate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {carriers.find(c => c.name === selectedCarrier)?.onTimeRate || 0}%
            </div>
            <p className="text-xs text-gray-500 mt-1">Historical</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Delivery Route Map */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              Delivery Route
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DeliveryMap 
              origin={origin}
              destination={destination}
              selectedCarrier={selectedCarrier}
            />
          </CardContent>
        </Card>

        {/* Carrier Comparison */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Carrier Comparison
              </CardTitle>
              <CardDescription>
                {carriers.length} carriers analyzed
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CarrierComparison 
                carriers={carriers}
                selectedCarrier={selectedCarrier}
              />
            </CardContent>
          </Card>
        </div>

        {/* AI Decision Analysis */}
        <div className="lg:col-span-2">
          <AIDecisionCard decision={decision} />
        </div>
      </div>

      {/* Database Status Footer */}
      <div className="text-xs text-gray-500 text-center py-2 border-t">
        <div className="flex items-center justify-center gap-2">
          <CheckCircle2 className="w-3 h-3 text-green-600" />
          <span>Connected to Transport Agent (Port 8006) - Real-time database data</span>
        </div>
      </div>
    </div>
  );
};

export default CarrierSelectionView;

