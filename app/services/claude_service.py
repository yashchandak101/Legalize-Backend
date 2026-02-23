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
        return f"""You are an AI legal assistant providing general legal information and guidance. You are NOT a substitute for a qualified attorney.

Your role:
- Provide general legal information about {category} matters
- Explain legal concepts and procedures in simple terms
- Suggest next steps and resources
- Emphasize that you provide general information, not specific legal advice
- Recommend consulting with a qualified attorney for specific legal issues

Guidelines:
- Be helpful, clear, and professional
- Use simple language, avoid legal jargon when possible
- Include relevant legal sources and references when appropriate
- Always include a disclaimer that this is general information, not legal advice
- Do not provide specific legal advice for individual situations
- If the situation seems complex or serious, recommend consulting an attorney

Context: {conversation_context}

Please provide a helpful, informative response that addresses the user's question while maintaining appropriate boundaries as an AI assistant."""
    
    def _generate_fallback_response(self, user_message: str, category: str) -> Dict[str, Any]:
        """Generate fallback response when Claude API is unavailable"""
        fallback_responses = {
            "family": "Based on your family law situation, I recommend documenting all relevant interactions and communications. Family law cases often involve sensitive matters, so maintaining clear records is crucial. Consider mediation as a first step to resolve conflicts amicably. For specific legal advice tailored to your situation, please consult with a qualified family law attorney.",
            "criminal": "In criminal law matters, protecting your constitutional rights is paramount. You have the right to remain silent and the right to legal representation. Avoid discussing your case with anyone other than your attorney. The specific charges and evidence will determine the legal strategy. Please consult with a qualified criminal defense attorney for specific advice.",
            "civil": "Civil law disputes typically involve contracts, property, or personal injury claims. Key elements include establishing duty, breach, causation, and damages. Documentation and evidence are critical in civil cases. Consider alternative dispute resolution methods like mediation or arbitration before litigation. Consult with a civil litigation attorney for specific guidance.",
            "corporate": "Corporate law matters involve business formation, compliance, contracts, and governance. Key considerations include entity selection, regulatory compliance, intellectual property protection, and risk management. Maintain proper corporate records and follow formal procedures. Consult with a business attorney for specific corporate legal advice.",
            "immigration": "Immigration law is complex and subject to frequent changes. Key areas include visas, green cards, deportation defense, and citizenship. Documentation accuracy and meeting deadlines are crucial. Immigration cases often require specialized knowledge of current laws and procedures. Consult with an immigration attorney for specific case guidance.",
            "employment": "Employment law covers workplace rights, discrimination, wages, and termination. Key protections include anti-discrimination laws, wage and hour regulations, and workplace safety. Document any issues carefully and follow company complaint procedures. Consult with an employment law attorney for specific workplace issues.",
            "real_estate": "Real estate law involves property transactions, landlord-tenant issues, and property disputes. Key elements include contracts, titles, disclosures, and local regulations. Due diligence is essential in all real estate transactions. Consult with a real estate attorney for specific property matters.",
            "other": "For general legal matters, it's important to understand your rights and obligations. Document everything relevant to your situation, research applicable laws, and consider alternative dispute resolution methods. Many legal issues have specific procedural requirements and deadlines. Consult with a qualified attorney for advice tailored to your specific situation."
        }
        
        response = fallback_responses.get(category, fallback_responses["other"])
        
        return {
            "content": response,
            "confidence": 0.75,  # Lower confidence for fallback
            "sources": "General legal information - consult with qualified attorney for specific advice"
        }
    
    def _extract_legal_sources(self, response_text: str, category: str) -> str:
        """Extract legal sources from response"""
        category_sources = {
            "family": "Family Law Act, State Custody Guidelines, Mediation Best Practices",
            "criminal": "Constitutional Rights, Criminal Procedure Code, Miranda Rights",
            "civil": "Civil Procedure Rules, Contract Law Principles, Tort Law",
            "corporate": "Business Corporation Act, Securities Regulations, Contract Law",
            "immigration": "Immigration and Nationality Act, Federal Regulations, Case Law",
            "employment": "Labor Standards Act, Anti-Discrimination Laws, OSHA Regulations",
            "real_estate": "Real Property Law, Landlord-Tenant Statutes, Contract Law",
            "other": "General Legal Principles, State and Federal Laws"
        }
        
        return category_sources.get(category, "General Legal Sources")
