import React, { useState } from 'react';
import WizardProgress from './WizardProgress';
import Step1BasicInformation from './steps/Step1BasicInformation';
import Step2Specifications from './steps/Step2Specifications';
import Step3VisualAssets from './steps/Step3VisualAssets';
import Step4PricingCosts from './steps/Step4PricingCosts';
import Step5InventoryLogistics from './steps/Step5InventoryLogistics';
import Step6BundleKit from './steps/Step6BundleKit';
import Step7MarketplaceCompliance from './steps/Step7MarketplaceCompliance';
import Step8ReviewActivation from './steps/Step8ReviewActivation';

/**
 * ProductWizard - 8-Step Product Creation Wizard
 * 
 * Comprehensive wizard for creating products matching Market Master functionality
 */
const ProductWizard = ({ 
  isOpen, 
  onClose, 
  onSave,
  categories = [],
  warehouses = [],
  marketplaces = [],
  availableProducts = []
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Step 1: Basic Information
    name: '',
    display_name: '',
    sku: '',
    category: '',
    product_type: 'simple',
    brand: '',
    model_number: '',
    description: '',
    key_features: [],
    
    // Step 2: Specifications
    length: '',
    width: '',
    height: '',
    weight: '',
    material: '',
    color: '',
    warranty: '',
    country_of_origin: '',
    specifications: {},
    
    // Step 3: Visual Assets
    images: [],
    video_url: '',
    
    // Step 4: Pricing & Costs
    price: '',
    cost: '',
    compare_price: '',
    profit_margin: '',
    currency: 'USD',
    taxable: false,
    tax_class: 'standard',
    tax_rate: '',
    enable_bulk_pricing: false,
    
    // Step 5: Inventory & Logistics
    track_inventory: true,
    low_stock_threshold: '',
    reorder_point: '',
    reorder_quantity: '',
    enable_low_stock_alerts: false,
    warehouse_inventory: {},
    shipping_weight: '',
    handling_time: '',
    fulfillment_method: 'standard',
    free_shipping: false,
    
    // Step 6: Bundle & Kit
    is_bundle: false,
    bundle_type: 'fixed',
    bundle_pricing: 'calculated',
    bundle_fixed_price: '',
    bundle_discount: '',
    bundle_products: [],
    
    // Step 7: Marketplace & Compliance
    selected_marketplaces: [],
    marketplace_config: {},
    gtin: '',
    upc: '',
    ean: '',
    isbn: '',
    has_age_restriction: false,
    min_age: '',
    is_hazmat: false,
    hazmat_class: '',
    certifications: '',
    safety_warnings: '',
    has_export_restrictions: false,
    
    // Step 8: Review & Activation
    publish_status: 'draft',
    publish_date: '',
    notify_subscribers: false,
    feature_product: false
  });

  const handleFormDataChange = (newData) => {
    setFormData(newData);
  };

  const handleNext = () => {
    if (currentStep < 8) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSaveDraft = () => {
    const draftData = {
      ...formData,
      publish_status: 'draft',
      status: 'draft'
    };
    onSave(draftData);
  };

  const handleSubmit = () => {
    const finalData = {
      ...formData,
      status: formData.publish_status === 'active' ? 'active' : 'draft'
    };
    onSave(finalData);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <Step1BasicInformation
            formData={formData}
            onChange={handleFormDataChange}
            categories={categories}
          />
        );
      case 2:
        return (
          <Step2Specifications
            formData={formData}
            onChange={handleFormDataChange}
          />
        );
      case 3:
        return (
          <Step3VisualAssets
            formData={formData}
            onChange={handleFormDataChange}
          />
        );
      case 4:
        return (
          <Step4PricingCosts
            formData={formData}
            onChange={handleFormDataChange}
          />
        );
      case 5:
        return (
          <Step5InventoryLogistics
            formData={formData}
            onChange={handleFormDataChange}
            warehouses={warehouses}
          />
        );
      case 6:
        return (
          <Step6BundleKit
            formData={formData}
            onChange={handleFormDataChange}
            availableProducts={availableProducts}
          />
        );
      case 7:
        return (
          <Step7MarketplaceCompliance
            formData={formData}
            onChange={handleFormDataChange}
            marketplaces={marketplaces}
          />
        );
      case 8:
        return (
          <Step8ReviewActivation
            formData={formData}
            onChange={handleFormDataChange}
          />
        );
      default:
        return null;
    }
  };

  const isLastStep = currentStep === 8;
  const isFirstStep = currentStep === 1;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Create New Product</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 pt-6">
          <WizardProgress currentStep={currentStep} totalSteps={8} />
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {renderStep()}
        </div>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div>
            <button
              onClick={handleSaveDraft}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors font-medium"
            >
              Save Draft
            </button>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handlePrevious}
              disabled={isFirstStep}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                isFirstStep
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
              }`}
            >
              Previous
            </button>

            {isLastStep ? (
              <button
                onClick={handleSubmit}
                className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium"
              >
                {formData.publish_status === 'active' ? 'Publish Product' : 'Save Product'}
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductWizard;
