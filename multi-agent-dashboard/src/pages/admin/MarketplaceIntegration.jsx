import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  CheckCircle2, XCircle, AlertCircle, Clock, 
  Plus, Settings, RefreshCw, Zap, Brain, TrendingUp
} from 'lucide-react';

/**
 * Marketplace Integration & AI Monitoring Dashboard
 * 
 * Features:
 * - Configure marketplace connections (12 platforms)
 * - AI-powered issue monitoring
 * - Human-in-the-loop decision making
 * - Self-learning knowledge management
 * - Auto-correction with confidence tracking
 */

const MarketplaceIntegration = () => {
  const [activeTab, setActiveTab] = useState('connections');
  const [connections, setConnections] = useState([]);
  const [pendingIssues, setPendingIssues] = useState([]);
  const [autoCorrected, setAutoCorrected] = useState([]);
  const [knowledgeBase, setKnowledgeBase] = useState([]);

  // Simulated data (replace with API calls)
  useEffect(() => {
    // Load connections
    setConnections([
      {
        id: 1,
        platform: 'Shopify',
        type: 'ecommerce',
        storeName: 'My Shopify Store',
        status: 'active',
        lastSync: '2 minutes ago',
        ordersToday: 45,
        issuesDetected: 2
      },
      {
        id: 2,
        platform: 'Amazon SP-API',
        type: 'marketplace',
        storeName: 'Amazon US Store',
        status: 'active',
        lastSync: '5 minutes ago',
        ordersToday: 128,
        issuesDetected: 0
      },
      {
        id: 3,
        platform: 'Mirakl',
        type: 'marketplace',
        storeName: 'Mirakl Marketplace',
        status: 'syncing',
        lastSync: 'In progress',
        ordersToday: 67,
        issuesDetected: 5
      },
      {
        id: 4,
        platform: 'WooCommerce',
        type: 'ecommerce',
        storeName: 'WooCommerce Store',
        status: 'error',
        lastSync: '2 hours ago',
        ordersToday: 0,
        issuesDetected: 12
      }
    ]);

    // Load pending issues
    setPendingIssues([
      {
        id: 1,
        platform: 'Shopify',
        issueType: 'missing_required_field',
        description: 'Product missing description',
        productId: 'PROD-12345',
        productName: 'Wireless Headphones Pro',
        aiSuggestion: 'High-quality wireless headphones with noise cancellation and 30-hour battery life',
        confidence: 0.85,
        reasoning: 'Generated from product title and category',
        timestamp: '5 minutes ago'
      },
      {
        id: 2,
        platform: 'Mirakl',
        issueType: 'invalid_format',
        description: 'Price missing decimal places',
        productId: 'PROD-67890',
        productName: 'Gaming Mouse RGB',
        currentValue: '45',
        aiSuggestion: '45.00',
        confidence: 0.99,
        reasoning: 'Formatted price to 2 decimal places per Mirakl requirements',
        timestamp: '12 minutes ago'
      },
      {
        id: 3,
        platform: 'Amazon SP-API',
        issueType: 'business_rule_violation',
        description: 'Product weight exceeds category limit',
        productId: 'PROD-11111',
        productName: 'Heavy Duty Backpack',
        currentValue: '15 kg',
        aiSuggestion: 'Split into multiple packages or change category to "Luggage"',
        confidence: 0.72,
        reasoning: 'Based on Amazon category guidelines',
        timestamp: '20 minutes ago'
      }
    ]);

    // Load auto-corrected issues
    setAutoCorrected([
      {
        id: 1,
        platform: 'Shopify',
        issueType: 'invalid_format',
        description: 'Price format corrected',
        productId: 'PROD-55555',
        correction: 'Added decimal places: 29 → 29.00',
        confidence: 0.99,
        timestamp: '1 hour ago',
        ruleId: 'RULE-001'
      },
      {
        id: 2,
        platform: 'WooCommerce',
        issueType: 'missing_required_field',
        description: 'Brand extracted from title',
        productId: 'PROD-66666',
        correction: 'Brand: "Sony" extracted from "Sony PlayStation 5"',
        confidence: 0.92,
        timestamp: '2 hours ago',
        ruleId: 'RULE-045'
      }
    ]);

    // Load knowledge base stats
    setKnowledgeBase([
      {
        patternId: 'PATTERN-001',
        description: 'Missing product description',
        occurrences: 47,
        successRate: 0.96,
        confidence: 0.92,
        autoCorrectEnabled: true
      },
      {
        patternId: 'PATTERN-002',
        description: 'Price format (missing decimals)',
        occurrences: 234,
        successRate: 0.99,
        confidence: 0.99,
        autoCorrectEnabled: true
      },
      {
        patternId: 'PATTERN-003',
        description: 'Brand extraction from title',
        occurrences: 89,
        successRate: 0.88,
        confidence: 0.85,
        autoCorrectEnabled: true
      }
    ]);
  }, []);

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { color: 'bg-green-500', icon: CheckCircle2, text: 'Active' },
      syncing: { color: 'bg-blue-500', icon: RefreshCw, text: 'Syncing' },
      error: { color: 'bg-red-500', icon: XCircle, text: 'Error' },
      inactive: { color: 'bg-gray-500', icon: Clock, text: 'Inactive' }
    };

    const config = statusConfig[status] || statusConfig.inactive;
    const Icon = config.icon;

    return (
      <Badge className={`${config.color} text-white`}>
        <Icon className="w-3 h-3 mr-1" />
        {config.text}
      </Badge>
    );
  };

  const handleApprove = (issueId) => {
    console.log('Approved issue:', issueId);
    // Move to auto-corrected and update knowledge base
    setPendingIssues(prev => prev.filter(issue => issue.id !== issueId));
  };

  const handleReject = (issueId) => {
    console.log('Rejected issue:', issueId);
    setPendingIssues(prev => prev.filter(issue => issue.id !== issueId));
  };

  const handleModify = (issueId) => {
    console.log('Modify issue:', issueId);
    // Open modal for custom correction
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Marketplace Integration</h1>
          <p className="text-muted-foreground">
            AI-Powered Multi-Channel Management with Self-Learning Auto-Correction
          </p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Add Connection
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Connections
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {connections.filter(c => c.status === 'active').length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              of {connections.length} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Reviews
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">
              {pendingIssues.length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Requires human decision
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Auto-Corrected Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {autoCorrected.length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              AI handled automatically
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Knowledge Base
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">
              {knowledgeBase.length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Learned patterns
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="connections">Connections</TabsTrigger>
          <TabsTrigger value="pending">
            Pending Reviews
            {pendingIssues.length > 0 && (
              <Badge className="ml-2 bg-yellow-600">{pendingIssues.length}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="autocorrected">Auto-Corrected</TabsTrigger>
          <TabsTrigger value="knowledge">Knowledge Base</TabsTrigger>
        </TabsList>

        {/* Connections Tab */}
        <TabsContent value="connections" className="space-y-4">
          {connections.map(connection => (
            <Card key={connection.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {connection.platform}
                      {getStatusBadge(connection.status)}
                    </CardTitle>
                    <CardDescription>{connection.storeName}</CardDescription>
                  </div>
                  <Button variant="outline" size="sm">
                    <Settings className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Last Sync</p>
                    <p className="font-medium">{connection.lastSync}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Orders Today</p>
                    <p className="font-medium">{connection.ordersToday}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Issues Detected</p>
                    <p className={`font-medium ${connection.issuesDetected > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
                      {connection.issuesDetected}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Pending Reviews Tab */}
        <TabsContent value="pending" className="space-y-4">
          {pendingIssues.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <CheckCircle2 className="w-12 h-12 mx-auto text-green-600 mb-4" />
                <p className="text-lg font-medium">All Clear!</p>
                <p className="text-muted-foreground">No pending issues require your attention</p>
              </CardContent>
            </Card>
          ) : (
            pendingIssues.map(issue => (
              <Card key={issue.id} className="border-l-4 border-l-yellow-500">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <AlertCircle className="w-5 h-5 text-yellow-600" />
                        {issue.description}
                      </CardTitle>
                      <CardDescription>
                        {issue.platform} • {issue.productName} • {issue.timestamp}
                      </CardDescription>
                    </div>
                    <Badge variant="outline">{issue.issueType}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* AI Suggestion */}
                  <Alert className="bg-blue-50 border-blue-200">
                    <Brain className="w-4 h-4 text-blue-600" />
                    <AlertDescription>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium text-blue-900">AI Suggestion</span>
                          <Badge className="bg-blue-600 text-white">
                            {(issue.confidence * 100).toFixed(0)}% confidence
                          </Badge>
                        </div>
                        <p className="text-sm text-blue-800">
                          {typeof issue.aiSuggestion === 'string' ? issue.aiSuggestion : JSON.stringify(issue.aiSuggestion)}
                        </p>
                        <p className="text-xs text-blue-600 italic">
                          {issue.reasoning}
                        </p>
                      </div>
                    </AlertDescription>
                  </Alert>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <Button 
                      className="flex-1 bg-green-600 hover:bg-green-700"
                      onClick={() => handleApprove(issue.id)}
                    >
                      <CheckCircle2 className="w-4 h-4 mr-2" />
                      Approve & Learn
                    </Button>
                    <Button 
                      variant="outline" 
                      className="flex-1"
                      onClick={() => handleModify(issue.id)}
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      Modify
                    </Button>
                    <Button 
                      variant="destructive" 
                      className="flex-1"
                      onClick={() => handleReject(issue.id)}
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* Auto-Corrected Tab */}
        <TabsContent value="autocorrected" className="space-y-4">
          {autoCorrected.map(item => (
            <Card key={item.id} className="border-l-4 border-l-green-500">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="w-5 h-5 text-green-600" />
                      {item.description}
                    </CardTitle>
                    <CardDescription>
                      {item.platform} • {item.productId} • {item.timestamp}
                    </CardDescription>
                  </div>
                  <Badge className="bg-green-600 text-white">
                    {(item.confidence * 100).toFixed(0)}% confidence
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{item.correction}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  Rule ID: {item.ruleId}
                </p>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Knowledge Base Tab */}
        <TabsContent value="knowledge" className="space-y-4">
          {knowledgeBase.map(pattern => (
            <Card key={pattern.patternId}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-purple-600" />
                      {pattern.description}
                    </CardTitle>
                    <CardDescription>
                      Pattern ID: {pattern.patternId}
                    </CardDescription>
                  </div>
                  {pattern.autoCorrectEnabled && (
                    <Badge className="bg-purple-600 text-white">
                      <Zap className="w-3 h-3 mr-1" />
                      Auto-Correct Enabled
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Occurrences</p>
                    <p className="text-2xl font-bold">{pattern.occurrences}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Success Rate</p>
                    <p className="text-2xl font-bold text-green-600">
                      {(pattern.successRate * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Confidence</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {(pattern.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MarketplaceIntegration;

