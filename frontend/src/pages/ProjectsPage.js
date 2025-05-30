import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import { useLayerMapping } from '../hooks/useLayerMapping';
import ProjectList from '../components/projects/ProjectList';
import CreateProjectModal from '../components/projects/CreateProjectModal';

const ProjectsPage = () => {
  const navigate = useNavigate();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const { setCurrentProject, loadProjectData } = useProject();
  const { autoEnableLayersForBoundaries } = useLayerMapping();

  // Handle project selection
  const handleProjectSelect = async (project) => {
    setCurrentProject(project);

    // Load project data if not already loaded
    if (!project.data) {
      const result = await loadProjectData(project);
      if (result.success && result.data.boundaries) {
        // Auto-enable layers based on available data
        autoEnableLayersForBoundaries(
          result.data.boundaries,
          project.coordinates
        );
      }
    } else {
      // Auto-enable layers for existing data
      autoEnableLayersForBoundaries(
        project.data,
        project.coordinates
      );
    }

    // Navigate to dashboard for this project
    navigate(`/dashboard/${project.id}`);
  };

  // Handle new project creation
  const handleProjectCreated = (newProject) => {
    setCurrentProject(newProject);
    
    // Auto-enable layers if project has data
    if (newProject.data) {
      autoEnableLayersForBoundaries(
        newProject.data,
        newProject.coordinates
      );
    }

    // Navigate to dashboard for new project
    navigate(`/dashboard/${newProject.id}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header with Create Button */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
              <p className="text-sm text-gray-600 mt-1">Manage your land development projects</p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-teal-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-teal-700 transition-colors flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span>New Project</span>
            </button>
          </div>
        </div>
      </div>
      
      <ProjectList 
        onProjectSelect={handleProjectSelect}
        onCreateProject={() => setShowCreateModal(true)}
      />

      <CreateProjectModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onProjectCreated={handleProjectCreated}
      />
    </div>
  );
};

export default ProjectsPage;