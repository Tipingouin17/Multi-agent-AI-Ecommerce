import React, { useState, useEffect } from 'react';
import { 
  Upload, FileText, DollarSign, Calendar, CheckCircle, XCircle, 
  AlertCircle, Download, Eye, Trash2, Plus, Search, Filter,
  TrendingUp, Package, MapPin, Truck, RefreshCw, Save
} from 'lucide-react';

/**
 * Carrier Contract Management UI
 * 
 * Features:
 * - Upload carrier contracts (PDF, Excel, CSV, Word)
 * - AI-powered contract parsing
 * - Automatic rate card updates
 * - Contract version history
 * - Rate card visualization
 * - Postal zone management
 * - Fuel surcharge tracking
 * - Service level configuration
 */

const CarrierContractManagement = () => {
  // State management
  const [carriers, setCarriers] = useState([]);
  const [selectedCarrier, setSelectedCarrier] = useState(null);
  const [contracts, setContracts] = useState([]);
  const [rateCards, setRateCards] = useState([]);
  const [postalZones, setPostalZones] = useState([]);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    carrier_id: '',
    contract_number: '',
    effective_date: '',
    expiry_date: '',
    file: null
  });

  // Load carriers on mount
  useEffect(() => {
    loadCarriers();
  }, []);

  // Load contracts when carrier is selected
  useEffect(() => {
    if (selectedCarrier) {
      loadContracts(selectedCarrier.id);
      loadRateCards(selectedCarrier.id);
      loadPostalZones(selectedCarrier.id);
    }
  }, [selectedCarrier]);

  const loadCarriers = async () => {
    try {
      const response = await fetch('/api/carriers');
      const data = await response.json();
      setCarriers(data);
      if (data.length > 0) {
        setSelectedCarrier(data[0]);
      }
    } catch (error) {
      console.error('Error loading carriers:', error);
    }
  };

  const loadContracts = async (carrierId) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/carriers/${carrierId}/contracts`);
      const data = await response.json();
      setContracts(data);
    } catch (error) {
      console.error('Error loading contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRateCards = async (carrierId) => {
    try {
      const response = await fetch(`/api/carriers/${carrierId}/rate-cards`);
      const data = await response.json();
      setRateCards(data);
    } catch (error) {
      console.error('Error loading rate cards:', error);
    }
  };

  const loadPostalZones = async (carrierId) => {
    try {
      const response = await fetch(`/api/carriers/${carrierId}/postal-zones`);
      const data = await response.json();
      setPostalZones(data);
    } catch (error) {
      console.error('Error loading postal zones:', error);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    
    if (!uploadForm.file || !uploadForm.carrier_id) {
      alert('Please select a carrier and file');
      return;
    }

    try {
      setLoading(true);
      
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      formData.append('carrier_id', uploadForm.carrier_id);
      formData.append('contract_number', uploadForm.contract_number);
      formData.append('effective_date', uploadForm.effective_date);
      formData.append('expiry_date', uploadForm.expiry_date);

      const response = await fetch('/api/contracts/upload', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.success) {
        alert('Contract uploaded and parsed successfully!');
        setUploadModalOpen(false);
        loadContracts(uploadForm.carrier_id);
        loadRateCards(uploadForm.carrier_id);
        setUploadForm({
          carrier_id: '',
          contract_number: '',
          effective_date: '',
          expiry_date: '',
          file: null
        });
      } else {
        alert(`Error: ${result.error}`);
      }
    } catch (error) {
      console.error('Error uploading contract:', error);
      alert('Error uploading contract');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteContract = async (contractId) => {
    if (!confirm('Are you sure you want to delete this contract?')) {
      return;
    }

    try {
      const response = await fetch(`/api/contracts/${contractId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        alert('Contract deleted successfully');
        loadContracts(selectedCarrier.id);
      } else {
        alert('Error deleting contract');
      }
    } catch (error) {
      console.error('Error deleting contract:', error);
      alert('Error deleting contract');
    }
  };

  const viewContractDetails = (contract) => {
    setSelectedContract(contract);
    setViewModalOpen(true);
  };

  const filteredContracts = contracts.filter(contract => {
    const matchesSearch = contract.contract_number.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || contract.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'expired': return 'text-red-400';
      case 'pending': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-5 h-5" />;
      case 'expired': return <XCircle className="w-5 h-5" />;
      case 'pending': return <AlertCircle className="w-5 h-5" />;
      default: return <AlertCircle className="w-5 h-5" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Carrier Contract Management</h1>
        <p className="text-gray-400">Upload and manage carrier contracts with AI-powered parsing</p>
      </div>

      {/* Carrier Selection */}
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Truck className="w-6 h-6 text-blue-400" />
            Select Carrier
          </h2>
          <button
            onClick={() => setUploadModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5" />
            Upload Contract
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
          {carriers.map(carrier => (
            <button
              key={carrier.id}
              onClick={() => setSelectedCarrier(carrier)}
              className={`p-4 rounded-lg border-2 transition-all ${
                selectedCarrier?.id === carrier.id
                  ? 'border-blue-500 bg-blue-900/30'
                  : 'border-gray-700 hover:border-gray-600 bg-gray-700/30'
              }`}
            >
              <div className="text-center">
                <Truck className="w-8 h-8 mx-auto mb-2 text-blue-400" />
                <div className="font-semibold text-sm">{carrier.name}</div>
                <div className="text-xs text-gray-400 mt-1">
                  {carrier.contract_count || 0} contracts
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {selectedCarrier && (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <FileText className="w-8 h-8 text-blue-400" />
                <span className="text-2xl font-bold">{contracts.length}</span>
              </div>
              <div className="text-gray-400">Total Contracts</div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <DollarSign className="w-8 h-8 text-green-400" />
                <span className="text-2xl font-bold">{rateCards.length}</span>
              </div>
              <div className="text-gray-400">Rate Cards</div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <MapPin className="w-8 h-8 text-purple-400" />
                <span className="text-2xl font-bold">{postalZones.length}</span>
              </div>
              <div className="text-gray-400">Postal Zones</div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <CheckCircle className="w-8 h-8 text-green-400" />
                <span className="text-2xl font-bold">
                  {contracts.filter(c => c.status === 'active').length}
                </span>
              </div>
              <div className="text-gray-400">Active Contracts</div>
            </div>
          </div>

          {/* Contracts Table */}
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold">Contracts</h2>
              
              <div className="flex gap-4">
                {/* Search */}
                <div className="relative">
                  <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search contracts..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Filter */}
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="expired">Expired</option>
                  <option value="pending">Pending</option>
                </select>
              </div>
            </div>

            {loading ? (
              <div className="text-center py-12">
                <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-400" />
                <p className="text-gray-400">Loading contracts...</p>
              </div>
            ) : filteredContracts.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-16 h-16 mx-auto mb-4 text-gray-600" />
                <p className="text-gray-400 mb-4">No contracts found</p>
                <button
                  onClick={() => setUploadModalOpen(true)}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                >
                  Upload First Contract
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-3 px-4">Contract Number</th>
                      <th className="text-left py-3 px-4">Effective Date</th>
                      <th className="text-left py-3 px-4">Expiry Date</th>
                      <th className="text-left py-3 px-4">Status</th>
                      <th className="text-left py-3 px-4">Uploaded</th>
                      <th className="text-right py-3 px-4">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredContracts.map(contract => (
                      <tr key={contract.id} className="border-b border-gray-700 hover:bg-gray-700/50">
                        <td className="py-3 px-4 font-medium">{contract.contract_number}</td>
                        <td className="py-3 px-4">{contract.effective_date}</td>
                        <td className="py-3 px-4">{contract.expiry_date}</td>
                        <td className="py-3 px-4">
                          <div className={`flex items-center gap-2 ${getStatusColor(contract.status)}`}>
                            {getStatusIcon(contract.status)}
                            <span className="capitalize">{contract.status}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-gray-400">
                          {new Date(contract.uploaded_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => viewContractDetails(contract)}
                              className="p-2 hover:bg-gray-600 rounded-lg transition-colors"
                              title="View Details"
                            >
                              <Eye className="w-5 h-5" />
                            </button>
                            <button
                              onClick={() => window.open(contract.file_path, '_blank')}
                              className="p-2 hover:bg-gray-600 rounded-lg transition-colors"
                              title="Download"
                            >
                              <Download className="w-5 h-5" />
                            </button>
                            <button
                              onClick={() => handleDeleteContract(contract.id)}
                              className="p-2 hover:bg-red-600 rounded-lg transition-colors"
                              title="Delete"
                            >
                              <Trash2 className="w-5 h-5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Rate Cards */}
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <DollarSign className="w-6 h-6 text-green-400" />
              Current Rate Cards
            </h2>

            {rateCards.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                No rate cards available. Upload a contract to generate rate cards.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-3 px-4">Weight Range</th>
                      <th className="text-left py-3 px-4">Zone</th>
                      <th className="text-left py-3 px-4">Price</th>
                      <th className="text-left py-3 px-4">Effective Date</th>
                      <th className="text-left py-3 px-4">Last Updated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rateCards.slice(0, 10).map(rate => (
                      <tr key={rate.id} className="border-b border-gray-700 hover:bg-gray-700/50">
                        <td className="py-3 px-4">
                          {rate.weight_min} - {rate.weight_max} kg
                        </td>
                        <td className="py-3 px-4">Zone {rate.zone}</td>
                        <td className="py-3 px-4 font-semibold text-green-400">
                          €{rate.price.toFixed(2)}
                        </td>
                        <td className="py-3 px-4">{rate.effective_date}</td>
                        <td className="py-3 px-4 text-gray-400">
                          {new Date(rate.updated_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {rateCards.length > 10 && (
                  <div className="text-center mt-4 text-gray-400">
                    Showing 10 of {rateCards.length} rate cards
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Postal Zones */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <MapPin className="w-6 h-6 text-purple-400" />
              Postal Zones
            </h2>

            {postalZones.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                No postal zones configured. Upload a contract to configure zones.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {postalZones.map(zone => (
                  <div key={zone.id} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg font-semibold">Zone {zone.zone_id}</span>
                      <span className="text-sm text-gray-400">
                        {zone.postal_codes?.length || 0} codes
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm mb-2">{zone.description}</p>
                    <div className="text-xs text-gray-500">
                      Updated: {new Date(zone.updated_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* Upload Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold">Upload Carrier Contract</h2>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="text-gray-400 hover:text-gray-300"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleFileUpload}>
              <div className="space-y-4">
                {/* Carrier Selection */}
                <div>
                  <label className="block text-sm font-medium mb-2">Carrier *</label>
                  <select
                    value={uploadForm.carrier_id}
                    onChange={(e) => setUploadForm({...uploadForm, carrier_id: e.target.value})}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select Carrier</option>
                    {carriers.map(carrier => (
                      <option key={carrier.id} value={carrier.id}>{carrier.name}</option>
                    ))}
                  </select>
                </div>

                {/* Contract Number */}
                <div>
                  <label className="block text-sm font-medium mb-2">Contract Number *</label>
                  <input
                    type="text"
                    value={uploadForm.contract_number}
                    onChange={(e) => setUploadForm({...uploadForm, contract_number: e.target.value})}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., DPD-2025-001"
                    required
                  />
                </div>

                {/* Dates */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Effective Date *</label>
                    <input
                      type="date"
                      value={uploadForm.effective_date}
                      onChange={(e) => setUploadForm({...uploadForm, effective_date: e.target.value})}
                      className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Expiry Date</label>
                    <input
                      type="date"
                      value={uploadForm.expiry_date}
                      onChange={(e) => setUploadForm({...uploadForm, expiry_date: e.target.value})}
                      className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* File Upload */}
                <div>
                  <label className="block text-sm font-medium mb-2">Contract File *</label>
                  <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
                    <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <input
                      type="file"
                      accept=".pdf,.xlsx,.xls,.csv,.docx"
                      onChange={(e) => setUploadForm({...uploadForm, file: e.target.files[0]})}
                      className="hidden"
                      id="file-upload"
                      required
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <span className="text-blue-400 hover:text-blue-300">Choose file</span>
                      <span className="text-gray-400"> or drag and drop</span>
                    </label>
                    <p className="text-sm text-gray-500 mt-2">
                      PDF, Excel, CSV, or Word (Max 10MB)
                    </p>
                    {uploadForm.file && (
                      <p className="text-sm text-green-400 mt-2">
                        Selected: {uploadForm.file.name}
                      </p>
                    )}
                  </div>
                </div>

                {/* Info Box */}
                <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                  <div className="flex gap-3">
                    <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-gray-300">
                      <p className="font-semibold mb-1">AI-Powered Parsing</p>
                      <p>
                        Our AI will automatically extract pricing tables, postal zones, 
                        fuel surcharges, and service levels from your contract. 
                        Rate cards will be updated automatically.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-4 mt-6">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="flex-1 px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5" />
                      Upload & Parse
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Contract Details Modal */}
      {viewModalOpen && selectedContract && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold">Contract Details</h2>
              <button
                onClick={() => setViewModalOpen(false)}
                className="text-gray-400 hover:text-gray-300"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-400">Contract Number</label>
                  <p className="text-lg font-semibold">{selectedContract.contract_number}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Status</label>
                  <div className={`flex items-center gap-2 ${getStatusColor(selectedContract.status)}`}>
                    {getStatusIcon(selectedContract.status)}
                    <span className="capitalize text-lg font-semibold">{selectedContract.status}</span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Effective Date</label>
                  <p className="text-lg">{selectedContract.effective_date}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Expiry Date</label>
                  <p className="text-lg">{selectedContract.expiry_date}</p>
                </div>
              </div>

              {/* Parsed Data */}
              {selectedContract.parsed_data && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">Parsed Contract Data</h3>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <pre className="text-sm overflow-x-auto">
                      {JSON.stringify(selectedContract.parsed_data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-4 mt-6">
              <button
                onClick={() => window.open(selectedContract.file_path, '_blank')}
                className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Download className="w-5 h-5" />
                Download Contract
              </button>
              <button
                onClick={() => setViewModalOpen(false)}
                className="flex-1 px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CarrierContractManagement;

