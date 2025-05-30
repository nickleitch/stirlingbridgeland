import React, { memo } from 'react';
import ProjectCard from './ProjectCard';
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
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Projects</h2>
        <p className="text-gray-600">Manage your land development projects</p>
      </div>

      {projects.length === 0 ? (
        <EmptyState onCreateProject={onCreateProject} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map(project => (
            <ProjectCard
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