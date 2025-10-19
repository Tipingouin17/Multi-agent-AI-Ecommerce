import React, { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Upload, RotateCcw, Palette, Moon, Sun } from 'lucide-react';

const ColorPicker = ({ label, value, onChange }) => {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="flex gap-2 items-center">
        <Input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-20 h-10 cursor-pointer"
        />
        <Input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 font-mono"
          placeholder="#000000"
        />
        <div 
          className="w-10 h-10 rounded border-2 border-gray-300"
          style={{ backgroundColor: value }}
        />
      </div>
    </div>
  );
};

export default function ThemeSettings() {
  const { theme, updateTheme, resetTheme, toggleMode, uploadLogo, isDark } = useTheme();
  const [uploading, setUploading] = useState(false);

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file');
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      alert('File size must be less than 2MB');
      return;
    }

    setUploading(true);
    try {
      await uploadLogo(file);
      alert('Logo uploaded successfully!');
    } catch (error) {
      console.error('Logo upload failed:', error);
      alert('Failed to upload logo');
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all theme settings to default?')) {
      resetTheme();
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Theme Settings</h1>
          <p className="text-gray-600 mt-1">
            Customize the appearance of your dashboard
          </p>
        </div>
        <Button variant="outline" onClick={handleReset}>
          <RotateCcw className="w-4 h-4 mr-2" />
          Reset to Default
        </Button>
      </div>

      {/* Dark Mode Toggle */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {isDark ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            Display Mode
          </CardTitle>
          <CardDescription>
            Switch between light and dark mode
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sun className="w-4 h-4 text-gray-600" />
              <span className="text-sm">Light</span>
            </div>
            <Switch
              checked={isDark}
              onCheckedChange={toggleMode}
            />
            <div className="flex items-center gap-2">
              <Moon className="w-4 h-4 text-gray-600" />
              <span className="text-sm">Dark</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Logo Upload */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Logo
          </CardTitle>
          <CardDescription>
            Upload your custom logo (PNG, JPG, SVG - max 2MB)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {theme.logoUrl && (
            <div className="flex items-center gap-4">
              <div className="w-32 h-32 border-2 border-gray-200 rounded-lg flex items-center justify-center bg-white p-4">
                <img 
                  src={theme.logoUrl} 
                  alt="Logo preview" 
                  className="max-w-full max-h-full object-contain"
                />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-600">
                  {theme.logo || 'Default logo'}
                </p>
              </div>
            </div>
          )}
          <div>
            <Input
              type="file"
              accept="image/*"
              onChange={handleLogoUpload}
              disabled={uploading}
              className="cursor-pointer"
            />
          </div>
        </CardContent>
      </Card>

      {/* Color Scheme */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Color Scheme
          </CardTitle>
          <CardDescription>
            Customize the color palette for your dashboard
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Primary Colors */}
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900">Primary Colors</h3>
              <ColorPicker
                label="Primary"
                value={theme.primary}
                onChange={(value) => updateTheme({ primary: value })}
              />
              <ColorPicker
                label="Primary Dark"
                value={theme.primaryDark}
                onChange={(value) => updateTheme({ primaryDark: value })}
              />
              <ColorPicker
                label="Primary Light"
                value={theme.primaryLight}
                onChange={(value) => updateTheme({ primaryLight: value })}
              />
            </div>

            {/* Secondary Colors */}
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900">Secondary Colors</h3>
              <ColorPicker
                label="Secondary"
                value={theme.secondary}
                onChange={(value) => updateTheme({ secondary: value })}
              />
              <ColorPicker
                label="Secondary Dark"
                value={theme.secondaryDark}
                onChange={(value) => updateTheme({ secondaryDark: value })}
              />
              <ColorPicker
                label="Secondary Light"
                value={theme.secondaryLight}
                onChange={(value) => updateTheme({ secondaryLight: value })}
              />
            </div>

            {/* Accent Colors */}
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900">Accent Colors</h3>
              <ColorPicker
                label="Accent"
                value={theme.accent}
                onChange={(value) => updateTheme({ accent: value })}
              />
              <ColorPicker
                label="Accent Dark"
                value={theme.accentDark}
                onChange={(value) => updateTheme({ accentDark: value })}
              />
              <ColorPicker
                label="Accent Light"
                value={theme.accentLight}
                onChange={(value) => updateTheme({ accentLight: value })}
              />
            </div>

            {/* Status Colors */}
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900">Status Colors</h3>
              <ColorPicker
                label="Success"
                value={theme.success}
                onChange={(value) => updateTheme({ success: value })}
              />
              <ColorPicker
                label="Warning"
                value={theme.warning}
                onChange={(value) => updateTheme({ warning: value })}
              />
              <ColorPicker
                label="Error"
                value={theme.error}
                onChange={(value) => updateTheme({ error: value })}
              />
              <ColorPicker
                label="Info"
                value={theme.info}
                onChange={(value) => updateTheme({ info: value })}
              />
            </div>
          </div>

          {/* Color Preview */}
          <div className="mt-8 p-6 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-4">Preview</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <div 
                  className="h-16 rounded-lg shadow-sm"
                  style={{ backgroundColor: theme.primary }}
                />
                <p className="text-xs text-center text-gray-600">Primary</p>
              </div>
              <div className="space-y-2">
                <div 
                  className="h-16 rounded-lg shadow-sm"
                  style={{ backgroundColor: theme.secondary }}
                />
                <p className="text-xs text-center text-gray-600">Secondary</p>
              </div>
              <div className="space-y-2">
                <div 
                  className="h-16 rounded-lg shadow-sm"
                  style={{ backgroundColor: theme.accent }}
                />
                <p className="text-xs text-center text-gray-600">Accent</p>
              </div>
              <div className="space-y-2">
                <div 
                  className="h-16 rounded-lg shadow-sm"
                  style={{ backgroundColor: theme.success }}
                />
                <p className="text-xs text-center text-gray-600">Success</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Notice */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> Theme changes are saved automatically and will persist across sessions.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

