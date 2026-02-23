import pytest
from app.core.extensions import db
from app.services.case_ai_suggestion_service import CaseAISuggestionService
from app.services.case_service import CaseService
from app.services.auth_service import AuthService
from app.domain.enums import RoleEnum
from app.models.case_ai_suggestion import CaseAISuggestion
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


class TestCaseAISuggestionService:
    """Test cases for CaseAISuggestionService."""

    def test_create_case_suggestion_success(self, sample_case, sample_client_user):
        """Test successful case suggestion creation."""
        case = sample_case
        client = sample_client_user
        
        suggestion = CaseAISuggestionService.create_case_suggestion(
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role,
            async_processing=False
        )
        
        assert suggestion is not None
        assert suggestion.case_id == case.id
        assert suggestion.user_id == client.id
        assert suggestion.suggestion_type == "case_suggestions"
        assert suggestion.status == "completed"  # Processed synchronously
        assert suggestion.suggestions is not None

    def test_create_case_suggestion_async(self, sample_case, sample_client_user):
        """Test case suggestion creation with async processing."""
        case = sample_case
        client = sample_client_user
        
        suggestion = CaseAISuggestionService.create_case_suggestion(
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role,
            async_processing=True
        )
        
        assert suggestion is not None
        assert suggestion.case_id == case.id
        assert suggestion.user_id == client.id
        assert suggestion.suggestion_type == "case_suggestions"
        assert suggestion.status == "pending"  # Not processed yet

    def test_create_case_suggestion_unauthorized_fails(self, sample_case, sample_client_user, sample_lawyer_user):
        """Test that unauthorized users cannot create suggestions."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Create a different user who doesn't have access
        other_user = User(
            email="other@test.example",
            password="hashed",
            role=RoleEnum.USER.value,
        )
        db.session.add(other_user)
        db.session.flush()
        
        with pytest.raises(ValueError, match="Unauthorized to access this case"):
            CaseAISuggestionService.create_case_suggestion(
                case_id=case.id,
                user_id=other_user.id,
                actor_role=other_user.role
            )

    def test_get_case_suggestions_authorized(self, sample_case, sample_client_user):
        """Test getting case suggestions for authorized user."""
        case = sample_case
        client = sample_client_user
        
        # Create a suggestion first
        suggestion = CaseAISuggestionService.create_case_suggestion(
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Get suggestions
        suggestions = CaseAISuggestionService.get_case_suggestions(
            case_id=case.id,
            user_id=client.id,
            user_role=client.role
        )
        
        assert len(suggestions) == 1
        assert suggestions[0].id == suggestion.id

    def test_get_case_suggestions_unauthorized_fails(self, sample_case, sample_client_user, sample_lawyer_user):
        """Test that unauthorized users cannot get case suggestions."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Create a suggestion for client
        suggestion = CaseAISuggestionService.create_case_suggestion(
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Try to get suggestions as unauthorized user
        other_user = User(
            email="other@test.example",
            password="hashed",
            role=RoleEnum.USER.value,
        )
        db.session.add(other_user)
        db.session.flush()
        
        with pytest.raises(ValueError, match="Unauthorized to access this case"):
            CaseAISuggestionService.get_case_suggestions(
                case_id=case.id,
                user_id=other_user.id,
                user_role=other_user.role
            )

    def test_get_user_suggestions(self, sample_case, sample_client_user):
        """Test getting user's suggestions."""
        case = sample_case
        client = sample_client_user
        
        # Create multiple suggestions
        suggestion1 = CaseAISuggestionService.create_case_suggestion(
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        suggestion2 = CaseAISuggestionService.create_case_suggestion(
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Get user suggestions
        suggestions = CaseAISuggestionService.get_user_suggestions(client.id)
        
        assert len(suggestions) == 2
        suggestion_ids = [s.id for s in suggestions]
        assert suggestion1.id in suggestion_ids
        assert suggestion2.id in suggestion_ids

    def test_get_suggestion_by_id_authorized(self, sample_case, sample_client_user):
        """Test getting suggestion by ID for authorized user."""
        case = sample_case
        client = sample_client_user
        
        # Create a suggestion
        suggestion = CaseAISuggestionService.create_case_suggestion(
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Get suggestion by ID
        retrieved_suggestion = CaseAISuggestionService.get_suggestion_by_id(
            suggestion_id=suggestion.id,
            user_id=client.id,
            user_role=client.role
        )
        
        assert retrieved_suggestion is not None
        assert retrieved_suggestion.id == suggestion.id

    def test_get_suggestion_by_id_unauthorized_fails(self, sample_case, sample_client_user, sample_lawyer_user):
        """Test that unauthorized users cannot get suggestion by ID."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Create a suggestion for client
        suggestion = CaseAISuggestionService.create_case_suggestion(
            case_id=case.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        # Try to get suggestion as unauthorized user
        other_user = User(
            email="other@test.example",
            password="hashed",
            role=RoleEnum.USER.value,
        )
        db.session.add(other_user)
        db.session.flush()
        
        with pytest.raises(ValueError, match="Unauthorized to access this suggestion"):
            CaseAISuggestionService.get_suggestion_by_id(
                suggestion_id=suggestion.id,
                user_id=other_user.id,
                user_role=other_user.role
            )

    def test_get_suggestion_by_id_not_found(self, sample_case, sample_client_user):
        """Test getting non-existent suggestion."""
        case = sample_case
        client = sample_client_user
        
        result = CaseAISuggestionService.get_suggestion_by_id(
            suggestion_id="non_existent_id",
            user_id=client.id,
            user_role=client.role
        )
        
        assert result is None

    def test_rate_limiting_case_suggestions(self, sample_case, sample_client_user):
        """Test rate limiting for case suggestions."""
        case = sample_case
        client = sample_client_user
        
        # Create suggestions up to the limit (5 per day)
        for i in range(5):
            suggestion = CaseAISuggestionService.create_case_suggestion(
                case_id=case.id,
                user_id=client.id,
                actor_role=client.role
            )
            assert suggestion.status == "completed"
        
        # The 6th one should fail due to rate limiting
        with pytest.raises(ValueError, match="Daily limit of 5 AI suggestions per case reached"):
            CaseAISuggestionService.create_case_suggestion(
                case_id=case.id,
                user_id=client.id,
                actor_role=client.role
            )

    def test_process_case_suggestion_success(self, sample_case, sample_client_user):
        """Test successful processing of case suggestion."""
        case = sample_case
        client = sample_client_user
        
        # Create suggestion in pending state
        suggestion = CaseAISuggestion(
            case_id=case.id,
            user_id=client.id,
            suggestion_type="case_suggestions",
            status="pending"
        )
        suggestion = CaseAISuggestionRepository.create(suggestion)
        
        # Process the suggestion
        success = CaseAISuggestionService._process_case_suggestion(suggestion.id)
        
        assert success is True
        
        # Check that suggestion was updated
        updated_suggestion = CaseAISuggestionRepository.get_by_id(suggestion.id)
        assert updated_suggestion.status == "completed"
        assert updated_suggestion.suggestions is not None

    def test_process_case_suggestion_not_found(self):
        """Test processing non-existent suggestion."""
        success = CaseAISuggestionService._process_case_suggestion("non_existent_id")
        assert success is False

    def test_create_document_suggestion_success(self, sample_case, sample_client_user):
        """Test successful document suggestion creation."""
        case = sample_case
        client = sample_client_user
        
        # Create a document first
        from app.models.case_document import CaseDocument
        document = CaseDocument(
            case_id=case.id,
            uploaded_by=client.id,
            filename="test_doc.pdf",
            original_filename="test_document.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            storage_path="/fake/path/test_doc.pdf"
        )
        document = CaseDocumentRepository.create(document)
        
        suggestion = CaseAISuggestionService.create_document_suggestion(
            document_id=document.id,
            user_id=client.id,
            actor_role=client.role,
            async_processing=False
        )
        
        assert suggestion is not None
        assert suggestion.case_id == case.id
        assert suggestion.user_id == client.id
        assert suggestion.suggestion_type == "document_analysis"
        assert suggestion.status == "completed"  # Processed synchronously

    def test_create_document_suggestion_unauthorized_fails(self, sample_case, sample_client_user, sample_lawyer_user):
        """Test that unauthorized users cannot create document suggestions."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Create a document first
        from app.models.case_document import CaseDocument
        document = CaseDocument(
            case_id=case.id,
            uploaded_by=client.id,
            filename="test_doc.pdf",
            original_filename="test_document.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            storage_path="/fake/path/test_doc.pdf"
        )
        document = CaseDocumentRepository.create(document)
        
        # Create a different user who doesn't have access
        other_user = User(
            email="other@test.example",
            password="hashed",
            role=RoleEnum.USER.value,
        )
        db.session.add(other_user)
        db.session.flush()
        
        with pytest.raises(ValueError, match="Unauthorized to access this document"):
            CaseAISuggestionService.create_document_suggestion(
                document_id=document.id,
                user_id=other_user.id,
                actor_role=other_user.role
            )

    def test_extract_document_text(self):
        """Test document text extraction."""
        # Create a mock document
        class MockDocument:
            def __init__(self, storage_path, original_filename):
                self.storage_path = storage_path
                self.original_filename = original_filename
        
        # Create a temporary file for testing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("This is test document content")
            temp_path = f.name
        
        try:
            document = MockDocument(temp_path, "test.txt")
            content = CaseAISuggestionService._extract_document_text(document)
            
            assert content == "This is test document content"
            
        finally:
            os.unlink(temp_path)

    def test_classify_document_type(self):
        """Test document type classification."""
        # Test various file types
        assert CaseAISuggestionService._classify_document_type("contract.pdf", "application/pdf") == "pdf"
        assert CaseAISuggestionService._classify_document_type("agreement.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document") == "contract"
        assert CaseAISuggestionService._classify_document_type("brief.txt", "text/plain") == "text_document"
        assert CaseAISuggestionService._classify_document_type("data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") == "spreadsheet"
        assert CaseAISuggestionService._classify_document_type("presentation.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation") == "presentation"
        
        # Test filename-based classification
        assert CaseAISuggestionService._classify_document_type("legal_contract.pdf", "application/pdf") == "contract"
        assert CaseAISuggestionService._classify_document_type("court_brief.doc", "application/msword") == "legal_brief"
        assert CaseAISuggestionService._classify_document_type("motion_to_dismiss.pdf", "application/pdf") == "legal_motion"
        
        # Test unknown type
        assert CaseAISuggestionService._classify_document_type("unknown.xyz", "application/unknown") == "unknown"
