/**
 * Project API Service
 * Centralized API calls for project management operations
 */

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

class ProjectAPIService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async makeRequest(endpoint, options = {}) {
    try {
      const url = `${this.baseURL}/api${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        return { success: true, data };
      } else {
        // Handle non-JSON responses (like file downloads)
        return { success: true, response };
      }
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      return { success: false, error: error.message };
    }
  }

  async healthCheck() {
    return this.makeRequest('/api/health');
  }

  async getBoundaryTypes() {
    return this.makeRequest('/api/boundary-types');
  }

  async createProject(projectData) {
    return this.makeRequest('/api/identify-land', {
      method: 'POST',
      body: JSON.stringify({
        project_name: projectData.name,
        latitude: projectData.latitude,
        longitude: projectData.longitude
      })
    });
  }

  async loadProjectData(project) {
    return this.makeRequest('/api/identify-land', {
      method: 'POST',
      body: JSON.stringify({
        project_name: project.name,
        latitude: project.coordinates.latitude,
        longitude: project.coordinates.longitude
      })
    });
  }

  async getProject(projectId) {
    return this.makeRequest(`/api/project/${projectId}`);
  }

  async listProjects(limit = 100, skip = 0, search = null) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      skip: skip.toString()
    });
    
    if (search) {
      params.append('search', search);
    }

    return this.makeRequest(`/api/projects?${params.toString()}`);
  }

  async downloadCADFiles(projectId) {
    try {
      const url = `${this.baseURL}/api/download-files/${projectId}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return { success: true, response };
    } catch (error) {
      console.error(`Error downloading CAD files:`, error);
      return { success: false, error: error.message };
    }
  }

  async deleteProject(projectId) {
    return this.makeRequest(`/api/projects/${projectId}`, {
      method: 'DELETE'
    });
  }

  async getStatistics() {
    return this.makeRequest('/api/statistics');
  }

  // Validation helpers
  validateCoordinates(latitude, longitude) {
    if (isNaN(latitude) || isNaN(longitude)) {
      return { valid: false, error: 'Please enter valid numbers for coordinates' };
    }
    
    if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
      return { 
        valid: false, 
        error: 'Please enter valid coordinate ranges:\nLatitude: -90 to 90\nLongitude: -180 to 180' 
      };
    }
    
    // Check if coordinates are in South Africa (rough bounds)
    if (latitude < -35 || latitude > -22 || longitude < 16 || longitude > 33) {
      return { 
        valid: false, 
        error: 'These coordinates appear to be outside South Africa. Continue anyway?',
        warning: true
      };
    }
    
    return { valid: true };
  }
}

export const projectAPI = new ProjectAPIService();
export default projectAPI;