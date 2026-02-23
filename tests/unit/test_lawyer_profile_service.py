import pytest
from app.core.extensions import db
from app.services.lawyer_profile_service import LawyerProfileService
from app.services.auth_service import AuthService
from app.domain.enums import RoleEnum
from app.models.lawyer_profile import LawyerProfile
from app.models.user import User


@pytest.fixture
def sample_lawyer_user():
    """A lawyer user for testing."""
    user = User(
        email="lawyer@test.example",
        password="hashed",
        role=RoleEnum.LAWYER.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture
def sample_client_user():
    """A client user for testing."""
    user = User(
        email="client@test.example",
        password="hashed",
        role=RoleEnum.USER.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture
def sample_admin_user():
    """An admin user for testing."""
    user = User(
        email="admin@test.example",
        password="hashed",
        role=RoleEnum.ADMIN.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


class TestLawyerProfileService:
    """Test cases for LawyerProfileService."""

    def test_create_lawyer_profile_success(self, sample_lawyer_user):
        """Test successful creation of lawyer profile."""
        user = sample_lawyer_user
        
        profile = LawyerProfileService.create_profile(
            user_id=user.id,
            bar_number="BAR12345",
            bar_state="CA",
            bio="Experienced corporate lawyer",
            specializations="Corporate,Contract",
            hourly_rate_cents=25000,  # $250/hour
            actor_id=user.id,
            actor_role=user.role
        )
        
        assert profile is not None
        assert profile.user_id == user.id
        assert profile.bar_number == "BAR12345"
        assert profile.bar_state == "CA"
        assert profile.bio == "Experienced corporate lawyer"
        assert profile.specializations == "Corporate,Contract"
        assert profile.hourly_rate_cents == 25000

    def test_create_profile_non_lawyer_fails(self, sample_client_user):
        """Test that non-lawyers cannot create profiles."""
        user = sample_client_user
        
        with pytest.raises(ValueError, match="Only lawyers can have profiles"):
            LawyerProfileService.create_profile(
                user_id=user.id,
                bar_number="BAR12345",
                actor_id=user.id,
                actor_role=user.role
            )

    def test_create_profile_unauthorized_fails(self, sample_lawyer_user, sample_client_user):
        """Test that users cannot create profiles for others."""
        lawyer = sample_lawyer_user
        client = sample_client_user
        
        with pytest.raises(ValueError, match="Lawyers can only create their own profile"):
            LawyerProfileService.create_profile(
                user_id=lawyer.id,
                bar_number="BAR12345",
                actor_id=client.id,
                actor_role=client.role
            )

    def test_update_profile_success(self, sample_lawyer_user):
        """Test successful profile update."""
        user = sample_lawyer_user
        
        # Create profile first
        profile = LawyerProfileService.create_profile(
            user_id=user.id,
            bar_number="BAR12345",
            actor_id=user.id,
            actor_role=user.role
        )
        
        # Update profile
        updated_profile = LawyerProfileService.update_profile(
            user_id=user.id,
            bio="Updated bio",
            hourly_rate_cents=30000,
            actor_id=user.id,
            actor_role=user.role
        )
        
        assert updated_profile is not None
        assert updated_profile.id == profile.id
        assert updated_profile.bio == "Updated bio"
        assert updated_profile.hourly_rate_cents == 30000
        assert updated_profile.bar_number == "BAR12345"  # Unchanged

    def test_get_profile_by_user_id(self, sample_lawyer_user):
        """Test getting profile by user ID."""
        user = sample_lawyer_user
        
        # Create profile
        created_profile = LawyerProfileService.create_profile(
            user_id=user.id,
            bar_number="BAR12345",
            actor_id=user.id,
            actor_role=user.role
        )
        
        # Get profile
        retrieved_profile = LawyerProfileService.get_profile_by_user_id(user.id)
        
        assert retrieved_profile is not None
        assert retrieved_profile.id == created_profile.id
        assert retrieved_profile.user_id == user.id

    def test_delete_profile_admin_only(self, sample_lawyer_user, sample_admin_user):
        """Test that only admins can delete profiles."""
        lawyer = sample_lawyer_user
        admin = sample_admin_user
        
        # Create profile
        profile = LawyerProfileService.create_profile(
            user_id=lawyer.id,
            bar_number="BAR12345",
            actor_id=admin.id,
            actor_role=admin.role
        )
        
        # Try to delete as lawyer (should fail)
        with pytest.raises(ValueError, match="Only admins can delete lawyer profiles"):
            LawyerProfileService.delete_profile(
                user_id=lawyer.id,
                actor_id=lawyer.id,
                actor_role=lawyer.role
            )
        
        # Delete as admin (should succeed)
        deleted = LawyerProfileService.delete_profile(
            user_id=lawyer.id,
            actor_id=admin.id,
            actor_role=admin.role
        )
        
        assert deleted is True
        
        # Verify profile is deleted
        retrieved_profile = LawyerProfileService.get_profile_by_user_id(lawyer.id)
        assert retrieved_profile is None
