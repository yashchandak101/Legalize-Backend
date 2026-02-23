import pytest
from app.core.extensions import db
from app.services.case_assignment_service import CaseAssignmentService
from app.services.case_service import CaseService
from app.services.auth_service import AuthService
from app.domain.enums import RoleEnum
from app.models.case_assignment import CaseAssignment
from app.models.user import User
from app.models.case import Case


@pytest.fixture
def sample_case():
    """A sample case for testing."""
    # Create a case owner first
    case_owner = User(
        email="caseowner@test.example",
        password="hashed",
        role=RoleEnum.USER.value,
    )
    db.session.add(case_owner)
    db.session.flush()
    
    return CaseService.create_case(
        user_id=case_owner.id,
        title="Test case",
        description="Description for test case",
    )


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


class TestCaseAssignmentService:
    """Test cases for CaseAssignmentService."""

    def test_assign_case_success(self, sample_case, sample_lawyer_user, sample_admin_user):
        """Test successful case assignment."""
        case = sample_case
        lawyer = sample_lawyer_user
        admin = sample_admin_user
        
        assignment = CaseAssignmentService.assign_case(
            case_id=case.id,
            lawyer_id=lawyer.id,
            assigned_by=admin.id,
            actor_role=admin.role
        )
        
        assert assignment is not None
        assert assignment.case_id == case.id
        assert assignment.lawyer_id == lawyer.id
        assert assignment.assigned_by == admin.id
        assert assignment.status == "active"
        
        # Check that case was updated
        updated_case = CaseService.get_case_by_id(case.id)
        assert updated_case.assigned_lawyer_id == lawyer.id
        assert updated_case.status == "assigned"

    def test_assign_case_non_admin_fails(self, sample_case, sample_lawyer_user, sample_client_user):
        """Test that non-admins cannot assign cases."""
        case = sample_case
        lawyer = sample_lawyer_user
        client = sample_client_user
        
        with pytest.raises(ValueError, match="Only admins can assign cases"):
            CaseAssignmentService.assign_case(
                case_id=case.id,
                lawyer_id=lawyer.id,
                assigned_by=client.id,
                actor_role=client.role
            )

    def test_assign_case_to_non_lawyer_fails(self, sample_case, sample_client_user, sample_admin_user):
        """Test that cases can only be assigned to lawyers."""
        case = sample_case
        client = sample_client_user
        admin = sample_admin_user
        
        with pytest.raises(ValueError, match="Assigned user must be a lawyer"):
            CaseAssignmentService.assign_case(
                case_id=case.id,
                lawyer_id=client.id,
                assigned_by=admin.id,
                actor_role=admin.role
            )

    def test_unassign_case_success(self, sample_case, sample_lawyer_user, sample_admin_user):
        """Test successful case unassignment."""
        case = sample_case
        lawyer = sample_lawyer_user
        admin = sample_admin_user
        
        # Assign first
        assignment = CaseAssignmentService.assign_case(
            case_id=case.id,
            lawyer_id=lawyer.id,
            assigned_by=admin.id,
            actor_role=admin.role
        )
        
        # Then unassign
        success = CaseAssignmentService.unassign_case(
            case_id=case.id,
            assigned_by=admin.id,
            actor_role=admin.role
        )
        
        assert success is True
        
        # Check that case was updated
        updated_case = CaseService.get_case_by_id(case.id)
        assert updated_case.assigned_lawyer_id is None
        assert updated_case.status == "open"
        
        # Check assignment was superseded
        updated_assignment = CaseAssignmentService.get_active_assignment(case.id)
        assert updated_assignment is None

    def test_get_active_assignment(self, sample_case, sample_lawyer_user, sample_admin_user):
        """Test getting active assignment for a case."""
        case = sample_case
        lawyer = sample_lawyer_user
        admin = sample_admin_user
        
        # No assignment initially
        assignment = CaseAssignmentService.get_active_assignment(case.id)
        assert assignment is None
        
        # Create assignment
        created_assignment = CaseAssignmentService.assign_case(
            case_id=case.id,
            lawyer_id=lawyer.id,
            assigned_by=admin.id,
            actor_role=admin.role
        )
        
        # Get active assignment
        active_assignment = CaseAssignmentService.get_active_assignment(case.id)
        assert active_assignment is not None
        assert active_assignment.id == created_assignment.id
        assert active_assignment.status == "active"

    def test_supersede_assignments(self, sample_case, sample_lawyer_user, sample_admin_user):
        """Test that new assignments supersede previous ones."""
        case = sample_case
        lawyer = sample_lawyer_user
        admin = sample_admin_user
        
        # Create first assignment
        first_assignment = CaseAssignmentService.assign_case(
            case_id=case.id,
            lawyer_id=lawyer.id,
            assigned_by=admin.id,
            actor_role=admin.role
        )
        
        # Create second assignment (same lawyer, but new assignment)
        second_assignment = CaseAssignmentService.assign_case(
            case_id=case.id,
            lawyer_id=lawyer.id,
            assigned_by=admin.id,
            actor_role=admin.role
        )
        
        # First assignment should be superseded
        updated_first = CaseAssignmentService.get_active_assignment(case.id)
        assert updated_first.id == second_assignment.id
        
        # Get all assignments to verify history
        assignments = CaseAssignmentService.get_case_assignments(case.id)
        assert len(assignments) == 2
        
        active_assignments = [a for a in assignments if a.status == "active"]
        superseded_assignments = [a for a in assignments if a.status == "superseded"]
        
        assert len(active_assignments) == 1
        assert len(superseded_assignments) == 1
        assert active_assignments[0].id == second_assignment.id
        assert superseded_assignments[0].id == first_assignment.id

    def test_can_user_access_case_permissions(self, sample_case, sample_client_user, sample_lawyer_user, sample_admin_user):
        """Test case access permissions."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        admin = sample_admin_user
        
        # Client can access their own case
        assert CaseAssignmentService.can_user_access_case(
            user_id=client.id,
            case_id=case.id,
            user_role=client.role
        ) is True
        
        # Lawyer cannot access unassigned case
        assert CaseAssignmentService.can_user_access_case(
            user_id=lawyer.id,
            case_id=case.id,
            user_role=lawyer.role
        ) is False
        
        # Admin can access any case
        assert CaseAssignmentService.can_user_access_case(
            user_id=admin.id,
            case_id=case.id,
            user_role=admin.role
        ) is True
        
        # Assign case to lawyer
        CaseAssignmentService.assign_case(
            case_id=case.id,
            lawyer_id=lawyer.id,
            assigned_by=admin.id,
            actor_role=admin.role
        )
        
        # Now lawyer can access assigned case
        assert CaseAssignmentService.can_user_access_case(
            user_id=lawyer.id,
            case_id=case.id,
            user_role=lawyer.role
        ) is True
