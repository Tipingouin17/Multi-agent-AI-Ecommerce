import React, { useState, useEffect } from 'react';
import { 
  Globe, DollarSign, RefreshCw, Calculator, Package, FileText,
  TrendingUp, MapPin, CreditCard, AlertCircle
} from 'lucide-react';
import { motion } from 'framer-motion';

const InternationalShippingDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [countries, setCountries] = useState([]);
  const [hsCodes, setHsCodes] = useState([]);
  const [exchangeRates, setExchangeRates] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Calculator states
  const [productValue, setProductValue] = useState('100');
  const [hsCode, setHsCode] = useState('6109');
  const [destCountry, setDestCountry] = useState('GB');
  const [weightKg, setWeightKg] = useState('1');
  const [landedCost, setLandedCost] = useState(null);
  const [calculating, setCalculating] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard data
      const dashboardRes = await fetch('http://localhost:8038/api/international/dashboard');
      const dashboardData = await dashboardRes.json();
      setDashboardData(dashboardData);
      
      // Fetch countries
      const countriesRes = await fetch('http://localhost:8038/api/international/countries');
      const countriesData = await countriesRes.json();
      setCountries(countriesData.countries || []);
      
      // Fetch HS codes
      const hsCodesRes = await fetch('http://localhost:8038/api/international/hs-codes');
      const hsCodesData = await hsCodesRes.json();
      setHsCodes(hsCodesData.hs_codes || []);
      
      // Fetch exchange rates
      const ratesRes = await fetch('http://localhost:8038/api/international/exchange-rates');
      const ratesData = await ratesRes.json();
      setExchangeRates(ratesData);
      
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateLandedCost = async () => {
    try {
      setCalculating(true);
      const response = await fetch('http://localhost:8038/api/international/landed-cost', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_value: parseFloat(productValue),
          hs_code: hsCode,
          destination_country: destCountry,
          origin_country: 'US',
          weight_kg: parseFloat(weightKg),
          currency: 'USD'
        })
      });
      const data = await response.json();
      setLandedCost(data);
    } catch (error) {
      console.error('Error calculating landed cost:', error);
    } finally {
      setCalculating(false);
    }
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const summary = dashboardData?.summary || {};

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">International Shipping</h1>
          <p className="text-gray-600 mt-1">Global shipping with customs and duty calculation</p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Supported Countries</p>
              <p className="text-2xl font-bold text-indigo-600 mt-1">
                {dashboardData?.supported_countries || 0}
              </p>
            </div>
            <div className="p-3 bg-indigo-50 rounded-lg">
              <Globe className="w-6 h-6 text-indigo-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Currencies</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {dashboardData?.supported_currencies || 0}
              </p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">HS Codes</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {dashboardData?.hs_codes_available || 0}
              </p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Shipments</p>
              <p className="text-2xl font-bold text-purple-600 mt-1">
                {summary.total_shipments || 0}
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <Package className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Landed Cost Calculator */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Calculator className="w-5 h-5 text-indigo-600" />
          Landed Cost Calculator
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Product Value (USD)
            </label>
            <input
              type="number"
              value={productValue}
              onChange={(e) => setProductValue(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="100.00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              HS Code
            </label>
            <select
              value={hsCode}
              onChange={(e) => setHsCode(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              {hsCodes.map(code => (
                <option key={code.hs_code} value={code.hs_code}>
                  {code.hs_code} - {code.description}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Destination
            </label>
            <select
              value={destCountry}
              onChange={(e) => setDestCountry(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              {countries.map(country => (
                <option key={country.code} value={country.code}>
                  {country.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Weight (kg)
            </label>
            <input
              type="number"
              value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="1.0"
              step="0.1"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={calculateLandedCost}
              disabled={calculating}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {calculating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Calculating...
                </>
              ) : (
                <>
                  <Calculator className="w-4 h-4" />
                  Calculate
                </>
              )}
            </button>
          </div>
        </div>

        {/* Landed Cost Results */}
        {landedCost && landedCost.success && (
          <div className="mt-6 border-t pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Cost Breakdown */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-4">Cost Breakdown</h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Product Cost</span>
                    <span className="font-semibold">${landedCost.costs.product_cost}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Shipping Cost</span>
                    <span className="font-semibold">${landedCost.costs.shipping_cost}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Insurance</span>
                    <span className="font-semibold">${landedCost.costs.insurance}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                    <span className="text-gray-600">Import Duty ({landedCost.duty_info.duty_rate}%)</span>
                    <span className="font-semibold text-yellow-700">${landedCost.costs.duty}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                    <span className="text-gray-600">VAT/GST ({landedCost.duty_info.vat_rate}%)</span>
                    <span className="font-semibold text-yellow-700">${landedCost.costs.vat}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Handling Fee</span>
                    <span className="font-semibold">${landedCost.costs.handling_fee}</span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-indigo-50 rounded-lg border-2 border-indigo-200">
                    <span className="font-bold text-gray-900">Total Landed Cost</span>
                    <span className="text-2xl font-bold text-indigo-600">${landedCost.costs.total_landed_cost}</span>
                  </div>
                </div>
              </div>

              {/* Percentage Breakdown */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-4">Percentage Breakdown</h4>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600">Product</span>
                      <span className="text-sm font-semibold">{landedCost.breakdown.product_percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-indigo-600 h-3 rounded-full" 
                        style={{ width: `${landedCost.breakdown.product_percentage}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600">Shipping</span>
                      <span className="text-sm font-semibold">{landedCost.breakdown.shipping_percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-blue-600 h-3 rounded-full" 
                        style={{ width: `${landedCost.breakdown.shipping_percentage}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600">Duties & Taxes</span>
                      <span className="text-sm font-semibold">{landedCost.breakdown.duties_taxes_percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-yellow-600 h-3 rounded-full" 
                        style={{ width: `${landedCost.breakdown.duties_taxes_percentage}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600">Fees</span>
                      <span className="text-sm font-semibold">{landedCost.breakdown.fees_percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-gray-600 h-3 rounded-full" 
                        style={{ width: `${landedCost.breakdown.fees_percentage}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" />
                      De minimis threshold for {landedCost.country_name}: ${landedCost.duty_info.de_minimis_threshold}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Exchange Rates */}
      {exchangeRates && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-indigo-600" />
            Current Exchange Rates (Base: {exchangeRates.base_currency})
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            {Object.entries(exchangeRates.rates || {}).map(([currency, rate]) => (
              <div key={currency} className="p-4 bg-gray-50 rounded-lg text-center">
                <p className="text-sm text-gray-600 mb-1">{currency}</p>
                <p className="text-lg font-bold text-gray-900">{rate.toFixed(4)}</p>
              </div>
            ))}
          </div>
          
          <p className="text-xs text-gray-500 mt-4">
            Last updated: {new Date(exchangeRates.last_updated).toLocaleString()}
          </p>
        </div>
      )}

      {/* Supported Countries */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-indigo-600" />
          Supported Countries ({countries.length})
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {countries.map(country => (
            <div key={country.code} className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-gray-900">{country.name}</h4>
                <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">{country.code}</span>
              </div>
              <div className="space-y-1 text-sm text-gray-600">
                <p>De minimis: ${country.de_minimis}</p>
                <p>VAT Rate: {country.vat_rate}%</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default InternationalShippingDashboard;
