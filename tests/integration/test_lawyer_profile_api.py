import pytest
import json
from app.domain.enums import RoleEnum


class TestLawyerProfileAPI:
    """Integration tests for lawyer profile API endpoints."""

    def test_get_my_profile_lawyer_success(self, client, auth_headers_lawyer, sample_lawyer_user):
        """Test lawyer getting their own profile."""
        # First create a profile
        profile_data = {
            "bar_number": "BAR12345",
            "bar_state": "CA", 
            "bio": "Test lawyer bio",
            "specializations": "Corporate,Contract",
            "hourly_rate_cents": 25000
        }
        
        response = client.put(
            "/api/lawyer-profiles/me",
            data=json.dumps(profile_data),
            content_type="application/json",
            headers=auth_headers_lawyer
        )
        assert response.status_code == 200
        
        # Then get the profile
        response = client.get(
            "/api/lawyer-profiles/me",
            headers=auth_headers_lawyer
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["bar_number"] == "BAR12345"
        assert data["bar_state"] == "CA"
        assert data["bio"] == "Test lawyer bio"

    def test_get_my_profile_non_lawyer_fails(self, client, auth_headers_client):
        """Test non-lawyer cannot access lawyer profile endpoint."""
        response = client.get(
            "/api/lawyer-profiles/me",
            headers=auth_headers_client
        )
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "Only lawyers can access profiles" in data["error"]

    def test_create_update_profile_lawyer_success(self, client, auth_headers_lawyer):
        """Test lawyer creating/updating their profile."""
        profile_data = {
            "bar_number": "BAR67890",
            "bar_state": "NY",
            "bio": "New York lawyer",
            "specializations": "Real Estate",
            "hourly_rate_cents": 30000
        }
        
        response = client.put(
            "/api/lawyer-profiles/me",
            data=json.dumps(profile_data),
            content_type="application/json",
            headers=auth_headers_lawyer
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["bar_number"] == "BAR67890"
        assert data["bar_state"] == "NY"
        assert data["bio"] == "New York lawyer"

    def test_get_lawyer_profile_by_user_id_public(self, client, auth_headers_client, sample_lawyer_user):
        """Test public access to lawyer profile by user ID."""
        # First create a profile for the lawyer
        profile_data = {
            "bar_number": "BAR11111",
            "bar_state": "TX",
            "bio": "Texas lawyer"
        }
        
        # Use lawyer's own auth to create profile
        lawyer_headers = {
            "Authorization": f"Bearer {sample_lawyer_user['token']}",
            "Content-Type": "application/json"
        }
        
        client.put(
            "/api/lawyer-profiles/me",
            data=json.dumps(profile_data),
            content_type="application/json",
            headers=lawyer_headers
        )
        
        # Now client can access the profile
        response = client.get(
            f"/api/lawyer-profiles/user/{sample_lawyer_user['user_id']}",
            headers=auth_headers_client
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["bar_number"] == "BAR11111"
        assert data["bar_state"] == "TX"

    def test_get_all_profiles_admin_only(self, client, auth_headers_admin, auth_headers_client):
        """Test only admins can view all profiles."""
        response = client.get(
            "/api/lawyer-profiles/",
            headers=auth_headers_client
        )
        assert response.status_code == 403
        
        response = client.get(
            "/api/lawyer-profiles/",
            headers=auth_headers_admin
        )
        assert response.status_code == 200

    def test_delete_profile_admin_only(self, client, auth_headers_admin, auth_headers_lawyer, sample_lawyer_user):
        """Test only admins can delete profiles."""
        # Create a profile first
        profile_data = {"bar_number": "BAR99999"}
        
        client.put(
            "/api/lawyer-profiles/me",
            data=json.dumps(profile_data),
            content_type="application/json",
            headers=auth_headers_lawyer
        )
        
        # Try to delete as lawyer (should fail)
        response = client.delete(
            f"/api/lawyer-profiles/user/{sample_lawyer_user['user_id']}",
            headers=auth_headers_lawyer
        )
        assert response.status_code == 403
        
        # Delete as admin (should succeed)
        response = client.delete(
            f"/api/lawyer-profiles/user/{sample_lawyer_user['user_id']}",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
