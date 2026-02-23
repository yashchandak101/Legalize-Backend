from ..models.case_comment import CaseComment
from ..core.extensions import db


class CaseCommentRepository:

    @staticmethod
    def create(comment: CaseComment):
        db.session.add(comment)
        db.session.commit()
        return comment

    @staticmethod
    def get_by_id(comment_id: str):
        return CaseComment.query.get(comment_id)

    @staticmethod
    def get_comments_for_case(case_id: str, include_internal: bool = False):
        """Get comments for a case, optionally including internal comments."""
        query = CaseComment.query.filter_by(case_id=case_id)
        
        if not include_internal:
            query = query.filter_by(is_internal=False)
        
        return query.order_by(CaseComment.created_at.asc()).all()

    @staticmethod
    def get_comments_for_case_by_role(case_id: str, user_role: str):
        """Get comments for a case based on user role."""
        if user_role in ['lawyer', 'admin']:
            # Lawyers and admins can see all comments
            return CaseCommentRepository.get_comments_for_case(case_id, include_internal=True)
        else:
            # Clients can only see non-internal comments
            return CaseCommentRepository.get_comments_for_case(case_id, include_internal=False)

    @staticmethod
    def update(comment: CaseComment):
        db.session.commit()
        return comment

    @staticmethod
    def delete(comment: CaseComment):
        db.session.delete(comment)
        db.session.commit()

    @staticmethod
    def get_user_comment(comment_id: str, user_id: str):
        """Get a specific comment by user (for authorization)."""
        return CaseComment.query.filter_by(id=comment_id, user_id=user_id).first()
