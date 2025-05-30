import React, { createContext, useContext, useReducer } from 'react';
import { LAYER_SECTIONS } from '../config/layerConfig';

// Action types
const LAYER_ACTIONS = {
  TOGGLE_LAYER: 'TOGGLE_LAYER',
  SET_LAYER_STATE: 'SET_LAYER_STATE',
  TOGGLE_SECTION: 'TOGGLE_SECTION',
  SET_LAYER_REFRESHING: 'SET_LAYER_REFRESHING',
  SET_LAYER_DOWNLOADING: 'SET_LAYER_DOWNLOADING',
  RESET_LAYERS: 'RESET_LAYERS',
  INITIALIZE_LAYERS: 'INITIALIZE_LAYERS'
};

// Initial state
const initialState = {
  layerStates: {},
  expandedSections: {
    "Base Data": true,
    "Initial Concept": false,
    "Specialist Input": false,
    "Environmental Screening": false,
    "Additional Design": false
  },
  layerRefreshing: {},
  layerDownloading: {}
};

// Reducer
const layerReducer = (state, action) => {
  switch (action.type) {
    case LAYER_ACTIONS.TOGGLE_LAYER:
      return {
        ...state,
        layerStates: {
          ...state.layerStates,
          [action.payload]: !state.layerStates[action.payload]
        }
      };
    
    case LAYER_ACTIONS.SET_LAYER_STATE:
      return {
        ...state,
        layerStates: {
          ...state.layerStates,
          [action.payload.layerId]: action.payload.enabled
        }
      };
    
    case LAYER_ACTIONS.TOGGLE_SECTION:
      return {
        ...state,
        expandedSections: {
          ...state.expandedSections,
          [action.payload]: !state.expandedSections[action.payload]
        }
      };
    
    case LAYER_ACTIONS.SET_LAYER_REFRESHING:
      return {
        ...state,
        layerRefreshing: {
          ...state.layerRefreshing,
          [action.payload.layerId]: action.payload.refreshing
        }
      };
    
    case LAYER_ACTIONS.SET_LAYER_DOWNLOADING:
      return {
        ...state,
        layerDownloading: {
          ...state.layerDownloading,
          [action.payload.layerId]: action.payload.downloading
        }
      };
    
    case LAYER_ACTIONS.RESET_LAYERS:
      const resetLayerStates = {};
      Object.values(LAYER_SECTIONS).forEach(section => {
        section.layers.forEach(layer => {
          resetLayerStates[layer.id] = false;
        });
      });
      return {
        ...state,
        layerStates: resetLayerStates
      };
    
    case LAYER_ACTIONS.INITIALIZE_LAYERS:
      return {
        ...state,
        layerStates: action.payload
      };
    
    default:
      return state;
  }
};

// Context
const LayerContext = createContext();

// Provider component
export const LayerProvider = ({ children }) => {
  const [state, dispatch] = useReducer(layerReducer, initialState);

  const toggleLayer = (layerId) => {
    dispatch({ type: LAYER_ACTIONS.TOGGLE_LAYER, payload: layerId });
  };

  const setLayerState = (layerId, enabled) => {
    dispatch({ 
      type: LAYER_ACTIONS.SET_LAYER_STATE, 
      payload: { layerId, enabled } 
    });
  };

  const toggleSection = (sectionName) => {
    dispatch({ type: LAYER_ACTIONS.TOGGLE_SECTION, payload: sectionName });
  };

  const setLayerRefreshing = (layerId, refreshing) => {
    dispatch({ 
      type: LAYER_ACTIONS.SET_LAYER_REFRESHING, 
      payload: { layerId, refreshing } 
    });
  };

  const setLayerDownloading = (layerId, downloading) => {
    dispatch({ 
      type: LAYER_ACTIONS.SET_LAYER_DOWNLOADING, 
      payload: { layerId, downloading } 
    });
  };

  const resetLayers = () => {
    dispatch({ type: LAYER_ACTIONS.RESET_LAYERS });
  };

  const initializeLayers = (layerStates) => {
    dispatch({ type: LAYER_ACTIONS.INITIALIZE_LAYERS, payload: layerStates });
  };

  const value = {
    // State
    layerStates: state.layerStates,
    expandedSections: state.expandedSections,
    layerRefreshing: state.layerRefreshing,
    layerDownloading: state.layerDownloading,
    
    // Actions
    toggleLayer,
    setLayerState,
    toggleSection,
    setLayerRefreshing,
    setLayerDownloading,
    resetLayers,
    initializeLayers
  };

  return (
    <LayerContext.Provider value={value}>
      {children}
    </LayerContext.Provider>
  );
};

// Hook to use the layer context
export const useLayer = () => {
  const context = useContext(LayerContext);
  if (!context) {
    throw new Error('useLayer must be used within a LayerProvider');
  }
  return context;
};

export default LayerContext;