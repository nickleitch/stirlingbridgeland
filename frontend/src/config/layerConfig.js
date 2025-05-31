/**
 * Layer Configuration
 * Centralized configuration for all map layers and sections
 */

export const LAYER_SECTIONS = {
  "Base Data": {
    color: "#3B82F6",
    layers: [
      { id: "property_boundaries", name: "Property Boundaries", type: "Farm Portions", color: "#FF4500" },
      { id: "zoning_designations", name: "Zoning Designations", type: "Zoning", color: "#9932CC" },
      { id: "roads_existing", name: "Roads Existing", type: "Roads", color: "#FF6347" },
      { id: "generated_contours", name: "Generated Contours", type: "Generated Contours", color: "#A0522D", generateable: true },
      { id: "water_bodies", name: "Water Bodies", type: "Water Bodies", color: "#00BFFF" },
      { id: "labels_primary", name: "Labels Primary", type: "Labels", color: "#2F4F4F" },
      { id: "survey_control", name: "Survey Control", type: "Survey", color: "#DC143C" },
      { id: "coordinate_grid", name: "Coordinate Grid", type: "Grid", color: "#808080" },
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
      { id: "disability_access", name: "Disability Access", type: "Accessibility", color: "#4169E1", stage: "SDP 4" }
    ]
  },
  "Final SDP": {
    color: "#7C3AED",
    layers: [
      { id: "construction_staging", name: "Construction Staging", type: "Construction", color: "#F4A460", stage: "Final SDP" },
      { id: "landscaping_zones", name: "Landscaping Zones", type: "Landscaping", color: "#98FB98", stage: "Final SDP" },
      { id: "telecommunications", name: "Telecommunications Proposed", type: "Infrastructure", color: "#9370DB", stage: "Final SDP" },
      { id: "recreational_facilities", name: "Recreational Facilities", type: "Recreation", color: "#20B2AA", stage: "Final SDP" }
    ]
  }
};

export const LAYER_TYPE_MAPPING = {
  'Farm Portions': 'property_boundaries',
  'Erven': 'property_boundaries', 
  'Holdings': 'property_boundaries',
  'Public Places': 'property_boundaries',
  'Roads': 'roads_existing',
  'Generated Contours': 'generated_contours',
  'Water Bodies': 'water_bodies',
  'Environmental Constraints': 'environmental_constraints'
};

export const getLayerIdForBoundaryType = (boundaryType) => {
  const mapping = LAYER_TYPE_MAPPING[boundaryType];
  if (Array.isArray(mapping)) {
    return mapping[0]; // Return first option for arrays
  }
  return mapping;
};

export const getLayerConfig = (layerId) => {
  for (const section of Object.values(LAYER_SECTIONS)) {
    const layer = section.layers.find(l => l.id === layerId);
    if (layer) return layer;
  }
  return null;
};
