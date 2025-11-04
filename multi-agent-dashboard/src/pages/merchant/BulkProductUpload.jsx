import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { 
  ArrowLeft, 
  Upload, 
  Download, 
  FileSpreadsheet,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText
} from 'lucide-react'
import api from '@/lib/api-enhanced'

/**
 * Bulk Product Upload Page
 * 
 * Allows merchants to upload multiple products at once via CSV file.
 * Features:
 * - CSV template download
 * - Drag-and-drop file upload
 * - Data validation
 * - Preview before import
 * - Progress tracking
 * - Error reporting
 */
const BulkProductUpload = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [file, setFile] = useState(null)
  const [previewData, setPreviewData] = useState(null)
  const [validationErrors, setValidationErrors] = useState([])
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState('idle') // idle, validating, uploading, complete, error

  // Parse CSV mutation
  const parseMutation = useMutation({
    mutationFn: (file) => api.product.parseProductCSV(file),
    onSuccess: (data) => {
      setPreviewData(data.products)
      setValidationErrors(data.errors || [])
      setUploadStatus('validated')
      if (data.errors?.length > 0) {
        toast.warning(`Found ${data.errors.length} validation errors`)
      } else {
        toast.success('CSV validated successfully')
      }
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to parse CSV file')
      setUploadStatus('error')
    }
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (products) => api.product.bulkCreateProducts(products),
    onMutate: () => {
      setUploadStatus('uploading')
      setUploadProgress(0)
    },
    onSuccess: (data) => {
      setUploadStatus('complete')
      setUploadProgress(100)
      toast.success(`Successfully imported ${data.created} products`)
      queryClient.invalidateQueries(['products'])
      setTimeout(() => navigate('/products'), 2000)
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to upload products')
      setUploadStatus('error')
    }
  })

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        toast.error('Please select a CSV file')
        return
      }
      setFile(selectedFile)
      setUploadStatus('validating')
      parseMutation.mutate(selectedFile)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      if (!droppedFile.name.endsWith('.csv')) {
        toast.error('Please select a CSV file')
        return
      }
      setFile(droppedFile)
      setUploadStatus('validating')
      parseMutation.mutate(droppedFile)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleDownloadTemplate = () => {
    // Create CSV template
    const template = [
      ['name', 'sku', 'description', 'category', 'price', 'cost', 'stock_quantity', 'status'],
      ['Sample Product', 'SKU-001', 'Product description', 'Electronics', '99.99', '50.00', '100', 'active'],
      ['Another Product', 'SKU-002', 'Another description', 'Clothing', '29.99', '15.00', '50', 'active']
    ]
    
    const csvContent = template.map(row => row.join(',')).join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'product_upload_template.csv'
    a.click()
    window.URL.revokeObjectURL(url)
    
    toast.success('Template downloaded')
  }

  const handleUpload = () => {
    if (validationErrors.length > 0) {
      toast.error('Please fix validation errors before uploading')
      return
    }
    uploadMutation.mutate(previewData)
  }

  const handleReset = () => {
    setFile(null)
    setPreviewData(null)
    setValidationErrors([])
    setUploadProgress(0)
    setUploadStatus('idle')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/products')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Products
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Bulk Product Upload</h1>
            <p className="text-gray-600">Import multiple products from a CSV file</p>
          </div>
        </div>
        <Button variant="outline" onClick={handleDownloadTemplate}>
          <Download className="w-4 h-4 mr-2" />
          Download Template
        </Button>
      </div>

      {/* Upload Area */}
      {uploadStatus === 'idle' && (
        <Card>
          <CardHeader>
            <CardTitle>Upload CSV File</CardTitle>
            <CardDescription>
              Select or drag and drop a CSV file containing your product data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-gray-400 transition-colors cursor-pointer"
            >
              <input
                type="file"
                id="csv-upload"
                accept=".csv"
                onChange={handleFileSelect}
                className="hidden"
              />
              <label htmlFor="csv-upload" className="cursor-pointer">
                <Upload className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <p className="text-lg font-medium mb-2">Click to upload or drag and drop</p>
                <p className="text-sm text-gray-500">CSV files only, up to 10MB</p>
              </label>
            </div>

            <Alert className="mt-6">
              <FileText className="w-4 h-4" />
              <AlertDescription>
                <strong>CSV Format Requirements:</strong>
                <ul className="list-disc list-inside mt-2 space-y-1 text-sm">
                  <li>First row must contain column headers</li>
                  <li>Required columns: name, sku, price</li>
                  <li>Optional columns: description, category, cost, stock_quantity, status</li>
                  <li>Use comma as delimiter</li>
                </ul>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* Validating State */}
      {uploadStatus === 'validating' && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
              <p className="text-lg font-medium">Validating CSV file...</p>
              <p className="text-sm text-gray-500 mt-2">Please wait while we check your data</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Preview & Validation */}
      {uploadStatus === 'validated' && previewData && (
        <>
          {/* Validation Summary */}
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center space-x-3">
                  <FileSpreadsheet className="w-8 h-8 text-blue-500" />
                  <div>
                    <p className="text-2xl font-bold">{previewData.length}</p>
                    <p className="text-sm text-gray-600">Total Products</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-8 h-8 text-green-500" />
                  <div>
                    <p className="text-2xl font-bold">{previewData.length - validationErrors.length}</p>
                    <p className="text-sm text-gray-600">Valid Products</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center space-x-3">
                  <XCircle className="w-8 h-8 text-red-500" />
                  <div>
                    <p className="text-2xl font-bold">{validationErrors.length}</p>
                    <p className="text-sm text-gray-600">Errors</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <Alert variant="destructive">
              <AlertTriangle className="w-4 h-4" />
              <AlertDescription>
                <strong>Validation Errors Found:</strong>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  {validationErrors.slice(0, 5).map((error, index) => (
                    <li key={index} className="text-sm">
                      Row {error.row}: {error.message}
                    </li>
                  ))}
                  {validationErrors.length > 5 && (
                    <li className="text-sm font-medium">
                      ... and {validationErrors.length - 5} more errors
                    </li>
                  )}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {/* Preview Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Preview Products</CardTitle>
                  <CardDescription>Review the data before importing</CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" onClick={handleReset}>
                    Cancel
                  </Button>
                  <Button 
                    onClick={handleUpload}
                    disabled={validationErrors.length > 0}
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Import {previewData.length - validationErrors.length} Products
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2 font-medium">Status</th>
                      <th className="text-left p-2 font-medium">Name</th>
                      <th className="text-left p-2 font-medium">SKU</th>
                      <th className="text-left p-2 font-medium">Price</th>
                      <th className="text-left p-2 font-medium">Stock</th>
                      <th className="text-left p-2 font-medium">Category</th>
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.slice(0, 10).map((product, index) => {
                      const hasError = validationErrors.some(e => e.row === index + 2)
                      return (
                        <tr key={index} className={`border-b ${hasError ? 'bg-red-50' : ''}`}>
                          <td className="p-2">
                            {hasError ? (
                              <Badge variant="destructive">Error</Badge>
                            ) : (
                              <Badge variant="default">Valid</Badge>
                            )}
                          </td>
                          <td className="p-2">{product.name}</td>
                          <td className="p-2">{product.sku}</td>
                          <td className="p-2">${product.price}</td>
                          <td className="p-2">{product.stock_quantity || 0}</td>
                          <td className="p-2">{product.category || '-'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
                {previewData.length > 10 && (
                  <p className="text-sm text-gray-500 text-center mt-4">
                    Showing 10 of {previewData.length} products
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Uploading State */}
      {uploadStatus === 'uploading' && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Upload className="w-16 h-16 mx-auto text-blue-500 mb-4 animate-bounce" />
              <p className="text-lg font-medium mb-4">Uploading products...</p>
              <Progress value={uploadProgress} className="w-64 mx-auto" />
              <p className="text-sm text-gray-500 mt-2">{uploadProgress}% complete</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Complete State */}
      {uploadStatus === 'complete' && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
              <p className="text-lg font-medium">Upload Complete!</p>
              <p className="text-sm text-gray-500 mt-2">
                Your products have been successfully imported
              </p>
              <Button className="mt-6" onClick={() => navigate('/products')}>
                View Products
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default BulkProductUpload
