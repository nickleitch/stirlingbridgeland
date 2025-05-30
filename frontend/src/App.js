import React, { useState, useRef, useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Layer definitions organized by sections
const LAYER_SECTIONS = {
  "Base Data": {
    color: "#3B82F6",
    layers: [
      { id: "property_boundaries", name: "Property Boundaries", type: "Farm Portions", color: "#FF4500" },
      { id: "zoning_designations", name: "Zoning Designations", type: "Zoning", color: "#9932CC" },
      { id: "roads_existing", name: "Roads Existing", type: "Roads", color: "#FF6347" },
      { id: "topography_basic", name: "Topography Basic", type: "Contours", color: "#8B4513" },
      { id: "water_bodies", name: "Water Bodies", type: "Water Bodies", color: "#00BFFF" },
      { id: "labels_primary", name: "Labels Primary", type: "Labels", color: "#2F4F4F" },
      { id: "survey_control", name: "Survey Control", type: "Survey", color: "#DC143C" },
      { id: "coordinate_grid", name: "Coordinate Grid", type: "Grid", color: "#808080" },
      { id: "contours_major", name: "Contours Major", type: "Contours", color: "#A0522D" },
      { id: "spot_levels", name: "Spot Levels", type: "Levels", color: "#4682B4" }
    ]
  },
  "Initial Concept": {
    color: "#8B5CF6",
    layers: [
      { id: "site_boundary", name: "Site Boundary", type: "Site Boundary", color: "#FF4500" },
      { id: "access_roads", name: "Access Roads", type: "Roads", color: "#FF6347" },
      { id: "drainage", name: "Drainage", type: "Water Bodies", color: "#00CED1" },
      { id: "utilities", name: "Utilities", type: "Infrastructure", color: "#FFD700" },
      { id: "concept_layout", name: "Concept Layout", type: "Planning", color: "#DA70D6" }
    ]
  },
  "Specialist Input": {
    color: "#EC4899",
    layers: [
      { id: "traffic_impact", name: "Traffic Impact", type: "Traffic", color: "#FF1493" },
      { id: "environmental_impact", name: "Environmental Impact", type: "Environmental Constraints", color: "#228B22" },
      { id: "geotechnical", name: "Geotechnical", type: "Engineering", color: "#8B4513" },
      { id: "heritage", name: "Heritage", type: "Heritage", color: "#DDA0DD" },
      { id: "services", name: "Services", type: "Infrastructure", color: "#FF8C00" }
    ]
  },
  "Environmental Screening": {
    color: "#F59E0B",
    layers: [
      { id: "environmental_constraints", name: "Environmental Constraints", type: "Environmental Constraints", color: "#228B22" },
      { id: "wetlands", name: "Wetlands", type: "Water Bodies", color: "#4682B4" },
      { id: "vegetation", name: "Vegetation", type: "Environmental", color: "#32CD32" },
      { id: "fauna", name: "Fauna", type: "Environmental", color: "#90EE90" },
      { id: "noise_impact", name: "Noise Impact", type: "Environmental", color: "#FFB6C1" },
      { id: "air_quality", name: "Air Quality", type: "Environmental", color: "#B0C4DE" },
      { id: "visual_impact", name: "Visual Impact", type: "Environmental", color: "#DEB887" }
    ]
  },
  "Additional Design": {
    color: "#10B981",
    layers: [
      { id: "major_hazard_buffers", name: "Major Hazard Installation Buffers", type: "Safety", color: "#FF4500", stage: "SDP 4" },
      { id: "fire_access", name: "Fire Access", type: "Safety", color: "#FF0000", stage: "SDP 4" },
      { id: "disability_access", name: "Disability Access", type: "Accessibility", color: "#4169E1", stage: "SDP 4" },
      { id: "construction_staging", name: "Construction Staging", type: "Construction", color: "#F4A460", stage: "Final SDP" },
      { id: "landscaping_zones", name: "Landscaping Zones", type: "Landscaping", color: "#98FB98", stage: "Final SDP" },
      { id: "telecommunications", name: "Telecommunications Proposed", type: "Infrastructure", color: "#9370DB", stage: "Final SDP" },
      { id: "recreational_facilities", name: "Recreational Facilities", type: "Recreation", color: "#20B2AA", stage: "Final SDP" }
    ]
  }
};

function App() {
  const [currentView, setCurrentView] = useState('projects'); // 'projects' or 'dashboard'
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [coordinates, setCoordinates] = useState({ latitude: '', longitude: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [layerStates, setLayerStates] = useState({});
  const [expandedSections, setExpandedSections] = useState({
    "Base Data": true,
    "Initial Concept": false,
    "Specialist Input": false,
    "Environmental Screening": false,
    "Additional Design": false
  });
  const [result, setResult] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectForm, setNewProjectForm] = useState({
    name: '',
    latitude: '',
    longitude: ''
  });
  const mapRef = useRef();

  // Initialize projects from localStorage
  useEffect(() => {
    const savedProjects = localStorage.getItem('stirling_projects');
    console.log('Loading projects from localStorage:', savedProjects);
    if (savedProjects) {
      try {
        const parsedProjects = JSON.parse(savedProjects);
        console.log('Parsed projects:', parsedProjects);
        setProjects(parsedProjects);
      } catch (error) {
        console.error('Error parsing saved projects:', error);
        localStorage.removeItem('stirling_projects');
      }
    }
  }, []);

  // Save projects to localStorage
  const saveProjects = (projectList) => {
    localStorage.setItem('stirling_projects', JSON.stringify(projectList));
    setProjects(projectList);
  };

  const createNewProject = () => {
    setNewProjectForm({ name: '', latitude: '', longitude: '' });
    setShowCreateModal(true);
  };

  const handleCreateProject = async () => {
    if (!newProjectForm.name || !newProjectForm.latitude || !newProjectForm.longitude) {
      setError('Please fill in all fields');
      return;
    }

    const newProject = {
      id: Date.now().toString(),
      name: newProjectForm.name,
      coordinates: { 
        latitude: parseFloat(newProjectForm.latitude), 
        longitude: parseFloat(newProjectForm.longitude) 
      },
      created: new Date().toISOString(),
      lastModified: new Date().toISOString(),
      layers: {},
      data: null
    };

    const updatedProjects = [...projects, newProject];
    saveProjects(updatedProjects);
    setShowCreateModal(false);
    setError(''); // Clear any errors
    setNewProjectForm({ name: '', latitude: '', longitude: '' }); // Reset form
    
    // Debug logging
    console.log('Created new project:', newProject);
    console.log('Updated projects list:', updatedProjects);
    console.log('Saved to localStorage:', localStorage.getItem('stirling_projects'));
    
    openProject(newProject);
  };

  const openProject = async (project) => {
    setCurrentProject(project);
    setCoordinates(project.coordinates);
    setCurrentView('dashboard');
    
    // Initialize layer states based on available data
    const initialLayerStates = {};
    Object.values(LAYER_SECTIONS).forEach(section => {
      section.layers.forEach(layer => {
        initialLayerStates[layer.id] = false; // Start with all layers off
      });
    });
    setLayerStates(initialLayerStates);

    // Load project data if not already loaded
    if (!project.data) {
      await loadProjectData(project);
    }
  };

  const loadProjectData = async (project) => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/identify-land`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: project.coordinates.latitude,
          longitude: project.coordinates.longitude,
          project_name: project.name
        })
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      setResult(data);
      
      // Update project with data - fix the stale closure issue
      const updatedProject = { ...project, data, lastModified: new Date().toISOString() };
      
      // Use functional update to get the latest projects state
      setProjects(currentProjects => {
        const updatedProjects = currentProjects.map(p => p.id === project.id ? updatedProject : p);
        // Save to localStorage
        localStorage.setItem('stirling_projects', JSON.stringify(updatedProjects));
        return updatedProjects;
      });
      
      setCurrentProject(updatedProject);

      // Auto-enable base data layers that have data
      const newLayerStates = { ...layerStates };
      if (data.boundaries) {
        data.boundaries.forEach(boundary => {
          const layerType = boundary.layer_type;
          let layerId = null;
          
          // Map existing data types to new Base Data layer structure
          switch(layerType) {
            case 'Farm Portions':
            case 'Erven':
            case 'Holdings':
            case 'Public Places':
              layerId = 'property_boundaries';
              break;
            case 'Roads':
              layerId = 'roads_existing';
              break;
            case 'Contours':
              layerId = 'topography_basic';
              break;
            case 'Water Bodies':
              layerId = 'water_bodies';
              break;
            case 'Environmental Constraints':
              // Keep this in Environmental Screening section
              layerId = Object.values(LAYER_SECTIONS).find(section => 
                section.layers.some(layer => layer.type === layerType)
              )?.layers.find(layer => layer.type === layerType)?.id;
              break;
            default:
              // For other layer types, find in any section
              layerId = Object.values(LAYER_SECTIONS).find(section => 
                section.layers.some(layer => layer.type === layerType)
              )?.layers.find(layer => layer.type === layerType)?.id;
          }
          
          if (layerId) {
            newLayerStates[layerId] = true;
          }
        });
      }
      setLayerStates(newLayerStates);

    } catch (err) {
      setError(`Failed to load project data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleLayer = (layerId) => {
    setLayerStates(prev => ({
      ...prev,
      [layerId]: !prev[layerId]
    }));
  };

  const toggleSection = (sectionName) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionName]: !prev[sectionName]
    }));
  };

  const backToProjects = () => {
    setCurrentView('projects');
    setCurrentProject(null);
    setResult(null);
    setError('');
  };

  // Get available boundaries for a layer type
  const getBoundariesForLayer = (layerId) => {
    if (!result?.boundaries) return [];
    
    // Map layer IDs to boundary types
    switch(layerId) {
      case 'property_boundaries':
        return result.boundaries.filter(boundary => 
          ['Farm Portions', 'Erven', 'Holdings', 'Public Places'].includes(boundary.layer_type)
        );
      case 'roads_existing':
        return result.boundaries.filter(boundary => boundary.layer_type === 'Roads');
      case 'topography_basic':
        return result.boundaries.filter(boundary => boundary.layer_type === 'Contours');
      case 'contours_major':
        return result.boundaries.filter(boundary => boundary.layer_type === 'Contours');
      case 'water_bodies':
        return result.boundaries.filter(boundary => boundary.layer_type === 'Water Bodies');
      case 'environmental_constraints':
        return result.boundaries.filter(boundary => boundary.layer_type === 'Environmental Constraints');
      default:
        // For other layers, find by matching type in layer definitions
        const layer = Object.values(LAYER_SECTIONS).find(section => 
          section.layers.some(l => l.id === layerId)
        )?.layers.find(l => l.id === layerId);
        
        if (layer) {
          return result.boundaries.filter(boundary => boundary.layer_type === layer.type);
        }
        return [];
    }
  };

  // Convert geometry to Leaflet format
  const convertGeometryToLeaflet = (geometry) => {
    if (!geometry || !geometry.rings) return [];
    return geometry.rings.map(ring => 
      ring.map(coord => [coord[1], coord[0]])
    );
  };

  // Get map bounds
  const getMapBounds = () => {
    if (!currentProject) return [[-26.2041, 28.0473], [-26.2041, 28.0473]];
    
    const { latitude, longitude } = currentProject.coordinates;
    return [[latitude - 0.01, longitude - 0.01], [latitude + 0.01, longitude + 0.01]];
  };

  if (currentView === 'projects') {
    return (
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <header className="bg-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center">
                <div className="flex flex-col items-center">
                  {/* Bridge arch design */}
                  <div className="mb-2">
                    <svg width="120" height="24" viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M10 22C10 22 30 2 60 2C90 2 110 22 110 22" stroke="#6B7280" strokeWidth="3" strokeLinecap="round" fill="none"/>
                    </svg>
                  </div>
                  {/* Company name */}
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600 tracking-wider">STIRLING BRIDGE</div>
                    <div className="text-sm font-medium text-gray-500 tracking-widest mt-1">DEVELOPMENTS</div>
                  </div>
                </div>
                <div className="ml-6 border-l border-gray-300 pl-6">
                  <h1 className="text-xl font-bold text-gray-900">LandDev Platform</h1>
                  <p className="text-sm text-gray-500">Project Management Dashboard</p>
                </div>
              </div>
              <button
                onClick={createNewProject}
                className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all transform hover:scale-105"
              >
                + New Project
              </button>
            </div>
          </div>
        </header>

        {/* Projects Grid */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Projects</h2>
            <p className="text-gray-600">Manage your land development projects</p>
          </div>

          {projects.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-6xl mb-4">📁</div>
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No Projects Yet</h3>
              <p className="text-gray-500 mb-6">Create your first land development project to get started</p>
              <button
                onClick={createNewProject}
                className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-8 py-4 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all transform hover:scale-105"
              >
                Create First Project
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map(project => (
                <div
                  key={project.id}
                  onClick={() => openProject(project)}
                  className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all cursor-pointer transform hover:scale-105"
                >
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{project.name}</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    📍 {project.coordinates.latitude.toFixed(4)}, {project.coordinates.longitude.toFixed(4)}
                  </p>
                  <div className="flex justify-between items-center text-xs text-gray-500">
                    <span>Created: {new Date(project.created).toLocaleDateString()}</span>
                    <span>Modified: {new Date(project.lastModified).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>

        {/* Create Project Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md w-full mx-4">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Project</h2>
              
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Project Name
                  </label>
                  <input
                    type="text"
                    value={newProjectForm.name}
                    onChange={(e) => setNewProjectForm(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter project name"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Latitude (Decimal Degrees)
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={newProjectForm.latitude}
                    onChange={(e) => setNewProjectForm(prev => ({ ...prev, latitude: e.target.value }))}
                    placeholder="-26.2041"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Longitude (Decimal Degrees)
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={newProjectForm.longitude}
                    onChange={(e) => setNewProjectForm(prev => ({ ...prev, longitude: e.target.value }))}
                    placeholder="28.0473"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex space-x-4 mt-8">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setError('');
                  }}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateProject}
                  className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all"
                >
                  Create Project
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Dashboard View
  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Top Navigation */}
      <nav className="bg-white shadow-sm border-b h-20 flex items-center px-4">
        <button
          onClick={backToProjects}
          className="mr-6 p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
        >
          ← Back to Projects
        </button>
        
        <div className="flex items-center">
          <div className="flex flex-col items-center mr-4">
            {/* Bridge arch design - smaller for dashboard */}
            <div className="mb-1">
              <svg width="60" height="12" viewBox="0 0 120 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 22C10 22 30 2 60 2C90 2 110 22 110 22" stroke="#6B7280" strokeWidth="3" strokeLinecap="round" fill="none"/>
              </svg>
            </div>
            {/* Company name - smaller for dashboard */}
            <div className="text-center">
              <div className="text-sm font-bold text-blue-600 tracking-wider">STIRLING BRIDGE</div>
              <div className="text-xs font-medium text-gray-500 tracking-widest">DEVELOPMENTS</div>
            </div>
          </div>
          <div className="border-l border-gray-300 pl-4">
            <h1 className="text-lg font-semibold text-gray-900">{currentProject?.name}</h1>
            <p className="text-xs text-gray-500">LandDev Platform</p>
          </div>
        </div>
        
        <div className="ml-auto flex items-center space-x-4">
          <span className="text-sm text-gray-600">
            📍 {currentProject?.coordinates.latitude.toFixed(4)}, {currentProject?.coordinates.longitude.toFixed(4)}
          </span>
          <div className="text-sm text-gray-500">Phase1BoundariesPresent</div>
        </div>
      </nav>

      <div className="flex-1 flex">
        {/* Left Sidebar */}
        <div className="w-80 bg-white shadow-lg flex flex-col">
          {/* Search */}
          <div className="p-4 border-b">
            <div className="relative">
              <input
                type="text"
                placeholder="Search layers..."
                value=""
                onChange={() => {}}
                className="w-full pl-8 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="absolute left-2 top-2.5 text-gray-400">🔍</div>
              <button className="absolute right-2 top-2 text-gray-400 hover:text-gray-600">
                →
              </button>
            </div>
          </div>

          {/* Layer Sections */}
          <div className="flex-1 overflow-y-auto">
            {Object.entries(LAYER_SECTIONS).map(([sectionName, section]) => (
              <div key={sectionName} className="border-b border-gray-100">
                <button
                  onClick={() => toggleSection(sectionName)}
                  className="w-full flex items-center justify-between p-4 hover:bg-gray-50 text-left"
                >
                  <div className="flex items-center">
                    <div 
                      className="w-3 h-3 rounded-full mr-3"
                      style={{ backgroundColor: section.color }}
                    ></div>
                    <span className="font-medium text-gray-900">{sectionName}</span>
                    <span className="ml-2 text-sm text-gray-500">{section.layers.length} layers</span>
                  </div>
                  <span className={`transition-transform ${expandedSections[sectionName] ? 'rotate-180' : ''}`}>
                    ▼
                  </span>
                </button>

                {expandedSections[sectionName] && (
                  <div className="pb-2">
                    {section.layers.map(layer => {
                      const hasData = getBoundariesForLayer(layer.id).length > 0;
                      const isEnabled = layerStates[layer.id];
                      
                      return (
                        <div 
                          key={layer.id} 
                          className={`mx-4 mb-2 p-3 rounded-lg ${hasData ? 'bg-gray-50' : 'bg-gray-25 opacity-60'}`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="font-medium text-sm text-gray-900">{layer.name}</div>
                              {layer.stage && (
                                <div className="text-xs text-gray-500 mt-1">{layer.stage}</div>
                              )}
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={isEnabled}
                                onChange={() => toggleLayer(layer.id)}
                                disabled={!hasData}
                                className="sr-only peer"
                              />
                              <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600 disabled:opacity-50"></div>
                            </label>
                          </div>
                          {hasData && (
                            <div className="mt-2 text-xs text-gray-600">
                              {getBoundariesForLayer(layer.id).length} features available
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Map Area */}
        <div className="flex-1 relative">
          {loading && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white p-6 rounded-lg shadow-xl">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent mx-auto mb-4"></div>
                <p className="text-gray-600">Loading project data...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute top-4 left-4 right-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg z-40">
              {error}
            </div>
          )}

          <MapContainer
            bounds={getMapBounds()}
            style={{ height: '100%', width: '100%' }}
            ref={mapRef}
          >
            {/* Satellite Imagery Base Layer */}
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              attribution='Tiles &copy; Esri'
              maxZoom={19}
            />
            
            {/* Street overlay for reference */}
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}"
              attribution=''
              opacity={0.3}
              maxZoom={19}
            />

            {/* Search point marker */}
            {currentProject && (
              <Marker position={[currentProject.coordinates.latitude, currentProject.coordinates.longitude]}>
                <Popup>
                  <div className="text-center">
                    <strong>{currentProject.name}</strong><br/>
                    {currentProject.coordinates.latitude.toFixed(6)}, {currentProject.coordinates.longitude.toFixed(6)}
                  </div>
                </Popup>
              </Marker>
            )}

            {/* Layer boundaries */}
            {result?.boundaries?.map((boundary, index) => {
              // Check if this layer is enabled based on new mapping
              let layerId = null;
              
              switch(boundary.layer_type) {
                case 'Farm Portions':
                case 'Erven':
                case 'Holdings':
                case 'Public Places':
                  layerId = 'property_boundaries';
                  break;
                case 'Roads':
                  layerId = 'roads_existing';
                  break;
                case 'Contours':
                  layerId = layerStates['topography_basic'] ? 'topography_basic' : 
                           layerStates['contours_major'] ? 'contours_major' : null;
                  break;
                case 'Water Bodies':
                  layerId = 'water_bodies';
                  break;
                case 'Environmental Constraints':
                  layerId = 'environmental_constraints';
                  break;
                default:
                  // For other layer types, find in any section
                  layerId = Object.values(LAYER_SECTIONS).find(section => 
                    section.layers.some(layer => layer.type === boundary.layer_type)
                  )?.layers.find(layer => layer.type === boundary.layer_type)?.id;
              }
              
              if (!layerId || !layerStates[layerId]) return null;

              const polygonCoords = convertGeometryToLeaflet(boundary.geometry);
              
              // Get color from the specific layer or use the boundary type mapping
              let color = "#000000";
              if (layerId === 'property_boundaries') {
                color = "#FF4500"; // Orange red for property boundaries
              } else {
                const layer = Object.values(LAYER_SECTIONS).find(section => 
                  section.layers.some(l => l.id === layerId)
                )?.layers.find(l => l.id === layerId);
                color = layer?.color || "#000000";
              }

              if (polygonCoords.length === 0) return null;

              return (
                <Polygon
                  key={index}
                  positions={polygonCoords}
                  pathOptions={{
                    color: color,
                    weight: 2,
                    opacity: 0.8,
                    fillColor: color,
                    fillOpacity: 0.2
                  }}
                >
                  <Popup>
                    <div>
                      <strong>{boundary.layer_name}</strong><br/>
                      <em>Type: {boundary.layer_type}</em><br/>
                      <small>Source: {boundary.source_api}</small>
                    </div>
                  </Popup>
                </Polygon>
              );
            })}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}

export default App;
