import React, { memo, useMemo, useState } from 'react';
import { LAYER_SECTIONS } from '../../config/layerConfig';
import { useProject } from '../../contexts/ProjectContext';

const DeleteConfirmationModal = memo(({ isOpen, onClose, onConfirm, projectName }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center mb-4">
          <div className="flex-shrink-0">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.232 15.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="ml-4">
            <h3 className="text-lg font-medium text-gray-900">Delete Project</h3>
            <p className="text-sm text-gray-500 mt-1">
              This action cannot be undone.
            </p>
          </div>
        </div>
        
        <p className="text-gray-700 mb-6">
          Are you sure you want to delete "<strong>{projectName}</strong>"? All project data and boundaries will be permanently removed.
        </p>
        
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            Delete Project
          </button>
        </div>
      </div>
    </div>
  );
});

DeleteConfirmationModal.displayName = 'DeleteConfirmationModal';

const ProgressCircle = memo(({ percentage, title, onClick, size = 'default' }) => {
  const numSegments = 10;
  const filledSegments = Math.round((percentage / 100) * numSegments);
  
  // Responsive sizing based on screen and size prop
  const sizeConfig = {
    small: { radius: 24, centerX: 30, centerY: 30, strokeWidth: 5, viewBox: "0 0 60 60" },
    default: { radius: 36, centerX: 45, centerY: 45, strokeWidth: 8, viewBox: "0 0 90 90" },
    responsive: { radius: 30, centerX: 37.5, centerY: 37.5, strokeWidth: 6, viewBox: "0 0 75 75" }
  };
  
  const config = sizeConfig[size] || sizeConfig.default;
  const { radius, centerX, centerY, strokeWidth, viewBox } = config;
  
  const segmentAngle = 360 / numSegments;
  const gapAngle = 3;

  const segments = [];
  
  for (let i = 0; i < numSegments; i++) {
    const startAngle = i * segmentAngle + gapAngle / 2;
    const endAngle = (i + 1) * segmentAngle - gapAngle / 2;
    
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;
    
    const x1 = centerX + radius * Math.cos(startRad);
    const y1 = centerY + radius * Math.sin(startRad);
    const x2 = centerX + radius * Math.cos(endRad);
    const y2 = centerY + radius * Math.sin(endRad);
    
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
    const pathData = `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;
    
    const isFilled = i < filledSegments;
    
    segments.push(
      <path
        key={i}
        className={`segment ${isFilled ? 'filled-segment' : 'bg-segment'}`}
        d={pathData}
        fill="none"
        strokeWidth={strokeWidth}
        strokeLinecap="butt"
        stroke={isFilled ? '#4a9b9e' : '#d4d4d8'}
      />
    );
  }

  const containerSizeClass = {
    small: "w-[60px] h-[60px]",
    default: "w-[90px] h-[90px]",
    responsive: "w-[75px] h-[75px] xl:w-[90px] xl:h-[90px]"
  };

  const textSizeClass = {
    small: "text-lg",
    default: "text-2xl",
    responsive: "text-xl xl:text-2xl"
  };

  const titleSizeClass = {
    small: "text-[10px]",
    default: "text-xs",
    responsive: "text-[10px] xl:text-xs"
  };

  return (
    <div 
      className="step cursor-pointer transition-all duration-200 hover:-translate-y-0.5 text-center flex-1 min-w-0"
      onClick={onClick}
    >
      <div className={`progress-circle relative ${containerSizeClass[size]} mx-auto mb-2`}>
        <svg 
          viewBox={viewBox}
          className="w-full h-full transform -rotate-90"
        >
          {segments}
        </svg>
        <div className={`progress-percentage absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 ${textSizeClass[size]} font-bold text-[#4a9b9e]`}>
          {percentage}%
        </div>
      </div>
      <div className={`step-title ${titleSizeClass[size]} font-semibold text-slate-600 whitespace-nowrap overflow-hidden text-ellipsis`}>
        {title}
      </div>
    </div>
  );
});

ProgressCircle.displayName = 'ProgressCircle';

const ProjectProgressSummaryForList = memo(({ project, onSelect }) => {
  const { deleteProject, loading } = useProject();
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (e) => {
    e.stopPropagation(); // Prevent project selection
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    setIsDeleting(true);
    try {
      const result = await deleteProject(project.id);
      if (result.success) {
        console.log(`Project "${project.name}" deleted successfully`);
      } else {
        alert(`Failed to delete project: ${result.error}`);
      }
    } catch (error) {
      console.error('Error deleting project:', error);
      alert(`Error deleting project: ${error.message}`);
    } finally {
      setIsDeleting(false);
      setShowDeleteModal(false);
    }
  };

  // Calculate progress based on available data for this project
  const sectionProgress = useMemo(() => {
    const availableBoundaryTypes = new Set();
    
    // Get boundary types available in this project's data
    if (project.data && Array.isArray(project.data)) {
      project.data.forEach(boundary => {
        if (boundary.layer_type) {
          availableBoundaryTypes.add(boundary.layer_type);
        }
      });
    }

    return Object.entries(LAYER_SECTIONS).map(([sectionName, section]) => {
      const totalLayers = section.layers.length;
      
      // For projects list, show progress based on available data
      let availableLayers = 0;
      
      section.layers.forEach(layer => {
        // Check if this layer type has data available
        switch(layer.type) {
          case 'Farm Portions':
          case 'Erven':  
          case 'Holdings':
          case 'Public Places':
            if (availableBoundaryTypes.has('Farm Portions') || 
                availableBoundaryTypes.has('Erven') ||
                availableBoundaryTypes.has('Holdings') ||
                availableBoundaryTypes.has('Public Places')) {
              availableLayers++;
            }
            break;
          case 'Roads':
            if (availableBoundaryTypes.has('Roads')) {
              availableLayers++;
            }
            break;
          case 'Contours':
            if (availableBoundaryTypes.has('Contours')) {
              availableLayers++;
            }
            break;
          case 'Water Bodies':
            if (availableBoundaryTypes.has('Water Bodies')) {
              availableLayers++;
            }
            break;
          case 'Environmental Constraints':
            if (availableBoundaryTypes.has('Environmental Constraints')) {
              availableLayers++;
            }
            break;
          default:
            // For other layer types, show as partially available
            if (availableBoundaryTypes.size > 0) {
              availableLayers += 0.3; // Partial credit
            }
        }
      });
      
      const percentage = totalLayers > 0 ? Math.round((availableLayers / totalLayers) * 100) : 0;
      
      return {
        name: sectionName,
        percentage: Math.min(percentage, 100), // Cap at 100%
        availableLayers: Math.round(availableLayers),
        totalLayers
      };
    });
  }, [project]);

  const handleStepClick = (stepData) => {
    console.log(`Project "${project.name}" - ${stepData.name}: ${stepData.percentage}% (${stepData.availableLayers}/${stepData.totalLayers} layers have data)`);
  };

  const handleProjectClick = () => {
    onSelect(project);
  };

  if (!project) return null;

  return (
    <>
      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={confirmDelete}
        projectName={project.name}
      />
      <div 
      className="bg-white rounded-xl shadow-lg p-6 mb-6 cursor-pointer hover:shadow-xl transition-all transform hover:scale-[1.01] border border-gray-100"
      onClick={handleProjectClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleProjectClick();
        }
      }}
      aria-label={`Open project ${project.name}`}
    >
      {/* Desktop Layout */}
      <div className="hidden lg:flex items-center gap-6">
        {/* Project Info */}
        <div className="min-w-[220px] flex-shrink-0">
          <div className="text-xl font-bold text-slate-800">
            {project.name}
          </div>
          <div className="text-sm text-slate-600 mt-1">
            Layer Progress Summary
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {project.data ? project.data.length : 0} boundaries available
          </div>
          <div className="text-xs text-gray-500 mt-2">
            📍 {project.coordinates.latitude.toFixed(4)}, {project.coordinates.longitude.toFixed(4)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Created: {new Date(project.created).toLocaleDateString()}
          </div>
        </div>

        {/* Steps Progress - Responsive sizing */}
        <div className="flex-1 flex items-center justify-between gap-2 xl:gap-4 min-w-0">
          {sectionProgress.map((step, index) => (
            <ProgressCircle
              key={step.name}
              percentage={step.percentage}
              title={step.name}
              onClick={(e) => {
                e.stopPropagation();
                handleStepClick(step);
              }}
              size="responsive"
            />
          ))}
        </div>

        {/* Click Arrow */}
        <div className="flex-shrink-0 ml-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleDelete}
              className="text-red-600 hover:text-red-800 focus:outline-none"
              disabled={isDeleting}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
            <div className="text-center">
              <div className="text-sm font-medium text-gray-900">
                {project.data ? project.data.length : 0}
              </div>
              <div className="text-xs text-gray-500">Boundaries</div>
            </div>
            
            <div className="w-6 h-6 text-gray-400">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile/Tablet Layout */}
      <div className="block lg:hidden">
        <div className="flex items-center justify-between mb-4">
          <div className="flex-1">
            <div className="text-lg font-bold text-slate-800">
              {project.name}
            </div>
            <div className="text-sm text-slate-600 mt-1">
              {project.data ? project.data.length : 0} boundaries • Layer Progress Summary
            </div>
            <div className="text-xs text-gray-500 mt-1">
              📍 {project.coordinates.latitude.toFixed(4)}, {project.coordinates.longitude.toFixed(4)}
            </div>
          </div>
          
          <div className="w-6 h-6 text-gray-400 ml-4">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
        
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {sectionProgress.map((step, index) => (
            <ProgressCircle
              key={step.name}
              percentage={step.percentage}
              title={step.name}
              onClick={(e) => {
                e.stopPropagation();
                handleStepClick(step);
              }}
              size="small"
            />
          ))}
        </div>
      </div>
    </div>
  );
});

ProjectProgressSummaryForList.displayName = 'ProjectProgressSummaryForList';

export default ProjectProgressSummaryForList;