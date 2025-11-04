import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Search, ChevronDown, ChevronUp } from 'lucide-react'

const Help = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedFaq, setExpandedFaq] = useState(null)

  const faqCategories = [
    {
      category: 'Orders & Shipping',
      faqs: [
        { q: 'How can I track my order?', a: 'You can track your order by logging into your account and visiting the Orders page. Click on any order to see detailed tracking information.' },
        { q: 'What are the shipping costs?', a: 'Shipping costs vary based on your location and chosen shipping method. You can see the exact cost during checkout.' },
        { q: 'How long does shipping take?', a: 'Standard shipping takes 5-7 business days. Express shipping is available for 2-3 day delivery.' }
      ]
    },
    {
      category: 'Returns & Refunds',
      faqs: [
        { q: 'What is your return policy?', a: 'We accept returns within 30 days of delivery. Items must be unused and in original packaging.' },
        { q: 'How do I return an item?', a: 'Log into your account, go to Orders, and click "Request Return" on the order you want to return.' },
        { q: 'When will I receive my refund?', a: 'Refunds are processed within 5-7 business days after we receive your return.' }
      ]
    },
    {
      category: 'Account & Payment',
      faqs: [
        { q: 'How do I reset my password?', a: 'Click "Forgot Password" on the login page and follow the instructions sent to your email.' },
        { q: 'What payment methods do you accept?', a: 'We accept all major credit cards, PayPal, and Apple Pay.' },
        { q: 'Is my payment information secure?', a: 'Yes, all payments are processed through secure, encrypted connections.' }
      ]
    }
  ]

  const toggleFaq = (categoryIndex, faqIndex) => {
    const key = `${categoryIndex}-${faqIndex}`
    setExpandedFaq(expandedFaq === key ? null : key)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-6 text-center">How can we help you?</h1>

        {/* Search */}
        <div className="mb-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <Input
              type="text"
              placeholder="Search for help..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* FAQ Categories */}
        <div className="space-y-6">
          {faqCategories.map((category, categoryIndex) => (
            <Card key={categoryIndex}>
              <CardHeader>
                <CardTitle>{category.category}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {category.faqs.map((faq, faqIndex) => {
                  const key = `${categoryIndex}-${faqIndex}`
                  const isExpanded = expandedFaq === key
                  return (
                    <div key={faqIndex} className="border-b last:border-0 pb-2">
                      <button
                        className="w-full flex items-center justify-between py-3 text-left hover:text-blue-600"
                        onClick={() => toggleFaq(categoryIndex, faqIndex)}
                      >
                        <span className="font-medium">{faq.q}</span>
                        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </button>
                      {isExpanded && (
                        <p className="text-gray-600 pb-3">{faq.a}</p>
                      )}
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Contact Support */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Still need help?</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">Can't find what you're looking for? Contact our support team.</p>
            <div className="flex space-x-4">
              <a href="mailto:support@example.com" className="text-blue-600 hover:underline">Email Support</a>
              <span className="text-gray-300">|</span>
              <a href="tel:+1234567890" className="text-blue-600 hover:underline">Call Us</a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Help
