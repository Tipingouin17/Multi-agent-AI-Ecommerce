/**
 * Multi-Step Wizard Component
 * 
 * A reusable wizard component for complex multi-step forms.
 * Provides step navigation, validation, progress tracking, and data persistence.
 * 
 * Usage:
 * <MultiStepWizard
 *   steps={[
 *     { id: 'step1', title: 'Basic Info', component: Step1Component },
 *     { id: 'step2', title: 'Details', component: Step2Component },
 *   ]}
 *   onComplete={(data) => console.log('Wizard completed:', data)}
 *   onCancel={() => console.log('Wizard cancelled')}
 * />
 */

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Check, ChevronLeft, ChevronRight, X } from 'lucide-react';

const MultiStepWizard = ({
  steps = [],
  initialData = {},
  onComplete,
  onCancel,
  title = 'Setup Wizard',
  description = 'Complete the following steps',
  allowSkip = false,
  persistData = true,
  storageKey = 'wizard_data'
}) => {
  // State management
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [wizardData, setWizardData] = useState(() => {
    // Load persisted data if enabled
    if (persistData && storageKey) {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        try {
          return { ...initialData, ...JSON.parse(saved) };
        } catch (e) {
          console.error('Failed to parse saved wizard data:', e);
        }
      }
    }
    return initialData;
  });
  const [completedSteps, setCompletedSteps] = useState(new Set());
  const [stepErrors, setStepErrors] = useState({});

  // Current step info
  const currentStep = steps[currentStepIndex];
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === steps.length - 1;
  const progress = ((currentStepIndex + 1) / steps.length) * 100;

  // Persist data to localStorage
  const persistWizardData = useCallback((data) => {
    if (persistData && storageKey) {
      try {
        localStorage.setItem(storageKey, JSON.stringify(data));
      } catch (e) {
        console.error('Failed to persist wizard data:', e);
      }
    }
  }, [persistData, storageKey]);

  // Update wizard data
  const updateData = useCallback((stepId, stepData) => {
    setWizardData(prev => {
      const updated = {
        ...prev,
        [stepId]: {
          ...prev[stepId],
          ...stepData
        }
      };
      persistWizardData(updated);
      return updated;
    });
  }, [persistWizardData]);

  // Validate current step
  const validateStep = useCallback(async () => {
    const step = steps[currentStepIndex];
    
    // If step has a validate function, call it
    if (step.validate) {
      try {
        const isValid = await step.validate(wizardData[step.id] || {}, wizardData);
        if (!isValid) {
          setStepErrors(prev => ({
            ...prev,
            [step.id]: 'Please fix the errors before continuing'
          }));
          return false;
        }
      } catch (error) {
        setStepErrors(prev => ({
          ...prev,
          [step.id]: error.message || 'Validation failed'
        }));
        return false;
      }
    }

    // Clear errors for this step
    setStepErrors(prev => {
      const updated = { ...prev };
      delete updated[step.id];
      return updated;
    });

    // Mark step as completed
    setCompletedSteps(prev => new Set([...prev, step.id]));
    
    return true;
  }, [currentStepIndex, steps, wizardData]);

  // Navigation handlers
  const goToNextStep = useCallback(async () => {
    const isValid = await validateStep();
    if (!isValid) return;

    if (isLastStep) {
      // Complete wizard
      if (persistData && storageKey) {
        localStorage.removeItem(storageKey);
      }
      onComplete?.(wizardData);
    } else {
      setCurrentStepIndex(prev => Math.min(prev + 1, steps.length - 1));
    }
  }, [isLastStep, validateStep, wizardData, onComplete, persistData, storageKey, steps.length]);

  const goToPreviousStep = useCallback(() => {
    setCurrentStepIndex(prev => Math.max(prev - 1, 0));
  }, []);

  const goToStep = useCallback((stepIndex) => {
    if (stepIndex >= 0 && stepIndex < steps.length) {
      setCurrentStepIndex(stepIndex);
    }
  }, [steps.length]);

  const handleCancel = useCallback(() => {
    if (persistData && storageKey) {
      localStorage.removeItem(storageKey);
    }
    onCancel?.();
  }, [onCancel, persistData, storageKey]);

  const handleSkip = useCallback(() => {
    if (allowSkip) {
      setCurrentStepIndex(prev => Math.min(prev + 1, steps.length - 1));
    }
  }, [allowSkip, steps.length]);

  // Render current step component
  const StepComponent = currentStep?.component;

  return (
    <div className="w-full max-w-4xl mx-auto">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCancel}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Progress bar */}
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">
                Step {currentStepIndex + 1} of {steps.length}
              </span>
              <span className="text-sm text-muted-foreground">
                {Math.round(progress)}% Complete
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          {/* Step indicators */}
          <div className="flex items-center justify-between mt-4">
            {steps.map((step, index) => {
              const isCompleted = completedSteps.has(step.id);
              const isCurrent = index === currentStepIndex;
              const hasError = stepErrors[step.id];

              return (
                <div
                  key={step.id}
                  className="flex flex-col items-center flex-1"
                >
                  <button
                    onClick={() => goToStep(index)}
                    className={`
                      w-10 h-10 rounded-full flex items-center justify-center
                      transition-all duration-200
                      ${isCurrent ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2' : ''}
                      ${isCompleted && !isCurrent ? 'bg-green-500 text-white' : ''}
                      ${!isCurrent && !isCompleted ? 'bg-muted text-muted-foreground' : ''}
                      ${hasError ? 'bg-destructive text-destructive-foreground' : ''}
                      hover:scale-110
                    `}
                    disabled={index > currentStepIndex && !isCompleted}
                  >
                    {isCompleted ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <span className="text-sm font-medium">{index + 1}</span>
                    )}
                  </button>
                  <span className={`
                    mt-2 text-xs text-center
                    ${isCurrent ? 'font-medium text-foreground' : 'text-muted-foreground'}
                  `}>
                    {step.title}
                  </span>
                </div>
              );
            })}
          </div>
        </CardHeader>

        <CardContent className="min-h-[400px]">
          {/* Error message */}
          {stepErrors[currentStep?.id] && (
            <div className="mb-4 p-3 bg-destructive/10 border border-destructive rounded-md">
              <p className="text-sm text-destructive">
                {stepErrors[currentStep.id]}
              </p>
            </div>
          )}

          {/* Render current step */}
          {StepComponent && (
            <StepComponent
              data={wizardData[currentStep.id] || {}}
              allData={wizardData}
              onUpdate={(data) => updateData(currentStep.id, data)}
              onNext={goToNextStep}
              onPrevious={goToPreviousStep}
            />
          )}
        </CardContent>

        <CardFooter className="flex items-center justify-between border-t pt-6">
          <div>
            {!isFirstStep && (
              <Button
                variant="outline"
                onClick={goToPreviousStep}
              >
                <ChevronLeft className="mr-2 h-4 w-4" />
                Previous
              </Button>
            )}
          </div>

          <div className="flex items-center gap-2">
            {allowSkip && !isLastStep && (
              <Button
                variant="ghost"
                onClick={handleSkip}
              >
                Skip
              </Button>
            )}
            
            <Button
              onClick={goToNextStep}
            >
              {isLastStep ? (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Complete
                </>
              ) : (
                <>
                  Next
                  <ChevronRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

export default MultiStepWizard;
