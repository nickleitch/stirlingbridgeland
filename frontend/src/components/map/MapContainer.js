import React, { memo, useRef } from 'react';
import { MapContainer as LeafletMapContainer, TileLayer } from 'react-leaflet';
import MapMarkers from './MapMarkers';
import BoundaryRenderer from './BoundaryRenderer';
import { useMapBounds } from '../../hooks/useMapBounds';
import { useProject } from '../../contexts/ProjectContext';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

const MapContainer = memo(() => {
  const mapRef = useRef();
  const { currentProject, loading, error } = useProject();
  const { getMapBounds } = useMapBounds();

  if (!currentProject) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="text-gray-400 text-6xl mb-4">🗺️</div>
          <h3 className="text-xl font-semibold text-gray-600">No Project Selected</h3>
          <p className="text-gray-500">Select a project to view the map</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 relative">
      {loading && (
        <LoadingSpinner
          overlay={true}
          message="Loading project data..."
          size="large"
        />
      )}

      {error && (
        <ErrorMessage
          error={error}
          className="absolute top-4 left-4 right-4 z-40"
        />
      )}

      <LeafletMapContainer
        bounds={getMapBounds()}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
      >
        {/* Satellite Imagery Base Layer */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution='Tiles &copy; Esri'
          maxZoom={19}
        />
        
        {/* Street overlay for reference */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}"
          attribution=''
          opacity={0.3}
          maxZoom={19}
        />

        {/* Map Markers */}
        <MapMarkers />

        {/* Boundary Renderer */}
        <BoundaryRenderer />
      </LeafletMapContainer>
    </div>
  );
});

MapContainer.displayName = 'MapContainer';

export default MapContainer;