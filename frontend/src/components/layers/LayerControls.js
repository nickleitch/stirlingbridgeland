import React, { memo } from 'react';
import { useProject } from '../../contexts/ProjectContext';
import { useLayer } from '../../contexts/LayerContext';
import { projectAPI } from '../../services/projectAPI';

const LayerControls = memo(({ 
  layerId, 
  layerName, 
  hasData, 
  isRefreshing, 
  isDownloading 
}) => {
  const { currentProject, loadProjectData } = useProject();
  const { setLayerRefreshing, setLayerDownloading } = useLayer();

  const handleLayerRefresh = async () => {
    if (!currentProject) return;
    
    setLayerRefreshing(layerId, true);
    
    try {
      console.log(`🔄 Refreshing layer: ${layerId} for project:`, currentProject.name);
      
      const result = await loadProjectData(currentProject);
      
      if (result.success) {
        console.log(`✅ Layer ${layerId} refreshed successfully`);
      } else {
        console.error(`❌ Error refreshing layer ${layerId}:`, result.error);
        alert(`Error refreshing layer. Please try again.`);
      }
    } catch (error) {
      console.error(`❌ Error refreshing layer ${layerId}:`, error);
      alert(`Error refreshing layer. Please try again.`);
    } finally {
      setLayerRefreshing(layerId, false);
    }
  };

  const handleLayerCADDownload = async () => {
    if (!currentProject) return;
    
    setLayerDownloading(layerId, true);
    
    try {
      console.log(`📐 Downloading CAD for layer: ${layerId} from project:`, currentProject.id);
      
      // For now, download the full CAD package
      // TODO: Implement layer-specific CAD downloads in the backend
      const response = await projectAPI.downloadCADFiles(currentProject.id);
      
      if (response.success) {
        const blob = await response.response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        // Create layer-specific filename
        const filename = `${currentProject.name.replace(/\s+/g, '_')}_${layerName.replace(/\s+/g, '_')}.zip`;
        link.download = filename;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        console.log(`✅ CAD file for layer ${layerId} downloaded successfully`);
      } else {
        throw new Error(response.error || 'Download failed');
      }
    } catch (error) {
      console.error(`❌ Error downloading CAD for layer ${layerId}:`, error);
      alert(`Error downloading CAD file for ${layerName}. Please try again.`);
    } finally {
      setLayerDownloading(layerId, false);
    }
  };

  if (!hasData) return null;

  return (
    <>
      <button
        onClick={handleLayerRefresh}
        disabled={isRefreshing}
        className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-all disabled:opacity-50"
        title={`Refresh ${layerName} data`}
        aria-label={`Refresh ${layerName} data`}
      >
        {isRefreshing ? (
          <div className="animate-spin w-3 h-3 border border-blue-500 border-t-transparent rounded-full"></div>
        ) : (
          <span className="text-xs">🔄</span>
        )}
      </button>
      
      <button
        onClick={handleLayerCADDownload}
        disabled={isDownloading}
        className="p-1 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-all disabled:opacity-50"
        title={`Download ${layerName} CAD file`}
        aria-label={`Download ${layerName} CAD file`}
      >
        {isDownloading ? (
          <div className="animate-spin w-3 h-3 border border-green-500 border-t-transparent rounded-full"></div>
        ) : (
          <span className="text-xs">📐</span>
        )}
      </button>
    </>
  );
});

LayerControls.displayName = 'LayerControls';

export default LayerControls;