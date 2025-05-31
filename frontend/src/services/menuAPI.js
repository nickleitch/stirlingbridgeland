import axios from 'axios';

const BACKEND_URL = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

class MenuAPIService {
  constructor() {
    this.baseURL = `${BACKEND_URL}/api/menu`;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // API Management Methods
  async getAPIStatus() {
    try {
      const response = await this.client.get('/api-status');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching API status:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch API status'
      };
    }
  }

  async getAPIConfigurations() {
    try {
      const response = await this.client.get('/api-configs');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching API configurations:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch API configurations'
      };
    }
  }

  async updateAPIConfiguration(apiName, configValues) {
    try {
      const response = await this.client.post('/api-config', {
        api_name: apiName,
        config_values: configValues
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error updating API configuration:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to update API configuration'
      };
    }
  }

  async getAPIDocumentation(apiName) {
    try {
      const response = await this.client.get(`/api-docs/${apiName}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching API documentation:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch API documentation'
      };
    }
  }

  // User Profile Methods
  async getUserProfile(userId = null) {
    try {
      const params = userId ? { user_id: userId } : {};
      const response = await this.client.get('/user-profile', { params });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching user profile:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch user profile'
      };
    }
  }

  async updateUserProfile(profileData, userId = null) {
    try {
      const params = userId ? { user_id: userId } : {};
      const response = await this.client.put('/user-profile', profileData, { params });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error updating user profile:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to update user profile'
      };
    }
  }

  async getUserStatistics(userId = null) {
    try {
      const params = userId ? { user_id: userId } : {};
      const response = await this.client.get('/user-stats', { params });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching user statistics:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch user statistics'
      };
    }
  }

  // Application Statistics
  async getAppStatistics() {
    try {
      const response = await this.client.get('/app-statistics');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching app statistics:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch app statistics'
      };
    }
  }
}

// Export singleton instance
export const menuAPI = new MenuAPIService();
export default menuAPI;