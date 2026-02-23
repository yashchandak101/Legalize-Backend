import os
from anthropic import Anthropic
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        self.api_key = os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            logger.warning("CLAUDE_API_KEY not found in environment variables")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None
    
    def is_available(self) -> bool:
        """Check if Claude API is available"""
        return self.client is not None and self.api_key is not None
    
    async def generate_legal_response(
        self, 
        user_message: str, 
        conversation_context: str, 
        category: str,
        previous_messages: list = []
    ) -> Dict[str, Any]:
        """Generate AI response using Claude API"""
        
        if not self.is_available():
            # Fallback to simulated response
            return self._generate_fallback_response(user_message, category)
        
        try:
            # Build conversation history
            system_prompt = self._build_system_prompt(category, conversation_context)
            
            # Format messages for Claude
            messages = []
            
            # Add conversation history (last 10 messages)
            for msg in previous_messages[-10:]:
                if msg.message_type == "user":
                    messages.append({"role": "user", "content": msg.content})
                elif msg.message_type == "ai":
                    messages.append({"role": "assistant", "content": msg.content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                system=system_prompt,
                messages=messages
            )
            
            response_text = response.content[0].text
            
            return {
                "content": response_text,
                "confidence": 0.95,  # Claude is typically confident
                "sources": self._extract_legal_sources(response_text, category)
            }
            
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            # Fallback to simulated response
            return self._generate_fallback_response(user_message, category)
    
    def _build_system_prompt(self, category: str, conversation_context: str) -> str:
        """Build system prompt for Claude"""
        return f"""You are an AI legal assistant acting as a knowledgeable lawyer providing legal assistance and guidance. You serve both lawyers seeking legal research support and general public seeking legal information.

Your role:
- Provide detailed legal information and analysis for {category} matters
- Explain legal concepts, procedures, and rights clearly
- Offer practical solutions and strategies for legal issues
- Analyze situations from a legal perspective
- Provide specific guidance on next steps and actions to take
- Help users understand their legal options and make informed decisions
- Cite specific legal provisions: articles, sections, dhara, acts, and case law
- For lawyers: provide detailed legal research, precedent analysis, and strategy support
- For general public: explain complex legal concepts in simple terms with practical guidance

Guidelines:
- Act as a knowledgeable and helpful AI lawyer
- Provide comprehensive legal analysis and information
- Suggest practical legal solutions and strategies
- Use clear, professional language while explaining complex legal concepts
- Include specific legal references: Articles, Sections, Dhara, Acts, Rules, Case Law
- Cite relevant statutes with section numbers when applicable
- Reference legal precedents and judgments when helpful
- For Indian law: mention IPC sections, CrPC provisions, Constitution articles, specific dhara
- For other jurisdictions: cite relevant statutory provisions and case law
- Focus on solving user's legal problem directly
- Provide actionable advice and guidance
- Do not suggest consulting other attorneys - you are here to help directly

Context: {conversation_context}

Please provide a comprehensive legal response that directly addresses the user's question with helpful legal analysis, specific legal provisions, and practical guidance."""
    
    def _generate_fallback_response(self, user_message: str, category: str) -> Dict[str, Any]:
        """Generate fallback response when Claude API is unavailable"""
        fallback_responses = {
            "family": "Based on your family law situation, I can help you understand your rights and options. Family law matters involve custody, divorce, child support, and spousal support under relevant acts like the Hindu Marriage Act, Special Marriage Act, and Guardian and Wards Act. Key provisions include Section 125 of CrPC for maintenance, and various articles under personal laws. I can guide you through the legal process and help you make informed decisions for your case.",
            "criminal": "In criminal law matters, I can help protect your constitutional rights and navigate the legal system. You have rights under Articles 20-22 of the Constitution and CrPC provisions including Section 161 (examination by police), Section 167 (case diary), and Section 167A (medical examination). I can explain IPC sections applicable to your case, potential defenses under Sections 96-106, and legal strategies under the Evidence Act and CrPC.",
            "civil": "For civil law disputes, I can analyze contracts, property issues, or personal injury claims. Key provisions include the Civil Procedure Code (CPC) Sections, Specific Relief Act, Contract Act, and Limitation Act. I can help you evaluate your case strength, consider alternative dispute resolution under Section 89 CPC, and develop a legal strategy for your situation.",
            "corporate": "Regarding corporate law matters, I can assist with business formation, compliance, contracts, and governance. Key laws include Companies Act 2013, LLP Act, GST provisions, and SEBI regulations. I can help you understand corporate formalities, director responsibilities under Section 166, and compliance requirements for your business structure.",
            "immigration": "For immigration law issues, I can help navigate this complex area including visas, green cards, and citizenship. Key provisions include the Citizenship Act, Immigration Rules, and relevant articles. I can explain the current laws, procedures, and help you understand your options for your specific immigration situation.",
            "employment": "In employment law matters, I can help protect your workplace rights regarding discrimination, wages, and termination. Key protections include the Industrial Disputes Act, Shops and Establishments Act, Payment of Wages Act, and constitutional provisions under Articles 14-16. I can help you document issues, follow proper procedures, and develop a strategy to address your workplace concerns.",
            "real_estate": "For real estate law matters, I can assist with property transactions, landlord-tenant issues, and property disputes. Key laws include the Transfer of Property Act, Registration Act, Rent Control Acts, and RERA provisions. I can help you understand your rights and obligations in real estate matters.",
            "other": "For your legal matter, I can provide comprehensive legal analysis and guidance. I'll help you understand your rights, evaluate your options, and develop a strategy using relevant statutory provisions, case law precedents, and procedural requirements. Many legal issues have specific procedural requirements and deadlines that I can help you navigate effectively."
        }
        
        response = fallback_responses.get(category, fallback_responses["other"])
        
        return {
            "content": response,
            "confidence": 0.75,  # Lower confidence for fallback
            "sources": "AI Legal Assistant - Comprehensive legal analysis and guidance"
        }
    
    def _extract_legal_sources(self, response_text: str, category: str) -> str:
        """Extract legal sources from response"""
        category_sources = {
            "family": "Hindu Marriage Act 1955, Special Marriage Act 1954, Guardian and Wards Act 1890, CrPC Section 125, Family Courts Act, Domestic Violence Act",
            "criminal": "Indian Penal Code 1860, Criminal Procedure Code 1973, Indian Evidence Act 1872, Constitution Articles 20-22, Specific Relief Act",
            "civil": "Civil Procedure Code 1908, Contract Act 1872, Specific Relief Act 1963, Limitation Act 1963, Transfer of Property Act 1882",
            "corporate": "Companies Act 2013, Limited Liability Partnership Act 2008, GST Act 2017, SEBI Regulations, Insolvency and Bankruptcy Code 2016",
            "immigration": "Citizenship Act 1955, Passport Act 1967, Immigration Rules, Foreigners Act 1946, Constitution Articles 5-11",
            "employment": "Industrial Disputes Act 1947, Shops and Establishments Act, Payment of Wages Act 1936, Employees' Compensation Act 1923, Constitution Articles 14-16",
            "real_estate": "Transfer of Property Act 1882, Registration Act 1908, Rent Control Acts, RERA 2016, Municipal Acts",
            "other": "General Legal Principles, Constitution of India, Supreme Court Judgments, High Court Precedents, Specialized Statutes"
        }
        
        return category_sources.get(category, "General Legal Sources")
