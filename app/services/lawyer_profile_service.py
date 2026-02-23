from typing import Optional
from ..models.lawyer_profile import LawyerProfile
from ..models.user import User
from ..repositories.lawyer_profile_repository import LawyerProfileRepository
from ..domain.enums import RoleEnum
from ..core.extensions import db


class LawyerProfileService:

    @staticmethod
    def create_profile(user_id: str, bar_number: Optional[str] = None, 
                      bar_state: Optional[str] = None, bio: Optional[str] = None,
                      specializations: Optional[str] = None, 
                      hourly_rate_cents: Optional[int] = None,
                      actor_id: str = None, actor_role: str = None) -> LawyerProfile:
        """
        Create a lawyer profile for a user.
        
        Args:
            user_id: The user ID to create profile for
            bar_number: Optional bar admission number
            bar_state: Optional state of bar admission
            bio: Optional professional bio
            specializations: Optional specializations (JSON string or comma-separated)
            hourly_rate_cents: Optional hourly rate in cents
            actor_id: ID of user performing the action
            actor_role: Role of user performing the action
            
        Returns:
            LawyerProfile: The created profile
            
        Raises:
            ValueError: If user is not a lawyer or unauthorized
        """
        # Verify user exists and is a lawyer
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        if user.role != RoleEnum.LAWYER.value:
            raise ValueError("Only lawyers can have profiles")
        
        # Check authorization: user can create own profile, admin can create any
        if actor_role == RoleEnum.LAWYER.value and actor_id != user_id:
            raise ValueError("Lawyers can only create their own profile")
        elif actor_role not in [RoleEnum.LAWYER.value, RoleEnum.ADMIN.value]:
            raise ValueError("Unauthorized to create lawyer profile")
        
        # Check if profile already exists
        existing_profile = LawyerProfileRepository.get_by_user_id(user_id)
        if existing_profile:
            raise ValueError("Profile already exists for this user")
        
        profile = LawyerProfile(
            user_id=user_id,
            bar_number=bar_number,
            bar_state=bar_state,
            bio=bio,
            specializations=specializations,
            hourly_rate_cents=hourly_rate_cents
        )
        
        return LawyerProfileRepository.create(profile)

    @staticmethod
    def update_profile(user_id: str, bar_number: Optional[str] = None,
                      bar_state: Optional[str] = None, bio: Optional[str] = None,
                      specializations: Optional[str] = None,
                      hourly_rate_cents: Optional[int] = None,
                      actor_id: str = None, actor_role: str = None) -> Optional[LawyerProfile]:
        """
        Update a lawyer profile.
        
        Args:
            user_id: The user ID whose profile to update
            actor_id: ID of user performing the action
            actor_role: Role of user performing the action
            
        Returns:
            LawyerProfile: The updated profile or None if not found
            
        Raises:
            ValueError: If unauthorized
        """
        profile = LawyerProfileRepository.get_by_user_id(user_id)
        if not profile:
            return None
        
        # Check authorization: user can update own profile, admin can update any
        if actor_role == RoleEnum.LAWYER.value and actor_id != user_id:
            raise ValueError("Lawyers can only update their own profile")
        elif actor_role not in [RoleEnum.LAWYER.value, RoleEnum.ADMIN.value]:
            raise ValueError("Unauthorized to update lawyer profile")
        
        # Update fields if provided
        if bar_number is not None:
            profile.bar_number = bar_number
        if bar_state is not None:
            profile.bar_state = bar_state
        if bio is not None:
            profile.bio = bio
        if specializations is not None:
            profile.specializations = specializations
        if hourly_rate_cents is not None:
            profile.hourly_rate_cents = hourly_rate_cents
        
        return LawyerProfileRepository.update(profile)

    @staticmethod
    def get_profile_by_user_id(user_id: str) -> Optional[LawyerProfile]:
        """Get lawyer profile by user ID."""
        return LawyerProfileRepository.get_by_user_id(user_id)

    @staticmethod
    def get_profile_by_id(profile_id: str) -> Optional[LawyerProfile]:
        """Get lawyer profile by profile ID."""
        return LawyerProfileRepository.get_by_id(profile_id)

    @staticmethod
    def get_all_profiles() -> list[LawyerProfile]:
        """Get all lawyer profiles."""
        return LawyerProfileRepository.get_all()

    @staticmethod
    def delete_profile(user_id: str, actor_id: str = None, actor_role: str = None) -> bool:
        """
        Delete a lawyer profile.
        
        Args:
            user_id: The user ID whose profile to delete
            actor_id: ID of user performing the action
            actor_role: Role of user performing the action
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            ValueError: If unauthorized
        """
        profile = LawyerProfileRepository.get_by_user_id(user_id)
        if not profile:
            return False
        
        # Only admins can delete profiles
        if actor_role != RoleEnum.ADMIN.value:
            raise ValueError("Only admins can delete lawyer profiles")
        
        LawyerProfileRepository.delete(profile)
        return True
