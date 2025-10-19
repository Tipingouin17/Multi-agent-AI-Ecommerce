import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Customer Home Page
 * 
 * Main landing page for customers with featured products, promotions,
 * and personalized recommendations.
 */
function Home() {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [newArrivals, setNewArrivals] = useState([]);
  const [promotions, setPromotions] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadHomePageData() {
      try {
        setLoading(true);
        
        // Load featured products
        const featured = await apiService.getFeaturedProducts();
        setFeaturedProducts(featured);
        
        // Load new arrivals
        const arrivals = await apiService.getNewArrivals();
        setNewArrivals(arrivals);
        
        // Load promotions
        const promos = await apiService.getPromotions();
        setPromotions(promos);
        
        // Load personalized recommendations
        const recs = await apiService.getRecommendations();
        setRecommendations(recs);
        
        setError(null);
      } catch (err) {
        setError("Failed to load home page data: " + err.message);
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    
    loadHomePageData();
  }, []);

  // Render loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-64 bg-gray-200 rounded-lg mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white p-4 rounded-lg shadow">
                  <div className="h-40 bg-gray-200 rounded-lg mb-4"></div>
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-8">
            <p>{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-2 bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Banner */}
      {promotions.length > 0 && (
        <div className="bg-blue-600 text-white">
          <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
            <div className="lg:grid lg:grid-cols-2 lg:gap-8 items-center">
              <div>
                <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
                  {promotions[0].title}
                </h1>
                <p className="mt-6 text-xl max-w-3xl">
                  {promotions[0].description}
                </p>
                <div className="mt-8">
                  <Link 
                    to={`/products?promotion=${promotions[0].id}`}
                    className="bg-white text-blue-600 hover:bg-blue-50 px-6 py-3 rounded-md font-medium"
                  >
                    Shop Now
                  </Link>
                </div>
              </div>
              <div className="mt-12 lg:mt-0">
                <img 
                  src={promotions[0].image_url} 
                  alt={promotions[0].title}
                  className="rounded-lg shadow-xl"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        {/* Featured Products */}
        <section className="mb-16">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Featured Products</h2>
            <Link to="/products" className="text-blue-600 hover:text-blue-800">
              View All
            </Link>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {featuredProducts.map(product => (
              <Link 
                key={product.id} 
                to={`/products/${product.id}`}
                className="bg-white rounded-lg shadow overflow-hidden hover:shadow-md transition-shadow"
              >
                <div className="h-48 overflow-hidden">
                  <img 
                    src={product.image_url} 
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-1">{product.name}</h3>
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-bold text-gray-900">${product.price.toFixed(2)}</span>
                    {product.rating && (
                      <div className="flex items-center">
                        <span className="text-yellow-400">★</span>
                        <span className="ml-1 text-sm text-gray-600">{product.rating}</span>
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* New Arrivals */}
        <section className="mb-16">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">New Arrivals</h2>
            <Link to="/products?sort=newest" className="text-blue-600 hover:text-blue-800">
              View All
            </Link>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {newArrivals.map(product => (
              <Link 
                key={product.id} 
                to={`/products/${product.id}`}
                className="bg-white rounded-lg shadow overflow-hidden hover:shadow-md transition-shadow"
              >
                <div className="h-48 overflow-hidden">
                  <img 
                    src={product.image_url} 
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-4">
                  <div className="flex items-center mb-2">
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">New</span>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-1">{product.name}</h3>
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-bold text-gray-900">${product.price.toFixed(2)}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* Personalized Recommendations */}
        {recommendations.length > 0 && (
          <section className="mb-16">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Recommended For You</h2>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {recommendations.map(product => (
                <Link 
                  key={product.id} 
                  to={`/products/${product.id}`}
                  className="bg-white rounded-lg shadow overflow-hidden hover:shadow-md transition-shadow"
                >
                  <div className="h-48 overflow-hidden">
                    <img 
                      src={product.image_url} 
                      alt={product.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="p-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-1">{product.name}</h3>
                    <div className="flex justify-between items-center">
                      <span className="text-lg font-bold text-gray-900">${product.price.toFixed(2)}</span>
                      {product.rating && (
                        <div className="flex items-center">
                          <span className="text-yellow-400">★</span>
                          <span className="ml-1 text-sm text-gray-600">{product.rating}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

export default Home;
