import React, { memo } from 'react';
import ProjectProgressSummaryForList from './ProjectProgressSummaryForList';
import { useProject } from '../../contexts/ProjectContext';

const EmptyState = memo(({ onCreateProject }) => (
  <div className="flex items-center justify-center min-h-[60vh]">
    <button
      onClick={onCreateProject}
      className="bg-teal-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-teal-700 transition-colors transform hover:scale-105 flex items-center space-x-2"
    >
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
      </svg>
      <span>Create First Project</span>
    </button>
  </div>
));

EmptyState.displayName = 'EmptyState';

const ProjectList = memo(({ onProjectSelect, onCreateProject }) => {
  const { projects } = useProject();

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {projects.length === 0 ? (
        <EmptyState onCreateProject={onCreateProject} />
      ) : (
        <div className="max-w-7xl mx-auto space-y-4">
          {projects.map(project => (
            <ProjectProgressSummaryForList
              key={project.id}
              project={project}
              onSelect={onProjectSelect}
            />
          ))}
        </div>
      )}
    </main>
  );
});

ProjectList.displayName = 'ProjectList';

export default ProjectList;