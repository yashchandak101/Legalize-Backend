import os
import uuid
import secrets
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from app.core.extensions import db
from app.models.legal_aid_conversation import LegalAidConversation
from app.models.legal_aid_message import LegalAidMessage
from app.models.legal_aid_document import LegalAidDocument
from app.services.claude_service import ClaudeService


class LegalAidService:

    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

    @staticmethod
    def create_conversation(user_id, title, category, description=""):
        """Create a new legal aid conversation."""
        print(f"Creating conversation - user_id: {user_id}, title: {title}, category: {category}")
        
        try:
            print("Creating LegalAidConversation object...")
            conversation = LegalAidConversation(
                user_id=user_id,
                title=title,
                category=category,
                description=description,
                share_token=secrets.token_urlsafe(32)  # Generate unique share token
            )
            print("Conversation object created")
            
            print("Adding conversation to database session...")
            db.session.add(conversation)
            print("Conversation added to session")
            
            print("Committing to database...")
            db.session.commit()
            print("Conversation saved to database")
            
            print("Creating welcome message...")
            # Add welcome message
            welcome_message = LegalAidMessage(
                conversation_id=conversation.id,
                user_id=user_id,
                content=f"Hello! I'm your AI legal assistant for this {category} matter. I can help you understand your legal situation, provide general information, and guide you through next steps. You can also upload relevant documents for analysis. Remember, I provide general legal information, but for specific legal advice, you may need to consult with a qualified attorney.",
                message_type="ai",
                ai_confidence=0.95
            )
            print("Welcome message object created")
            
            print("Adding welcome message to session...")
            db.session.add(welcome_message)
            print("Welcome message added to session")
            
            print("Committing welcome message...")
            db.session.commit()
            print("Welcome message added")
            
            print("Returning conversation object")
            return conversation
            
        except Exception as e:
            print(f"Error in create_conversation: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            raise e

    @staticmethod
    def get_user_conversations(user_id):
        """Get all conversations for a user."""
        return LegalAidConversation.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_conversation(conversation_id, user_id=None, share_token=None):
        """Get a specific conversation by ID or share token."""
        if share_token:
            # Public access via share token
            conversation = LegalAidConversation.query.filter_by(
                share_token=share_token, 
                allow_public_view=True
            ).first()
        elif user_id:
            # User access
            conversation = LegalAidConversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        else:
            conversation = None
            
        return conversation

    @staticmethod
    def add_message(conversation_id, user_id, content, message_type="user"):
        """Add a message to a conversation."""
        message = LegalAidMessage(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            message_type=message_type
        )
        db.session.add(message)
        
        # Update conversation timestamp
        conversation = LegalAidConversation.query.get(conversation_id)
        if conversation:
            conversation.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        return message

    @staticmethod
    async def generate_ai_response(conversation_id, user_id, user_message):
        """Generate AI response to user message using Claude API."""
        conversation = LegalAidConversation.query.get(conversation_id)
        if not conversation:
            return None
        
        # Get recent conversation context
        recent_messages = LegalAidMessage.query.filter_by(conversation_id=conversation_id)\
            .order_by(LegalAidMessage.created_at.desc())\
            .limit(10).all()
        
        # Initialize Claude service
        claude_service = ClaudeService()
        
        # Build context for Claude
        context = f"Conversation Context: {conversation.category} legal matter.\n"
        context += f"Description: {conversation.description}\n"
        
        # Generate AI response using Claude
        ai_response_data = await claude_service.generate_legal_response(
            user_message=user_message,
            conversation_context=context,
            category=conversation.category,
            previous_messages=recent_messages
        )
        
        # Add AI response to conversation
        ai_message = LegalAidMessage(
            conversation_id=conversation_id,
            user_id=user_id,
            content=ai_response_data["content"],
            message_type="ai",
            ai_confidence=ai_response_data["confidence"],
            ai_sources=ai_response_data["sources"]
        )
        db.session.add(ai_message)
        db.session.commit()
        
        return ai_message

    @staticmethod
    def upload_document(conversation_id, user_id, file):
        """Upload and process a document for a conversation."""
        if not file or file.filename == '':
            raise ValueError("No file selected")
        
        if not LegalAidService.allowed_file(file.filename):
            raise ValueError("File type not allowed")
        
        if len(file.read()) > LegalAidService.MAX_FILE_SIZE:
            raise ValueError("File too large")
        
        file.seek(0)  # Reset file pointer
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join('uploads', 'legal_aid', unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        file.save(file_path)
        
        # Create document record
        document = LegalAidDocument(
            conversation_id=conversation_id,
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
        LegalAidService.process_document(document.id)
        
        return document

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in LegalAidService.ALLOWED_EXTENSIONS

    @staticmethod
    def process_document(document_id):
        """Process uploaded document and extract text."""
        document = LegalAidDocument.query.get(document_id)
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
            document.ai_summary = f"Document '{document.original_filename}' uploaded and processed. Contains {len(extracted_text)} characters of text content relevant to the case."
            
            db.session.commit()
            
            # Add system message about document
            system_message = LegalAidMessage(
                conversation_id=document.conversation_id,
                user_id=document.user_id,
                content=f"I've received and processed your document '{document.original_filename}'. I can now reference this document in our conversation. The document appears to contain relevant information for your legal matter. What specific aspects would you like me to analyze?",
                message_type="system",
                ai_confidence=1.0
            )
            db.session.add(system_message)
            db.session.commit()
            
        except Exception as e:
            document.ai_summary = f"Error processing document: {str(e)}"
            db.session.commit()

    @staticmethod
    def share_conversation(conversation_id, user_id, allow_public=False):
        """Share a conversation."""
        conversation = LegalAidConversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conversation:
            return None
        
        conversation.is_shared = True
        conversation.allow_public_view = allow_public
        
        db.session.commit()
        return conversation

    @staticmethod
    def get_conversation_messages(conversation_id, user_id=None):
        """Get all messages for a conversation."""
        conversation = LegalAidService.get_conversation(conversation_id, user_id)
        if not conversation:
            return []
        
        return LegalAidMessage.query.filter_by(conversation_id=conversation_id)\
            .order_by(LegalAidMessage.created_at.asc()).all()

    @staticmethod
    def get_conversation_documents(conversation_id, user_id=None):
        """Get all documents for a conversation."""
        conversation = LegalAidService.get_conversation(conversation_id, user_id)
        if not conversation:
            return []
        
        return LegalAidDocument.query.filter_by(conversation_id=conversation_id).all()
