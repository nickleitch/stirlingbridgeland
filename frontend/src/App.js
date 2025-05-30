import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ProjectProvider } from './contexts/ProjectContext';
import { LayerProvider } from './contexts/LayerContext';
import ErrorBoundary from './components/ErrorBoundary';
import Navigation from './components/navigation/Navigation';
import ProjectsPage from './pages/ProjectsPage';
import DashboardPage from './pages/DashboardPage';
import APIManagementPage from './pages/APIManagementPage';
import UserProfilePage from './pages/UserProfilePage';
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

// Main App Layout with Navigation
const AppLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main>
        {children}
      </main>
    </div>
  );
};

// Dashboard Layout (no navigation for immersive experience)
const DashboardLayout = ({ children }) => {
  return children;
};

// Root App component with providers and routing
const App = () => {
  return (
    <ErrorBoundary>
      <ProjectProvider>
        <LayerProvider>
          <Router>
            <Routes>
              {/* Dashboard route - full screen without navigation */}
              <Route 
                path="/dashboard/:projectId" 
                element={
                  <DashboardLayout>
                    <DashboardPage />
                  </DashboardLayout>
                } 
              />
              
              {/* All other routes - with navigation */}
              <Route 
                path="/" 
                element={
                  <AppLayout>
                    <ProjectsPage />
                  </AppLayout>
                } 
              />
              <Route 
                path="/api-management" 
                element={
                  <AppLayout>
                    <APIManagementPage />
                  </AppLayout>
                } 
              />
              <Route 
                path="/profile" 
                element={
                  <AppLayout>
                    <UserProfilePage />
                  </AppLayout>
                } 
              />
            </Routes>
          </Router>
        </LayerProvider>
      </ProjectProvider>
    </ErrorBoundary>
  );
};

export default App;