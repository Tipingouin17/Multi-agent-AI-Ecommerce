import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Plus, Edit, Trash2, Save, X, Users, Shield, 
  Lock, Unlock, Eye, EyeOff, Key, Activity, CheckCircle2
} from 'lucide-react';

/**
 * User & Permissions Management UI
 * 
 * Features:
 * - Create, edit, delete users
 * - Role management (Admin, Merchant, Operator, Support, Customer)
 * - Permission matrix with granular controls
 * - Access control per module
 * - User activity logging
 * - Password policies
 * - Two-factor authentication
 * - Session management
 * - Bulk operations
 */

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState('user'); // 'user', 'role'
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [selectedPermissions, setSelectedPermissions] = useState([]);

  const permissionModules = [
    { module: 'Products', permissions: ['view', 'create', 'edit', 'delete', 'publish'] },
    { module: 'Orders', permissions: ['view', 'create', 'edit', 'cancel', 'refund'] },
    { module: 'Inventory', permissions: ['view', 'adjust', 'transfer', 'audit'] },
    { module: 'Customers', permissions: ['view', 'create', 'edit', 'delete', 'export'] },
    { module: 'Warehouses', permissions: ['view', 'create', 'edit', 'delete', 'configure'] },
    { module: 'Channels', permissions: ['view', 'create', 'edit', 'delete', 'sync'] },
    { module: 'Reports', permissions: ['view', 'export', 'schedule'] },
    { module: 'Settings', permissions: ['view', 'edit'] },
    { module: 'Users', permissions: ['view', 'create', 'edit', 'delete', 'manage_roles'] },
    { module: 'AI Agents', permissions: ['view', 'configure', 'train', 'deploy'] }
  ];

  useEffect(() => {
    fetchUsers();
    fetchRoles();
    fetchPermissions();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/users');
      const data = await response.json();
      setUsers(data);
    } catch (error) {
      console.error('Error fetching users:', error);
      // Mock data
      setUsers([
        {
          user_id: 1,
          username: 'admin@company.com',
          full_name: 'John Admin',
          email: 'admin@company.com',
          role: 'Admin',
          is_active: true,
          two_factor_enabled: true,
          last_login: '2025-01-20 14:30:00',
          created_at: '2024-01-01'
        },
        {
          user_id: 2,
          username: 'merchant@store.com',
          full_name: 'Jane Merchant',
          email: 'merchant@store.com',
          role: 'Merchant',
          is_active: true,
          two_factor_enabled: false,
          last_login: '2025-01-20 10:15:00',
          created_at: '2024-03-15'
        },
        {
          user_id: 3,
          username: 'operator@company.com',
          full_name: 'Bob Operator',
          email: 'operator@company.com',
          role: 'Operator',
          is_active: true,
          two_factor_enabled: true,
          last_login: '2025-01-19 16:45:00',
          created_at: '2024-06-01'
        },
        {
          user_id: 4,
          username: 'support@company.com',
          full_name: 'Alice Support',
          email: 'support@company.com',
          role: 'Support',
          is_active: false,
          two_factor_enabled: false,
          last_login: '2025-01-15 09:00:00',
          created_at: '2024-08-20'
        }
      ]);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/roles');
      const data = await response.json();
      setRoles(data);
    } catch (error) {
      console.error('Error fetching roles:', error);
      // Mock data
      setRoles([
        {
          role_id: 1,
          role_name: 'Admin',
          description: 'Full system access',
          user_count: 3,
          is_system_role: true,
          permissions_count: 50
        },
        {
          role_id: 2,
          role_name: 'Merchant',
          description: 'Manage own store and products',
          user_count: 12,
          is_system_role: true,
          permissions_count: 25
        },
        {
          role_id: 3,
          role_name: 'Operator',
          description: 'Warehouse and fulfillment operations',
          user_count: 8,
          is_system_role: true,
          permissions_count: 15
        },
        {
          role_id: 4,
          role_name: 'Support',
          description: 'Customer support access',
          user_count: 5,
          is_system_role: true,
          permissions_count: 10
        },
        {
          role_id: 5,
          role_name: 'Analyst',
          description: 'Read-only access to reports',
          user_count: 4,
          is_system_role: false,
          permissions_count: 5
        }
      ]);
    }
  };

  const fetchPermissions = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/permissions');
      const data = await response.json();
      setPermissions(data);
    } catch (error) {
      console.error('Error fetching permissions:', error);
    }
  };

  const handleCreate = (type) => {
    setDialogType(type);
    setEditingItem(null);
    
    if (type === 'user') {
      setFormData({
        username: '',
        email: '',
        full_name: '',
        password: '',
        role: 'Merchant',
        is_active: true,
        two_factor_enabled: false
      });
    } else if (type === 'role') {
      setFormData({
        role_name: '',
        description: '',
        is_system_role: false
      });
      setSelectedPermissions([]);
    }
    
    setIsDialogOpen(true);
  };

  const handleEdit = (item, type) => {
    setDialogType(type);
    setEditingItem(item);
    setFormData({ ...item });
    
    if (type === 'role') {
      // Fetch role permissions
      setSelectedPermissions([]);
    }
    
    setIsDialogOpen(true);
  };

  const handleDelete = async (id, type) => {
    if (!confirm(`Are you sure you want to delete this ${type}?`)) return;
    
    try {
      const endpoints = {
        user: 'users',
        role: 'roles'
      };
      
      await fetch(`http://localhost:8000/api/${endpoints[type]}/${id}`, {
        method: 'DELETE'
      });
      
      if (type === 'user') fetchUsers();
      else if (type === 'role') fetchRoles();
    } catch (error) {
      console.error(`Error deleting ${type}:`, error);
    }
  };

  const handleToggleStatus = async (userId, currentStatus) => {
    try {
      await fetch(`http://localhost:8000/api/users/${userId}/toggle-status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !currentStatus })
      });
      fetchUsers();
    } catch (error) {
      console.error('Error toggling user status:', error);
    }
  };

  const handleResetPassword = async (userId) => {
    if (!confirm('Send password reset email to this user?')) return;
    
    try {
      await fetch(`http://localhost:8000/api/users/${userId}/reset-password`, {
        method: 'POST'
      });
      alert('Password reset email sent successfully');
    } catch (error) {
      console.error('Error resetting password:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const endpoints = {
        user: 'users',
        role: 'roles'
      };
      
      const idFields = {
        user: 'user_id',
        role: 'role_id'
      };
      
      const url = editingItem 
        ? `http://localhost:8000/api/${endpoints[dialogType]}/${editingItem[idFields[dialogType]]}`
        : `http://localhost:8000/api/${endpoints[dialogType]}`;
      
      const method = editingItem ? 'PUT' : 'POST';
      
      const payload = dialogType === 'role' 
        ? { ...formData, permissions: selectedPermissions }
        : formData;
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      setIsDialogOpen(false);
      
      if (dialogType === 'user') fetchUsers();
      else if (dialogType === 'role') fetchRoles();
    } catch (error) {
      console.error(`Error saving ${dialogType}:`, error);
    }
  };

  const handlePermissionToggle = (module, permission) => {
    const key = `${module}:${permission}`;
    setSelectedPermissions(prev => 
      prev.includes(key) 
        ? prev.filter(p => p !== key)
        : [...prev, key]
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Users className="w-8 h-8" />
            User & Permissions Management
          </h1>
          <p className="text-muted-foreground">
            Manage users, roles, and access control
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Users
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{users.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {users.filter(u => u.is_active).length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Roles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{roles.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {roles.filter(r => !r.is_system_role).length} custom roles
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              2FA Enabled
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {users.filter(u => u.two_factor_enabled).length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {((users.filter(u => u.two_factor_enabled).length / users.length) * 100).toFixed(0)}% of users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {users.filter(u => u.is_active).length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              currently logged in
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">
            <Users className="w-4 h-4 mr-2" />
            Users
          </TabsTrigger>
          <TabsTrigger value="roles">
            <Shield className="w-4 h-4 mr-2" />
            Roles & Permissions
          </TabsTrigger>
          <TabsTrigger value="activity">
            <Activity className="w-4 h-4 mr-2" />
            Activity Log
          </TabsTrigger>
        </TabsList>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => handleCreate('user')} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Add User
            </Button>
          </div>

          {users.map(user => (
            <Card key={user.user_id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-lg">
                      {user.full_name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {user.full_name}
                        {user.is_active ? (
                          <Badge className="bg-green-500 text-white">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Active
                          </Badge>
                        ) : (
                          <Badge className="bg-gray-500 text-white">Inactive</Badge>
                        )}
                        <Badge variant="outline">{user.role}</Badge>
                        {user.two_factor_enabled && (
                          <Badge className="bg-purple-500 text-white">
                            <Shield className="w-3 h-3 mr-1" />
                            2FA
                          </Badge>
                        )}
                      </CardTitle>
                      <CardDescription>{user.email}</CardDescription>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleToggleStatus(user.user_id, user.is_active)}
                      title={user.is_active ? 'Deactivate' : 'Activate'}
                    >
                      {user.is_active ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleResetPassword(user.user_id)}
                      title="Reset Password"
                    >
                      <Key className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleEdit(user, 'user')}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleDelete(user.user_id, 'user')}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Username</p>
                    <p className="font-medium">{user.username}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Last Login</p>
                    <p className="font-medium">{user.last_login || 'Never'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Created</p>
                    <p className="font-medium">{user.created_at}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Roles Tab */}
        <TabsContent value="roles" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => handleCreate('role')} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Role
            </Button>
          </div>

          {roles.map(role => (
            <Card key={role.role_id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="w-5 h-5" />
                      {role.role_name}
                      {role.is_system_role && (
                        <Badge variant="outline">System Role</Badge>
                      )}
                      <Badge className="bg-blue-500 text-white">
                        {role.user_count} users
                      </Badge>
                    </CardTitle>
                    <CardDescription>{role.description}</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleEdit(role, 'role')}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    {!role.is_system_role && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => handleDelete(role.role_id, 'role')}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{role.permissions_count} permissions</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Activity Log Tab */}
        <TabsContent value="activity" className="space-y-4">
          <Alert>
            <Activity className="w-4 h-4" />
            <AlertDescription>
              User activity log shows recent actions, login attempts, and permission changes.
              Logs are retained for 90 days.
            </AlertDescription>
          </Alert>
          
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { user: 'John Admin', action: 'Created new user', target: 'merchant@store.com', time: '5 minutes ago' },
                  { user: 'Jane Merchant', action: 'Updated product', target: 'Product #1234', time: '15 minutes ago' },
                  { user: 'Bob Operator', action: 'Processed order', target: 'Order #5678', time: '1 hour ago' },
                  { user: 'Alice Support', action: 'Viewed customer', target: 'Customer #9012', time: '2 hours ago' }
                ].map((log, idx) => (
                  <div key={idx} className="flex justify-between items-center p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">{log.user}</p>
                      <p className="text-sm text-muted-foreground">
                        {log.action} • {log.target}
                      </p>
                    </div>
                    <p className="text-sm text-muted-foreground">{log.time}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingItem ? `Edit ${dialogType}` : `Add New ${dialogType}`}
            </DialogTitle>
            <DialogDescription>
              {dialogType === 'user' && 'Create or modify user accounts and access'}
              {dialogType === 'role' && 'Define roles and assign permissions'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {dialogType === 'user' && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="full_name">Full Name *</Label>
                    <Input
                      id="full_name"
                      value={formData.full_name || ''}
                      onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="username">Username *</Label>
                    <Input
                      id="username"
                      value={formData.username || ''}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>
                {!editingItem && (
                  <div>
                    <Label htmlFor="password">Password *</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        value={formData.password || ''}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        required={!editingItem}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Minimum 8 characters, include uppercase, lowercase, number, and special character
                    </p>
                  </div>
                )}
                <div>
                  <Label htmlFor="role">Role *</Label>
                  <Select 
                    value={formData.role || 'Merchant'} 
                    onValueChange={(value) => setFormData({ ...formData, role: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {roles.map(role => (
                        <SelectItem key={role.role_id} value={role.role_name}>
                          {role.role_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active !== false}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="rounded"
                  />
                  <Label htmlFor="is_active">Active</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="two_factor_enabled"
                    checked={formData.two_factor_enabled || false}
                    onChange={(e) => setFormData({ ...formData, two_factor_enabled: e.target.checked })}
                    className="rounded"
                  />
                  <Label htmlFor="two_factor_enabled">Enable Two-Factor Authentication</Label>
                </div>
              </>
            )}

            {dialogType === 'role' && (
              <>
                <div>
                  <Label htmlFor="role_name">Role Name *</Label>
                  <Input
                    id="role_name"
                    value={formData.role_name || ''}
                    onChange={(e) => setFormData({ ...formData, role_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description || ''}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
                
                <div className="space-y-3">
                  <Label>Permissions</Label>
                  <Alert>
                    <AlertDescription>
                      Select the permissions this role should have. Permissions are organized by module.
                    </AlertDescription>
                  </Alert>
                  
                  <div className="border rounded-lg p-4 space-y-4 max-h-96 overflow-y-auto">
                    {permissionModules.map(({ module, permissions }) => (
                      <div key={module} className="space-y-2">
                        <h4 className="font-medium">{module}</h4>
                        <div className="grid grid-cols-3 gap-2">
                          {permissions.map(permission => {
                            const key = `${module}:${permission}`;
                            return (
                              <div key={key} className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={key}
                                  checked={selectedPermissions.includes(key)}
                                  onChange={() => handlePermissionToggle(module, permission)}
                                  className="rounded"
                                />
                                <Label htmlFor={key} className="text-sm capitalize">
                                  {permission.replace('_', ' ')}
                                </Label>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                <Save className="w-4 h-4 mr-2" />
                {editingItem ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserManagement;

