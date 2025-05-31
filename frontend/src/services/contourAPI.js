/**
 * Contour Generation API Service
 * Handles frontend communication with the contour generation backend
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

console.log('ContourAPI initialized with backend URL:', BACKEND_URL);

// Helper function to construct API URLs
const constructApiUrl = (endpoint) => {
  const url = BACKEND_URL.endsWith('/api') 
    ? `${BACKEND_URL}${endpoint}`
    : `${BACKEND_URL}/api${endpoint}`;
  return url;
};

export const contourAPI = {
  /**
   * Generate contour lines for a specified area
   */
  generateContours: async (params) => {
    try {
      const { 
        latitude, 
        longitude, 
        contour_interval = 10.0,  // 10m intervals (safer default)
        grid_size_km = 2.0,    // 2km grid (more focused)
        grid_points = 9,      // 9x9 grid (81 points, under 100 limit)
        dataset = "srtm30m",
        property_boundaries = []  // Property boundaries for filtering
      } = params;

      if (!latitude || !longitude) {
        throw new Error('Latitude and longitude are required');
      }

      const requestBody = {
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        contour_interval: parseFloat(contour_interval),
        grid_size_km: parseFloat(grid_size_km),
        grid_points: parseInt(grid_points),
        dataset: dataset,
        property_boundaries: property_boundaries
      };

      console.log('Generating contours with params:', requestBody);

      const apiUrl = constructApiUrl('/contours/generate');
      console.log('Making contour API request to:', apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        mode: 'cors',
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP error! status: ${response.status}`);
      }

      return {
        success: true,
        data: data.contour_data,
        message: data.message,
        timestamp: data.timestamp
      };

    } catch (error) {
      console.error('Contour generation failed:', error);
      return {
        success: false,
        error: error.message || 'Failed to generate contours'
      };
    }
  },

  /**
   * Get available contour styling options
   */
  getContourStyles: async () => {
    try {
      const apiUrl = constructApiUrl('/contours/styles');
      console.log('Getting contour styles from:', apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        mode: 'cors'
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP error! status: ${response.status}`);
      }

      return {
        success: true,
        data: data,
        timestamp: data.timestamp
      };

    } catch (error) {
      console.error('Failed to get contour styles:', error);
      return {
        success: false,
        error: error.message || 'Failed to get contour styles'
      };
    }
  },

  /**
   * Get available elevation datasets
   */
  getElevationDatasets: async () => {
    try {
      const apiUrl = constructApiUrl('/elevation/datasets');
      console.log('Getting elevation datasets from:', apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        mode: 'cors'
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP error! status: ${response.status}`);
      }

      return {
        success: true,
        data: data,
        timestamp: data.timestamp
      };

    } catch (error) {
      console.error('Failed to get elevation datasets:', error);
      return {
        success: false,
        error: error.message || 'Failed to get elevation datasets'
      };
    }
  },

  /**
   * Convert contour data to map layer format
   */
  convertToMapLayers: (contourData) => {
    try {
      if (!contourData || !contourData.contour_lines) {
        return [];
      }

      const layers = [];
      
      // Group contours by type
      const contourGroups = {
        minor: [],
        major: [],
        index: []
      };

      contourData.contour_lines.forEach(contour => {
        const contourType = contour.properties.contour_type || 'minor';
        if (contourGroups[contourType]) {
          contourGroups[contourType].push(contour);
        }
      });

      // Create layers for each contour type
      Object.entries(contourGroups).forEach(([type, contours]) => {
        if (contours.length > 0) {
          layers.push({
            layer_name: `Contours ${type.charAt(0).toUpperCase() + type.slice(1)}`,
            layer_type: "Generated Contours",
            geometry: {
              type: "FeatureCollection",
              features: contours
            },
            properties: {
              contour_type: type,
              total_contours: contours.length,
              interval: contourData.parameters?.contour_interval || 2.0,
              dataset: contourData.parameters?.dataset || 'srtm30m'
            },
            source_api: "ContourGenerationService",
            contour_data: true,
            style: contours[0]?.properties?.style || {}
          });
        }
      });

      return layers;

    } catch (error) {
      console.error('Failed to convert contour data to map layers:', error);
      return [];
    }
  },

  /**
   * Convert contour data to boundaries format for integration with existing system
   */
  convertToBoundaries: (contourData) => {
    try {
      if (!contourData || !contourData.boundaries) {
        return [];
      }

      return contourData.boundaries.map((boundary, index) => ({
        ...boundary,
        id: `contour_${index}`,
        generated: true,
        timestamp: new Date().toISOString()
      }));

    } catch (error) {
      console.error('Failed to convert contour data to boundaries:', error);
      return [];
    }
  }
};

export default contourAPI;
