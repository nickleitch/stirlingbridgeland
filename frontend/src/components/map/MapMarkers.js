import React, { memo } from 'react';
import { Marker, Popup } from 'react-leaflet';
import { useProject } from '../../contexts/ProjectContext';

const MapMarkers = memo(() => {
  const { currentProject } = useProject();

  if (!currentProject) return null;

  return (
    <Marker position={[currentProject.coordinates.latitude, currentProject.coordinates.longitude]}>
      <Popup>
        <div className="text-center">
          <strong>{currentProject.name}</strong><br/>
          {currentProject.coordinates.latitude.toFixed(6)}, {currentProject.coordinates.longitude.toFixed(6)}
        </div>
      </Popup>
    </Marker>
  );
});

MapMarkers.displayName = 'MapMarkers';

export default MapMarkers;