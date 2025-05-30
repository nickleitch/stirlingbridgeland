import React, { memo } from 'react';
import LayerControls from './LayerControls';
import { useLayer } from '../../contexts/LayerContext';
import { useBoundaryData } from '../../hooks/useBoundaryData';

const LayerItem = memo(({ layer }) => {
  const { 
    layerStates, 
    toggleLayer, 
    layerRefreshing, 
    layerDownloading 
  } = useLayer();
  
  const { getBoundariesForLayer } = useBoundaryData();
  
  const hasData = getBoundariesForLayer(layer.id).length > 0;
  const isEnabled = layerStates[layer.id];
  const isRefreshing = layerRefreshing[layer.id];
  const isDownloading = layerDownloading[layer.id];

  return (
    <div 
      className={`mx-4 mb-2 p-3 rounded-lg ${hasData ? 'bg-gray-50' : 'bg-gray-25 opacity-60'}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="font-medium text-sm text-gray-900">{layer.name}</div>
          {layer.stage && (
            <div className="text-xs text-gray-500 mt-1">{layer.stage}</div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Layer Controls - Refresh and CAD Download */}
          <LayerControls
            layerId={layer.id}
            layerName={layer.name}
            hasData={hasData}
            isRefreshing={isRefreshing}
            isDownloading={isDownloading}
          />
          
          {/* Layer Toggle Switch */}
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={isEnabled}
              onChange={() => toggleLayer(layer.id)}
              disabled={!hasData}
              className="sr-only peer"
              aria-label={`Toggle ${layer.name} layer`}
            />
            <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600 disabled:opacity-50"></div>
          </label>
        </div>
      </div>
      
      {hasData && (
        <div className="mt-2 text-xs text-gray-600">
          {getBoundariesForLayer(layer.id).length} features available
        </div>
      )}
    </div>
  );
});

LayerItem.displayName = 'LayerItem';

export default LayerItem;