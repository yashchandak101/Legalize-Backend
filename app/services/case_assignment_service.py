from typing import Optional, List
from datetime import datetime, timezone
from ..models.case_assignment import CaseAssignment
from ..models.case import Case
from ..models.user import User
from ..repositories.case_assignment_repository import CaseAssignmentRepository
from ..domain.case_rules import validate_case_status_transition, STATUS_ASSIGNED
from ..domain.enums import RoleEnum
from ..core.extensions import db


class CaseAssignmentService:

    @staticmethod
    def assign_case(case_id: str, lawyer_id: str, assigned_by: str, 
                   actor_role: str) -> Optional[CaseAssignment]:
        """
        Assign a case to a lawyer.
        
        Args:
            case_id: The case ID to assign
            lawyer_id: The lawyer ID to assign to
            assigned_by: The user ID making the assignment
            actor_role: Role of user performing the action
            
        Returns:
            CaseAssignment: The created assignment
            
        Raises:
            ValueError: If case not found, lawyer not found, or unauthorized
        """
        # Verify case exists
        case = Case.query.get(case_id)
        if not case:
            raise ValueError("Case not found")
        
        # Verify lawyer exists and is a lawyer
        lawyer = User.query.get(lawyer_id)
        if not lawyer:
            raise ValueError("Lawyer not found")
        
        if lawyer.role != RoleEnum.LAWYER.value:
            raise ValueError("Assigned user must be a lawyer")
        
        # Check authorization: only admins can assign cases
        if actor_role != RoleEnum.ADMIN.value:
            raise ValueError("Only admins can assign cases")
        
        # Supersede any previous active assignments
        CaseAssignmentRepository.supersede_previous_assignments(case_id)
        
        # Create new assignment
        assignment = CaseAssignment(
            case_id=case_id,
            lawyer_id=lawyer_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(timezone.utc),
            status="active"
        )
        
        # Update case with assigned lawyer and status
        case.assigned_lawyer_id = lawyer_id
        if case.status != STATUS_ASSIGNED:
            validate_case_status_transition(case.status, STATUS_ASSIGNED)
            case.status = STATUS_ASSIGNED
        
        # Save both assignment and case updates
        db.session.add(assignment)
        db.session.commit()
        
        # Create notifications
        from ..services.notification_service import NotificationService
        NotificationService.create_case_assigned_notification(
            case_id=case_id,
            lawyer_id=lawyer_id,
            client_id=case.user_id
        )
        
        return assignment

    @staticmethod
    def unassign_case(case_id: str, assigned_by: str, actor_role: str) -> bool:
        """
        Unassign a case (supersede current assignment).
        
        Args:
            case_id: The case ID to unassign
            assigned_by: The user ID making the unassignment
            actor_role: Role of user performing the action
            
        Returns:
            bool: True if unassigned successfully
            
        Raises:
            ValueError: If case not found or unauthorized
        """
        # Verify case exists
        case = Case.query.get(case_id)
        if not case:
            raise ValueError("Case not found")
        
        # Check authorization: only admins can unassign cases
        if actor_role != RoleEnum.ADMIN.value:
            raise ValueError("Only admins can unassign cases")
        
        # Supersede current assignment
        superseded = CaseAssignmentRepository.supersede_previous_assignments(case_id)
        
        if superseded:
            # Update case to remove assigned lawyer and change status
            case.assigned_lawyer_id = None
            # Set status back to open or in_progress based on business rules
            # For now, we'll set to open
            from ..domain.case_rules import STATUS_OPEN
            case.status = STATUS_OPEN
            db.session.commit()
            return True
        
        return False

    @staticmethod
    def get_active_assignment(case_id: str) -> Optional[CaseAssignment]:
        """Get the active assignment for a case."""
        return CaseAssignmentRepository.get_active_assignment_for_case(case_id)

    @staticmethod
    def get_case_assignments(case_id: str) -> List[CaseAssignment]:
        """Get all assignments for a case (history)."""
        return CaseAssignmentRepository.get_assignments_for_case(case_id)

    @staticmethod
    def get_lawyer_assignments(lawyer_id: str, active_only: bool = False) -> List[CaseAssignment]:
        """Get assignments for a lawyer."""
        if active_only:
            return CaseAssignmentRepository.get_active_assignments_for_lawyer(lawyer_id)
        else:
            return CaseAssignmentRepository.get_assignments_for_lawyer(lawyer_id)

    @staticmethod
    def can_user_access_case(user_id: str, case_id: str, user_role: str) -> bool:
        """
        Check if a user can access a case based on assignments and ownership.
        
        Args:
            user_id: The user ID
            case_id: The case ID
            user_role: The user's role
            
        Returns:
            bool: True if user can access the case
        """
        case = Case.query.get(case_id)
        if not case:
            return False
        
        # Admins can access all cases
        if user_role == RoleEnum.ADMIN.value:
            return True
        
        # Case owner (client) can access their own cases
        if case.user_id == user_id:
            return True
        
        # Lawyers can access cases assigned to them
        if user_role == RoleEnum.LAWYER.value:
            assignment = CaseAssignmentRepository.get_active_assignment_for_case(case_id)
            if assignment and assignment.lawyer_id == user_id:
                return True
        
        return False
