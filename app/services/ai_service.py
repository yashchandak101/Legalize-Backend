import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class AIService:
    """AI Service interface for legal assistance and case analysis."""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.default_provider = os.getenv("AI_PROVIDER", "openai")  # openai or anthropic

    def generate_case_suggestions(self, case_id: str, case_title: str, case_description: str, 
                                 case_documents: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate AI-powered suggestions for a case.
        
        Args:
            case_id: The case ID for context
            case_title: The case title
            case_description: The case description
            case_documents: List of document metadata for context
            
        Returns:
            Dict containing suggestions and metadata
        """
        try:
            # Prepare the prompt
            prompt = self._build_case_suggestion_prompt(
                case_title, case_description, case_documents
            )
            
            # Generate suggestions using the default provider
            if self.default_provider == "openai" and self.openai_api_key:
                return self._generate_with_openai(prompt, case_id, "case_suggestions")
            elif self.default_provider == "anthropic" and self.anthropic_api_key:
                return self._generate_with_anthropic(prompt, case_id, "case_suggestions")
            else:
                # Fallback to mock suggestions if no API key
                return self._generate_mock_suggestions(case_id, "case_suggestions")
                
        except Exception as e:
            logger.error(f"Error generating AI suggestions for case {case_id}: {str(e)}")
            return {
                "case_id": case_id,
                "suggestion_type": "case_suggestions",
                "status": "error",
                "error": str(e),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

    def analyze_document(self, document_id: str, document_content: str, 
                          document_type: str = "unknown") -> Dict[str, Any]:
        """
        Analyze a document using AI.
        
        Args:
            document_id: The document ID
            document_content: The document text content
            document_type: Type of document (contract, brief, etc.)
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Prepare the prompt
            prompt = self._build_document_analysis_prompt(document_content, document_type)
            
            # Generate analysis using the default provider
            if self.default_provider == "openai" and self.openai_api_key:
                return self._generate_with_openai(prompt, document_id, "document_analysis")
            elif self.default_provider == "anthropic" and self.anthropic_api_key:
                return self._generate_with_anthropic(prompt, document_id, "document_analysis")
            else:
                # Fallback to mock analysis
                return self._generate_mock_analysis(document_id, "document_analysis")
                
        except Exception as e:
            logger.error(f"Error analyzing document {document_id}: {str(e)}")
            return {
                "document_id": document_id,
                "suggestion_type": "document_analysis",
                "status": "error",
                "error": str(e),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

    def _build_case_suggestion_prompt(self, title: str, description: str, 
                                     documents: List[Dict[str, Any]] = None) -> str:
        """Build the prompt for case suggestions."""
        prompt = f"""
As a legal AI assistant, analyze the following case and provide actionable suggestions:

Case Title: {title}
Case Description: {description}
"""
        
        if documents:
            prompt += "\nAvailable Documents:\n"
            for doc in documents[:5]:  # Limit to first 5 documents
                prompt += f"- {doc.get('original_filename', 'Unknown')}: {doc.get('mime_type', 'Unknown')}\n"
        
        prompt += """
Please provide suggestions in the following JSON format:
{
    "legal_issues": ["Issue 1", "Issue 2"],
    "recommended_actions": ["Action 1", "Action 2"],
    "relevant_laws": ["Law 1", "Law 2"],
    "timeline_suggestions": ["Timeline item 1", "Timeline item 2"],
    "risk_assessment": "Low/Medium/High risk with explanation",
    "next_steps": ["Step 1", "Step 2"]
}

Focus on practical, actionable advice that would be helpful for a lawyer handling this case.
"""
        return prompt

    def _build_document_analysis_prompt(self, content: str, document_type: str) -> str:
        """Build the prompt for document analysis."""
        # Truncate content if too long
        if len(content) > 10000:
            content = content[:10000] + "...[truncated]"
        
        prompt = f"""
As a legal AI assistant, analyze the following {document_type} document:

Document Content:
{content}

Please provide analysis in the following JSON format:
{{
    "document_type": "{document_type}",
    "key_points": ["Point 1", "Point 2"],
    "legal_terms": ["Term 1", "Term 2"],
    "risks": ["Risk 1", "Risk 2"],
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "summary": "Brief summary of the document"
}}

Focus on identifying key legal terms, potential risks, and actionable recommendations.
"""
        return prompt

    def _generate_with_openai(self, prompt: str, entity_id: str, suggestion_type: str) -> Dict[str, Any]:
        """Generate suggestions using OpenAI API."""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful legal AI assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                suggestions = json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    suggestions = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON response")
            
            return {
                "entity_id": entity_id,
                "suggestion_type": suggestion_type,
                "status": "completed",
                "suggestions": suggestions,
                "provider": "openai",
                "model": "gpt-4",
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    def _generate_with_anthropic(self, prompt: str, entity_id: str, suggestion_type: str) -> Dict[str, Any]:
        """Generate suggestions using Anthropic Claude API."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            
            # Try to parse JSON
            try:
                suggestions = json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    suggestions = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON response")
            
            return {
                "entity_id": entity_id,
                "suggestion_type": suggestion_type,
                "status": "completed",
                "suggestions": suggestions,
                "provider": "anthropic",
                "model": "claude-3-sonnet",
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise

    def _generate_mock_suggestions(self, entity_id: str, suggestion_type: str) -> Dict[str, Any]:
        """Generate mock suggestions when no API is available."""
        mock_suggestions = {
            "legal_issues": [
                "Contract interpretation needed",
                "Statute of limitations consideration",
                "Jurisdiction verification required"
            ],
            "recommended_actions": [
                "Review all relevant contracts",
                "Research applicable statutes",
                "Verify court jurisdiction"
            ],
            "relevant_laws": [
                "Contract Law Act",
                "Civil Procedure Code",
                "Statute of Limitations Act"
            ],
            "timeline_suggestions": [
                "Initial client consultation completed",
                "Document review phase: 2-3 weeks",
                "Legal research: 1-2 weeks"
            ],
            "risk_assessment": "Medium risk - requires careful documentation and timely filing",
            "next_steps": [
                "Gather all relevant documents",
                "Conduct legal research",
                "Prepare initial case strategy"
            ]
        }
        
        return {
            "entity_id": entity_id,
            "suggestion_type": suggestion_type,
            "status": "completed",
            "suggestions": mock_suggestions,
            "provider": "mock",
            "model": "mock",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    def _generate_mock_analysis(self, entity_id: str, suggestion_type: str) -> Dict[str, Any]:
        """Generate mock document analysis when no API is available."""
        mock_analysis = {
            "document_type": "unknown",
            "key_points": [
                "Document contains legal terminology",
                "Multiple parties involved in agreement",
                "Specific dates and deadlines mentioned"
            ],
            "legal_terms": [
                "Indemnification clause",
                "Force majeure provision",
                "Governing law specification"
            ],
            "risks": [
                "Ambiguous language in section 3",
                "Missing signatures on page 5",
                "Unclear dispute resolution process"
            ],
            "recommendations": [
                "Clarify ambiguous language",
                "Ensure all signatures are present",
                "Define dispute resolution mechanism"
            ],
            "summary": "This document appears to be a legal agreement that requires careful review of key clauses and proper execution."
        }
        
        return {
            "entity_id": entity_id,
            "suggestion_type": suggestion_type,
            "status": "completed",
            "suggestions": mock_analysis,
            "provider": "mock",
            "model": "mock",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }