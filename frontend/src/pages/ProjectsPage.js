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