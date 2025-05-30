import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import { useLayerMapping } from '../hooks/useLayerMapping';
import { DashboardHeader } from '../components/common/Header';
import Dashboard from '../components/dashboard/Dashboard';

const DashboardPage = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { 
    currentProject, 
    setCurrentProject, 
    projects, 
    loadProjectData 
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
      />

      <Dashboard />
    </div>
  );
};

export default DashboardPage;