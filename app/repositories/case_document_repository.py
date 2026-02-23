from ..models.case_document import CaseDocument
from ..core.extensions import db


class CaseDocumentRepository:

    @staticmethod
    def create(document: CaseDocument):
        db.session.add(document)
        db.session.commit()
        return document

    @staticmethod
    def get_by_id(document_id: str):
        return CaseDocument.query.get(document_id)

    @staticmethod
    def get_documents_for_case(case_id: str, include_deleted: bool = False):
        """Get documents for a case, optionally including deleted ones."""
        query = CaseDocument.query.filter_by(case_id=case_id)
        
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        
        return query.order_by(CaseDocument.created_at.desc()).all()

    @staticmethod
    def get_user_document(document_id: str, user_id: str):
        """Get a specific document by uploader (for authorization)."""
        return CaseDocument.query.filter_by(id=document_id, uploaded_by=user_id).first()

    @staticmethod
    def update(document: CaseDocument):
        db.session.commit()
        return document

    @staticmethod
    def soft_delete(document: CaseDocument):
        """Soft delete a document."""
        document.is_deleted = True
        db.session.commit()
        return document

    @staticmethod
    def hard_delete(document: CaseDocument):
        """Permanently delete a document."""
        db.session.delete(document)
        db.session.commit()

    @staticmethod
    def get_by_filename(case_id: str, filename: str):
        """Get a document by case and filename."""
        return CaseDocument.query.filter_by(
            case_id=case_id,
            filename=filename,
            is_deleted=False
        ).first()
