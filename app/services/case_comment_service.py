from typing import Optional, List
from ..models.case_comment import CaseComment
from ..repositories.case_comment_repository import CaseCommentRepository
from ..domain.enums import RoleEnum


class CaseCommentService:

    @staticmethod
    def create_comment(case_id: str, user_id: str, body: str, 
                      is_internal: bool = False, actor_role: str = None) -> CaseComment:
        """
        Create a comment on a case.
        
        Args:
            case_id: The case ID to comment on
            user_id: The user ID making the comment
            body: The comment text
            is_internal: Whether comment is internal (lawyers/admins only)
            actor_role: The role of the user making the comment
            
        Returns:
            CaseComment: The created comment
            
        Raises:
            ValueError: If unauthorized or invalid
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, case_id, actor_role):
            raise ValueError("Unauthorized to access this case")
        
        # Check internal comment permissions
        if is_internal and actor_role not in [RoleEnum.LAWYER.value, RoleEnum.ADMIN.value]:
            raise ValueError("Only lawyers and admins can create internal comments")
        
        # Validate comment body
        if not body or not body.strip():
            raise ValueError("Comment body cannot be empty")
        
        comment = CaseComment(
            case_id=case_id,
            user_id=user_id,
            body=body.strip(),
            is_internal=is_internal
        )
        
        created_comment = CaseCommentRepository.create(comment)
        
        # Create notification for case owner and assigned lawyer
        from ..services.notification_service import NotificationService
        from ..models.case import Case
        
        # Get case details
        comment_with_case = db.session.query(Case).filter_by(id=comment.case_id).first()
        if comment_with_case:
            # Notify case owner
            NotificationService.create_comment_notification(
                user_id=comment_with_case.user_id,
                case_id=comment.case_id,
                comment_id=created_comment.id,
                commenter_name="You"  # TODO: Get actual user name
            )
            
            # Notify assigned lawyer if exists
            if comment_with_case.assigned_lawyer_id:
                NotificationService.create_comment_notification(
                    user_id=comment_with_case.assigned_lawyer_id,
                    case_id=comment.case_id,
                    comment_id=created_comment.id,
                    commenter_name="You"  # TODO: Get actual user name
                )
        
        return created_comment

    @staticmethod
    def get_case_comments(case_id: str, user_id: str, user_role: str) -> List[CaseComment]:
        """
        Get comments for a case based on user role.
        
        Args:
            case_id: The case ID
            user_id: The user ID requesting comments
            user_role: The role of the user
            
        Returns:
            List[CaseComment]: List of comments
            
        Raises:
            ValueError: If unauthorized
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, case_id, user_role):
            raise ValueError("Unauthorized to access this case")
        
        return CaseCommentRepository.get_comments_for_case_by_role(case_id, user_role)

    @staticmethod
    def update_comment(comment_id: str, user_id: str, body: str = None, 
                       is_internal: bool = None, actor_role: str = None) -> Optional[CaseComment]:
        """
        Update a comment.
        
        Args:
            comment_id: The comment ID to update
            user_id: The user ID updating the comment
            body: New comment body (optional)
            is_internal: New internal flag (optional)
            actor_role: The role of the user
            
        Returns:
            CaseComment: The updated comment or None if not found
            
        Raises:
            ValueError: If unauthorized or invalid
        """
        comment = CaseCommentRepository.get_user_comment(comment_id, user_id)
        if not comment:
            return None
        
        # Check internal comment permissions
        if is_internal is not None and is_internal != comment.is_internal:
            if actor_role not in [RoleEnum.LAWYER.value, RoleEnum.ADMIN.value]:
                raise ValueError("Only lawyers and admins can modify internal flag")
        
        # Update fields if provided
        if body is not None:
            if not body or not body.strip():
                raise ValueError("Comment body cannot be empty")
            comment.body = body.strip()
        
        if is_internal is not None:
            comment.is_internal = is_internal
        
        return CaseCommentRepository.update(comment)

    @staticmethod
    def delete_comment(comment_id: str, user_id: str, actor_role: str = None) -> bool:
        """
        Delete a comment.
        
        Args:
            comment_id: The comment ID to delete
            user_id: The user ID deleting the comment
            actor_role: The role of the user
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            ValueError: If unauthorized
        """
        comment = CaseCommentRepository.get_user_comment(comment_id, user_id)
        if not comment:
            return False
        
        # Users can only delete their own comments
        CaseCommentRepository.delete(comment)
        return True

    @staticmethod
    def can_user_view_comment(comment_id: str, user_id: str, user_role: str) -> bool:
        """
        Check if a user can view a specific comment.
        
        Args:
            comment_id: The comment ID
            user_id: The user ID
            user_role: The role of the user
            
        Returns:
            bool: True if user can view the comment
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        comment = CaseCommentRepository.get_by_id(comment_id)
        if not comment:
            return False
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, comment.case_id, user_role):
            return False
        
        # Check internal comment visibility
        if comment.is_internal and user_role not in [RoleEnum.LAWYER.value, RoleEnum.ADMIN.value]:
            return False
        
        return True
