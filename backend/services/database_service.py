"""
Database Service Layer
Provides unified interface for MongoDB operations with proper error handling and connection management.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os

from .validation_service import ProjectInDB, ProjectResponse

logger = logging.getLogger(__name__)

class DatabaseService:
    """Centralized database service for MongoDB operations"""
    
    def __init__(self, mongo_url: str = None, database_name: str = None):
        self.mongo_url = mongo_url or os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.database_name = database_name or os.environ.get('DB_NAME', 'stirling_landdev')
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.projects_collection: Optional[AsyncIOMotorCollection] = None
        self.connected = False
    
    async def connect(self) -> bool:
        """Establish database connection and setup collections"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_url)
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.database = self.client[self.database_name]
            self.projects_collection = self.database["projects"]
            
            # Create indexes for better performance
            await self.projects_collection.create_index("project_id", unique=True)
            await self.projects_collection.create_index("created")
            await self.projects_collection.create_index([("name", "text")])  # Text search index
            
            self.connected = True
            logger.info(f"✅ Connected to MongoDB: {self.database_name}")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {str(e)}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected database error: {str(e)}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("❌ Disconnected from MongoDB")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health and return status"""
        if not self.connected or not self.client:
            return {
                "status": "disconnected",
                "database": self.database_name,
                "collections": 0
            }
        
        try:
            # Ping database
            await self.client.admin.command('ping')
            
            # Get collection stats
            collections = await self.database.list_collection_names()
            project_count = await self.projects_collection.count_documents({})
            
            return {
                "status": "connected",
                "database": self.database_name,
                "collections": len(collections),
                "project_count": project_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "database": self.database_name
            }
    
    async def create_project(self, project_data: ProjectInDB) -> Dict[str, Any]:
        """Create a new project in the database"""
        if not self.connected:
            raise ConnectionError("Database not connected")
        
        try:
            result = await self.projects_collection.insert_one(project_data.dict())
            logger.info(f"Project created successfully: {project_data.project_id}")
            
            return {
                "success": True,
                "project_id": project_data.project_id,
                "inserted_id": str(result.inserted_id)
            }
            
        except DuplicateKeyError:
            error_msg = f"Project with ID {project_data.project_id} already exists"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "duplicate_key"
            }
        except Exception as e:
            error_msg = f"Failed to create project: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "database_error"
            }
    
    async def get_project(self, project_id: str) -> Optional[ProjectInDB]:
        """Retrieve a project by ID"""
        if not self.connected:
            raise ConnectionError("Database not connected")
        
        try:
            project_doc = await self.projects_collection.find_one(
                {"project_id": project_id},
                {"_id": 0}  # Exclude MongoDB _id field
            )
            
            if project_doc:
                logger.info(f"Project retrieved successfully: {project_id}")
                return ProjectInDB(**project_doc)
            else:
                logger.warning(f"Project not found: {project_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve project {project_id}: {str(e)}")
            raise
    
    async def list_projects(self, limit: int = 100, skip: int = 0, 
                          search_term: str = None) -> Dict[str, Any]:
        """List projects with optional search and pagination"""
        if not self.connected:
            raise ConnectionError("Database not connected")
        
        try:
            # Build query
            query = {}
            if search_term:
                query["$text"] = {"$search": search_term}
            
            # Get total count
            total_count = await self.projects_collection.count_documents(query)
            
            # Get projects with pagination
            cursor = self.projects_collection.find(
                query,
                {"_id": 0}  # Exclude MongoDB _id field
            ).sort("created", -1).skip(skip).limit(limit)
            
            projects = []
            async for project_doc in cursor:
                project_data = ProjectInDB(**project_doc)
                project_response = ProjectResponse(
                    id=project_data.project_id,
                    name=project_data.name,
                    coordinates=project_data.coordinates,
                    created=project_data.created,
                    lastModified=project_data.last_modified,
                    data=None,  # Don't include full data in list view
                    layers=None
                )
                projects.append(project_response)
            
            logger.info(f"Retrieved {len(projects)} projects (total: {total_count})")
            
            return {
                "success": True,
                "projects": projects,
                "total_count": total_count,
                "returned_count": len(projects),
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            error_msg = f"Failed to list projects: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "projects": []
            }
    
    async def update_project(self, project_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing project"""
        if not self.connected:
            raise ConnectionError("Database not connected")
        
        try:
            # Add last_modified timestamp
            update_data["last_modified"] = datetime.now().isoformat()
            
            result = await self.projects_collection.update_one(
                {"project_id": project_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return {
                    "success": False,
                    "error": f"Project {project_id} not found",
                    "error_type": "not_found"
                }
            
            logger.info(f"Project updated successfully: {project_id}")
            return {
                "success": True,
                "project_id": project_id,
                "modified_count": result.modified_count
            }
            
        except Exception as e:
            error_msg = f"Failed to update project {project_id}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "database_error"
            }
    
    async def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete a project"""
        if not self.connected:
            raise ConnectionError("Database not connected")
        
        try:
            result = await self.projects_collection.delete_one({"project_id": project_id})
            
            if result.deleted_count == 0:
                return {
                    "success": False,
                    "error": f"Project {project_id} not found",
                    "error_type": "not_found"
                }
            
            logger.info(f"Project deleted successfully: {project_id}")
            return {
                "success": True,
                "project_id": project_id,
                "deleted_count": result.deleted_count
            }
            
        except Exception as e:
            error_msg = f"Failed to delete project {project_id}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "database_error"
            }
    
    async def get_project_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.connected:
            raise ConnectionError("Database not connected")
        
        try:
            total_projects = await self.projects_collection.count_documents({})
            
            # Get projects by status
            pipeline = [
                {"$group": {
                    "_id": "$data.response.status",
                    "count": {"$sum": 1}
                }}
            ]
            
            status_counts = {}
            async for doc in self.projects_collection.aggregate(pipeline):
                status_counts[doc["_id"]] = doc["count"]
            
            # Get recent projects (last 7 days)
            from datetime import timedelta
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            recent_projects = await self.projects_collection.count_documents({
                "created": {"$gte": week_ago}
            })
            
            return {
                "total_projects": total_projects,
                "status_breakdown": status_counts,
                "recent_projects_7_days": recent_projects,
                "database_name": self.database_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global database service instance
db_service = DatabaseService()
