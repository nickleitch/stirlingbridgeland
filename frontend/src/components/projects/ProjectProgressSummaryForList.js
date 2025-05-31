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
  const radius = 20;
  const stroke = 3;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDasharray = `${circumference} ${circumference}`;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  const segments = [];
  const segmentCount = 8;
  const segmentAngle = 360 / segmentCount;
  const gapAngle = 4; // Degrees
  
  for (let i = 0; i < segmentCount; i++) {
    const startAngle = i * segmentAngle;
    const endAngle = startAngle + segmentAngle - gapAngle;
    const progress = Math.max(0, Math.min(1, (percentage - i * (100 / segmentCount)) / (100 / segmentCount)));
    
    if (progress > 0) {
      const actualEndAngle = startAngle + (endAngle - startAngle) * progress;
      
      const x1 = 50 + 40 * Math.cos((startAngle - 90) * Math.PI / 180);
      const y1 = 50 + 40 * Math.sin((startAngle - 90) * Math.PI / 180);
      const x2 = 50 + 40 * Math.cos((actualEndAngle - 90) * Math.PI / 180);
      const y2 = 50 + 40 * Math.sin((actualEndAngle - 90) * Math.PI / 180);
      
      const largeArcFlag = actualEndAngle - startAngle <= 180 ? "0" : "1";
      
      const pathData = [
        "M", 50, 50,
        "L", x1, y1,
        "A", 40, 40, 0, largeArcFlag, 1, x2, y2,
        "Z"
      ].join(" ");
      
      segments.push(
        <path
          key={i}
          d={pathData}
          fill="#4a9b9e"
          fillOpacity={0.8}
        />
      );
    }
  }

  const viewBox = "0 0 100 100";
  
  const containerSizeClass = {
    small: "w-12 h-12",
    default: "w-16 h-16",
    responsive: "w-12 h-12 xl:w-16 xl:h-16"
  };
  
  const textSizeClass = {
    small: "text-[8px]",
    default: "text-[10px]",
    responsive: "text-[8px] xl:text-[10px]"
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
  const { deleteProject } = useProject();
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
        // The project will be automatically removed from the list by the ProjectContext
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
    if (!project) return [];
    
    const projectData = project.data || [];
    const layerSectionCounts = {};
    
    // Count boundaries by layer section
    Object.keys(LAYER_SECTIONS).forEach(sectionName => {
      layerSectionCounts[sectionName] = 0;
    });
    
    projectData.forEach(boundary => {
      const layerType = boundary.layer_type;
      
      // Find which section this layer type belongs to
      for (const [sectionName, sectionInfo] of Object.entries(LAYER_SECTIONS)) {
        const layerIds = sectionInfo.layers.map(layer => layer.id);
        const layerTypes = sectionInfo.layers.map(layer => layer.type);
        
        if (layerTypes.includes(layerType)) {
          layerSectionCounts[sectionName]++;
          break;
        }
      }
    });
    
    // Calculate progress for each section
    return Object.entries(LAYER_SECTIONS).map(([sectionName, sectionInfo]) => {
      const count = layerSectionCounts[sectionName];
      const totalPossibleLayers = sectionInfo.layers.length;
      const percentage = totalPossibleLayers > 0 ? Math.round((Math.min(count, totalPossibleLayers) / totalPossibleLayers) * 100) : 0;
      
      return {
        name: sectionName,
        count,
        totalPossibleLayers,
        percentage,
        color: sectionInfo.color
      };
    });
  }, [project]);

  const handleProjectClick = () => {
    if (onSelect) {
      onSelect(project);
    }
  };

  const handleStepClick = (step) => {
    console.log(`Clicked on step: ${step.name}`);
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

          {/* Actions and Info */}
          <div className="flex-shrink-0 ml-4">
            <div className="flex items-center space-x-3">
              <button
                onClick={handleDelete}
                className="text-red-600 hover:text-red-800 focus:outline-none p-1 rounded hover:bg-red-50"
                disabled={isDeleting}
                title="Delete Project"
              >
                {isDeleting ? (
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                )}
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

        {/* Mobile Layout */}
        <div className="lg:hidden">
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <div className="text-lg font-bold text-slate-800">
                {project.name}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Created: {new Date(project.created).toLocaleDateString()}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={handleDelete}
                className="text-red-600 hover:text-red-800 focus:outline-none p-1 rounded hover:bg-red-50"
                disabled={isDeleting}
                title="Delete Project"
              >
                {isDeleting ? (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                )}
              </button>
              <div className="text-center">
                <div className="text-sm font-medium text-gray-900">
                  {project.data ? project.data.length : 0}
                </div>
                <div className="text-xs text-gray-500">Data</div>
              </div>
              <div className="text-xs text-gray-500">
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
    </>
  );
});

ProjectProgressSummaryForList.displayName = 'ProjectProgressSummaryForList';

export default ProjectProgressSummaryForList;