import React, { useState, memo } from 'react';
import { contourAPI } from '../../services/contourAPI';
import { useProject } from '../../contexts/ProjectContext';

const ContourGenerationControls = memo(({ layerId, layerName, onContourGenerated }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Fixed settings for reliability (no user configuration)
  const fixedSettings = {
    contour_interval: 10.0,  // 10m intervals (safer default)
    grid_size_km: 2.0,       // 2km grid (focused coverage)
    grid_points: 12,         // 12x12 grid (reliable)
    dataset: 'srtm30m'       // Recommended dataset
  };

  const { currentProject, updateProject } = useProject();

  const addBoundariesToProject = async (projectId, newBoundaries) => {
    if (!currentProject || currentProject.id !== projectId) {
      console.error('Cannot add boundaries: project not found or not current');
      return;
    }

    // Merge new boundaries with existing ones
    const existingBoundaries = currentProject.data || [];
    const updatedBoundaries = [...existingBoundaries, ...newBoundaries];
    
    // Update the project locally first
    const updatedProject = {
      ...currentProject,
      data: updatedBoundaries,
      last_updated: new Date().toISOString()
    };

    updateProject(updatedProject);
    
    // Save to backend using the new PUT endpoint
    try {
      const backendUrl = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/projects/${projectId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        mode: 'cors',
        body: JSON.stringify({
          data: updatedBoundaries
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to save project: ${response.status}`);
      }

      const result = await response.json();
      console.log(`Successfully saved ${newBoundaries.length} contour boundaries to project ${projectId}`);
      
    } catch (error) {
      console.error('Failed to save contours to backend:', error);
      // Still show success message since contours are displayed locally
      console.warn('Contours are visible locally but may not persist after page reload');
    }
  };

  const handleGenerateContours = async () => {
    if (!currentProject || !currentProject.coordinates) {
      alert('Please select a project first');
      return;
    }

    setIsGenerating(true);
    
    try {
      const params = {
        latitude: currentProject.coordinates.latitude,
        longitude: currentProject.coordinates.longitude,
        ...settings
      };

      console.log('Generating contours for project:', currentProject.name, 'with params:', params);

      const response = await contourAPI.generateContours(params);

      if (response.success) {
        // Convert contour data to boundaries format
        const contourBoundaries = contourAPI.convertToBoundaries(response.data);
        
        if (contourBoundaries.length > 0) {
          // Add contour boundaries to the project
          await addBoundariesToProject(currentProject.id, contourBoundaries);
          
          // Notify parent component
          if (onContourGenerated) {
            onContourGenerated(response.data);
          }

          console.log(`Generated ${contourBoundaries.length} contour boundaries`);
          alert(`Successfully generated ${contourBoundaries.length} contour lines with ${settings.contour_interval}m intervals`);
        } else {
          alert('No contour lines were generated for this area');
        }
      } else {
        throw new Error(response.error);
      }
    } catch (error) {
      console.error('Contour generation failed:', error);
      alert(`Failed to generate contours: ${error.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="relative">
      <div className="flex items-center space-x-1">
        {/* Generate Button */}
        <button
          onClick={() => setShowSettings(true)}
          disabled={isGenerating || !currentProject}
          className="p-1 rounded hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Generate Contours"
          aria-label="Generate elevation contours"
        >
          {isGenerating ? (
            <svg className="w-4 h-4 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle 
                className="opacity-25" 
                cx="12" 
                cy="12" 
                r="10" 
                stroke="currentColor" 
                strokeWidth="4"
              />
              <path 
                className="opacity-75" 
                fill="currentColor" 
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          )}
        </button>

        {/* Settings Button */}
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="p-1 rounded hover:bg-gray-200 transition-colors"
          title="Contour Settings"
          aria-label="Configure contour generation settings"
        >
          <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="absolute top-8 right-0 z-10 bg-white border border-gray-200 rounded-lg shadow-lg p-4 w-80">
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-gray-900">Contour Generation Settings</h4>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Contour Interval (meters)
              </label>
              <select
                value={settings.contour_interval}
                onChange={(e) => setSettings(prev => ({ ...prev, contour_interval: parseFloat(e.target.value) }))}
                className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={0.5}>0.5m (Very Detailed)</option>
                <option value={1.0}>1.0m (Detailed)</option>
                <option value={2.0}>2.0m (Standard)</option>
                <option value={5.0}>5.0m (Overview)</option>
                <option value={10.0}>10.0m (General)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Analysis Area (km)
              </label>
              <select
                value={settings.grid_size_km}
                onChange={(e) => setSettings(prev => ({ ...prev, grid_size_km: parseFloat(e.target.value) }))}
                className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={1.0}>1km x 1km</option>
                <option value={2.0}>2km x 2km</option>
                <option value={3.0}>3km x 3km (Standard)</option>
                <option value={5.0}>5km x 5km</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Resolution
              </label>
              <select
                value={settings.grid_points}
                onChange={(e) => setSettings(prev => ({ ...prev, grid_points: parseInt(e.target.value) }))}
                className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={10}>10x10 (Standard)</option>
                <option value={15}>15x15 (High Quality - May Exceed API Limits)</option>
                <option value={20}>20x20 (Very High Quality - May Exceed API Limits)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Elevation Dataset
              </label>
              <select
                value={settings.dataset}
                onChange={(e) => setSettings(prev => ({ ...prev, dataset: e.target.value }))}
                className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="srtm30m">SRTM 30m (Recommended)</option>
                <option value="srtm90m">SRTM 90m</option>
                <option value="aster30m">ASTER 30m</option>
              </select>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-gray-200">
              <button
                onClick={() => setShowSettings(false)}
                className="px-3 py-1 text-xs text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowSettings(false);
                  handleGenerateContours();
                }}
                disabled={isGenerating || !currentProject}
                className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Generate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

ContourGenerationControls.displayName = 'ContourGenerationControls';

export default ContourGenerationControls;