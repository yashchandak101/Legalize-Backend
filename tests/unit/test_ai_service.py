import pytest
from app.services.ai_service import AIService


class TestAIService:
    """Test cases for AIService."""

    def test_ai_service_initialization(self):
        """Test AI service initialization."""
        ai_service = AIService()
        
        assert ai_service.default_provider in ["openai", "anthropic", "mock"]
        assert ai_service.default_provider == "openai"  # Default should be openai

    def test_generate_case_suggestions_mock(self):
        """Test generating case suggestions with mock provider."""
        ai_service = AIService()
        
        # Override provider to mock for testing
        ai_service.default_provider = "mock"
        ai_service.openai_api_key = None
        ai_service.anthropic_api_key = None
        
        result = ai_service.generate_case_suggestions(
            case_id="test_case_id",
            case_title="Test Case",
            case_description="Test description for case analysis"
        )
        
        assert result is not None
        assert result["entity_id"] == "test_case_id"
        assert result["suggestion_type"] == "case_suggestions"
        assert result["status"] == "completed"
        assert result["provider"] == "mock"
        assert "suggestions" in result
        assert "legal_issues" in result["suggestions"]
        assert "recommended_actions" in result["suggestions"]

    def test_generate_case_suggestions_with_documents(self):
        """Test generating case suggestions with document context."""
        ai_service = AIService()
        
        # Override provider to mock for testing
        ai_service.default_provider = "mock"
        ai_service.openai_api_key = None
        ai_service.anthropic_api_key = None
        
        documents = [
            {"original_filename": "contract.pdf", "mime_type": "application/pdf"},
            {"original_filename": "brief.docx", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        ]
        
        result = ai_service.generate_case_suggestions(
            case_id="test_case_id",
            case_title="Test Case",
            case_description="Test description",
            case_documents=documents
        )
        
        assert result is not None
        assert result["status"] == "completed"
        assert "suggestions" in result

    def test_analyze_document_mock(self):
        """Test document analysis with mock provider."""
        ai_service = AIService()
        
        # Override provider to mock for testing
        ai_service.default_provider = "mock"
        ai_service.openai_api_key = None
        ai_service.anthropic_api_key = None
        
        result = ai_service.analyze_document(
            document_id="test_doc_id",
            document_content="This is a test document content for legal analysis.",
            document_type="contract"
        )
        
        assert result is not None
        assert result["entity_id"] == "test_doc_id"
        assert result["suggestion_type"] == "document_analysis"
        assert result["status"] == "completed"
        assert result["provider"] == "mock"
        assert "suggestions" in result
        assert "key_points" in result["suggestions"]
        assert "legal_terms" in result["suggestions"]

    def test_build_case_suggestion_prompt(self):
        """Test building case suggestion prompt."""
        ai_service = AIService()
        
        prompt = ai_service._build_case_suggestion_prompt(
            title="Test Case Title",
            description="Test case description",
            documents=None
        )
        
        assert "Test Case Title" in prompt
        assert "Test case description" in prompt
        assert "legal_issues" in prompt
        assert "recommended_actions" in prompt

    def test_build_case_suggestion_prompt_with_documents(self):
        """Test building case suggestion prompt with documents."""
        ai_service = AIService()
        
        documents = [
            {"original_filename": "contract.pdf", "mime_type": "application/pdf"},
            {"original_filename": "brief.docx", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        ]
        
        prompt = ai_service._build_case_suggestion_prompt(
            title="Test Case",
            description="Test description",
            documents=documents
        )
        
        assert "contract.pdf" in prompt
        assert "brief.docx" in prompt
        assert "Available Documents:" in prompt

    def test_build_document_analysis_prompt(self):
        """Test building document analysis prompt."""
        ai_service = AIService()
        
        content = "This is a legal contract document with important terms."
        document_type = "contract"
        
        prompt = ai_service._build_document_analysis_prompt(content, document_type)
        
        assert "This is a legal contract document with important terms." in prompt
        assert "contract" in prompt
        assert "key_points" in prompt
        assert "legal_terms" in prompt

    def test_build_document_analysis_prompt_long_content(self):
        """Test building document analysis prompt with long content."""
        ai_service = AIService()
        
        # Create very long content
        long_content = "A" * 15000  # 15,000 characters
        
        prompt = ai_service._build_document_analysis_prompt(long_content, "contract")
        
        # Should truncate content
        assert len(prompt) < len(long_content) + 1000  # Allow for template text
        assert "A" * 10000 in prompt  # First 10,000 characters should be there
        assert "...[truncated]" in prompt  # Should indicate truncation

    def test_generate_mock_suggestions(self):
        """Test generating mock suggestions."""
        ai_service = AIService()
        
        result = ai_service._generate_mock_suggestions("test_id", "case_suggestions")
        
        assert result["entity_id"] == "test_id"
        assert result["suggestion_type"] == "case_suggestions"
        assert result["status"] == "completed"
        assert result["provider"] == "mock"
        assert result["model"] == "mock"
        assert "suggestions" in result
        assert len(result["suggestions"]["legal_issues"]) > 0

    def test_generate_mock_analysis(self):
        """Test generating mock document analysis."""
        ai_service = AIService()
        
        result = ai_service._generate_mock_analysis("test_id", "document_analysis")
        
        assert result["entity_id"] == "test_id"
        assert result["suggestion_type"] == "document_analysis"
        assert result["status"] == "completed"
        assert result["provider"] == "mock"
        assert result["model"] == "mock"
        assert "suggestions" in result
        assert "key_points" in result["suggestions"]
        assert "legal_terms" in result["suggestions"]

    def test_error_handling(self):
        """Test error handling in AI service."""
        ai_service = AIService()
        
        # Test with invalid case_id (should not raise error, but return error status)
        result = ai_service.generate_case_suggestions(
            case_id="",
            case_title="",
            case_description=""
        )
        
        # Should still return a result, but with error status
        assert result is not None
        assert result["entity_id"] == ""
        assert result["status"] == "error"

    def test_error_handling_document(self):
        """Test error handling in document analysis."""
        ai_service = AIService()
        
        # Test with invalid document_id (should not raise error, but return error status)
        result = ai_service.analyze_document(
            document_id="",
            document_content="",
            document_type=""
        )
        
        # Should still return a result, but with error status
        assert result is not None
        assert result["entity_id"] == ""
        assert result["status"] == "error"
