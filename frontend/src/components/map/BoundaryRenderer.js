import React, { memo } from 'react';
import { Polygon, Polyline, Popup } from 'react-leaflet';
import { useProject } from '../../contexts/ProjectContext';
import { useLayer } from '../../contexts/LayerContext';
import { useBoundaryData } from '../../hooks/useBoundaryData';
import { getLayerConfig } from '../../config/layerConfig';

const BoundaryRenderer = memo(() => {
  const { currentProject } = useProject();
  const { layerStates } = useLayer();
  const { relevantBoundaries, convertGeometryToLeaflet } = useBoundaryData();

  if (!relevantBoundaries.length || !currentProject) return null;

  console.log(`Rendering ${relevantBoundaries.length} relevant boundaries`);

  return relevantBoundaries.map((boundary, index) => {
    // Determine which layer this boundary belongs to
    let layerId = null;
    
    switch(boundary.layer_type) {
      case 'Farm Portions':
      case 'Erven':
      case 'Holdings':
      case 'Public Places':
        layerId = 'property_boundaries';
        break;
      case 'Roads':
        layerId = 'roads_existing';
        break;
      case 'Contours':
        layerId = layerStates['topography_basic'] ? 'topography_basic' : 
                 layerStates['contours_major'] ? 'contours_major' : null;
        break;
      case 'Water Bodies':
        layerId = 'water_bodies';
        break;
      case 'Environmental Constraints':
        layerId = 'environmental_constraints';
        break;
      default:
        // For other layer types, find in layer configuration
        const allLayers = Object.values(require('../../config/layerConfig').LAYER_SECTIONS)
          .flatMap(section => section.layers);
        const matchingLayer = allLayers.find(layer => layer.type === boundary.layer_type);
        layerId = matchingLayer?.id;
    }

    // Skip if layer is not enabled
    if (!layerId || !layerStates[layerId]) {
      return null;
    }

    const geometryCoords = convertGeometryToLeaflet(boundary.geometry);
    
    // Get color from the layer configuration
    let color = "#000000";
    if (layerId === 'property_boundaries') {
      color = "#FF4500"; // Orange red for property boundaries
    } else {
      const layerConfig = getLayerConfig(layerId);
      color = layerConfig?.color || "#000000";
    }

    if (geometryCoords.length === 0) return null;

    // Determine if this is a polygon or polyline based on geometry and layer type
    const isPolyline = boundary.geometry?.paths || 
                     boundary.layer_type === 'Contours' || 
                     boundary.layer_type === 'Roads';

    const PopupContent = (
      <div>
        <strong>{boundary.layer_name}</strong><br/>
        <em>Type: {boundary.layer_type}</em><br/>
        <small>Source: {boundary.source_api}</small><br/>
        <small style={{color: '#22c55e'}}>✓ Contains search coordinates</small>
      </div>
    );

    if (isPolyline) {
      // Render as polyline (for contours, roads, etc.)
      return geometryCoords.map((path, pathIndex) => (
        <Polyline
          key={`boundary-${index}-${pathIndex}`}
          positions={path}
          pathOptions={{
            color: color,
            weight: 3,
            opacity: 0.9
          }}
        >
          <Popup>{PopupContent}</Popup>
        </Polyline>
      ));
    } else {
      // Render as polygon (for property boundaries, etc.)
      return (
        <Polygon
          key={`boundary-${index}`}
          positions={geometryCoords}
          pathOptions={{
            color: color,
            weight: 3,
            opacity: 0.9,
            fillColor: color,
            fillOpacity: 0.3
          }}
        >
          <Popup>{PopupContent}</Popup>
        </Polygon>
      );
    }
  }).filter(Boolean); // Remove null entries
});

BoundaryRenderer.displayName = 'BoundaryRenderer';

export default BoundaryRenderer;