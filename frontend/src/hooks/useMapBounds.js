import { useCallback } from 'react';
import { useProject } from '../contexts/ProjectContext';

/**
 * Custom hook for calculating map bounds based on current project
 */
export const useMapBounds = () => {
  const { currentProject } = useProject();

  const getMapBounds = useCallback(() => {
    if (!currentProject) {
      // Default bounds (Johannesburg area)
      return [[-26.2041, 28.0473], [-26.2041, 28.0473]];
    }
    
    const { latitude, longitude } = currentProject.coordinates;
    
    // Create bounds with a small buffer around the coordinates
    const buffer = 0.01; // Approximately 1km at this scale
    
    return [
      [latitude - buffer, longitude - buffer], // Southwest corner
      [latitude + buffer, longitude + buffer]  // Northeast corner
    ];
  }, [currentProject]);

  const getBoundsForBoundaries = useCallback((boundaries) => {
    if (!boundaries || boundaries.length === 0) {
      return getMapBounds();
    }

    let minLat = Infinity;
    let maxLat = -Infinity;
    let minLng = Infinity;
    let maxLng = -Infinity;

    boundaries.forEach(boundary => {
      if (!boundary.geometry) return;

      // Handle polygon boundaries
      if (boundary.geometry.rings) {
        boundary.geometry.rings.forEach(ring => {
          ring.forEach(coord => {
            const [lng, lat] = coord;
            minLat = Math.min(minLat, lat);
            maxLat = Math.max(maxLat, lat);
            minLng = Math.min(minLng, lng);
            maxLng = Math.max(maxLng, lng);
          });
        });
      }

      // Handle polyline boundaries
      if (boundary.geometry.paths) {
        boundary.geometry.paths.forEach(path => {
          path.forEach(coord => {
            const [lng, lat] = coord;
            minLat = Math.min(minLat, lat);
            maxLat = Math.max(maxLat, lat);
            minLng = Math.min(minLng, lng);
            maxLng = Math.max(maxLng, lng);
          });
        });
      }
    });

    // If we couldn't calculate bounds, fall back to default
    if (minLat === Infinity || maxLat === -Infinity || 
        minLng === Infinity || maxLng === -Infinity) {
      return getMapBounds();
    }

    // Add a small buffer around the calculated bounds
    const latBuffer = (maxLat - minLat) * 0.1 || 0.01;
    const lngBuffer = (maxLng - minLng) * 0.1 || 0.01;

    return [
      [minLat - latBuffer, minLng - lngBuffer], // Southwest corner
      [maxLat + latBuffer, maxLng + lngBuffer]  // Northeast corner
    ];
  }, [getMapBounds]);

  const getCenterPoint = useCallback(() => {
    if (!currentProject) {
      return [-26.2041, 28.0473]; // Default center (Johannesburg)
    }
    
    return [currentProject.coordinates.latitude, currentProject.coordinates.longitude];
  }, [currentProject]);

  return {
    getMapBounds,
    getBoundsForBoundaries,
    getCenterPoint
  };
};

export default useMapBounds;