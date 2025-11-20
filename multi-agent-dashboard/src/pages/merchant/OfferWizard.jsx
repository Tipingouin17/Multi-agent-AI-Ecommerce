/**
 * Offer Creation Wizard
 * Multi-step wizard for creating special offers and promotions
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MultiStepWizard from '@/components/ui/MultiStepWizard';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import { Checkbox } from '@/components/ui/checkbox';
import { apiService } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

// ============================================================================
// WIZARD STEPS
// ============================================================================

// Step 1: Basic Information
const BasicInfoStep = ({ data, onUpdate }) => {
  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="name">Offer Name *</Label>
        <Input
          id="name"
          value={data.name || ''}
          onChange={(e) => onUpdate({ name: e.target.value })}
          placeholder="e.g., Summer Sale 2024"
          required
        />
      </div>

      <div>
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={data.description || ''}
          onChange={(e) => onUpdate({ description: e.target.value })}
          placeholder="Describe your offer..."
          rows={4}
        />
      </div>

      <div>
        <Label htmlFor="offer_type">Offer Type *</Label>
        <Select
          value={data.offer_type || ''}
          onValueChange={(value) => onUpdate({ offer_type: value })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select offer type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="percentage">Percentage Discount</SelectItem>
            <SelectItem value="fixed_amount">Fixed Amount Discount</SelectItem>
            <SelectItem value="buy_x_get_y">Buy X Get Y</SelectItem>
            <SelectItem value="bundle">Bundle Deal</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="display_badge">Display Badge</Label>
        <Input
          id="display_badge"
          value={data.display_badge || ''}
          onChange={(e) => onUpdate({ display_badge: e.target.value })}
          placeholder="e.g., Limited Time, Flash Sale"
        />
      </div>
    </div>
  );
};

// Step 2: Discount Configuration
const DiscountConfigStep = ({ data, allData, onUpdate }) => {
  const offerType = allData.step1?.offer_type;

  return (
    <div className="space-y-4">
      {(offerType === 'percentage' || offerType === 'fixed_amount') && (
        <>
          <div>
            <Label htmlFor="discount_type">Discount Type</Label>
            <Select
              value={data.discount_type || offerType}
              onValueChange={(value) => onUpdate({ discount_type: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="percentage">Percentage</SelectItem>
                <SelectItem value="fixed">Fixed Amount</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="discount_value">
              Discount Value * {data.discount_type === 'percentage' ? '(%)' : '($)'}
            </Label>
            <Input
              id="discount_value"
              type="number"
              step="0.01"
              value={data.discount_value || ''}
              onChange={(e) => onUpdate({ discount_value: parseFloat(e.target.value) })}
              placeholder={data.discount_type === 'percentage' ? '10' : '5.00'}
              required
            />
          </div>
        </>
      )}

      <div>
        <Label htmlFor="min_purchase_amount">Minimum Purchase Amount ($)</Label>
        <Input
          id="min_purchase_amount"
          type="number"
          step="0.01"
          value={data.min_purchase_amount || ''}
          onChange={(e) => onUpdate({ min_purchase_amount: parseFloat(e.target.value) })}
          placeholder="0.00"
        />
      </div>

      <div>
        <Label htmlFor="max_discount_amount">Maximum Discount Amount ($)</Label>
        <Input
          id="max_discount_amount"
          type="number"
          step="0.01"
          value={data.max_discount_amount || ''}
          onChange={(e) => onUpdate({ max_discount_amount: parseFloat(e.target.value) })}
          placeholder="No limit"
        />
      </div>

      <div className="flex items-center space-x-2">
        <Checkbox
          id="stackable"
          checked={data.stackable || false}
          onCheckedChange={(checked) => onUpdate({ stackable: checked })}
        />
        <Label htmlFor="stackable">
          Allow stacking with other offers
        </Label>
      </div>
    </div>
  );
};

// Step 3: Scheduling
const SchedulingStep = ({ data, onUpdate }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Checkbox
          id="is_scheduled"
          checked={data.is_scheduled || false}
          onCheckedChange={(checked) => onUpdate({ is_scheduled: checked })}
        />
        <Label htmlFor="is_scheduled">
          Schedule this offer for specific dates
        </Label>
      </div>

      {data.is_scheduled && (
        <>
          <div>
            <Label htmlFor="start_date">Start Date & Time</Label>
            <Input
              id="start_date"
              type="datetime-local"
              value={data.start_date || ''}
              onChange={(e) => onUpdate({ start_date: e.target.value })}
            />
          </div>

          <div>
            <Label htmlFor="end_date">End Date & Time</Label>
            <Input
              id="end_date"
              type="datetime-local"
              value={data.end_date || ''}
              onChange={(e) => onUpdate({ end_date: e.target.value })}
            />
          </div>
        </>
      )}

      <div className="p-4 bg-muted rounded-md">
        <p className="text-sm text-muted-foreground">
          {data.is_scheduled
            ? 'This offer will automatically activate and deactivate based on the scheduled dates.'
            : 'This offer will remain active until manually paused or cancelled.'}
        </p>
      </div>
    </div>
  );
};

// Step 4: Usage Limits
const UsageLimitsStep = ({ data, onUpdate }) => {
  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="total_usage_limit">Total Usage Limit</Label>
        <Input
          id="total_usage_limit"
          type="number"
          value={data.total_usage_limit || ''}
          onChange={(e) => onUpdate({ total_usage_limit: parseInt(e.target.value) })}
          placeholder="Unlimited"
        />
        <p className="text-sm text-muted-foreground mt-1">
          Maximum number of times this offer can be used across all customers
        </p>
      </div>

      <div>
        <Label htmlFor="usage_limit_per_customer">Usage Limit Per Customer</Label>
        <Input
          id="usage_limit_per_customer"
          type="number"
          value={data.usage_limit_per_customer || ''}
          onChange={(e) => onUpdate({ usage_limit_per_customer: parseInt(e.target.value) })}
          placeholder="Unlimited"
        />
        <p className="text-sm text-muted-foreground mt-1">
          Maximum number of times a single customer can use this offer
        </p>
      </div>

      <div>
        <Label htmlFor="priority">Priority</Label>
        <Input
          id="priority"
          type="number"
          value={data.priority || 0}
          onChange={(e) => onUpdate({ priority: parseInt(e.target.value) })}
          placeholder="0"
        />
        <p className="text-sm text-muted-foreground mt-1">
          Higher priority offers are shown first (0 = normal priority)
        </p>
      </div>
    </div>
  );
};

// Step 5: Review & Confirm
const ReviewStep = ({ allData }) => {
  const step1 = allData.step1 || {};
  const step2 = allData.step2 || {};
  const step3 = allData.step3 || {};
  const step4 = allData.step4 || {};

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="pt-6">
          <h3 className="font-semibold mb-4">Basic Information</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Name:</dt>
              <dd className="font-medium">{step1.name}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Type:</dt>
              <dd className="font-medium capitalize">{step1.offer_type?.replace('_', ' ')}</dd>
            </div>
            {step1.display_badge && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Badge:</dt>
                <dd className="font-medium">{step1.display_badge}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <h3 className="font-semibold mb-4">Discount Configuration</h3>
          <dl className="space-y-2">
            {step2.discount_value && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Discount:</dt>
                <dd className="font-medium">
                  {step2.discount_type === 'percentage'
                    ? `${step2.discount_value}%`
                    : `$${step2.discount_value}`}
                </dd>
              </div>
            )}
            {step2.min_purchase_amount && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Min Purchase:</dt>
                <dd className="font-medium">${step2.min_purchase_amount}</dd>
              </div>
            )}
            {step2.max_discount_amount && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Max Discount:</dt>
                <dd className="font-medium">${step2.max_discount_amount}</dd>
              </div>
            )}
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Stackable:</dt>
              <dd className="font-medium">{step2.stackable ? 'Yes' : 'No'}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {step3.is_scheduled && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="font-semibold mb-4">Schedule</h3>
            <dl className="space-y-2">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Start:</dt>
                <dd className="font-medium">{new Date(step3.start_date).toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">End:</dt>
                <dd className="font-medium">{new Date(step3.end_date).toLocaleString()}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="pt-6">
          <h3 className="font-semibold mb-4">Usage Limits</h3>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Total Limit:</dt>
              <dd className="font-medium">{step4.total_usage_limit || 'Unlimited'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Per Customer:</dt>
              <dd className="font-medium">{step4.usage_limit_per_customer || 'Unlimited'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Priority:</dt>
              <dd className="font-medium">{step4.priority || 0}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const OfferWizard = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // Validation functions
  const validateStep1 = (data) => {
    if (!data.name || !data.offer_type) {
      throw new Error('Please fill in all required fields');
    }
    return true;
  };

  const validateStep2 = (data, allData) => {
    const offerType = allData.step1?.offer_type;
    if ((offerType === 'percentage' || offerType === 'fixed_amount') && !data.discount_value) {
      throw new Error('Please enter a discount value');
    }
    return true;
  };

  const validateStep3 = (data) => {
    if (data.is_scheduled) {
      if (!data.start_date || !data.end_date) {
        throw new Error('Please select start and end dates');
      }
      if (new Date(data.end_date) <= new Date(data.start_date)) {
        throw new Error('End date must be after start date');
      }
    }
    return true;
  };

  // Wizard steps configuration
  const steps = [
    {
      id: 'step1',
      title: 'Basic Info',
      component: BasicInfoStep,
      validate: validateStep1
    },
    {
      id: 'step2',
      title: 'Discount',
      component: DiscountConfigStep,
      validate: validateStep2
    },
    {
      id: 'step3',
      title: 'Schedule',
      component: SchedulingStep,
      validate: validateStep3
    },
    {
      id: 'step4',
      title: 'Limits',
      component: UsageLimitsStep
    },
    {
      id: 'step5',
      title: 'Review',
      component: ReviewStep
    }
  ];

  // Handle wizard completion
  const handleComplete = async (wizardData) => {
    try {
      // Combine all step data
      const offerData = {
        ...wizardData.step1,
        ...wizardData.step2,
        ...wizardData.step3,
        ...wizardData.step4
      };

      // Create offer via API
      await apiService.createOffer(offerData);

      toast({
        title: 'Success',
        description: 'Offer created successfully!',
      });

      // Navigate to offers list
      navigate('/merchant/offers');
    } catch (error) {
      console.error('Error creating offer:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to create offer',
        variant: 'destructive',
      });
    }
  };

  // Handle wizard cancellation
  const handleCancel = () => {
    navigate('/merchant/offers');
  };

  return (
    <div className="container mx-auto py-8">
      <MultiStepWizard
        steps={steps}
        title="Create New Offer"
        description="Set up a special offer or promotion for your products"
        onComplete={handleComplete}
        onCancel={handleCancel}
        persistData={true}
        storageKey="offer_wizard_data"
      />
    </div>
  );
};

export default OfferWizard;
