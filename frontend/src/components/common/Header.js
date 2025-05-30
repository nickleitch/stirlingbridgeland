import React, { memo } from 'react';

const StirlingBridgeLogo = memo(({ size = 'large' }) => {
  const isLarge = size === 'large';
  
  return (
    <div className="flex flex-col items-center">
      <div className={isLarge ? "mb-2" : "mb-1"}>
        <svg 
          width={isLarge ? "120" : "60"} 
          height={isLarge ? "24" : "12"} 
          viewBox="0 0 120 24" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path 
            d="M10 22C10 22 30 2 60 2C90 2 110 22 110 22" 
            stroke="#6B7280" 
            strokeWidth="3" 
            strokeLinecap="round" 
            fill="none"
          />
        </svg>
      </div>
      <div className="text-center">
        <div className={`${isLarge ? 'text-2xl' : 'text-sm'} font-bold text-blue-600 tracking-wider`}>
          STIRLING BRIDGE
        </div>
        <div className={`${isLarge ? 'text-sm mt-1' : 'text-xs'} font-medium text-gray-500 tracking-widest`}>
          DEVELOPMENTS
        </div>
      </div>
    </div>
  );
});

StirlingBridgeLogo.displayName = 'StirlingBridgeLogo';

const ProjectsHeader = memo(({ onCreateProject }) => (
  <header className="bg-white shadow-lg">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-center py-6">
        <div className="flex items-center">
          <StirlingBridgeLogo size="large" />
          <div className="ml-6 border-l border-gray-300 pl-6">
            <h1 className="text-xl font-bold text-gray-900">LandDev Platform</h1>
            <p className="text-sm text-gray-500">Project Management Dashboard</p>
          </div>
        </div>
        <button
          onClick={onCreateProject}
          className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all transform hover:scale-105"
        >
          + New Project
        </button>
      </div>
    </div>
  </header>
));

ProjectsHeader.displayName = 'ProjectsHeader';

const DashboardHeader = memo(({ currentProject, onBackToProjects }) => (
  <nav className="bg-white shadow-sm border-b h-20 flex items-center px-4">
    <button
      onClick={onBackToProjects}
      className="mr-6 p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
      aria-label="Back to Projects"
    >
      ← Back to Projects
    </button>
    
    <div className="flex items-center">
      <div className="mr-4">
        <StirlingBridgeLogo size="small" />
      </div>
      <div className="border-l border-gray-300 pl-4">
        <h1 className="text-lg font-semibold text-gray-900">{currentProject?.name}</h1>
        <p className="text-xs text-gray-500">LandDev Platform</p>
      </div>
    </div>
    
    <div className="ml-auto flex items-center space-x-4">
      <div className="border-l border-gray-300 pl-4">
        <span className="text-sm text-gray-600" title="Project Coordinates">
          📍 {currentProject?.coordinates.latitude.toFixed(4)}, {currentProject?.coordinates.longitude.toFixed(4)}
        </span>
        <div className="text-sm text-gray-500">Phase1BoundariesPresent</div>
      </div>
    </div>
  </nav>
));

DashboardHeader.displayName = 'DashboardHeader';

export { StirlingBridgeLogo, ProjectsHeader, DashboardHeader };