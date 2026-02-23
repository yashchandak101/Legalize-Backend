import pytest
import json
from app.domain.enums import RoleEnum


class TestCaseAssignmentAPI:
    """Integration tests for case assignment API endpoints."""

    def test_assign_case_admin_success(self, client, auth_headers_admin, sample_case, sample_lawyer_user):
        """Test admin assigning a case to lawyer."""
        assignment_data = {
            "lawyer_id": sample_lawyer_user['user_id']
        }
        
        response = client.post(
            f"/api/assignments/cases/{sample_case['id']}/assign",
            data=json.dumps(assignment_data),
            content_type="application/json",
            headers=auth_headers_admin
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data["case_id"] == sample_case['id']
        assert data["lawyer_id"] == sample_lawyer_user['user_id']
        assert data["status"] == "active"

    def test_assign_case_non_admin_fails(self, client, auth_headers_client, sample_case, sample_lawyer_user):
        """Test non-admin cannot assign cases."""
        assignment_data = {
            "lawyer_id": sample_lawyer_user['user_id']
        }
        
        response = client.post(
            f"/api/assignments/cases/{sample_case['id']}/assign",
            data=json.dumps(assignment_data),
            content_type="application/json",
            headers=auth_headers_client
        )
        assert response.status_code == 403

    def test_unassign_case_admin_success(self, client, auth_headers_admin, sample_case, sample_lawyer_user):
        """Test admin unassigning a case."""
        # First assign the case
        assignment_data = {"lawyer_id": sample_lawyer_user['user_id']}
        
        client.post(
            f"/api/assignments/cases/{sample_case['id']}/assign",
            data=json.dumps(assignment_data),
            content_type="application/json",
            headers=auth_headers_admin
        )
        
        # Then unassign
        response = client.post(
            f"/api/assignments/cases/{sample_case['id']}/unassign",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "unassigned successfully" in data["message"]

    def test_get_case_assignments_authorized(self, client, auth_headers_admin, sample_case, sample_lawyer_user):
        """Test getting case assignments for authorized users."""
        # Assign case first
        assignment_data = {"lawyer_id": sample_lawyer_user['user_id']}
        
        client.post(
            f"/api/assignments/cases/{sample_case['id']}/assign",
            data=json.dumps(assignment_data),
            content_type="application/json",
            headers=auth_headers_admin
        )
        
        # Get assignments as admin
        response = client.get(
            f"/api/assignments/cases/{sample_case['id']}/assignments",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]["case_id"] == sample_case['id']

    def test_get_case_assignments_unauthorized_fails(self, client, auth_headers_client, sample_case):
        """Test unauthorized users cannot view case assignments."""
        response = client.get(
            f"/api/assignments/cases/{sample_case['id']}/assignments",
            headers=auth_headers_client
        )
        assert response.status_code == 403

    def test_get_lawyer_assignments_lawyer_own(self, client, auth_headers_lawyer, sample_case, sample_lawyer_user):
        """Test lawyer can view their own assignments."""
        # Assign case to lawyer first
        assignment_data = {"lawyer_id": sample_lawyer_user['user_id']}
        
        # Use admin to assign
        admin_headers = {
            "Authorization": f"Bearer {sample_lawyer_user['admin_token']}",
            "Content-Type": "application/json"
        }
        
        client.post(
            f"/api/assignments/cases/{sample_case['id']}/assign",
            data=json.dumps(assignment_data),
            content_type="application/json",
            headers=admin_headers
        )
        
        # Lawyer views their assignments
        response = client.get(
            f"/api/assignments/lawyers/{sample_lawyer_user['user_id']}/assignments",
            headers=auth_headers_lawyer
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]["lawyer_id"] == sample_lawyer_user['user_id']

    def test_get_my_assignments_lawyer(self, client, auth_headers_lawyer, sample_case, sample_lawyer_user):
        """Test lawyer viewing their own assignments via /my-assignments endpoint."""
        # Assign case to lawyer first
        assignment_data = {"lawyer_id": sample_lawyer_user['user_id']}
        
        admin_headers = {
            "Authorization": f"Bearer {sample_lawyer_user['admin_token']}",
            "Content-Type": "application/json"
        }
        
        client.post(
            f"/api/assignments/cases/{sample_case['id']}/assign",
            data=json.dumps(assignment_data),
            content_type="application/json",
            headers=admin_headers
        )
        
        # Lawyer views their assignments
        response = client.get(
            "/api/assignments/my-assignments",
            headers=auth_headers_lawyer
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]["lawyer_id"] == sample_lawyer_user['user_id']

    def test_get_active_assignment(self, client, auth_headers_admin, sample_case, sample_lawyer_user):
        """Test getting active assignment for a case."""
        # Assign case first
        assignment_data = {"lawyer_id": sample_lawyer_user['user_id']}
        
        client.post(
            f"/api/assignments/cases/{sample_case['id']}/assign",
            data=json.dumps(assignment_data),
            content_type="application/json",
            headers=auth_headers_admin
        )
        
        # Get active assignment
        response = client.get(
            f"/api/assignments/cases/{sample_case['id']}/assignment",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["case_id"] == sample_case['id']
        assert data["status"] == "active"
