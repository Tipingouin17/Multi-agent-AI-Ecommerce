import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User, 
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Smile,
  Frown,
  Meh
} from 'lucide-react';

// Sentiment indicator component
const SentimentIndicator = ({ sentiment }) => {
  const icons = {
    positive: { Icon: Smile, color: 'text-green-600', bg: 'bg-green-100' },
    neutral: { Icon: Meh, color: 'text-gray-600', bg: 'bg-gray-100' },
    negative: { Icon: Frown, color: 'text-red-600', bg: 'bg-red-100' },
  };

  const { Icon, color, bg } = icons[sentiment] || icons.neutral;

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full ${bg}`}>
      <Icon className={`w-4 h-4 ${color}`} />
      <span className={`text-xs font-medium ${color} capitalize`}>{sentiment}</span>
    </div>
  );
};

// Chat message component
const ChatMessage = ({ message, isBot }) => {
  return (
    <div className={`flex gap-3 ${isBot ? '' : 'flex-row-reverse'}`}>
      <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
        isBot ? 'bg-blue-600' : 'bg-gray-600'
      }`}>
        {isBot ? (
          <Bot className="w-5 h-5 text-white" />
        ) : (
          <User className="w-5 h-5 text-white" />
        )}
      </div>
      <div className={`flex-1 ${isBot ? '' : 'flex flex-col items-end'}`}>
        <div className={`inline-block max-w-[80%] px-4 py-3 rounded-lg ${
          isBot 
            ? 'bg-blue-50 text-gray-900 border border-blue-200' 
            : 'bg-gray-700 text-white'
        }`}>
          <p className="text-sm">{message.text}</p>
          {message.suggestions && message.suggestions.length > 0 && (
            <div className="mt-3 space-y-2">
              <p className="text-xs font-semibold text-gray-600">Suggested responses:</p>
              {message.suggestions.map((suggestion, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  size="sm"
                  className="w-full text-left justify-start text-xs"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 mt-1 px-1">
          <span className="text-xs text-gray-500">{message.time}</span>
          {message.sentiment && <SentimentIndicator sentiment={message.sentiment} />}
          {!isBot && message.read && <CheckCircle2 className="w-3 h-3 text-blue-600" />}
        </div>
      </div>
    </div>
  );
};

// Conversation stats component
const ConversationStats = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            Total Messages
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-gray-900">{stats.totalMessages}</div>
          <p className="text-xs text-gray-500 mt-1">Last 24 hours</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            Avg Response Time
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-blue-600">{stats.avgResponseTime}s</div>
          <p className="text-xs text-gray-500 mt-1">AI-powered</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            Satisfaction Rate
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">{stats.satisfactionRate}%</div>
          <p className="text-xs text-gray-500 mt-1">Customer feedback</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            Active Chats
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-purple-600">{stats.activeChats}</div>
          <p className="text-xs text-gray-500 mt-1">Currently ongoing</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default function CustomerCommunicationView() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: 'Hello! How can I help you today?',
      isBot: true,
      time: '10:30 AM',
      suggestions: [
        'Track my order',
        'Return a product',
        'Check delivery status',
        'Speak to a human agent'
      ]
    },
    {
      id: 2,
      text: 'I would like to track my order #12345',
      isBot: false,
      time: '10:31 AM',
      sentiment: 'neutral',
      read: true
    },
    {
      id: 3,
      text: 'Let me check that for you! Your order #12345 is currently in transit and expected to arrive tomorrow by 5 PM. Would you like me to send you real-time tracking updates?',
      isBot: true,
      time: '10:31 AM',
      sentiment: 'positive',
      suggestions: [
        'Yes, send me updates',
        'No, thank you',
        'Change delivery address'
      ]
    },
  ]);

  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      text: inputValue,
      isBot: false,
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      sentiment: 'neutral',
      read: false
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const botMessage = {
        id: messages.length + 2,
        text: 'Thank you for your message. I\'m processing your request and will get back to you shortly with the information you need.',
        isBot: true,
        time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        sentiment: 'positive'
      };
      setMessages(prev => [...prev, botMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const stats = {
    totalMessages: 1247,
    avgResponseTime: 2.3,
    satisfactionRate: 94,
    activeChats: 12
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <MessageSquare className="w-8 h-8 text-blue-600" />
            Customer Communication Agent
          </h1>
          <p className="text-gray-600 mt-1">
            AI-powered chatbot with sentiment analysis and auto-responses
          </p>
        </div>
      </div>

      {/* Stats Overview */}
      <ConversationStats stats={stats} />

      {/* Main Chat Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Window */}
        <div className="lg:col-span-2">
          <Card className="h-[700px] flex flex-col">
            <CardHeader className="border-b">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Live Chat</CardTitle>
                  <CardDescription>
                    Real-time customer conversation with AI assistance
                  </CardDescription>
                </div>
                <Badge variant="success" className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  Online
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col p-0">
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((message) => (
                  <ChatMessage 
                    key={message.id} 
                    message={message} 
                    isBot={message.isBot} 
                  />
                ))}
                {isTyping && (
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="bg-blue-50 border border-blue-200 px-4 py-3 rounded-lg">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t p-4">
                <div className="flex gap-2">
                  <Input
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Type your message..."
                    className="flex-1"
                  />
                  <Button onClick={handleSend} disabled={!inputValue.trim()}>
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar - AI Insights */}
        <div className="space-y-4">
          {/* Sentiment Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Sentiment Analysis</CardTitle>
              <CardDescription>
                Real-time customer mood tracking
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Positive</span>
                  <span className="text-sm font-bold text-green-600">65%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: '65%' }} />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Neutral</span>
                  <span className="text-sm font-bold text-gray-600">25%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-gray-500 h-2 rounded-full" style={{ width: '25%' }} />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Negative</span>
                  <span className="text-sm font-bold text-red-600">10%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-red-500 h-2 rounded-full" style={{ width: '10%' }} />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Common Topics */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Common Topics</CardTitle>
              <CardDescription>
                Most frequent customer inquiries
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Order Tracking</span>
                  <Badge>42%</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Returns</span>
                  <Badge>28%</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Product Info</span>
                  <Badge>18%</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Delivery Issues</span>
                  <Badge>12%</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Suggestions */}
          <Card className="bg-purple-50 border-purple-200">
            <CardHeader>
              <CardTitle className="text-lg text-purple-900">AI Suggestions</CardTitle>
              <CardDescription>
                Recommended actions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-purple-600 mt-0.5" />
                <p className="text-sm text-purple-900">
                  Customer seems satisfied. Consider offering a discount code for next purchase.
                </p>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                <p className="text-sm text-purple-900">
                  Issue resolved successfully. Send follow-up survey.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

