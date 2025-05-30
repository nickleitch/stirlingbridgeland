import React, { memo, useMemo } from 'react';
import { LAYER_SECTIONS } from '../../config/layerConfig';

const ProgressCircle = memo(({ percentage, title, onClick }) => {
  const numSegments = 10;
  const filledSegments = Math.round((percentage / 100) * numSegments);
  const radius = 36;
  const centerX = 45;
  const centerY = 45;
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
        strokeWidth="8"
        strokeLinecap="butt"
        stroke={isFilled ? '#4a9b9e' : '#d4d4d8'}
      />
    );
  }

  return (
    <div 
      className="step cursor-pointer transition-all duration-200 hover:-translate-y-0.5 text-center flex-1"
      onClick={onClick}
    >
      <div className="progress-circle relative w-[90px] h-[90px] mx-auto mb-2">
        <svg 
          viewBox="0 0 90 90" 
          className="w-full h-full transform -rotate-90"
        >
          {segments}
        </svg>
        <div className="progress-percentage absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-2xl font-bold text-[#4a9b9e]">
          {percentage}%
        </div>
      </div>
      <div className="step-title text-xs font-semibold text-slate-600 whitespace-nowrap">
        {title}
      </div>
    </div>
  );
});

ProgressCircle.displayName = 'ProgressCircle';

const ProjectProgressSummaryForList = memo(({ project }) => {
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
      // This is a simplified calculation - in a real app you might want to store this in the project data
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

  if (!project) return null;

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 mb-4">
      <div className="flex items-center gap-6">
        {/* Project Info */}
        <div className="min-w-[200px]">
          <div className="text-xl font-bold text-slate-800">
            {project.name}
          </div>
          <div className="text-sm text-slate-600 mt-1">
            Layer Progress Summary
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {project.data ? project.data.length : 0} boundaries available
          </div>
        </div>

        {/* Steps Progress */}
        <div className="flex-1 flex items-center justify-between gap-4">
          {sectionProgress.map((step, index) => (
            <ProgressCircle
              key={step.name}
              percentage={step.percentage}
              title={step.name}
              onClick={() => handleStepClick(step)}
            />
          ))}
        </div>
      </div>

      {/* Responsive Layout for smaller screens */}
      <div className="block lg:hidden mt-6">
        <div className="text-center mb-4">
          <div className="text-xl font-bold text-slate-800">
            {project.name}
          </div>
          <div className="text-sm text-slate-600 mt-1">
            Layer Progress Summary
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {project.data ? project.data.length : 0} boundaries available
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {sectionProgress.map((step, index) => (
            <div key={step.name} className="flex flex-col items-center">
              <ProgressCircle
                percentage={step.percentage}
                title={step.name}
                onClick={() => handleStepClick(step)}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

ProjectProgressSummaryForList.displayName = 'ProjectProgressSummaryForList';

export default ProjectProgressSummaryForList;