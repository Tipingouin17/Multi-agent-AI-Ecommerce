/**
 * Browser-based page rendering test
 * Run this in the browser console to test if pages actually render
 */

const MERCHANT_PAGES = [
  '/dashboard',
  '/products',
  '/orders',
  '/inventory',
  '/marketplaces',
  '/analytics',
  '/product-form',
  '/bulk-upload',
  '/fulfillment',
  '/product-analytics',
  '/returns',
  '/shipping',
  '/inventory-alerts',
  '/order-analytics',
  '/refunds',
  '/customers',
  '/campaigns',
  '/promotions',
  '/reviews',
  '/marketing-analytics',
  '/segmentation',
  '/loyalty',
  '/email-campaigns',
  '/automation',
  '/store-settings',
  '/payment-settings',
  '/shipping-settings',
  '/tax-settings',
  '/email-templates',
  '/notifications',
  '/domain',
  '/api-settings',
  '/financial-dashboard',
  '/sales-reports',
  '/profit-loss',
  '/revenue-analytics',
  '/expenses',
  '/tax-reports'
];

async function testPage(path) {
  return new Promise((resolve) => {
    // Navigate to page
    window.location.href = path;
    
    // Wait for page to load
    setTimeout(() => {
      const hasContent = document.body.innerText.trim().length > 100;
      const hasError = document.body.innerText.includes('Something went wrong');
      const isBlank = document.body.innerText.trim().length < 50;
      
      resolve({
        path,
        hasContent,
        hasError,
        isBlank,
        textLength: document.body.innerText.trim().length
      });
    }, 2000);
  });
}

async function runAllTests() {
  const results = [];
  
  console.log('Starting browser rendering tests...');
  console.log('This will take about', MERCHANT_PAGES.length * 2, 'seconds');
  
  for (const page of MERCHANT_PAGES) {
    console.log('Testing:', page);
    const result = await testPage(page);
    results.push(result);
    
    if (result.hasError) {
      console.error('❌ ERROR:', page);
    } else if (result.isBlank) {
      console.warn('⚠️  BLANK:', page);
    } else if (result.hasContent) {
      console.log('✅ OK:', page);
    }
  }
  
  // Summary
  const working = results.filter(r => r.hasContent && !r.hasError && !r.isBlank).length;
  const errors = results.filter(r => r.hasError).length;
  const blank = results.filter(r => r.isBlank).length;
  
  console.log('\n=== SUMMARY ===');
  console.log('Working:', working, '/', results.length);
  console.log('Errors:', errors);
  console.log('Blank:', blank);
  
  return results;
}

// Auto-run
console.log('Browser rendering test loaded. Run runAllTests() to start.');
