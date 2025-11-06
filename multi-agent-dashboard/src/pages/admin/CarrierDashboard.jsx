import React, { useState, useEffect } from 'react';
import { 
  Truck, Upload, DollarSign, Package, Clock, CheckCircle,
  AlertCircle, RefreshCw, Download, Plus, Search, FileText,
  TrendingUp, BarChart3, Zap, MapPin
} from 'lucide-react';
import { motion } from 'framer-motion';

const CarrierDashboard = () => {
  const [carriers, setCarriers] = useState([]);
  const [rateCards, setRateCards] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('carriers');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedCarrier, setSelectedCarrier] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch carriers
      const carriersRes = await fetch('http://localhost:8034/api/carriers');
      const carriersData = await carriersRes.json();
      setCarriers(carriersData.carriers || []);

      // Fetch rate card uploads
      const rateCardsRes = await fetch('http://localhost:8034/api/rate-cards');
      const rateCardsData = await rateCardsRes.json();
      setRateCards(rateCardsData.uploads || []);

    } catch (error) {
      console.error('Error fetching carrier data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUploadRateCard = async () => {
    if (!selectedFile || !selectedCarrier) {
      alert('Please select a carrier and file');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(
        `http://localhost:8034/api/carriers/${selectedCarrier}/upload-rate-card`,
        {
          method: 'POST',
          body: formData
        }
      );

      const result = await response.json();

      if (result.success) {
        setExtractedData(result.extracted_data);
        alert(`Success! Extracted ${result.rates_count} rates from ${result.services_count} services.`);
        fetchData();
        setShowUploadModal(false);
        setSelectedFile(null);
      } else {
        alert('Upload failed: ' + result.message);
      }
    } catch (error) {
      console.error('Error uploading rate card:', error);
      alert('Error uploading rate card');
    } finally {
      setUploading(false);
    }
  };

  const handleImportRates = async (uploadId) => {
    try {
      const response = await fetch(
        `http://localhost:8034/api/rate-cards/${uploadId}/import`,
        { method: 'POST' }
      );

      const result = await response.json();

      if (result.success) {
        alert(`Successfully imported ${result.rates_imported} rates!`);
        fetchData();
      } else {
        alert('Import failed');
      }
    } catch (error) {
      console.error('Error importing rates:', error);
      alert('Error importing rates');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'text-yellow-600 bg-yellow-50',
      'processing': 'text-blue-600 bg-blue-50',
      'completed': 'text-green-600 bg-green-50',
      'extracted': 'text-purple-600 bg-purple-50',
      'imported': 'text-green-600 bg-green-50',
      'failed': 'text-red-600 bg-red-50'
    };
    return colors[status] || 'text-gray-600 bg-gray-50';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateMetrics = () => {
    const activeCarriers = carriers.filter(c => c.is_active).length;
    const totalUploads = rateCards.length;
    const successfulExtractions = rateCards.filter(r => r.extraction_status === 'extracted' || r.extraction_status === 'imported').length;
    const totalRatesImported = rateCards.reduce((sum, r) => sum + (r.rates_imported_count || 0), 0);
    
    return {
      activeCarriers,
      totalUploads,
      successfulExtractions,
      totalRatesImported
    };
  };

  const metrics = calculateMetrics();

  if (loading && carriers.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Carrier Management</h1>
          <p className="text-gray-600 mt-1">AI-powered rate card extraction and carrier selection</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            <Upload className="w-4 h-4" />
            Upload Rate Card
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Carriers</p>
              <p className="text-2xl font-bold text-indigo-600 mt-1">{metrics.activeCarriers}</p>
            </div>
            <div className="p-3 bg-indigo-50 rounded-lg">
              <Truck className="w-6 h-6 text-indigo-600" />
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
              <p className="text-sm text-gray-600">Rate Cards Uploaded</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">{metrics.totalUploads}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <FileText className="w-6 h-6 text-blue-600" />
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
              <p className="text-sm text-gray-600">AI Extractions</p>
              <p className="text-2xl font-bold text-purple-600 mt-1">{metrics.successfulExtractions}</p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <Zap className="w-6 h-6 text-purple-600" />
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
              <p className="text-sm text-gray-600">Rates Imported</p>
              <p className="text-2xl font-bold text-green-600 mt-1">{metrics.totalRatesImported}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {[
              { id: 'carriers', label: 'Carriers', count: carriers.length },
              { id: 'rate-cards', label: 'Rate Card Uploads', count: rateCards.length }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
                <span className="ml-2 px-2 py-1 text-xs rounded-full bg-gray-100">
                  {tab.count}
                </span>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Carriers Tab */}
          {activeTab === 'carriers' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {carriers.map((carrier) => (
                  <div key={carrier.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-50 rounded-lg">
                          <Truck className="w-5 h-5 text-indigo-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{carrier.carrier_name}</h3>
                          <p className="text-sm text-gray-500">{carrier.carrier_code}</p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${
                        carrier.is_active ? 'bg-green-50 text-green-600' : 'bg-gray-50 text-gray-600'
                      }`}>
                        {carrier.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">DIM Divisor</span>
                        <span className="font-medium">{carrier.dim_weight_divisor || 139}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Tracking</span>
                        <span className="font-medium">{carrier.supports_tracking ? '✓' : '✗'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Labels</span>
                        <span className="font-medium">{carrier.supports_labels ? '✓' : '✗'}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        setSelectedCarrier(carrier.id);
                        setShowUploadModal(true);
                      }}
                      className="mt-4 w-full flex items-center justify-center gap-2 px-3 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 text-sm font-medium"
                    >
                      <Upload className="w-4 h-4" />
                      Upload Rate Card
                    </button>
                  </div>
                ))}
              </div>

              {carriers.length === 0 && (
                <div className="text-center py-12">
                  <Truck className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No carriers configured</p>
                </div>
              )}
            </div>
          )}

          {/* Rate Cards Tab */}
          {activeTab === 'rate-cards' && (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        File Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Carrier
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Upload Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Extraction Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Rates Imported
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Uploaded
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {rateCards.map((rateCard) => (
                      <tr key={rateCard.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <FileText className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm font-medium text-gray-900">
                              {rateCard.upload_filename}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          Carrier #{rateCard.carrier_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(rateCard.upload_status)}`}>
                            {rateCard.upload_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(rateCard.extraction_status)}`}>
                            {rateCard.extraction_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {rateCard.rates_imported_count || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(rateCard.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {rateCard.extraction_status === 'extracted' && (
                            <button
                              onClick={() => handleImportRates(rateCard.id)}
                              className="text-indigo-600 hover:text-indigo-900 font-medium"
                            >
                              Import Rates
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {rateCards.length === 0 && (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No rate cards uploaded yet</p>
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                  >
                    <Upload className="w-4 h-4" />
                    Upload Your First Rate Card
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Upload Rate Card</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Carrier
                </label>
                <select
                  value={selectedCarrier || ''}
                  onChange={(e) => setSelectedCarrier(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Choose a carrier...</option>
                  {carriers.filter(c => c.is_active).map(carrier => (
                    <option key={carrier.id} value={carrier.id}>
                      {carrier.carrier_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload File (PDF, Excel, or Image)
                </label>
                <input
                  type="file"
                  accept=".pdf,.xlsx,.xls,.png,.jpg,.jpeg"
                  onChange={handleFileSelect}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
                {selectedFile && (
                  <p className="mt-2 text-sm text-gray-600">
                    Selected: {selectedFile.name}
                  </p>
                )}
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  <strong>AI will extract:</strong> Service levels, zones, weight brackets, 
                  base rates, fuel surcharges, and additional fees automatically.
                </p>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowUploadModal(false);
                  setSelectedFile(null);
                  setSelectedCarrier(null);
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUploadRateCard}
                disabled={!selectedFile || !selectedCarrier || uploading}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Processing...' : 'Upload & Extract'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CarrierDashboard;
