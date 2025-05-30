import { useCallback } from 'react';
import { useLayer } from '../contexts/LayerContext';
import { useBoundaryData } from './useBoundaryData';
import { LAYER_TYPE_MAPPING, getLayerIdForBoundaryType } from '../config/layerConfig';

/**
 * Custom hook for managing layer mapping and auto-enabling layers based on data
 */
export const useLayerMapping = () => {
  const { setLayerState, initializeLayers } = useLayer();
  const { getRelevantBoundaries } = useBoundaryData();

  const autoEnableLayersForBoundaries = useCallback((boundaries, coordinates) => {
    if (!boundaries || boundaries.length === 0) return;

    // Get relevant boundaries for the coordinates
    const relevantBoundaries = getRelevantBoundaries(
      boundaries,
      coordinates.latitude,
      coordinates.longitude
    );

    console.log(`Auto-enabling layers for ${relevantBoundaries.length} relevant boundaries`);

    const layerStates = {};

    relevantBoundaries.forEach(boundary => {
      const layerType = boundary.layer_type;
      const layerId = getLayerIdForBoundaryType(layerType);
      
      if (layerId) {
        layerStates[layerId] = true;
        console.log(`✅ Auto-enabled layer: ${layerId} for boundary type: ${layerType}`);
      } else {
        console.log(`❌ No layer mapping found for boundary type: ${layerType}`);
      }
    });

    // Initialize all layers with defaults, then enable the ones with data
    const allLayerStates = {};
    Object.values(require('../config/layerConfig').LAYER_SECTIONS).forEach(section => {
      section.layers.forEach(layer => {
        allLayerStates[layer.id] = layerStates[layer.id] || false;
      });
    });

    initializeLayers(allLayerStates);
  }, [getRelevantBoundaries, initializeLayers]);

  const toggleLayersByBoundaryType = useCallback((boundaryType, enabled) => {
    const layerId = getLayerIdForBoundaryType(boundaryType);
    if (layerId) {
      setLayerState(layerId, enabled);
    }
  }, [setLayerState]);

  const getEnabledLayersForBoundaryTypes = useCallback((boundaryTypes) => {
    const enabledLayers = {};
    
    boundaryTypes.forEach(boundaryType => {
      const layerId = getLayerIdForBoundaryType(boundaryType);
      if (layerId) {
        enabledLayers[layerId] = true;
      }
    });

    return enabledLayers;
  }, []);

  const getBoundaryTypesForLayer = useCallback((layerId) => {
    const boundaryTypes = [];
    
    for (const [boundaryType, mapping] of Object.entries(LAYER_TYPE_MAPPING)) {
      if (Array.isArray(mapping)) {
        if (mapping.includes(layerId)) {
          boundaryTypes.push(boundaryType);
        }
      } else if (mapping === layerId) {
        boundaryTypes.push(boundaryType);
      }
    }

    return boundaryTypes;
  }, []);

  return {
    autoEnableLayersForBoundaries,
    toggleLayersByBoundaryType,
    getEnabledLayersForBoundaryTypes,
    getBoundaryTypesForLayer
  };
};

export default useLayerMapping;