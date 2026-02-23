import pytest
import tempfile
import os
from io import BytesIO
from app.core.extensions import db
from app.services.case_document_service import CaseDocumentService
from app.services.case_service import CaseService
from app.services.auth_service import AuthService
from app.domain.enums import RoleEnum
from app.models.case_document import CaseDocument
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
def mock_file():
    """A mock file for testing."""
    file_content = b"This is a test file content"
    file = BytesIO(file_content)
    file.filename = "test.txt"
    file.content_type = "text/plain"
    return file


class TestCaseDocumentService:
    """Test cases for CaseDocumentService."""

    def test_is_allowed_file_valid_extensions(self):
        """Test allowed file extensions."""
        assert CaseDocumentService.is_allowed_file("document.pdf") is True
        assert CaseDocumentService.is_allowed_file("image.jpg") is True
        assert CaseDocumentService.is_allowed_file("spreadsheet.xlsx") is True
        assert CaseDocumentService.is_allowed_file("script.exe") is False
        assert CaseDocumentService.is_allowed_file("archive.zip") is False

    def test_generate_unique_filename(self):
        """Test unique filename generation."""
        filename = CaseDocumentService.generate_unique_filename("test.pdf")
        assert filename.endswith(".pdf")
        assert len(filename) > 10  # Should have UUID + extension
        
        filename_no_ext = CaseDocumentService.generate_unique_filename("test")
        assert "." not in filename_no_ext

    def test_save_uploaded_file_success(self, sample_case, sample_client_user, mock_file):
        """Test successful file upload."""
        case = sample_case
        client = sample_client_user
        
        document = CaseDocumentService.save_uploaded_file(
            file=mock_file,
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        assert document is not None
        assert document.case_id == case.id
        assert document.uploaded_by == client.id
        assert document.original_filename == "test.txt"
        assert document.mime_type == "text/plain"
        assert document.size_bytes > 0
        assert document.is_deleted is False

    def test_save_uploaded_file_unauthorized_fails(self, sample_case, sample_lawyer_user, mock_file):
        """Test that unauthorized users cannot upload files."""
        case = sample_case
        lawyer = sample_lawyer_user
        
        # Lawyer not assigned to case should not be able to upload
        with pytest.raises(ValueError, match="Unauthorized to access this case"):
            CaseDocumentService.save_uploaded_file(
                file=mock_file,
                case_id=case.id,
                user_id=lawyer.id,
                actor_role=lawyer.role
            )

    def test_save_uploaded_file_invalid_type_fails(self, sample_case, sample_client_user):
        """Test that invalid file types are rejected."""
        case = sample_case
        client = sample_client_user
        
        # Create mock file with invalid extension
        invalid_file = BytesIO(b"test content")
        invalid_file.filename = "malware.exe"
        invalid_file.content_type = "application/octet-stream"
        
        with pytest.raises(ValueError, match="File type not allowed"):
            CaseDocumentService.save_uploaded_file(
                file=invalid_file,
                case_id=case.id,
                user_id=client.id,
                actor_role=client.role
            )

    def test_get_case_documents_success(self, sample_case, sample_client_user, mock_file):
        """Test getting documents for a case."""
        case = sample_case
        client = sample_client_user
        
        # Upload a document first
        document = CaseDocumentService.save_uploaded_file(
            file=mock_file,
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Get documents
        documents = CaseDocumentService.get_case_documents(
            case_id=case.id,
            user_id=client.id,
            user_role=client.role
        )
        
        assert len(documents) == 1
        assert documents[0].id == document.id

    def test_get_case_documents_unauthorized_fails(self, sample_case, sample_lawyer_user):
        """Test that unauthorized users cannot access documents."""
        case = sample_case
        lawyer = sample_lawyer_user
        
        with pytest.raises(ValueError, match="Unauthorized to access this case"):
            CaseDocumentService.get_case_documents(
                case_id=case.id,
                user_id=lawyer.id,
                user_role=lawyer.role
            )

    def test_get_document_by_id_success(self, sample_case, sample_client_user, mock_file):
        """Test getting a specific document by ID."""
        case = sample_case
        client = sample_client_user
        
        # Upload a document first
        document = CaseDocumentService.save_uploaded_file(
            file=mock_file,
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Get document by ID
        retrieved_document = CaseDocumentService.get_document_by_id(
            document_id=document.id,
            user_id=client.id,
            user_role=client.role
        )
        
        assert retrieved_document is not None
        assert retrieved_document.id == document.id

    def test_get_document_by_id_not_found(self, sample_case, sample_client_user):
        """Test getting non-existent document."""
        case = sample_case
        client = sample_client_user
        
        document = CaseDocumentService.get_document_by_id(
            document_id="non-existent-id",
            user_id=client.id,
            user_role=client.role
        )
        
        assert document is None

    def test_delete_document_success(self, sample_case, sample_client_user, mock_file):
        """Test successful document deletion."""
        case = sample_case
        client = sample_client_user
        
        # Upload a document first
        document = CaseDocumentService.save_uploaded_file(
            file=mock_file,
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Delete document
        deleted = CaseDocumentService.delete_document(
            document_id=document.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        assert deleted is True
        
        # Verify document is soft deleted
        retrieved_document = CaseDocumentService.get_document_by_id(
            document_id=document.id,
            user_id=client.id,
            user_role=client.role
        )
        
        assert retrieved_document is None  # Soft deleted documents are not returned

    def test_delete_document_unauthorized_fails(self, sample_case, sample_client_user, sample_lawyer_user, mock_file):
        """Test that users cannot delete others' documents."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Upload document by client
        document = CaseDocumentService.save_uploaded_file(
            file=mock_file,
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Lawyer tries to delete client's document (should fail)
        deleted = CaseDocumentService.delete_document(
            document_id=document.id,
            user_id=lawyer.id,
            actor_role=lawyer.role
        )
        
        assert deleted is False

    def test_can_user_access_document_success(self, sample_case, sample_client_user, mock_file):
        """Test document access permissions."""
        case = sample_case
        client = sample_client_user
        
        # Upload a document first
        document = CaseDocumentService.save_uploaded_file(
            file=mock_file,
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Client can access their own document
        can_access = CaseDocumentService.can_user_access_document(
            document_id=document.id,
            user_id=client.id,
            user_role=client.role
        )
        
        assert can_access is True

    def test_can_user_access_document_unauthorized_fails(self, sample_case, sample_client_user, sample_lawyer_user, mock_file):
        """Test document access permissions for unauthorized users."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Upload document by client
        document = CaseDocumentService.save_uploaded_file(
            file=mock_file,
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Lawyer not assigned to case cannot access
        can_access = CaseDocumentService.can_user_access_document(
            document_id=document.id,
            user_id=lawyer.id,
            user_role=lawyer.role
        )
        
        assert can_access is False
