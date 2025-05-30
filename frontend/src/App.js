import React, { useState, useEffect } from 'react';
import { ProjectProvider } from './contexts/ProjectContext';
import { LayerProvider } from './contexts/LayerContext';
import { useProject } from './contexts/ProjectContext';
import { useLayerMapping } from './hooks/useLayerMapping';
import ErrorBoundary from './components/ErrorBoundary';
import { ProjectsHeader, DashboardHeader } from './components/common/Header';
import ProjectList from './components/projects/ProjectList';
import CreateProjectModal from './components/projects/CreateProjectModal';
import Dashboard from './components/dashboard/Dashboard';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Main app component that handles view state
const AppContent = () => {
  const [currentView, setCurrentView] = useState('projects');
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  const { 
    currentProject, 
    setCurrentProject, 
    loadProjectData 
  } = useProject();
  
  const { autoEnableLayersForBoundaries } = useLayerMapping();

  // Handle project selection
  const handleProjectSelect = async (project) => {
    setCurrentProject(project);
    setCurrentView('dashboard');

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
  };

  // Handle new project creation
  const handleProjectCreated = (newProject) => {
    setCurrentProject(newProject);
    setCurrentView('dashboard');
    
    // Auto-enable layers if project has data
    if (newProject.data) {
      autoEnableLayersForBoundaries(
        newProject.data,
        newProject.coordinates
      );
    }
  };

  // Handle back to projects
  const handleBackToProjects = () => {
    setCurrentView('projects');
    setCurrentProject(null);
  };

  // Render projects view
  if (currentView === 'projects') {
    return (
      <div className="min-h-screen bg-gray-100">
        <ProjectsHeader onCreateProject={() => setShowCreateModal(true)} />
        
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
  }

  // Render dashboard view
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

// Root App component with providers
const App = () => {
  return (
    <ErrorBoundary>
      <ProjectProvider>
        <LayerProvider>
          <AppContent />
        </LayerProvider>
      </ProjectProvider>
    </ErrorBoundary>
  );
};

export default App;