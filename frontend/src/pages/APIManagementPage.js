import React, { useState, useEffect } from 'react';
import menuAPI from '../services/menuAPI';

const APIManagementPage = () => {
  const [apiStatus, setApiStatus] = useState(null);
  const [apiConfigs, setApiConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAPI, setSelectedAPI] = useState(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configValues, setConfigValues] = useState({});
  const [updateStatus, setUpdateStatus] = useState(null);

  useEffect(() => {
    loadAPIData();
  }, []);

  const loadAPIData = async () => {
    setLoading(true);
    try {
      const [statusResult, configsResult] = await Promise.all([
        menuAPI.getAPIStatus(),
        menuAPI.getAPIConfigurations()
      ]);

      if (statusResult.success) {
        setApiStatus(statusResult.data);
      } else {
        setError(statusResult.error);
      }

      if (configsResult.success) {
        setApiConfigs(configsResult.data);
      }
    } catch (err) {
      setError('Failed to load API data');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigureAPI = (api) => {
    setSelectedAPI(api);
    setConfigValues({});
    setShowConfigModal(true);
    setUpdateStatus(null);
  };

  const handleUpdateConfiguration = async () => {
    if (!selectedAPI) return;

    try {
      const result = await menuAPI.updateAPIConfiguration(selectedAPI.name, configValues);
      if (result.success) {
        setUpdateStatus({ type: 'success', message: 'Configuration updated successfully!' });
        // Reload API status
        setTimeout(() => {
          loadAPIData();
          setShowConfigModal(false);
        }, 1500);
      } else {
        setUpdateStatus({ type: 'error', message: result.error });
      }
    } catch (err) {
      setUpdateStatus({ type: 'error', message: 'Failed to update configuration' });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'not_configured': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'connected': return 'Connected';
      case 'error': return 'Error';
      case 'not_configured': return 'Not Configured';
      default: return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading API Management...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading API Management</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadAPIData}
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">API Management</h1>
          <p className="mt-2 text-gray-600">
            Monitor and configure external API integrations for the Stirling Bridge LandDev Platform
          </p>
        </div>

        {/* API Status Overview */}
        {apiStatus && (
          <div className="bg-white rounded-lg shadow mb-8">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">API Status Overview</h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-teal-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-teal-600">{apiStatus.total_configured}</div>
                  <div className="text-sm text-teal-700">Configured APIs</div>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{apiStatus.total_available}</div>
                  <div className="text-sm text-blue-700">Available APIs</div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-gray-600">
                    {apiStatus.apis.filter(api => api.status === 'connected').length}
                  </div>
                  <div className="text-sm text-gray-700">Connected</div>
                </div>
              </div>

              {/* API List */}
              <div className="space-y-4">
                {apiStatus.apis.map((api, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(api.status)}`}>
                            {getStatusText(api.status)}
                          </div>
                        </div>
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">{api.name}</h3>
                          {api.error_message && (
                            <p className="text-sm text-red-600 mt-1">{api.error_message}</p>
                          )}
                          {api.last_check && (
                            <p className="text-xs text-gray-500 mt-1">
                              Last checked: {new Date(api.last_check).toLocaleString()}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        {!api.is_configured && (
                          <button
                            onClick={() => handleConfigureAPI(api)}
                            className="bg-teal-600 text-white px-3 py-1 rounded text-sm hover:bg-teal-700 transition-colors"
                          >
                            Configure
                          </button>
                        )}
                        <button
                          onClick={loadAPIData}
                          className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 transition-colors"
                        >
                          Refresh
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Configuration Instructions */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Configuration Guide</h2>
          </div>
          <div className="p-6">
            <div className="prose max-w-none">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Getting Started</h3>
              <p className="text-gray-600 mb-4">
                The Stirling Bridge LandDev Platform integrates with several external APIs to provide comprehensive 
                land development data. Some APIs require configuration while others work out of the box.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">Free APIs (No Configuration)</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Chief Surveyor General (CSG)</li>
                    <li>• SANBI BGIS</li>
                  </ul>
                </div>
                
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">Requires Configuration</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• ArcGIS Online (Client ID & Secret)</li>
                    <li>• AfriGIS (API Key)</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Configuration Modal */}
      {showConfigModal && selectedAPI && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Configure {selectedAPI.name}
                </h3>
                <button
                  onClick={() => setShowConfigModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-3">
                  Note: This is a demo configuration. In a production environment, 
                  you would need actual API credentials.
                </p>
                
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Test Configuration Key
                    </label>
                    <input
                      type="text"
                      placeholder="Enter test value"
                      value={configValues.test_key || ''}
                      onChange={(e) => setConfigValues({...configValues, test_key: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                </div>
              </div>

              {updateStatus && (
                <div className={`mb-4 p-3 rounded-md text-sm ${
                  updateStatus.type === 'success' 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-red-100 text-red-700'
                }`}>
                  {updateStatus.message}
                </div>
              )}

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowConfigModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpdateConfiguration}
                  className="px-4 py-2 text-sm font-medium text-white bg-teal-600 rounded-md hover:bg-teal-700 transition-colors"
                >
                  Update Configuration
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default APIManagementPage;