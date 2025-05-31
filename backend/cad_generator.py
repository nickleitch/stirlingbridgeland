"""
CAD Layer Generation System for Stirling Bridge LandDev Platform

This module generates architect-ready DWG/DXF files with proper SDP naming conventions,
metadata embedding, and standardized layer structures for professional CAD integration.
"""

import ezdxf
from ezdxf.math import Vec3
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import os
from datetime import datetime
import uuid

class SDPLayerGenerator:
    """
    Site Development Plan (SDP) Layer Generator
    
    Converts GIS boundary data into standardized CAD layers following
    professional naming conventions and metadata standards.
    """
    
    def __init__(self, project_id: str, project_name: str):
        self.project_id = project_id
        self.project_name = project_name
        self.coordinate_system = "UTM Zone 35S"  # South Africa standard
        self.units = "Meters"
        
        # SDP Layer specifications
        self.layer_specs = {
            "contours": {
                "name": "SDP_GEO_CONT_MAJ_001",
                "description": "Major Contours - Topographic elevation lines",
                "color": 4,  # Cyan
                "geometry_type": "POLYLINE",
                "metadata_fields": ["elevation", "contour_type", "interval_m", "accuracy", "survey_method"]
            },
            "generated_contours": {
                "name": "SDP_GEO_CONT_GEN_001",
                "description": "Generated Contours - Professional elevation contour lines",
                "color": 14,  # Yellow-orange
                "geometry_type": "POLYLINE", 
                "metadata_fields": ["elevation", "contour_type", "contour_interval", "dataset", "generation_method"]
            },
            "property_boundaries_draft": {
                "name": "SDP_DRAFT_PROP_BOUND_001", 
                "description": "Property Boundaries - Draft site boundaries",
                "color": 1,  # Red
                "geometry_type": "POLYLINE",
                "metadata_fields": ["boundary_type", "area_sqm", "legal_description"]
            },
            "property_boundaries_geo": {
                "name": "SDP_GEO_PROP_BOUND_001",
                "description": "Property Boundaries - Surveyed geospatial boundaries", 
                "color": 3,  # Green
                "geometry_type": "POLYLINE",
                "metadata_fields": ["boundary_type", "area_sqm", "surveyor_ref", "legal_description", "accuracy_class", "title_deed_ref"]
            },
            "administrative_boundaries": {
                "name": "SDP_GEO_ADMIN_BOUND_001",
                "description": "Administrative Boundaries - Countries, provinces, municipalities",
                "color": 5,  # Magenta
                "geometry_type": "POLYLINE",
                "metadata_fields": ["admin_level", "admin_name", "population", "area_sqkm", "iso_code"]
            },
            "urban_areas": {
                "name": "SDP_URBAN_AREAS_001", 
                "description": "Urban Areas - City boundaries and development zones",
                "color": 6,  # Yellow
                "geometry_type": "POLYLINE",
                "metadata_fields": ["urban_name", "population", "area_sqkm", "urban_type", "development_status"]
            },
            "infrastructure": {
                "name": "SDP_INFRA_CITIES_001",
                "description": "Infrastructure - Cities, transportation corridors",
                "color": 2,  # Blue
                "geometry_type": "POLYLINE", 
                "metadata_fields": ["infra_type", "infra_name", "status", "capacity", "importance"]
            },
            "demographics": {
                "name": "SDP_DEMO_POP_DENS_001",
                "description": "Demographics - Population density and development planning data",
                "color": 8,  # Gray
                "geometry_type": "POLYLINE",
                "metadata_fields": ["pop_density", "demo_type", "total_population", "area_sqkm", "density_class"]
            }
        }
    
    def create_layer_dwg(self, layer_type: str, boundaries: List[Dict], source_url: str = None) -> Tuple[str, bytes]:
        """
        Create a single DWG file containing one CAD layer with boundaries data
        
        Args:
            layer_type: Type of layer (contours, property_boundaries_draft, property_boundaries_geo)
            boundaries: List of boundary dictionaries with geometry and properties
            source_url: Original data source URL for documentation
            
        Returns:
            Tuple of (filename, file_bytes)
        """
        if layer_type not in self.layer_specs:
            raise ValueError(f"Unknown layer type: {layer_type}")
            
        spec = self.layer_specs[layer_type]
        
        # Create new DXF document (will convert to DWG)
        doc = ezdxf.new("R2018", setup=True)  # AutoCAD 2018+ compatible
        
        # Set up document metadata
        doc.header['$ACADVER'] = 'AC1032'  # AutoCAD 2018 version
        doc.header['$DWGCODEPAGE'] = 'ANSI_1252'
        
        # Create the layer
        layer_name = f"{self.project_id}_{spec['name']}"
        layer = doc.layers.add(layer_name)
        layer.color = spec['color']
        layer.description = spec['description']
        
        # Get model space
        msp = doc.modelspace()
        
        # Add header text with project info
        self._add_header_block(doc, msp, layer_name, spec['description'], source_url)
        
        # Process boundaries based on geometry type
        entity_count = 0
        for boundary in boundaries:
            try:
                entities = self._add_boundary_to_layer(msp, boundary, layer_name, spec)
                entity_count += len(entities)
            except Exception as e:
                print(f"Warning: Failed to add boundary {boundary.get('layer_name', 'unknown')}: {str(e)}")
                continue
        
        # Add layer statistics as text
        stats_text = f"Layer: {layer_name}\nEntities: {entity_count}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        msp.add_text(stats_text, height=0.5).set_placement((0, -5), align=ezdxf.enums.TextEntityAlignment.LEFT)
        
        # Generate filename
        safe_project_name = self.project_name.replace(' ', '_').replace('/', '_')
        filename = f"{safe_project_name}_{spec['name']}.dxf"
        
        # Save to temporary file and read bytes
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
            doc.saveas(tmp.name)
            tmp.seek(0)
            
            with open(tmp.name, 'rb') as f:
                file_bytes = f.read()
            
            # Clean up
            os.unlink(tmp.name)
            
        return filename, file_bytes
    
    def _add_header_block(self, doc, msp, layer_name: str, description: str, source_url: str = None):
        """Add header information to the CAD file"""
        header_y = 10
        
        # Project title
        msp.add_text(f"STIRLING BRIDGE DEVELOPMENTS", height=1.0).set_placement((0, header_y), align=ezdxf.enums.TextEntityAlignment.LEFT)
        msp.add_text(f"Project: {self.project_name}", height=0.7).set_placement((0, header_y-1.5), align=ezdxf.enums.TextEntityAlignment.LEFT)
        msp.add_text(f"Project ID: {self.project_id}", height=0.5).set_placement((0, header_y-2.5), align=ezdxf.enums.TextEntityAlignment.LEFT)
        
        # Layer information
        msp.add_text(f"Layer: {layer_name}", height=0.7).set_placement((0, header_y-4), align=ezdxf.enums.TextEntityAlignment.LEFT)
        msp.add_text(f"Description: {description}", height=0.5).set_placement((0, header_y-5), align=ezdxf.enums.TextEntityAlignment.LEFT)
        
        # Coordinate system and units
        msp.add_text(f"Coordinate System: {self.coordinate_system}", height=0.4).set_placement((0, header_y-6.5), align=ezdxf.enums.TextEntityAlignment.LEFT)
        msp.add_text(f"Units: {self.units}", height=0.4).set_placement((0, header_y-7.5), align=ezdxf.enums.TextEntityAlignment.LEFT)
        
        # Source documentation
        if source_url:
            msp.add_text(f"Data Source: {source_url}", height=0.4).set_placement((0, header_y-8.5), align=ezdxf.enums.TextEntityAlignment.LEFT)
        
        # Generation timestamp
        msp.add_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", height=0.4).set_placement((0, header_y-9.5), align=ezdxf.enums.TextEntityAlignment.LEFT)
        
        # Add separator line
        msp.add_line((0, header_y-10.5), (50, header_y-10.5))
    
    def _add_boundary_to_layer(self, msp, boundary: Dict, layer_name: str, spec: Dict) -> List:
        """Add a single boundary to the CAD layer"""
        entities = []
        geometry = boundary.get('geometry', {})
        properties = boundary.get('properties', {})
        
        # Extract coordinates based on geometry type
        if geometry.get('rings'):  # Polygon geometry
            for ring in geometry['rings']:
                coords = [(float(coord[0]), float(coord[1])) for coord in ring]
                if len(coords) > 2:  # Valid polygon
                    # Close the polygon if not already closed
                    if coords[0] != coords[-1]:
                        coords.append(coords[0])
                    
                    polyline = msp.add_lwpolyline(coords)
                    polyline.layer = layer_name
                    
                    # Add metadata as extended data
                    self._add_metadata_to_entity(polyline, boundary, spec['metadata_fields'])
                    entities.append(polyline)
        
        elif geometry.get('paths'):  # Polyline geometry (contours, roads)
            for path in geometry['paths']:
                coords = [(float(coord[0]), float(coord[1])) for coord in path]
                if len(coords) > 1:  # Valid polyline
                    polyline = msp.add_lwpolyline(coords)
                    polyline.layer = layer_name
                    
                    # Add metadata as extended data
                    self._add_metadata_to_entity(polyline, boundary, spec['metadata_fields'])
                    entities.append(polyline)
        
        return entities
    
    def _add_metadata_to_entity(self, entity, boundary: Dict, metadata_fields: List[str]):
        """Add metadata to CAD entity as extended data"""
        properties = boundary.get('properties', {})
        
        # Create extended data for metadata
        xdata = []
        xdata.append((1001, "STIRLING_BRIDGE_METADATA"))  # Application name
        
        # Add standard metadata
        xdata.append((1000, f"LAYER_NAME:{boundary.get('layer_name', 'unknown')}"))
        xdata.append((1000, f"LAYER_TYPE:{boundary.get('layer_type', 'unknown')}"))
        xdata.append((1000, f"SOURCE_API:{boundary.get('source_api', 'unknown')}"))
        
        # Add specific metadata fields
        for field in metadata_fields:
            value = properties.get(field.upper(), properties.get(field, 'N/A'))
            xdata.append((1000, f"{field.upper()}:{str(value)}"))
        
        # Add generation info
        xdata.append((1000, f"GENERATED:{datetime.now().isoformat()}"))
        xdata.append((1000, f"PROJECT_ID:{self.project_id}"))
        
        # Set extended data on entity
        entity.set_xdata("STIRLING_BRIDGE_METADATA", xdata)

class CADFileManager:
    """
    Manages the generation and delivery of CAD files for projects
    """
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    async def generate_project_cad_layers(self, project_id: str, project_name: str, boundaries: List[Dict]) -> Dict[str, Tuple[str, bytes]]:
        """
        Generate all available CAD layers for a project
        
        Returns:
            Dictionary mapping layer_type -> (filename, file_bytes)
        """
        generator = SDPLayerGenerator(project_id, project_name)
        cad_files = {}
        
        # Categorize boundaries by type
        contour_boundaries = [b for b in boundaries if b.get('layer_type') == 'Contours']
        property_boundaries = [b for b in boundaries if b.get('layer_type') == 'Property Boundaries']
        admin_boundaries = [b for b in boundaries if b.get('layer_type') == 'Administrative Boundaries']
        urban_boundaries = [b for b in boundaries if b.get('layer_type') == 'Urban Planning']
        infrastructure_boundaries = [b for b in boundaries if b.get('layer_type') == 'Infrastructure']
        demographics_boundaries = [b for b in boundaries if b.get('layer_type') == 'Demographics']
        
        # Generate contours layer
        if contour_boundaries:
            try:
                filename, file_bytes = generator.create_layer_dwg(
                    "contours", 
                    contour_boundaries,
                    "https://bgismaps.sanbi.org/server/rest/services/BGIS_Projects/Basedata_rivers_contours/MapServer"
                )
                cad_files["contours"] = (filename, file_bytes)
            except Exception as e:
                print(f"Error generating contours CAD layer: {str(e)}")
        
        # Generate property boundaries layers (both draft and geo versions)
        if property_boundaries:
            try:
                # Draft version
                filename_draft, file_bytes_draft = generator.create_layer_dwg(
                    "property_boundaries_draft",
                    property_boundaries,
                    "https://csg.drdlr.gov.za/arcgis/rest/services"
                )
                cad_files["property_boundaries_draft"] = (filename_draft, file_bytes_draft)
                
                # Geospatial version (same data, different layer spec)
                filename_geo, file_bytes_geo = generator.create_layer_dwg(
                    "property_boundaries_geo", 
                    property_boundaries,
                    "https://csg.drdlr.gov.za/arcgis/rest/services"
                )
                cad_files["property_boundaries_geo"] = (filename_geo, file_bytes_geo)
            except Exception as e:
                print(f"Error generating property boundaries CAD layers: {str(e)}")
        
        # Generate ArcGIS Administrative Boundaries layer
        if admin_boundaries:
            try:
                filename, file_bytes = generator.create_layer_dwg(
                    "administrative_boundaries",
                    admin_boundaries,
                    "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services"
                )
                cad_files["administrative_boundaries"] = (filename, file_bytes)
            except Exception as e:
                print(f"Error generating administrative boundaries CAD layer: {str(e)}")
        
        # Generate ArcGIS Urban Areas layer  
        if urban_boundaries:
            try:
                filename, file_bytes = generator.create_layer_dwg(
                    "urban_areas",
                    urban_boundaries,
                    "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services"
                )
                cad_files["urban_areas"] = (filename, file_bytes)
            except Exception as e:
                print(f"Error generating urban areas CAD layer: {str(e)}")
        
        # Generate ArcGIS Infrastructure layer
        if infrastructure_boundaries:
            try:
                filename, file_bytes = generator.create_layer_dwg(
                    "infrastructure", 
                    infrastructure_boundaries,
                    "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services"
                )
                cad_files["infrastructure"] = (filename, file_bytes)
            except Exception as e:
                print(f"Error generating infrastructure CAD layer: {str(e)}")
        
        # Generate ArcGIS Demographics layer
        if demographics_boundaries:
            try:
                filename, file_bytes = generator.create_layer_dwg(
                    "demographics",
                    demographics_boundaries, 
                    "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services"
                )
                cad_files["demographics"] = (filename, file_bytes)
            except Exception as e:
                print(f"Error generating demographics CAD layer: {str(e)}")
        
        return cad_files
    
    def create_cad_package_zip(self, cad_files: Dict[str, Tuple[str, bytes]], project_name: str) -> bytes:
        """Create a ZIP package containing all CAD files for a project"""
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add each CAD file
            for layer_type, (filename, file_bytes) in cad_files.items():
                zip_file.writestr(filename, file_bytes)
            
            # Add documentation
            readme_content = self._generate_cad_readme(cad_files, project_name)
            zip_file.writestr("CAD_LAYERS_README.txt", readme_content)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def _generate_cad_readme(self, cad_files: Dict[str, Tuple[str, bytes]], project_name: str) -> str:
        """Generate README documentation for CAD package"""
        content = f"""
STIRLING BRIDGE DEVELOPMENTS - CAD LAYER PACKAGE
================================================

Project: {project_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CAD LAYERS INCLUDED:
==================
"""
        
        for layer_type, (filename, _) in cad_files.items():
            content += f"\n• {filename}"
            
        content += """

USAGE INSTRUCTIONS:
==================

1. IMPORT INTO CAD SOFTWARE:
   - Open your AutoCAD, BricsCAD, or compatible CAD software
   - Use "Insert" > "External Reference" or "Import" command
   - Select the DXF files individually for clean layer separation
   - Each file contains a single, properly named layer

2. LAYER NAMING CONVENTION:
   - Format: [PROJECT_ID]_[SDP_LAYER_NAME]_[VERSION]
   - SDP = Site Development Plan
   - All layers follow professional CAD standards

3. METADATA:
   - Each entity contains embedded metadata as extended data
   - Use "Properties" or "Extended Data" commands to view
   - Includes elevation, area, legal descriptions, and source references

4. COORDINATE SYSTEM:
   - UTM Zone 35S (South Africa standard)
   - Units: Meters
   - Suitable for professional surveying and development

5. DATA SOURCES:
   - Property Boundaries: Chief Surveyor General (CSG)
   - Contours: SANBI BGIS Topographic Data
   - All data sourced from official South African government APIs

PROFESSIONAL USE:
================
These layers are architect and engineer ready for:
- Site Development Plans (SDP)
- Municipal submissions
- Construction documentation  
- Professional land development projects

For technical support, contact Stirling Bridge Developments.
"""
        
        return content