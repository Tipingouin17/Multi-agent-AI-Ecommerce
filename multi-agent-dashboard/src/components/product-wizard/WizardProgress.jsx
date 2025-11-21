import React from 'react';

/**
 * WizardProgress Component
 * 
 * Displays the progress bar and step indicator for the product creation wizard
 */
const WizardProgress = ({ currentStep, totalSteps = 8 }) => {
  const steps = [
    { id: 1, name: 'Basic Information', shortName: 'Basic Info' },
    { id: 2, name: 'Specifications', shortName: 'Specs' },
    { id: 3, name: 'Visual Assets', shortName: 'Media' },
    { id: 4, name: 'Pricing & Costs', shortName: 'Pricing' },
    { id: 5, name: 'Inventory & Logistics', shortName: 'Inventory' },
    { id: 6, name: 'Bundle & Kit Config', shortName: 'Bundles' },
    { id: 7, name: 'Marketplace & Compliance', shortName: 'Marketplace' },
    { id: 8, name: 'Review & Activation', shortName: 'Review' }
  ];

  const progressPercentage = Math.round((currentStep / totalSteps) * 100);

  return (
    <div className="mb-8">
      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            Step {currentStep} of {totalSteps}
          </span>
          <span className="text-sm font-medium text-blue-600">
            {progressPercentage}% Complete
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Step Indicators */}
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className="flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all duration-200 ${
                  step.id < currentStep
                    ? 'bg-green-500 text-white'
                    : step.id === currentStep
                    ? 'bg-blue-600 text-white ring-4 ring-blue-200'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {step.id < currentStep ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  step.id
                )}
              </div>
              <span
                className={`mt-2 text-xs font-medium text-center max-w-[80px] ${
                  step.id === currentStep ? 'text-blue-600' : 'text-gray-500'
                }`}
              >
                {step.shortName}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div
                className={`flex-1 h-1 mx-2 rounded transition-all duration-200 ${
                  step.id < currentStep ? 'bg-green-500' : 'bg-gray-200'
                }`}
              ></div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default WizardProgress;
