"""
Application Configuration
Centralized configuration management with environment variable support and validation.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field, validator
import logging

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Info
    app_name: str = Field(default="Stirling Bridge LandDev API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")
    
    # Database Configuration
    mongo_url: str = Field(default="mongodb://localhost:27017", env="MONGO_URL")
    database_name: str = Field(default="stirling_landdev", env="DB_NAME")
    
    # API Timeouts and Limits
    api_timeout: float = Field(default=30.0, env="API_TIMEOUT")
    cache_ttl_seconds: int = Field(default=300, env="CACHE_TTL_SECONDS")
    max_boundaries_per_request: int = Field(default=1000, env="MAX_BOUNDARIES_PER_REQUEST")
    
    # External API Configuration
    arcgis_client_id: Optional[str] = Field(default=None, env="ARCGIS_CLIENT_ID")
    arcgis_client_secret: Optional[str] = Field(default=None, env="ARCGIS_CLIENT_SECRET")
    afrigis_api_key: Optional[str] = Field(default=None, env="AFRIGIS_API_KEY")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # File Storage Configuration
    temp_file_dir: str = Field(default="/tmp", env="TEMP_FILE_DIR")
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    
    # CAD Generation Configuration
    cad_coordinate_system: str = Field(default="UTM Zone 35S", env="CAD_COORDINATE_SYSTEM")
    cad_units: str = Field(default="Meters", env="CAD_UNITS")
    
    # API Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=3600, env="RATE_LIMIT_WINDOW_SECONDS")
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed_environments = ['development', 'staging', 'production', 'testing']
        if v not in allowed_environments:
            raise ValueError(f'Environment must be one of: {allowed_environments}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('cors_allow_methods', pre=True)
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(',')]
        return v
    
    @validator('cors_allow_headers', pre=True)
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(',')]
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == 'development'
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == 'production'
    
    @property
    def has_arcgis_credentials(self) -> bool:
        """Check if ArcGIS credentials are configured"""
        return bool(self.arcgis_client_id and self.arcgis_client_secret)
    
    @property
    def has_afrigis_credentials(self) -> bool:
        """Check if AfriGIS credentials are configured"""
        return bool(self.afrigis_api_key)
    
    def setup_logging(self):
        """Configure application logging"""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format=self.log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('stirling_bridge.log') if self.is_production else None
            ]
        )
        
        # Suppress noisy third-party loggers in production
        if self.is_production:
            logging.getLogger('httpx').setLevel(logging.WARNING)
            logging.getLogger('motor').setLevel(logging.WARNING)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

class APIEndpoints:
    """API endpoint configuration"""
    
    # CSG API
    CSG_BASE_URL = "https://dffeportal.environment.gov.za/hosting/rest/services/CSG_Cadaster/CSG_Cadastral_Data/MapServer"
    
    # SANBI BGIS API
    SANBI_BASE_URL = "https://bgismaps.sanbi.org/server/rest/services"
    SANBI_SERVICES = {
        "contours": {
            "url": f"{SANBI_BASE_URL}/BGIS_Projects/Basedata_rivers_contours/MapServer",
            "layers": {
                "contours_north": 6,
                "contours_south": 7,
                "rivers": 4
            }
        },
        "conservation_gauteng": {
            "url": f"{SANBI_BASE_URL}/2024_Gauteng_CBA_Map/MapServer",
            "layers": {
                "protected_areas": 0
            }
        }
    }
    
    # AfriGIS API
    AFRIGIS_BASE_URL = "https://ogc.afrigis.co.za/mapservice"

class LayerConfiguration:
    """CAD layer configuration and color schemes"""
    
    LAYER_COLORS = {
        "Farm Portions": "#00FF00",      # Green
        "Erven": "#0000FF",              # Blue
        "Holdings": "#FFFF00",           # Yellow
        "Public Places": "#FF00FF",      # Magenta
        "Contours": "#8B4513",           # Brown
        "Water Bodies": "#00BFFF",       # Deep Sky Blue
        "Environmental Constraints": "#228B22",  # Forest Green
        "Roads": "#FF6347",              # Tomato Red
        "Administrative Boundaries": "#800080",  # Purple
        "Infrastructure": "#FFA500",     # Orange
        "Demographics": "#808080"        # Gray
    }
    
    LAYER_WEIGHTS = {
        "Farm Portions": 0.6,
        "Erven": 0.4,
        "Holdings": 0.5,
        "Public Places": 0.3,
        "Contours": 0.2,
        "Water Bodies": 0.8,
        "Environmental Constraints": 0.7,
        "Roads": 0.9,
        "Administrative Boundaries": 0.5,
        "Infrastructure": 0.6,
        "Demographics": 0.4
    }
    
    BOUNDARY_LAYERS = {
        "farm_portions": {"layer_id": 1, "name": "Farm Portions"},
        "erven": {"layer_id": 2, "name": "Erven"},
        "holdings": {"layer_id": 3, "name": "Holdings"},
        "public_places": {"layer_id": 4, "name": "Public Places"}
    }

# Global settings instance
settings = Settings()

# Setup logging on import
settings.setup_logging()
