import os
import uuid
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from app.core.extensions import db
from app.models.legal_chat import LegalChat
from app.models.legal_chat_message import LegalChatMessage
from app.models.legal_chat_document import LegalChatDocument


class LegalChatService:

    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

    @staticmethod
    def create_chat(user_id, title, category):
        """Create a new legal chat session."""
        chat = LegalChat(
            user_id=user_id,
            title=title,
            category=category,
            ai_context=f"Legal assistance chat about {category} matters. User is seeking legal guidance and information."
        )
        db.session.add(chat)
        db.session.commit()
        
        # Add welcome message
        welcome_message = LegalChatMessage(
            chat_id=chat.id,
            user_id=user_id,
            content=f"Hello! I'm your AI legal assistant. I'm here to help you with your {category} legal matters. Please describe your situation, and feel free to upload any relevant documents. Remember, I provide general legal information and guidance, but for specific legal advice, you may need to consult with a qualified attorney.",
            message_type="ai",
            ai_confidence=0.95
        )
        db.session.add(welcome_message)
        db.session.commit()
        
        return chat

    @staticmethod
    def get_user_chats(user_id):
        """Get all chat sessions for a user."""
        return LegalChat.query.filter_by(user_id=user_id).order_by(LegalChat.updated_at.desc()).all()

    @staticmethod
    def get_chat(chat_id, user_id):
        """Get a specific chat session for a user."""
        return LegalChat.query.filter_by(id=chat_id, user_id=user_id).first()

    @staticmethod
    def add_message(chat_id, user_id, content, message_type="user"):
        """Add a message to a chat session."""
        message = LegalChatMessage(
            chat_id=chat_id,
            user_id=user_id,
            content=content,
            message_type=message_type
        )
        db.session.add(message)
        
        # Update chat timestamp
        chat = LegalChat.query.get(chat_id)
        if chat:
            chat.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        return message

    @staticmethod
    def generate_ai_response(chat_id, user_id, user_message):
        """Generate AI response to user message."""
        chat = LegalChat.query.get(chat_id)
        if not chat:
            return None
        
        # Get recent conversation context
        recent_messages = LegalChatMessage.query.filter_by(chat_id=chat_id)\
            .order_by(LegalChatMessage.created_at.desc())\
            .limit(10).all()
        
        # Build context for AI
        context = f"Chat Context: {chat.ai_context}\n\n"
        context += "Recent Messages:\n"
        for msg in reversed(recent_messages):
            sender = "User" if msg.message_type == "user" else "AI Assistant"
            context += f"{sender}: {msg.content}\n"
        
        # Generate AI response (simulated - replace with actual AI service)
        ai_response = LegalChatService._simulate_ai_response(user_message, chat.category)
        
        # Add AI response to chat
        ai_message = LegalChatMessage(
            chat_id=chat_id,
            user_id=user_id,
            content=ai_response["content"],
            message_type="ai",
            ai_confidence=ai_response["confidence"],
            ai_sources=ai_response["sources"]
        )
        db.session.add(ai_message)
        db.session.commit()
        
        return ai_message

    @staticmethod
    def _simulate_ai_response(user_message, category):
        """Simulate AI response (replace with actual AI service)."""
        responses = {
            "family": [
                {
                    "content": "Based on what you've described, this appears to be a family law matter. Common considerations in family law cases include child custody arrangements, division of assets, and spousal support. It's important to gather all relevant documentation and consider mediation as a first step. Would you like me to elaborate on any specific aspect?",
                    "confidence": 0.85,
                    "sources": "Family Law Act, State Custody Guidelines"
                },
                {
                    "content": "Family law matters can be emotionally challenging. I recommend documenting all relevant interactions, keeping communications civil, and focusing on the best interests of any children involved. Legal processes vary by jurisdiction, so local regulations may apply to your situation.",
                    "confidence": 0.82,
                    "sources": "Family Court Procedures, Child Welfare Guidelines"
                }
            ],
            "criminal": [
                {
                    "content": "Criminal law matters require immediate attention to your rights. You have the right to remain silent and the right to legal representation. It's crucial to avoid discussing your case with anyone other than your attorney. The specific charges and evidence will determine the legal strategy moving forward.",
                    "confidence": 0.90,
                    "sources": "Constitutional Rights, Criminal Procedure Code"
                }
            ],
            "civil": [
                {
                    "content": "Civil law disputes typically involve contracts, property, or personal injury claims. Key elements include establishing duty, breach, causation, and damages. Documentation and evidence are critical in civil cases. Consider alternative dispute resolution methods before litigation.",
                    "confidence": 0.87,
                    "sources": "Civil Procedure Rules, Contract Law Principles"
                }
            ]
        }
        
        import random
        category_responses = responses.get(category, responses["civil"])
        return random.choice(category_responses)

    @staticmethod
    def upload_document(chat_id, user_id, file):
        """Upload and process a document for a chat session."""
        if not file or file.filename == '':
            raise ValueError("No file selected")
        
        if not LegalChatService.allowed_file(file.filename):
            raise ValueError("File type not allowed")
        
        if len(file.read()) > LegalChatService.MAX_FILE_SIZE:
            raise ValueError("File too large")
        
        file.seek(0)  # Reset file pointer
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join('uploads', 'legal_chat', unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        file.save(file_path)
        
        # Create document record
        document = LegalChatDocument(
            chat_id=chat_id,
            user_id=user_id,
            filename=unique_filename,
            original_filename=filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            file_type=filename.rsplit('.', 1)[1].lower(),
            mime_type=file.mimetype
        )
        
        db.session.add(document)
        db.session.commit()
        
        # Process document
        LegalChatService.process_document(document.id)
        
        return document

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in LegalChatService.ALLOWED_EXTENSIONS

    @staticmethod
    def process_document(document_id):
        """Process uploaded document and extract text."""
        document = LegalChatDocument.query.get(document_id)
        if not document:
            return
        
        try:
            # Extract text based on file type
            if document.file_type == 'txt':
                with open(document.file_path, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()
            else:
                # For PDF and other formats, you would use appropriate libraries
                extracted_text = f"Document content from {document.original_filename} would be extracted here for analysis."
            
            document.extracted_text = extracted_text
            document.ai_summary = f"Document '{document.original_filename}' uploaded and processed. Contains {len(extracted_text)} characters of text content."
            
            db.session.commit()
            
            # Add system message about document
            system_message = LegalChatMessage(
                chat_id=document.chat_id,
                user_id=document.user_id,
                content=f"I've received and processed your document '{document.original_filename}'. I can now reference this document in our conversation. What specific aspects would you like me to analyze?",
                message_type="system",
                ai_confidence=1.0
            )
            db.session.add(system_message)
            db.session.commit()
            
        except Exception as e:
            document.ai_summary = f"Error processing document: {str(e)}"
            db.session.commit()

    @staticmethod
    def request_lawyer(chat_id, user_id, reason):
        """Request a lawyer for a chat session."""
        chat = LegalChat.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return None
        
        chat.lawyer_requested = True
        chat.lawyer_request_reason = reason
        chat.status = "lawyer_requested"
        
        db.session.commit()
        
        # Add system message
        system_message = LegalChatMessage(
            chat_id=chat_id,
            user_id=user_id,
            content=f"Your request for legal representation has been received. Reason: {reason}. A qualified attorney will review your case and contact you shortly. In the meantime, I'm here to continue providing general legal information.",
            message_type="system",
            ai_confidence=1.0
        )
        db.session.add(system_message)
        db.session.commit()
        
        return chat

    @staticmethod
    def get_chat_messages(chat_id, user_id):
        """Get all messages for a chat session."""
        chat = LegalChat.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return []
        
        return LegalChatMessage.query.filter_by(chat_id=chat_id)\
            .order_by(LegalChatMessage.created_at.asc()).all()

    @staticmethod
    def get_chat_documents(chat_id, user_id):
        """Get all documents for a chat session."""
        chat = LegalChat.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return []
        
        return LegalChatDocument.query.filter_by(chat_id=chat_id).all()
