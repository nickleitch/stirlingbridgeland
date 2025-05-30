import React, { memo } from 'react';
import ProjectCard from './ProjectCard';
import ProjectProgressSummaryForList from './ProjectProgressSummaryForList';
import { useProject } from '../../contexts/ProjectContext';

const EmptyState = memo(({ onCreateProject }) => (
  <div className="text-center py-12">
    <div className="text-gray-400 text-6xl mb-4">📁</div>
    <h3 className="text-xl font-semibold text-gray-600 mb-2">No Projects Yet</h3>
    <p className="text-gray-500 mb-6">Create your first land development project to get started</p>
    <button
      onClick={onCreateProject}
      className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-8 py-4 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all transform hover:scale-105"
    >
      Create First Project
    </button>
  </div>
));

EmptyState.displayName = 'EmptyState';

const ProjectList = memo(({ onProjectSelect, onCreateProject }) => {
  const { projects } = useProject();

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Projects</h2>
            <p className="text-gray-600">
              Manage your land development projects
              {projects.length > 0 && (
                <span className="ml-2 text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                  {projects.length} project{projects.length !== 1 ? 's' : ''}
                </span>
              )}
            </p>
          </div>
        </div>
      </div>

      {projects.length === 0 ? (
        <EmptyState onCreateProject={onCreateProject} />
      ) : (
        <div className="max-w-7xl mx-auto space-y-4">
          {/* Show unified progress summary with project info for each project */}
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