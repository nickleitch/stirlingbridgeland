import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { projectAPI } from '../services/projectAPI';

// Action types
const PROJECT_ACTIONS = {
  SET_PROJECTS: 'SET_PROJECTS',
  SET_CURRENT_PROJECT: 'SET_CURRENT_PROJECT',
  ADD_PROJECT: 'ADD_PROJECT',
  UPDATE_PROJECT: 'UPDATE_PROJECT',
  DELETE_PROJECT: 'DELETE_PROJECT',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR'
};

// Initial state
const initialState = {
  projects: [],
  currentProject: null,
  loading: false,
  error: null
};

// Reducer
const projectReducer = (state, action) => {
  switch (action.type) {
    case PROJECT_ACTIONS.SET_PROJECTS:
      return {
        ...state,
        projects: action.payload
      };
    
    case PROJECT_ACTIONS.SET_CURRENT_PROJECT:
      return {
        ...state,
        currentProject: action.payload
      };
    
    case PROJECT_ACTIONS.ADD_PROJECT:
      // Check if project already exists to prevent duplicates
      const existingProject = state.projects.find(p => p.id === action.payload.id);
      if (existingProject) {
        // Update existing project instead of adding duplicate
        const updatedProjects = state.projects.map(project =>
          project.id === action.payload.id ? action.payload : project
        );
        localStorage.setItem('stirling_projects', JSON.stringify(updatedProjects));
        return {
          ...state,
          projects: updatedProjects
        };
      } else {
        // Add new project
        const newProjects = [...state.projects, action.payload];
        localStorage.setItem('stirling_projects', JSON.stringify(newProjects));
        return {
          ...state,
          projects: newProjects
        };
      }
    
    case PROJECT_ACTIONS.UPDATE_PROJECT:
      const updatedProjects = state.projects.map(project =>
        project.id === action.payload.id ? action.payload : project
      );
      // Persist to localStorage
      localStorage.setItem('stirling_projects', JSON.stringify(updatedProjects));
      return {
        ...state,
        projects: updatedProjects,
        currentProject: state.currentProject?.id === action.payload.id 
          ? action.payload 
          : state.currentProject
      };
    
    case PROJECT_ACTIONS.DELETE_PROJECT:
      const filteredProjects = state.projects.filter(project => project.id !== action.payload);
      // Persist to localStorage
      localStorage.setItem('stirling_projects', JSON.stringify(filteredProjects));
      return {
        ...state,
        projects: filteredProjects,
        currentProject: state.currentProject?.id === action.payload ? null : state.currentProject
      };
    
    case PROJECT_ACTIONS.SET_LOADING:
      return {
        ...state,
        loading: action.payload
      };
    
    case PROJECT_ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload
      };
    
    case PROJECT_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };
    
    default:
      return state;
  }
};

// Context
const ProjectContext = createContext();

// Provider component
export const ProjectProvider = ({ children }) => {
  const [state, dispatch] = useReducer(projectReducer, initialState);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      dispatch({ type: PROJECT_ACTIONS.SET_LOADING, payload: true });
      
      // First load from localStorage for immediate display
      let localProjects = [];
      const savedProjects = localStorage.getItem('stirling_projects');
      if (savedProjects) {
        try {
          const parsedProjects = JSON.parse(savedProjects);
          localProjects = Array.isArray(parsedProjects) ? parsedProjects : [];
          // Remove duplicates by ID
          localProjects = localProjects.filter((project, index, self) => 
            index === self.findIndex(p => p.id === project.id)
          );
          dispatch({ type: PROJECT_ACTIONS.SET_PROJECTS, payload: localProjects });
        } catch (error) {
          console.error('Error parsing saved projects:', error);
          localStorage.removeItem('stirling_projects');
        }
      }

      // Then sync with database
      try {
        const response = await projectAPI.listProjects();
        if (response.success && response.data.projects) {
          const dbProjects = response.data.projects.map(project => ({
            id: project.id,
            name: project.name,
            coordinates: project.coordinates,
            created: project.created,
            lastModified: project.lastModified,
            layers: {},
            data: null
          }));
          
          // Merge and deduplicate local and database projects
          const mergedProjects = [...localProjects];
          dbProjects.forEach(dbProject => {
            const existingIndex = mergedProjects.findIndex(p => p.id === dbProject.id);
            if (existingIndex >= 0) {
              // Update existing project with latest data from database
              mergedProjects[existingIndex] = dbProject;
            } else {
              // Add new project from database
              mergedProjects.push(dbProject);
            }
          });
          
          // Remove duplicates one more time and save
          const finalProjects = mergedProjects.filter((project, index, self) => 
            index === self.findIndex(p => p.id === project.id)
          );
          
          localStorage.setItem('stirling_projects', JSON.stringify(finalProjects));
          dispatch({ type: PROJECT_ACTIONS.SET_PROJECTS, payload: finalProjects });
        }
      } catch (error) {
        console.log('Database sync not available, using localStorage only:', error);
      }
    } catch (error) {
      dispatch({ type: PROJECT_ACTIONS.SET_ERROR, payload: error.message });
    } finally {
      dispatch({ type: PROJECT_ACTIONS.SET_LOADING, payload: false });
    }
  };

  const createProject = async (projectData) => {
    try {
      dispatch({ type: PROJECT_ACTIONS.SET_LOADING, payload: true });
      dispatch({ type: PROJECT_ACTIONS.CLEAR_ERROR });

      const response = await projectAPI.createProject(projectData);
      
      if (response.success) {
        const newProject = {
          id: response.data.project_id,
          name: projectData.name,
          coordinates: { 
            latitude: projectData.latitude, 
            longitude: projectData.longitude 
          },
          created: new Date().toISOString(),
          lastModified: new Date().toISOString(),
          layers: {},
          data: response.data.boundaries || null
        };
        
        dispatch({ type: PROJECT_ACTIONS.ADD_PROJECT, payload: newProject });
        return { success: true, project: newProject };
      } else {
        throw new Error(response.error || 'Failed to create project');
      }
    } catch (error) {
      dispatch({ type: PROJECT_ACTIONS.SET_ERROR, payload: error.message });
      return { success: false, error: error.message };
    } finally {
      dispatch({ type: PROJECT_ACTIONS.SET_LOADING, payload: false });
    }
  };

  const loadProjectData = async (project) => {
    try {
      dispatch({ type: PROJECT_ACTIONS.SET_LOADING, payload: true });
      dispatch({ type: PROJECT_ACTIONS.CLEAR_ERROR });

      const response = await projectAPI.loadProjectData(project);
      
      if (response.success) {
        const updatedProject = {
          ...project,
          data: response.data.boundaries,
          lastModified: new Date().toISOString()
        };
        
        dispatch({ type: PROJECT_ACTIONS.UPDATE_PROJECT, payload: updatedProject });
        return { success: true, data: response.data };
      } else {
        throw new Error(response.error || 'Failed to load project data');
      }
    } catch (error) {
      dispatch({ type: PROJECT_ACTIONS.SET_ERROR, payload: error.message });
      return { success: false, error: error.message };
    } finally {
      dispatch({ type: PROJECT_ACTIONS.SET_LOADING, payload: false });
    }
  };

  const updateProject = (projectData) => {
    dispatch({ type: PROJECT_ACTIONS.UPDATE_PROJECT, payload: projectData });
  };

  const deleteProject = async (projectId) => {
    try {
      dispatch({ type: PROJECT_ACTIONS.SET_LOADING, payload: true });
      dispatch({ type: PROJECT_ACTIONS.CLEAR_ERROR });

      const response = await projectAPI.deleteProject(projectId);
      
      if (response.success) {
        dispatch({ type: PROJECT_ACTIONS.DELETE_PROJECT, payload: projectId });
        return { success: true };
      } else {
        throw new Error(response.error || 'Failed to delete project');
      }
    } catch (error) {
      dispatch({ type: PROJECT_ACTIONS.SET_ERROR, payload: error.message });
      return { success: false, error: error.message };
    } finally {
      dispatch({ type: PROJECT_ACTIONS.SET_LOADING, payload: false });
    }
  };

  const setCurrentProject = (project) => {
    dispatch({ type: PROJECT_ACTIONS.SET_CURRENT_PROJECT, payload: project });
  };

  const clearError = () => {
    dispatch({ type: PROJECT_ACTIONS.CLEAR_ERROR });
  };

  const value = {
    // State
    projects: state.projects,
    currentProject: state.currentProject,
    loading: state.loading,
    error: state.error,
    
    // Actions
    loadProjects,
    createProject,
    loadProjectData,
    updateProject,
    setCurrentProject,
    clearError
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
};

// Hook to use the project context
export const useProject = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};

export default ProjectContext;