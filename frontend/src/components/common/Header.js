import React, { memo } from 'react';

const LandstreamLogo = memo(({ size = 'large' }) => {
  const isLarge = size === 'large';
  
  return (
    <div className="flex items-center">
      {/* Landstream Logo SVG */}
      <div className={isLarge ? "h-8 w-8 mr-3" : "h-6 w-6 mr-2"}>
        <svg viewBox="0 0 100 100" className={isLarge ? "h-8 w-8" : "h-6 w-6"}>
          <circle 
            cx="50" 
            cy="50" 
            r="45" 
            fill="none" 
            stroke="#374151" 
            strokeWidth="8"
          />
          {/* Horizontal line */}
          <line 
            x1="20" 
            y1="50" 
            x2="80" 
            y2="50" 
            stroke="#374151" 
            strokeWidth="6"
          />
          {/* Vertical line */}
          <line 
            x1="50" 
            y1="20" 
            x2="50" 
            y2="80" 
            stroke="#374151" 
            strokeWidth="6"
          />
          {/* Bottom extension */}
          <line 
            x1="50" 
            y1="80" 
            x2="50" 
            y2="95" 
            stroke="#374151" 
            strokeWidth="6"
          />
        </svg>
      </div>
      <div>
        <div className={`${isLarge ? 'text-lg' : 'text-sm'} font-bold text-gray-900 tracking-wider`}>
          LANDSTREAM
        </div>
        <div className={`${isLarge ? 'text-xs' : 'text-xs'} text-gray-500 -mt-1 tracking-wide`}>
          URBAN PLANNING & DEVELOPMENT
        </div>
      </div>
    </div>
  );
});

LandstreamLogo.displayName = 'LandstreamLogo';

const ProjectsHeader = memo(({ onCreateProject }) => (
  <header className="bg-white shadow-lg">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-center py-6">
        <div className="flex items-center">
          <LandstreamLogo size="large" />
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

const DashboardHeader = memo(({ currentProject, onBackToProjects, onDeleteProject }) => (
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
        <LandstreamLogo size="small" />
      </div>
      <div className="border-l border-gray-300 pl-4">
        <h1 className="text-lg font-semibold text-gray-900">{currentProject?.name}</h1>
        <p className="text-xs text-gray-500">Urban Planning & Development</p>
      </div>
    </div>
    
    <div className="ml-auto flex items-center space-x-4">
      <div className="border-l border-gray-300 pl-4 mr-4">
        <span className="text-sm text-gray-600" title="Project Coordinates">
          📍 {currentProject?.coordinates.latitude.toFixed(4)}, {currentProject?.coordinates.longitude.toFixed(4)}
        </span>
        <div className="text-sm text-gray-500">Phase1BoundariesPresent</div>
      </div>
      
      {/* Project Actions */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onDeleteProject}
          className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
          aria-label="Delete Project"
          title="Delete Project"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  </nav>
));

DashboardHeader.displayName = 'DashboardHeader';

export { LandstreamLogo, ProjectsHeader, DashboardHeader };