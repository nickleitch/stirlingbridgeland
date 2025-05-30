import React, { memo } from 'react';

const ProjectCard = memo(({ project, onSelect }) => {
  const handleClick = () => {
    onSelect(project);
  };

  return (
    <div
      onClick={handleClick}
      className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all cursor-pointer transform hover:scale-[1.02] border border-gray-100"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
      aria-label={`Open project ${project.name}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-4">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl font-bold">
                  {project.name.charAt(0).toUpperCase()}
                </span>
              </div>
            </div>
            
            <div className="flex-1 min-w-0">
              <h3 className="text-xl font-semibold text-gray-900 truncate">
                {project.name}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                📍 {project.coordinates.latitude.toFixed(4)}, {project.coordinates.longitude.toFixed(4)}
              </p>
              <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                <span>Created: {new Date(project.created).toLocaleDateString()}</span>
                <span>•</span>
                <span>Modified: {new Date(project.lastModified).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex-shrink-0 ml-4">
          <div className="flex items-center space-x-3">
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
    </div>
  );
});

ProjectCard.displayName = 'ProjectCard';

export default ProjectCard;