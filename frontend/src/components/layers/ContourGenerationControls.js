import React, { useState, memo } from 'react';
import { contourAPI } from '../../services/contourAPI';
import { useProject } from '../../contexts/ProjectContext';

const ContourGenerationControls = memo(({ layerId, layerName, onContourGenerated }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    contour_interval: 10.0,  // 10m intervals (safer default)
    grid_size_km: 2.0,       // 2km grid (focused coverage)
    grid_points: 12,         // 12x12 grid (reliable)
    dataset: 'srtm30m'       // Recommended dataset
  });

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
      // Get property boundaries from current project (only Farm Portions and Erven)
      const propertyBoundaries = (currentProject.data || []).filter(boundary => 
        boundary.layer_type === 'Farm Portions' || boundary.layer_type === 'Erven'
      );

      const params = {
        latitude: currentProject.coordinates.latitude,
        longitude: currentProject.coordinates.longitude,
        property_boundaries: propertyBoundaries,  // Pass boundaries for filtering
        ...settings
      };

      console.log('Generating contours for project:', currentProject.name, 'with params:', params);
      console.log(`Using ${propertyBoundaries.length} property boundaries for filtering`);

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
          alert(`Successfully generated ${contourBoundaries.length} contour lines with ${settings.contour_interval}m intervals (filtered to property boundaries)`);
        } else {
          alert('No contour lines were generated within the property boundaries');
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
        {/* Generate Button - Simplified (no settings) */}
        <button
          onClick={handleGenerateContours}
          disabled={isGenerating || !currentProject}
          className="p-1 rounded hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Generate 10m Contours (within property boundaries)"
          aria-label="Generate elevation contours filtered to property boundaries"
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

        {/* Info text */}
        <span className="text-xs text-gray-500">
          10m intervals
        </span>
      </div>
    </div>
  );
});

ContourGenerationControls.displayName = 'ContourGenerationControls';

export default ContourGenerationControls;