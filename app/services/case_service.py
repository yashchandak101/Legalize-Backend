from app.core.extensions import db
from app.models.case import Case
from app.domain.case_rules import validate_case_status_transition
from app.services.case_assignment_service import CaseAssignmentService
from app.domain.enums import RoleEnum


class CaseService:

    # ---------------------------------
    # Create Case
    # ---------------------------------
    @staticmethod
    def create_case(user_id, title, description):
        case = Case(
            user_id=user_id,
            title=title,
            description=description,
        )
        db.session.add(case)
        db.session.commit()
        return case

    # ---------------------------------
    # Get All Cases For User
    # ---------------------------------
    @staticmethod
    def get_user_cases(user_id, assigned_lawyer_id=None):
        """Get cases for a user, optionally filtered by assigned lawyer."""
        query = Case.query.filter_by(user_id=user_id)
        
        if assigned_lawyer_id:
            query = query.filter_by(assigned_lawyer_id=assigned_lawyer_id)
            
        return query.all()

    # ---------------------------------
    # Get Cases For Lawyer
    # ---------------------------------
    @staticmethod
    def get_lawyer_cases(lawyer_id, active_only=True):
        """Get cases assigned to a lawyer."""
        query = Case.query.filter_by(assigned_lawyer_id=lawyer_id)
        
        if active_only:
            # Only return cases that are not closed
            query = query.filter(Case.status != 'closed')
            
        return query.all()

    # ---------------------------------
    # Get All Cases (Admin only)
    # ---------------------------------
    @staticmethod
    def get_all_cases():
        """Get all cases (admin only)."""
        return Case.query.all()

    # ---------------------------------
    # Get Case By ID
    # ---------------------------------
    @staticmethod
    def get_case_by_id(case_id):
        session = db.session() if callable(db.session) else db.session
        return session.get(Case, case_id)

    # ---------------------------------
    # Update Case (FULL UPDATE)
    # ---------------------------------
    @staticmethod
    def update_case(case_id, title=None, description=None, status=None, actor_id=None, actor_role=None):
        session = db.session() if callable(db.session) else db.session
        case = session.get(Case, case_id)

        if not case:
            return None

        # Check authorization if actor info provided
        if actor_id and actor_role:
            if not CaseAssignmentService.can_user_access_case(actor_id, case_id, actor_role):
                raise ValueError("Unauthorized to update this case")

        if title is not None:
            case.title = title

        if description is not None:
            case.description = description

        if status is not None:
            validate_case_status_transition(case.status, status)
            case.status = status

        db.session.commit()
        db.session.refresh(case)
        return case

    # ---------------------------------
    # Delete Case (By ID)
    # ---------------------------------
    @staticmethod
    def delete_case(case_id, actor_id=None, actor_role=None):
        session = db.session() if callable(db.session) else db.session
        case = session.get(Case, case_id)

        if not case:
            return None

        # Check authorization if actor info provided
        if actor_id and actor_role:
            if not CaseAssignmentService.can_user_access_case(actor_id, case_id, actor_role):
                raise ValueError("Unauthorized to delete this case")

        db.session.delete(case)
        db.session.commit()
        return True

    # ---------------------------------
    # Filter Cases (for different user types)
    # ---------------------------------
    @staticmethod
    def get_cases_for_user(user_id, user_role, filters=None):
        """
        Get cases based on user role with optional filtering.
        
        Args:
            user_id: The user ID
            user_role: The user's role
            filters: Optional dict of filters (status, assigned_lawyer_id, etc.)
        """
        query = Case.query
        
        if user_role == RoleEnum.USER.value:
            # Clients can only see their own cases
            query = query.filter_by(user_id=user_id)
        elif user_role == RoleEnum.LAWYER.value:
            # Lawyers can only see cases assigned to them
            query = query.filter_by(assigned_lawyer_id=user_id)
        elif user_role == RoleEnum.ADMIN.value:
            # Admins can see all cases
            pass
        else:
            # Unknown role, return empty
            return []
        
        # Apply filters
        if filters:
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('assigned_lawyer_id'):
                query = query.filter_by(assigned_lawyer_id=filters['assigned_lawyer_id'])
        
        return query.all()