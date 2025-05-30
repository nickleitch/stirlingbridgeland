import React, { memo } from 'react';

const ProjectCard = memo(({ project, onSelect }) => {
  const handleClick = () => {
    onSelect(project);
  };

  return (
    <div
      onClick={handleClick}
      className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all cursor-pointer transform hover:scale-105"
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
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{project.name}</h3>
      <p className="text-sm text-gray-600 mb-4">
        📍 {project.coordinates.latitude.toFixed(4)}, {project.coordinates.longitude.toFixed(4)}
      </p>
      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>Created: {new Date(project.created).toLocaleDateString()}</span>
        <span>Modified: {new Date(project.lastModified).toLocaleDateString()}</span>
      </div>
    </div>
  );
});

ProjectCard.displayName = 'ProjectCard';

export default ProjectCard;