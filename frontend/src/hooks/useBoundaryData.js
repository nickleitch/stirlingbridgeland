import { useMemo, useCallback } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { LAYER_TYPE_MAPPING, getLayerIdForBoundaryType } from '../config/layerConfig';

/**
 * Custom hook for managing boundary data and layer mapping
 */
export const useBoundaryData = () => {
  const { currentProject } = useProject();

  // Helper function to check if a point is inside a polygon (ray casting algorithm)
  const isPointInPolygon = useCallback((point, polygon) => {
    const [x, y] = point;
    let inside = false;
    
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const [xi, yi] = polygon[i];
      const [xj, yj] = polygon[j];
      
      if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
        inside = !inside;
      }
    }
    
    return inside;
  }, []);

  // Helper function to check if coordinates are inside a boundary
  const isCoordinateInBoundary = useCallback((latitude, longitude, boundary) => {
    if (!boundary.geometry || !boundary.geometry.rings || boundary.geometry.rings.length === 0) {
      return false;
    }
    
    // Check the outer ring (first ring is usually the outer boundary)
    const outerRing = boundary.geometry.rings[0];
    if (!outerRing || outerRing.length < 3) return false;
    
    // Convert to [lat, lng] format and check if point is inside
    const polygonPoints = outerRing.map(coord => [coord[1], coord[0]]); // Convert [lng, lat] to [lat, lng]
    return isPointInPolygon([latitude, longitude], polygonPoints);
  }, [isPointInPolygon]);

  // Filter boundaries to show only relevant ones for the search coordinates
  const getRelevantBoundaries = useCallback((boundaries, searchLat, searchLng) => {
    if (!boundaries || boundaries.length === 0) return [];
    
    // First, find boundaries that contain the search point
    const containingBoundaries = boundaries.filter(boundary => 
      isCoordinateInBoundary(searchLat, searchLng, boundary)
    );
    
    // If we found boundaries containing the point, return only those
    if (containingBoundaries.length > 0) {
      console.log(`Found ${containingBoundaries.length} boundaries containing search point:`, 
        containingBoundaries.map(b => `${b.layer_type}: ${b.layer_name}`));
      return containingBoundaries;
    }
    
    // If no boundaries contain the point, find the closest one(s)
    console.log('No boundaries contain search point, finding closest boundaries');
    
    // Calculate distance from search point to each boundary's centroid
    const boundariesWithDistance = boundaries.map(boundary => {
      if (!boundary.geometry || !boundary.geometry.rings || boundary.geometry.rings.length === 0) {
        return { ...boundary, distance: Infinity };
      }
      
      const ring = boundary.geometry.rings[0];
      if (!ring || ring.length === 0) return { ...boundary, distance: Infinity };
      
      // Calculate centroid of the boundary
      let centroidLng = 0, centroidLat = 0;
      ring.forEach(coord => {
        centroidLng += coord[0];
        centroidLat += coord[1];
      });
      centroidLng /= ring.length;
      centroidLat /= ring.length;
      
      // Calculate distance (simple Euclidean distance for small areas)
      const distance = Math.sqrt(
        Math.pow(searchLat - centroidLat, 2) + Math.pow(searchLng - centroidLng, 2)
      );
      
      return { ...boundary, distance };
    });
    
    // Sort by distance and return the closest boundary
    const sortedBoundaries = boundariesWithDistance
      .filter(b => b.distance !== Infinity)
      .sort((a, b) => a.distance - b.distance);
    
    const closestBoundary = sortedBoundaries.length > 0 ? [sortedBoundaries[0]] : [];
    
    if (closestBoundary.length > 0) {
      console.log(`Selected closest boundary: ${closestBoundary[0].layer_type}: ${closestBoundary[0].layer_name}`);
    }
    
    return closestBoundary;
  }, [isCoordinateInBoundary]);

  // Get available boundaries for a specific layer type
  const getBoundariesForLayer = useCallback((layerId, boundaries = null) => {
    const projectBoundaries = boundaries || currentProject?.data || [];
    if (!projectBoundaries.length || !currentProject) return [];
    
    // For Base Data layers, show all available boundaries (less restrictive filtering)
    const isBaseDataLayer = [
      'property_boundaries', 'zoning_designations', 'roads_existing', 
      'topography_basic', 'water_bodies', 'labels_primary', 'survey_control',
      'coordinate_grid', 'contours_major', 'spot_levels', 'elevation_data',
      'generated_contours'
    ].includes(layerId);
    
    let boundariesToFilter = projectBoundaries;
    
    // Only apply restrictive filtering for non-base data layers
    if (!isBaseDataLayer) {
      boundariesToFilter = getRelevantBoundaries(
        projectBoundaries, 
        currentProject.coordinates.latitude, 
        currentProject.coordinates.longitude
      );
    }
    
    console.log(`Layer ${layerId} (Base Data: ${isBaseDataLayer}): Filtering ${projectBoundaries.length} total boundaries to ${boundariesToFilter.length} boundaries`);
    
    // Map layer IDs to boundary types
    switch(layerId) {
      case 'property_boundaries':
        return boundariesToFilter.filter(boundary => 
          ['Farm Portions', 'Erven', 'Holdings', 'Public Places'].includes(boundary.layer_type)
        );
      case 'roads_existing':
        return boundariesToFilter.filter(boundary => boundary.layer_type === 'Roads');
      case 'topography_basic':
      case 'contours_major':
        return boundariesToFilter.filter(boundary => boundary.layer_type === 'Contours');
      case 'generated_contours':
        return boundariesToFilter.filter(boundary => boundary.layer_type === 'Generated Contours');
      case 'elevation_data':
        return boundariesToFilter.filter(boundary => boundary.layer_type === 'Elevation Data');
      case 'water_bodies':
        return boundariesToFilter.filter(boundary => boundary.layer_type === 'Water Bodies');
      case 'environmental_constraints':
        return boundariesToFilter.filter(boundary => boundary.layer_type === 'Environmental Constraints');
      default:
        // For other layers, use the layer type mapping
        const layerType = Object.keys(LAYER_TYPE_MAPPING).find(type => {
          const mapping = LAYER_TYPE_MAPPING[type];
          return Array.isArray(mapping) ? mapping.includes(layerId) : mapping === layerId;
        });
        
        if (layerType) {
          return boundariesToFilter.filter(boundary => boundary.layer_type === layerType);
        }
        return [];
    }
  }, [currentProject, getRelevantBoundaries]);

  // Convert geometry to Leaflet format
  const convertGeometryToLeaflet = useCallback((geometry) => {
    if (!geometry) return [];
    
    // Handle polygons (rings)
    if (geometry.rings) {
      return geometry.rings.map(ring => 
        ring.map(coord => [coord[1], coord[0]])
      );
    }
    
    // Handle polylines (paths) - for contours, roads, etc.
    if (geometry.paths) {
      return geometry.paths.map(path => 
        path.map(coord => [coord[1], coord[0]])
      );
    }
    
    return [];
  }, []);

  // Get all relevant boundaries for the current project
  const relevantBoundaries = useMemo(() => {
    if (!currentProject?.data || !currentProject.coordinates) return [];
    
    return getRelevantBoundaries(
      currentProject.data,
      currentProject.coordinates.latitude,
      currentProject.coordinates.longitude
    );
  }, [currentProject, getRelevantBoundaries]);

  return {
    // Data
    relevantBoundaries,
    
    // Functions
    getBoundariesForLayer,
    convertGeometryToLeaflet,
    getRelevantBoundaries,
    isCoordinateInBoundary,
    isPointInPolygon
  };
};

export default useBoundaryData;