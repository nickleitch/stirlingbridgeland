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

function App() {
  const [coordinates, setCoordinates] = useState({
    latitude: '',
    longitude: ''
  });
  const [projectName, setProjectName] = useState('');

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [showMap, setShowMap] = useState(false);
  const [mapLoading, setMapLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const mapRef = useRef();

  const handleCoordinateChange = (field, value) => {
    setCoordinates(prev => ({
      ...prev,
      [field]: value
    }));
    setError('');
  };

  const handleIdentifyLand = async () => {
    if (!coordinates.latitude || !coordinates.longitude) {
      setError('Please enter both latitude and longitude');
      return;
    }

    setLoading(true);
    setError('');
    setShowMap(false);

    try {
      const response = await fetch(`${BACKEND_URL}/api/identify-land`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          latitude: parseFloat(coordinates.latitude),
          longitude: parseFloat(coordinates.longitude),
          project_name: projectName || 'Land Development Project'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      
      // Show map if we have boundary data or valid coordinates
      if (data.boundaries && data.boundaries.length > 0) {
        setMapLoading(true);
        setTimeout(() => {
          setShowMap(true);
          setMapLoading(false);
        }, 500); // Small delay to ensure smooth transition
      } else if (data.coordinates) {
        // Show map even without boundaries if coordinates are valid
        setMapLoading(true);
        setTimeout(() => {
          setShowMap(true);
          setMapLoading(false);
        }, 500);
      }
    } catch (err) {
      setError(`Failed to identify land: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFiles = async () => {
    if (!result) {
      setError('Please complete land identification first');
      return;
    }

    setDownloading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/download-files/${result.project_id}`, {
        method: 'GET'
      });

      if (!response.ok) {
        throw new Error('Failed to generate files');
      }

      // Get the filename from the response headers or use a default
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `land_data_${result.project_id}.zip`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (err) {
      setError(`Failed to download files: ${err.message}`);
    } finally {
      setDownloading(false);
    }
  };

  // Convert CSG geometry to Leaflet polygon coordinates
  const convertGeometryToLeaflet = (geometry) => {
    if (!geometry || !geometry.rings) return [];
    
    return geometry.rings.map(ring => 
      ring.map(coord => [coord[1], coord[0]]) // Leaflet expects [lat, lng]
    );
  };

  // Get color for different boundary types
  const getLayerColor = (layerType) => {
    const colorMap = {
      "Farm Portions": "#00FF00", 
      "Erven": "#0000FF",
      "Holdings": "#FFFF00",
      "Public Places": "#FF00FF"
    };
    return colorMap[layerType] || "#000000";
  };

  // Get map bounds to fit all boundaries
  const getMapBounds = () => {
    if (!result || !result.boundaries || result.boundaries.length === 0) {
      // Default to search coordinates
      const lat = parseFloat(coordinates.latitude);
      const lng = parseFloat(coordinates.longitude);
      
      // Check if coordinates are valid
      if (isNaN(lat) || isNaN(lng)) {
        return [[-26.2041, 28.0473], [-26.2041, 28.0473]]; // Default to Johannesburg
      }
      
      return [[lat - 0.01, lng - 0.01], [lat + 0.01, lng + 0.01]];
    }

    let minLat = Infinity, maxLat = -Infinity;
    let minLng = Infinity, maxLng = -Infinity;

    result.boundaries.forEach(boundary => {
      if (boundary.geometry && boundary.geometry.rings) {
        boundary.geometry.rings[0].forEach(coord => {
          const [lng, lat] = coord;
          minLat = Math.min(minLat, lat);
          maxLat = Math.max(maxLat, lat);
          minLng = Math.min(minLng, lng);
          maxLng = Math.max(maxLng, lng);
        });
      }
    });

    // Add some padding
    const padding = 0.001;
    return [
      [minLat - padding, minLng - padding],
      [maxLat + padding, maxLng + padding]
    ];
  };

  // Extract farm information from boundaries
  const getFarmInfo = () => {
    if (!result || !result.boundaries) return [];
    
    const farmInfo = [];
    const farmMap = new Map();

    result.boundaries.forEach(boundary => {
      if (boundary.properties) {
        const farmName = boundary.properties.FARMNAME || 
                        boundary.properties.NAME || 
                        boundary.properties.FARM_NAME || 
                        boundary.properties.PropertyName ||
                        'Unknown Farm';
        
        const farmNumber = boundary.properties.FARM_NO || 
                          boundary.properties.FARM_NUMBER ||
                          boundary.properties.PARCEL_NO ||
                          'N/A';
        
        const size = boundary.properties.AREA || 
                    boundary.properties.HECTARES || 
                    boundary.properties.SIZE ||
                    boundary.properties.EXTENT ||
                    null;

        const key = `${farmName}_${farmNumber}`;
        
        if (!farmMap.has(key)) {
          farmMap.set(key, {
            name: farmName,
            number: farmNumber,
            size: size,
            layerType: boundary.layer_type,
            color: getLayerColor(boundary.layer_type),
            count: 1
          });
        } else {
          farmMap.get(key).count++;
        }
      }
    });

    return Array.from(farmMap.values()).sort((a, b) => a.name.localeCompare(b.name));
  };

  const BoundaryCard = ({ boundary }) => (
    <div className="bg-gray-50 p-4 rounded-lg border-l-4" 
         style={{ borderLeftColor: getLayerColor(boundary.layer_type) }}>
      <h4 className="font-semibold text-gray-800">{boundary.layer_name}</h4>
      <p className="text-sm text-gray-600 mb-2">Type: {boundary.layer_type}</p>
      <p className="text-sm text-gray-600">Source: {boundary.source_api}</p>
      
      {boundary.properties && Object.keys(boundary.properties).length > 0 && (
        <div className="mt-2">
          <p className="text-xs font-medium text-gray-700">Properties:</p>
          <div className="text-xs text-gray-600 max-h-20 overflow-y-auto">
            {Object.entries(boundary.properties).slice(0, 3).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="font-medium">{key}:</span>
                <span className="truncate ml-2">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const MapComponent = () => {
    const bounds = getMapBounds();
    const searchLat = parseFloat(coordinates.latitude);
    const searchLng = parseFloat(coordinates.longitude);

    // Check if coordinates are valid before rendering map
    if (isNaN(searchLat) || isNaN(searchLng)) {
      return (
        <div className="bg-white rounded-xl shadow-xl p-6 mb-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">📍 Map Visualization</h3>
          <div className="h-96 w-full rounded-lg border-2 border-gray-200 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <div className="text-gray-400 text-6xl mb-4">🗺️</div>
              <p className="text-gray-600">Invalid coordinates provided</p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="bg-white rounded-xl shadow-xl p-6 mb-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-4">📍 Boundary Map Visualization</h3>
        <div className="h-96 w-full rounded-lg overflow-hidden border-2 border-gray-200">
          <MapContainer
            bounds={bounds}
            style={{ height: '100%', width: '100%' }}
            ref={mapRef}
          >
            {/* Satellite Imagery Base Layer */}
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
              maxZoom={19}
            />
            
            {/* Optional: Street overlay for reference */}
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}"
              attribution=''
              opacity={0.3}
              maxZoom={19}
            />
            
            {/* Search point marker */}
            <Marker position={[searchLat, searchLng]}>
              <Popup>
                <div className="text-center">
                  <strong>Search Location</strong><br/>
                  {searchLat.toFixed(6)}, {searchLng.toFixed(6)}
                </div>
              </Popup>
            </Marker>

            {/* Boundary polygons */}
            {result && result.boundaries && result.boundaries.map((boundary, index) => {
              const polygonCoords = convertGeometryToLeaflet(boundary.geometry);
              const color = getLayerColor(boundary.layer_type);
              
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
                      {boundary.properties && boundary.properties.PARCEL_NO && (
                        <><br/><small>Parcel: {boundary.properties.PARCEL_NO}</small></>
                      )}
                      {boundary.properties && boundary.properties.FARMNAME && (
                        <><br/><small>Farm: {boundary.properties.FARMNAME}</small></>
                      )}
                    </div>
                  </Popup>
                </Polygon>
              );
            })}
          </MapContainer>
        </div>

        {/* Map Legend */}
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-gray-800 mb-3">🛰️ Satellite Map Legend</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries({
              "Parent Farm Boundaries": "#FF0000",
              "Farm Portions": "#00FF00", 
              "Erven": "#0000FF",
              "Holdings": "#FFFF00",
              "Public Places": "#FF00FF"
            }).map(([type, color]) => (
              <div key={type} className="flex items-center">
                <div 
                  className="w-4 h-4 rounded border-2 mr-2"
                  style={{ backgroundColor: color, borderColor: color }}
                ></div>
                <span className="text-sm text-gray-700">{type}</span>
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center">
            <div className="w-4 h-4 mr-2">📍</div>
            <span className="text-sm text-gray-700">Search Location</span>
          </div>
          <div className="mt-2 text-xs text-gray-600">
            🛰️ High-resolution satellite imagery with street overlays for enhanced land analysis
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-gradient-to-r from-green-600 to-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">SB</span>
              </div>
              <div className="ml-4">
                <h1 className="text-2xl font-bold text-gray-900">Stirling Bridge LandDev</h1>
                <p className="text-sm text-gray-500">Land Identification & Development Platform</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Identify Land for Development
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Enter coordinates to retrieve comprehensive boundary data and cadastral information 
            for South African land development projects
          </p>
        </div>

        {/* Input Form */}
        <div className="bg-white rounded-xl shadow-xl p-8 mb-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">Project Details</h3>
          
          <div className="grid grid-cols-1 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Project Name
              </label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="Enter project name"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <h4 className="text-lg font-semibold text-gray-800 mb-4">Land Coordinates</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Latitude (Decimal Degrees)
              </label>
              <input
                type="number"
                step="any"
                value={coordinates.latitude}
                onChange={(e) => handleCoordinateChange('latitude', e.target.value)}
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
                value={coordinates.longitude}
                onChange={(e) => handleCoordinateChange('longitude', e.target.value)}
                placeholder="28.0473"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={handleIdentifyLand}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 text-white px-8 py-4 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all transform hover:scale-105 disabled:opacity-50 disabled:transform-none"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></div>
                  Identifying Land...
                </div>
              ) : (
                '🛰️ Identify Land & Show Satellite Map'
              )}
            </button>
            
            {result && result.boundaries && result.boundaries.length > 0 && (
              <button
                onClick={handleDownloadFiles}
                disabled={downloading}
                className="bg-blue-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-blue-700 transition-all transform hover:scale-105 disabled:opacity-50 disabled:transform-none"
              >
                {downloading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></div>
                    Preparing Files...
                  </div>
                ) : (
                  '📁 Download Land Data Files'
                )}
              </button>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-8">
            {error}
          </div>
        )}

        {/* Map Loading State */}
        {mapLoading && (
          <div className="bg-white rounded-xl shadow-xl p-6 mb-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">📍 Loading Map...</h3>
            <div className="h-96 w-full rounded-lg border-2 border-gray-200 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent mx-auto mb-4"></div>
                <p className="text-gray-600">Preparing map visualization...</p>
              </div>
            </div>
          </div>
        )}

        {/* Map Visualization */}
        {showMap && result && !mapLoading && (
          <MapComponent />
        )}

        {/* Results */}
        {result && (
          <div className="bg-white rounded-xl shadow-xl p-8">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">Land Identification Results</h3>
                <p className="text-gray-600">Project ID: {result.project_id}</p>
                <p className="text-gray-600">
                  Coordinates: {result.coordinates.latitude}, {result.coordinates.longitude}
                </p>
              </div>
              <div className={`px-4 py-2 rounded-full text-sm font-medium ${
                result.status === 'completed' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {result.status === 'completed' ? 'Data Retrieved' : 'No Data Found'}
              </div>
            </div>

            {result.boundaries && result.boundaries.length > 0 ? (
              <div>
                <h4 className="text-lg font-semibold text-gray-800 mb-4">
                  Boundary Layers Found ({result.boundaries.length})
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {result.boundaries.map((boundary, index) => (
                    <BoundaryCard key={index} boundary={boundary} />
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-gray-400 text-6xl mb-4">📍</div>
                <h4 className="text-lg font-semibold text-gray-600 mb-2">No Boundary Data Found</h4>
                <p className="text-gray-500">
                  No cadastral or boundary information was found for the specified coordinates.
                  Please verify the coordinates and try again.
                </p>
              </div>
            )}

            {result.files_generated && result.files_generated.length > 0 && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h4 className="text-lg font-semibold text-gray-800 mb-3">Files Ready for Download</h4>
                <div className="flex flex-wrap gap-2 mb-4">
                  {result.files_generated.map((file, index) => (
                    <span key={index} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                      {file}
                    </span>
                  ))}
                </div>
                <p className="text-sm text-gray-600">
                  Click "Download Land Data Files" to get a ZIP file containing all boundary data, 
                  DWG-ready files, and project information for your development team.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Info Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <span className="text-green-600 text-2xl">🛰️</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Satellite Map View</h3>
            <p className="text-gray-600">
              High-resolution satellite imagery shows actual terrain, vegetation, buildings, and land features for comprehensive analysis
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <span className="text-blue-600 text-2xl">📐</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">DWG Ready</h3>
            <p className="text-gray-600">
              Automatically format boundary data for CAD software with proper geotagged layers
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <span className="text-purple-600 text-2xl">📁</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Download Ready Files</h3>
            <p className="text-gray-600">
              Download organized boundary files, DWG-ready data, and project information for your development team
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
