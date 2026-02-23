import pytest
from app.core.extensions import db
from app.services.case_comment_service import CaseCommentService
from app.services.case_service import CaseService
from app.services.auth_service import AuthService
from app.domain.enums import RoleEnum
from app.models.case_comment import CaseComment
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


class TestCaseCommentService:
    """Test cases for CaseCommentService."""

    def test_create_comment_success(self, sample_case, sample_client_user):
        """Test successful comment creation."""
        case = sample_case
        client = sample_client_user
        
        comment = CaseCommentService.create_comment(
            case_id=case.id,
            user_id=client.id,
            body="This is a test comment",
            is_internal=False,
            actor_role=client.role
        )
        
        assert comment is not None
        assert comment.case_id == case.id
        assert comment.user_id == client.id
        assert comment.body == "This is a test comment"
        assert comment.is_internal is False

    def test_create_internal_comment_lawyer_success(self, sample_case, sample_lawyer_user):
        """Test successful internal comment creation by lawyer."""
        case = sample_case
        lawyer = sample_lawyer_user
        
        comment = CaseCommentService.create_comment(
            case_id=case.id,
            user_id=lawyer.id,
            body="Internal lawyer note",
            is_internal=True,
            actor_role=lawyer.role
        )
        
        assert comment is not None
        assert comment.is_internal is True

    def test_create_internal_comment_client_fails(self, sample_case, sample_client_user):
        """Test that clients cannot create internal comments."""
        case = sample_case
        client = sample_client_user
        
        with pytest.raises(ValueError, match="Only lawyers and admins can create internal comments"):
            CaseCommentService.create_comment(
                case_id=case.id,
                user_id=client.id,
                body="Internal comment",
                is_internal=True,
                actor_role=client.role
            )

    def test_create_comment_empty_body_fails(self, sample_case, sample_client_user):
        """Test that empty comment body fails."""
        case = sample_case
        client = sample_client_user
        
        with pytest.raises(ValueError, match="Comment body cannot be empty"):
            CaseCommentService.create_comment(
                case_id=case.id,
                user_id=client.id,
                body="",
                actor_role=client.role
            )

    def test_get_case_comments_client_view(self, sample_case, sample_client_user, sample_lawyer_user):
        """Test that clients only see non-internal comments."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Create public comment
        public_comment = CaseCommentService.create_comment(
            case_id=case.id,
            user_id=client.id,
            body="Public comment",
            is_internal=False,
            actor_role=client.role
        )
        
        # Create internal comment
        internal_comment = CaseCommentService.create_comment(
            case_id=case.id,
            user_id=lawyer.id,
            body="Internal comment",
            is_internal=True,
            actor_role=lawyer.role
        )
        
        # Client should only see public comments
        comments = CaseCommentService.get_case_comments(
            case_id=case.id,
            user_id=client.id,
            user_role=client.role
        )
        
        assert len(comments) == 1
        assert comments[0].id == public_comment.id
        assert comments[0].is_internal is False

    def test_get_case_comments_lawyer_view(self, sample_case, sample_client_user, sample_lawyer_user):
        """Test that lawyers see all comments."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Create public comment
        public_comment = CaseCommentService.create_comment(
            case_id=case.id,
            user_id=client.id,
            body="Public comment",
            is_internal=False,
            actor_role=client.role
        )
        
        # Create internal comment
        internal_comment = CaseCommentService.create_comment(
            case_id=case.id,
            user_id=lawyer.id,
            body="Internal comment",
            is_internal=True,
            actor_role=lawyer.role
        )
        
        # Lawyer should see both comments
        comments = CaseCommentService.get_case_comments(
            case_id=case.id,
            user_id=lawyer.id,
            user_role=lawyer.role
        )
        
        assert len(comments) == 2
        comment_ids = [c.id for c in comments]
        assert public_comment.id in comment_ids
        assert internal_comment.id in comment_ids

    def test_update_comment_success(self, sample_case, sample_client_user):
        """Test successful comment update."""
        case = sample_case
        client = sample_client_user
        
        # Create comment first
        comment = CaseCommentService.create_comment(
            case_id=case.id,
            user_id=client.id,
            body="Original comment",
            actor_role=client.role
        )
        
        # Update comment
        updated_comment = CaseCommentService.update_comment(
            comment_id=comment.id,
            user_id=client.id,
            body="Updated comment",
            actor_role=client.role
        )
        
        assert updated_comment is not None
        assert updated_comment.body == "Updated comment"

    def test_update_comment_unauthorized_fails(self, sample_case, sample_client_user, sample_lawyer_user):
        """Test that users cannot update others' comments."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Create comment by client
        comment = CaseCommentService.create_comment(
            case_id=case.id,
            user_id=client.id,
            body="Original comment",
            actor_role=client.role
        )
        
        # Lawyer tries to update client's comment (should fail)
        updated = CaseCommentService.update_comment(
            comment_id=comment.id,
            user_id=lawyer.id,
            body="Hijacked comment",
            actor_role=lawyer.role
        )
        
        assert updated is None

    def test_delete_comment_success(self, sample_case, sample_client_user):
        """Test successful comment deletion."""
        case = sample_case
        client = sample_client_user
        
        # Create comment first
        comment = CaseCommentService.create_comment(
            case_id=case.id,
            user_id=client.id,
            body="Comment to delete",
            actor_role=client.role
        )
        
        # Delete comment
        deleted = CaseCommentService.delete_comment(
            comment_id=comment.id,
            user_id=client.id,
            actor_role=client.role
        )
        
        assert deleted is True

    def test_delete_comment_unauthorized_fails(self, sample_case, sample_client_user, sample_lawyer_user):
        """Test that users cannot delete others' comments."""
        case = sample_case
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Create comment by client
        comment = CaseCommentService.create_comment(
            case_id=case.id,
            user_id=client.id,
            body="Comment to delete",
            actor_role=client.role
        )
        
        # Lawyer tries to delete client's comment (should fail)
        deleted = CaseCommentService.delete_comment(
            comment_id=comment.id,
            user_id=lawyer.id,
            actor_role=lawyer.role
        )
        
        assert deleted is False
