import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import { useLayerMapping } from '../hooks/useLayerMapping';
import { DashboardHeader } from '../components/common/Header';
import DeleteConfirmationModal from '../components/common/DeleteConfirmationModal';
import Dashboard from '../components/dashboard/Dashboard';

const DashboardPage = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const { 
    currentProject, 
    setCurrentProject, 
    projects, 
    loadProjectData,
    deleteProject 
  } = useProject();
  const { autoEnableLayersForBoundaries } = useLayerMapping();

  useEffect(() => {
    // If we have a projectId but no currentProject, try to find and load it
    if (projectId && (!currentProject || currentProject.id !== projectId)) {
      const project = projects.find(p => p.id === projectId);
      if (project) {
        setCurrentProject(project);
        
        // Load project data if not already loaded
        if (!project.data) {
          loadProjectData(project).then(result => {
            if (result.success && result.data.boundaries) {
              autoEnableLayersForBoundaries(
                result.data.boundaries,
                project.coordinates
              );
            }
          });
        } else {
          // Auto-enable layers for existing data
          autoEnableLayersForBoundaries(
            project.data,
            project.coordinates
          );
        }
      } else {
        // Project not found, redirect to projects page
        navigate('/');
      }
    }
  }, [projectId, currentProject, projects, setCurrentProject, loadProjectData, autoEnableLayersForBoundaries, navigate]);

  // Handle back to projects
  const handleBackToProjects = () => {
    navigate('/');
    setCurrentProject(null);
  };

  // Handle delete project
  const handleDeleteProject = () => {
    setShowDeleteModal(true);
  };

  // Confirm delete project
  const handleConfirmDelete = async () => {
    if (!currentProject) return;

    try {
      const result = await deleteProject(currentProject.id);
      if (result.success) {
        // Navigate back to projects page after successful deletion
        navigate('/');
        setCurrentProject(null);
      } else {
        // Handle error - you could show a toast or error message here
        console.error('Failed to delete project:', result.error);
        alert('Failed to delete project: ' + result.error);
      }
    } catch (error) {
      console.error('Error deleting project:', error);
      alert('An error occurred while deleting the project');
    }
  };

  // If no current project, show loading or redirect
  if (!currentProject) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto"></div>
          <p className="mt-4 text-white">Loading project...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      <DashboardHeader 
        currentProject={currentProject}
        onBackToProjects={handleBackToProjects}
        onDeleteProject={handleDeleteProject}
      />

      <Dashboard />

      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleConfirmDelete}
        projectName={currentProject.name}
      />
    </div>
  );
};

export default DashboardPage;