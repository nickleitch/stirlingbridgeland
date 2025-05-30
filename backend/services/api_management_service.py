"""
API Management Service
Handles API status monitoring, configuration, and management for navigation menu.
"""

import os
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from ..config.settings import settings
from .validation_service import APIStatus, APIConfiguration, APIConfigurationUpdate, APIStatusResponse

class APIManagementService:
    """Service for managing API configurations and status monitoring"""
    
    def __init__(self):
        self.api_configs = {
            "CSG": {
                "name": "Chief Surveyor General (CSG)",
                "description": "South African cadastral data",
                "config_fields": {},
                "test_url": "https://dffeportal.environment.gov.za/hosting/rest/services/CSG_Cadaster/CSG_Cadastral_Data/MapServer?f=json",
                "requires_auth": False
            },
            "SANBI_BGIS": {
                "name": "SANBI BGIS",
                "description": "Biodiversity and environmental data",
                "config_fields": {},
                "test_url": "https://bgismaps.sanbi.org/server/rest/services/BGIS_Projects/Basedata_rivers_contours/MapServer?f=json",
                "requires_auth": False
            },
            "ArcGIS_Online": {
                "name": "ArcGIS Online",
                "description": "ArcGIS online services and imagery",
                "config_fields": {
                    "client_id": {
                        "type": "string",
                        "required": True,
                        "description": "ArcGIS Client ID",
                        "env_var": "ARCGIS_CLIENT_ID"
                    },
                    "client_secret": {
                        "type": "password",
                        "required": True,
                        "description": "ArcGIS Client Secret",
                        "env_var": "ARCGIS_CLIENT_SECRET"
                    }
                },
                "test_url": "https://www.arcgis.com/sharing/rest/info?f=json",
                "requires_auth": True
            },
            "AfriGIS": {
                "name": "AfriGIS",
                "description": "African geographic information services",
                "config_fields": {
                    "api_key": {
                        "type": "password",
                        "required": True,
                        "description": "AfriGIS API Key",
                        "env_var": "AFRIGIS_API_KEY"
                    }
                },
                "test_url": "https://ogc.afrigis.co.za/mapservice",
                "requires_auth": True
            }
        }
    
    async def get_api_status(self) -> APIStatusResponse:
        """Get status of all configured APIs"""
        api_statuses = []
        timestamp = datetime.now().isoformat()
        
        for api_name, config in self.api_configs.items():
            status = await self._check_api_status(api_name, config)
            api_statuses.append(status)
        
        total_configured = sum(1 for status in api_statuses if status.is_configured)
        total_available = len(api_statuses)
        
        return APIStatusResponse(
            apis=api_statuses,
            total_configured=total_configured,
            total_available=total_available,
            timestamp=timestamp
        )
    
    async def _check_api_status(self, api_name: str, config: Dict[str, Any]) -> APIStatus:
        """Check the status of a specific API"""
        is_configured = self._is_api_configured(api_name, config)
        
        if not is_configured:
            return APIStatus(
                name=config["name"],
                is_configured=False,
                status="not_configured",
                last_check=datetime.now().isoformat(),
                error_message="API credentials not configured"
            )
        
        # Test API connection
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(config["test_url"])
                if response.status_code == 200:
                    status = "connected"
                    error_message = None
                else:
                    status = "error"
                    error_message = f"HTTP {response.status_code}: {response.text[:100]}"
        except Exception as e:
            status = "error"
            error_message = str(e)[:100]
        
        return APIStatus(
            name=config["name"],
            is_configured=is_configured,
            status=status,
            last_check=datetime.now().isoformat(),
            error_message=error_message
        )
    
    def _is_api_configured(self, api_name: str, config: Dict[str, Any]) -> bool:
        """Check if API is properly configured"""
        if not config.get("requires_auth", False):
            return True
        
        config_fields = config.get("config_fields", {})
        for field_name, field_config in config_fields.items():
            if field_config.get("required", False):
                env_var = field_config.get("env_var")
                if env_var and not os.getenv(env_var):
                    return False
        
        return True
    
    def get_api_configuration(self, api_name: str) -> Optional[APIConfiguration]:
        """Get configuration schema for a specific API"""
        if api_name not in self.api_configs:
            return None
        
        config = self.api_configs[api_name]
        return APIConfiguration(
            api_name=config["name"],
            config_fields=config.get("config_fields", {})
        )
    
    async def update_api_configuration(self, update: APIConfigurationUpdate) -> bool:
        """Update API configuration (save to environment/settings)"""
        api_key = None
        for key, config in self.api_configs.items():
            if config["name"] == update.api_name:
                api_key = key
                break
        
        if not api_key:
            return False
        
        config = self.api_configs[api_key]
        config_fields = config.get("config_fields", {})
        
        # Update environment variables (in a real implementation, 
        # this would update the .env file or external configuration store)
        updated = False
        for field_name, value in update.config_values.items():
            if field_name in config_fields:
                env_var = config_fields[field_name].get("env_var")
                if env_var:
                    os.environ[env_var] = value
                    updated = True
        
        return updated
    
    def get_all_api_configurations(self) -> List[APIConfiguration]:
        """Get configuration schemas for all APIs"""
        configurations = []
        for api_name, config in self.api_configs.items():
            if config.get("config_fields"):
                configurations.append(APIConfiguration(
                    api_name=config["name"],
                    config_fields=config["config_fields"]
                ))
        
        return configurations
    
    def get_api_documentation(self, api_name: str) -> Optional[Dict[str, Any]]:
        """Get documentation and setup instructions for an API"""
        if api_name not in self.api_configs:
            return None
        
        config = self.api_configs[api_name]
        return {
            "name": config["name"],
            "description": config["description"],
            "requires_auth": config.get("requires_auth", False),
            "config_fields": config.get("config_fields", {}),
            "setup_instructions": self._get_setup_instructions(api_name)
        }
    
    def _get_setup_instructions(self, api_name: str) -> Dict[str, Any]:
        """Get setup instructions for specific API"""
        instructions = {
            "ArcGIS_Online": {
                "steps": [
                    "1. Go to https://developers.arcgis.com/",
                    "2. Sign in or create an ArcGIS Developer account",
                    "3. Go to 'Dashboard' → 'Applications'",
                    "4. Click 'New Application'",
                    "5. Fill in application details and create",
                    "6. Copy the Client ID and Client Secret",
                    "7. Add these credentials in the API Management section"
                ],
                "documentation_url": "https://developers.arcgis.com/documentation/",
                "pricing": "Free tier available with usage limits"
            },
            "AfriGIS": {
                "steps": [
                    "1. Go to https://www.afrigis.co.za/",
                    "2. Contact AfriGIS sales team",
                    "3. Sign up for a developer account",
                    "4. Obtain API key from your dashboard",
                    "5. Add the API key in the API Management section"
                ],
                "documentation_url": "https://www.afrigis.co.za/developers/",
                "pricing": "Commercial license required"
            }
        }
        
        return instructions.get(api_name, {
            "steps": ["This API doesn't require additional setup"],
            "documentation_url": "",
            "pricing": "Free"
        })

# Global service instance
api_management_service = APIManagementService()
