import React, { useState, useEffect } from 'react';
import menuAPI from '../services/menuAPI';

const UserProfilePage = () => {
  const [profile, setProfile] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [updateStatus, setUpdateStatus] = useState(null);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    setLoading(true);
    try {
      const [profileResult, statsResult] = await Promise.all([
        menuAPI.getUserProfile(),
        menuAPI.getUserStatistics()
      ]);

      if (profileResult.success) {
        setProfile(profileResult.data);
        setEditForm(profileResult.data);
      } else {
        setError(profileResult.error);
      }

      if (statsResult.success) {
        setStatistics(statsResult.data);
      }
    } catch (err) {
      setError('Failed to load profile data');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setUpdateStatus(null);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditForm(profile);
    setUpdateStatus(null);
  };

  const handleSaveProfile = async () => {
    try {
      const updateData = {
        username: editForm.username !== profile.username ? editForm.username : undefined,
        email: editForm.email !== profile.email ? editForm.email : undefined,
        full_name: editForm.full_name !== profile.full_name ? editForm.full_name : undefined,
        organization: editForm.organization !== profile.organization ? editForm.organization : undefined,
      };

      // Remove undefined values
      const cleanUpdateData = Object.fromEntries(
        Object.entries(updateData).filter(([_, value]) => value !== undefined)
      );

      if (Object.keys(cleanUpdateData).length === 0) {
        setUpdateStatus({ type: 'info', message: 'No changes to save' });
        setIsEditing(false);
        return;
      }

      const result = await menuAPI.updateUserProfile(cleanUpdateData);
      
      if (result.success) {
        setProfile(result.data);
        setEditForm(result.data);
        setIsEditing(false);
        setUpdateStatus({ type: 'success', message: 'Profile updated successfully!' });
        
        // Clear status after 3 seconds
        setTimeout(() => setUpdateStatus(null), 3000);
      } else {
        setUpdateStatus({ type: 'error', message: result.error });
      }
    } catch (err) {
      setUpdateStatus({ type: 'error', message: 'Failed to update profile' });
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not available';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Invalid date';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading user profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-6xl mb-4">👤</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Profile</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadProfileData}
            className="bg-teal-600 text-white px-4 py-2 rounded-md hover:bg-teal-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">User Profile</h1>
          <p className="mt-2 text-gray-600">
            Manage your account information and view your activity statistics
          </p>
        </div>

        {/* Status Message */}
        {updateStatus && (
          <div className={`mb-6 p-4 rounded-md ${
            updateStatus.type === 'success' ? 'bg-green-100 text-green-700' :
            updateStatus.type === 'error' ? 'bg-red-100 text-red-700' :
            'bg-blue-100 text-blue-700'
          }`}>
            {updateStatus.message}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Profile Information */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">Profile Information</h2>
                {!isEditing && (
                  <button
                    onClick={handleEdit}
                    className="bg-teal-600 text-white px-4 py-2 rounded-md text-sm hover:bg-teal-700 transition-colors"
                  >
                    Edit Profile
                  </button>
                )}
              </div>
              
              <div className="p-6">
                {profile && (
                  <div className="space-y-6">
                    {/* Profile Picture Placeholder */}
                    <div className="flex items-center space-x-6">
                      <div className="h-20 w-20 bg-gradient-to-r from-teal-500 to-teal-600 rounded-full flex items-center justify-center">
                        <svg className="h-10 w-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">
                          {profile.full_name || profile.username}
                        </h3>
                        <p className="text-sm text-gray-500">
                          User ID: {profile.user_id}
                        </p>
                      </div>
                    </div>

                    {/* Profile Fields */}
                    <div className="grid grid-cols-1 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Username
                        </label>
                        {isEditing ? (
                          <input
                            type="text"
                            value={editForm.username || ''}
                            onChange={(e) => setEditForm({...editForm, username: e.target.value})}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
                          />
                        ) : (
                          <p className="text-gray-900">{profile.username}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Full Name
                        </label>
                        {isEditing ? (
                          <input
                            type="text"
                            value={editForm.full_name || ''}
                            onChange={(e) => setEditForm({...editForm, full_name: e.target.value})}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
                          />
                        ) : (
                          <p className="text-gray-900">{profile.full_name || 'Not provided'}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Email
                        </label>
                        {isEditing ? (
                          <input
                            type="email"
                            value={editForm.email || ''}
                            onChange={(e) => setEditForm({...editForm, email: e.target.value})}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
                          />
                        ) : (
                          <p className="text-gray-900">{profile.email || 'Not provided'}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Organization
                        </label>
                        {isEditing ? (
                          <input
                            type="text"
                            value={editForm.organization || ''}
                            onChange={(e) => setEditForm({...editForm, organization: e.target.value})}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
                          />
                        ) : (
                          <p className="text-gray-900">{profile.organization || 'Not provided'}</p>
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Account Created
                          </label>
                          <p className="text-gray-900">{formatDate(profile.created_at)}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Last Login
                          </label>
                          <p className="text-gray-900">{formatDate(profile.last_login)}</p>
                        </div>
                      </div>
                    </div>

                    {/* Edit Actions */}
                    {isEditing && (
                      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                        <button
                          onClick={handleCancelEdit}
                          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSaveProfile}
                          className="px-4 py-2 text-sm font-medium text-white bg-teal-600 rounded-md hover:bg-teal-700 transition-colors"
                        >
                          Save Changes
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Statistics Sidebar */}
          <div>
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Activity Statistics</h2>
              </div>
              
              <div className="p-6">
                {statistics && (
                  <div className="space-y-4">
                    <div className="bg-teal-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-teal-600">
                        {statistics.total_projects}
                      </div>
                      <div className="text-sm text-teal-700">Total Projects</div>
                    </div>

                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {statistics.projects_this_week}
                      </div>
                      <div className="text-sm text-blue-700">This Week</div>
                    </div>

                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {statistics.projects_today}
                      </div>
                      <div className="text-sm text-green-700">Today</div>
                    </div>

                    {statistics.account_age_days !== undefined && (
                      <div className="bg-purple-50 p-4 rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                          {statistics.account_age_days}
                        </div>
                        <div className="text-sm text-purple-700">Days Active</div>
                      </div>
                    )}

                    {statistics.last_project_date && (
                      <div className="pt-4 border-t border-gray-200">
                        <div className="text-sm text-gray-600">
                          <strong>Last Project:</strong><br />
                          {formatDate(statistics.last_project_date)}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfilePage;