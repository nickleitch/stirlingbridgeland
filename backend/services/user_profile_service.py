"""
User Profile Service
Handles user profile management and settings for the application.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from .validation_service import UserProfile, UserProfileUpdate, ValidationUtils
from .database_service import db_service

class UserProfileService:
    """Service for managing user profiles and settings"""
    
    def __init__(self):
        self.collection_name = "user_profiles"
        # Default user profile for MVP (single-user system)
        self.default_user_id = "default_user"
    
    async def get_user_profile(self, user_id: Optional[str] = None) -> UserProfile:
        """Get user profile by ID or return default profile"""
        if not user_id:
            user_id = self.default_user_id
        
        try:
            # Try to get from database first
            if not db_service.connected:
                await db_service.connect()
                
            collection = db_service.database[self.collection_name]
            
            user_doc = await collection.find_one({"user_id": user_id})
            
            if user_doc:
                return UserProfile(
                    user_id=user_doc["user_id"],
                    username=user_doc["username"],
                    email=user_doc.get("email"),
                    full_name=user_doc.get("full_name"),
                    organization=user_doc.get("organization"),
                    created_at=user_doc["created_at"],
                    last_login=user_doc.get("last_login")
                )
            else:
                # Create default profile if doesn't exist
                return await self.create_default_profile(user_id)
                
        except Exception as e:
            print(f"Error getting user profile: {e}")
            # Return fallback default profile
            return UserProfile(
                user_id=user_id,
                username="Land Developer",
                email=None,
                full_name="Default User",
                organization="Stirling Bridge LandDev",
                created_at=datetime.now().isoformat(),
                last_login=None
            )
    
    async def create_default_profile(self, user_id: str) -> UserProfile:
        """Create a default user profile"""
        profile = UserProfile(
            user_id=user_id,
            username="Land Developer",
            email=None,
            full_name="Default User",
            organization="Stirling Bridge LandDev",
            created_at=datetime.now().isoformat(),
            last_login=None
        )
        
        try:
            if not db_service.connected:
                await db_service.connect()
                
            collection = db_service.database[self.collection_name]
            
            profile_doc = {
                "user_id": profile.user_id,
                "username": profile.username,
                "email": profile.email,
                "full_name": profile.full_name,
                "organization": profile.organization,
                "created_at": profile.created_at,
                "last_login": profile.last_login
            }
            
            await collection.insert_one(profile_doc)
            
        except Exception as e:
            print(f"Error creating default profile: {e}")
        
        return profile
    
    async def update_user_profile(self, user_id: Optional[str], update_data: UserProfileUpdate) -> UserProfile:
        """Update user profile with provided data"""
        if not user_id:
            user_id = self.default_user_id
        
        # Get current profile
        current_profile = await self.get_user_profile(user_id)
        
        # Prepare update data
        update_fields = {}
        if update_data.username:
            if not ValidationUtils.validate_username(update_data.username):
                raise ValueError("Invalid username format")
            update_fields["username"] = update_data.username
        
        if update_data.email:
            if not ValidationUtils.validate_email(update_data.email):
                raise ValueError("Invalid email format")
            update_fields["email"] = update_data.email
        
        if update_data.full_name:
            update_fields["full_name"] = update_data.full_name
        
        if update_data.organization:
            update_fields["organization"] = update_data.organization
        
        if not update_fields:
            return current_profile
        
        try:
            if not db_service.connected:
                await db_service.connect()
                
            collection = db_service.database[self.collection_name]
            
            # Update in database
            await collection.update_one(
                {"user_id": user_id},
                {"$set": update_fields}
            )
            
            # Return updated profile
            return await self.get_user_profile(user_id)
            
        except Exception as e:
            print(f"Error updating user profile: {e}")
            raise ValueError(f"Failed to update profile: {str(e)}")
    
    async def update_last_login(self, user_id: Optional[str] = None) -> None:
        """Update last login timestamp"""
        if not user_id:
            user_id = self.default_user_id
        
        try:
            if not db_service.connected:
                await db_service.connect()
                
            collection = db_service.database[self.collection_name]
            
            await collection.update_one(
                {"user_id": user_id},
                {"$set": {"last_login": datetime.now().isoformat()}},
                upsert=True
            )
        except Exception as e:
            print(f"Error updating last login: {e}")
    
    async def get_user_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get user-specific statistics"""
        if not user_id:
            user_id = self.default_user_id
        
        try:
            if not db_service.connected:
                await db_service.connect()
                
            projects_collection = db_service.database["projects"]
            
            # Count user's projects
            total_projects = await projects_collection.count_documents({})
            
            # Get recent activity (projects created in last 7 days)
            from datetime import datetime, timedelta
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            recent_projects = await projects_collection.count_documents({
                "created": {"$gte": week_ago}
            })
            
            # Get today's projects
            today = datetime.now().date().isoformat()
            today_projects = await projects_collection.count_documents({
                "created": {"$regex": f"^{today}"}
            })
            
            return {
                "total_projects": total_projects,
                "projects_this_week": recent_projects,
                "projects_today": today_projects,
                "last_project_date": await self._get_last_project_date(),
                "account_age_days": await self._get_account_age_days(user_id)
            }
            
        except Exception as e:
            print(f"Error getting user statistics: {e}")
            return {
                "total_projects": 0,
                "projects_this_week": 0,
                "projects_today": 0,
                "last_project_date": None,
                "account_age_days": 0
            }
    
    async def _get_last_project_date(self) -> Optional[str]:
        """Get the date of the most recent project"""
        try:
            if not db_service.connected:
                await db_service.connect()
                
            projects_collection = db_service.database["projects"]
            
            # Get most recent project
            cursor = projects_collection.find().sort("created", -1).limit(1)
            async for project in cursor:
                return project.get("created")
            
            return None
        except Exception:
            return None
    
    async def _get_account_age_days(self, user_id: str) -> int:
        """Calculate account age in days"""
        try:
            profile = await self.get_user_profile(user_id)
            created_date = datetime.fromisoformat(profile.created_at.replace('Z', '+00:00'))
            age = datetime.now() - created_date.replace(tzinfo=None)
            return age.days
        except Exception:
            return 0
    
    async def delete_user_profile(self, user_id: str) -> bool:
        """Delete user profile (admin function)"""
        if user_id == self.default_user_id:
            return False  # Cannot delete default user
        
        try:
            if not db_service.connected:
                await db_service.connect()
                
            collection = db_service.database[self.collection_name]
            
            result = await collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"Error deleting user profile: {e}")
            return False

# Global service instance
user_profile_service = UserProfileService()
