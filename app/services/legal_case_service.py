import os
import uuid
import json
import secrets
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from app.core.extensions import db
from app.models.legal_case import LegalCase
from app.models.legal_case_message import LegalCaseMessage
from app.models.legal_case_document import LegalCaseDocument
from app.models.legal_case_share import LegalCaseShare


class LegalCaseService:

    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

    @staticmethod
    def create_case(user_id, title, description, category, urgency="medium"):
        """Create a new legal case with AI chat functionality."""
        case = LegalCase(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            urgency=urgency,
            ai_context=f"Legal case about {category} matters. User is seeking legal guidance and information.",
            share_token=secrets.token_urlsafe(32)  # Generate unique share token
        )
        db.session.add(case)
        db.session.commit()
        
        # Add welcome message
        welcome_message = LegalCaseMessage(
            case_id=case.id,
            user_id=user_id,
            content=f"Hello! I'm your AI legal assistant for this {category} case. I can help you understand your legal situation, provide general information, and guide you through next steps. You can also upload relevant documents for analysis. Remember, I provide general legal information, but for specific legal advice, you may need to consult with a qualified attorney.",
            message_type="ai",
            ai_confidence=0.95
        )
        db.session.add(welcome_message)
        db.session.commit()
        
        # Generate initial AI analysis
        LegalCaseService.generate_ai_analysis(case.id)
        
        return case

    @staticmethod
    def get_user_cases(user_id, include_shared=False):
        """Get all cases for a user, optionally including shared cases."""
        # User's own cases
        cases = LegalCase.query.filter_by(user_id=user_id).all()
        
        if include_shared:
            # Get cases shared with user
            shared_cases = db.session.query(LegalCase).join(LegalCaseShare).filter(
                LegalCaseShare.shared_with_user_id == user_id
            ).all()
            
            # Combine and remove duplicates
            all_cases = list({case.id: case for case in cases + shared_cases}.values())
            return all_cases
        
        return cases

    @staticmethod
    def get_case(case_id, user_id=None, share_token=None):
        """Get a specific case by ID or share token."""
        if share_token:
            # Public access via share token
            case = LegalCase.query.filter_by(
                share_token=share_token, 
                allow_public_view=True
            ).first()
        elif user_id:
            # User access (own case or shared)
            case = LegalCase.query.filter_by(id=case_id, user_id=user_id).first()
            if not case:
                # Check if case is shared with user
                case = db.session.query(LegalCase).join(LegalCaseShare).filter(
                    LegalCase.id == case_id,
                    LegalCaseShare.shared_with_user_id == user_id
                ).first()
        else:
            case = None
            
        return case

    @staticmethod
    def add_message(case_id, user_id, content, message_type="user"):
        """Add a message to a case."""
        message = LegalCaseMessage(
            case_id=case_id,
            user_id=user_id,
            content=content,
            message_type=message_type
        )
        db.session.add(message)
        
        # Update case timestamp
        case = LegalCase.query.get(case_id)
        if case:
            case.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        return message

    @staticmethod
    def generate_ai_response(case_id, user_id, user_message):
        """Generate AI response to user message."""
        case = LegalCase.query.get(case_id)
        if not case:
            return None
        
        # Get recent conversation context
        recent_messages = LegalCaseMessage.query.filter_by(case_id=case_id)\
            .order_by(LegalCaseMessage.created_at.desc())\
            .limit(10).all()
        
        # Build context for AI
        context = f"Case Context: {case.ai_context}\n"
        context += f"Case Description: {case.description}\n"
        context += "Recent Messages:\n"
        for msg in reversed(recent_messages):
            sender = "User" if msg.message_type == "user" else "AI Assistant"
            context += f"{sender}: {msg.content}\n"
        
        # Generate AI response (simulated - replace with actual AI service)
        ai_response = LegalCaseService._simulate_ai_response(user_message, case.category)
        
        # Add AI response to case
        ai_message = LegalCaseMessage(
            case_id=case_id,
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
                    "content": "Based on your family law situation, I recommend documenting all relevant interactions and communications. Family law cases often involve sensitive matters, so maintaining clear records is crucial. Consider mediation as a first step to resolve conflicts amicably. Would you like me to explain specific family law procedures that might apply to your situation?",
                    "confidence": 0.85,
                    "sources": "Family Law Act, State Custody Guidelines, Mediation Best Practices"
                },
                {
                    "content": "Family law matters require careful consideration of all parties' rights and responsibilities. I suggest gathering relevant documents like financial records, communication logs, and any existing agreements. The court's primary consideration is typically the best interests of any children involved. What specific aspect of your family law case would you like me to address?",
                    "confidence": 0.82,
                    "sources": "Family Court Procedures, Child Welfare Guidelines"
                }
            ],
            "criminal": [
                {
                    "content": "In criminal law matters, protecting your constitutional rights is paramount. You have the right to remain silent and the right to legal representation. Avoid discussing your case with anyone other than your attorney. The specific charges and evidence will determine the legal strategy. Have you been formally charged, or are you under investigation?",
                    "confidence": 0.90,
                    "sources": "Constitutional Rights, Criminal Procedure Code, Miranda Rights"
                }
            ],
            "civil": [
                {
                    "content": "Civil law disputes typically involve contracts, property, or personal injury claims. Key elements include establishing duty, breach, causation, and damages. Documentation and evidence are critical in civil cases. Consider alternative dispute resolution methods like mediation or arbitration before litigation. What type of civil dispute are you facing?",
                    "confidence": 0.87,
                    "sources": "Civil Procedure Rules, Contract Law Principles, Tort Law"
                }
            ]
        }
        
        import random
        category_responses = responses.get(category, responses["civil"])
        return random.choice(category_responses)

    @staticmethod
    def generate_ai_analysis(case_id):
        """Generate AI analysis for a case."""
        case = LegalCase.query.get(case_id)
        if not case:
            return
        
        # Simulate AI analysis
        ai_summary = f"This {case.category} case involves {case.urgency} priority matters requiring careful legal consideration. The case appears to involve standard {case.category} legal issues that may benefit from professional legal guidance."
        ai_recommendations = f"Recommended actions: 1) Document all relevant facts and evidence, 2) Consult with a qualified {case.category} attorney, 3) Consider alternative dispute resolution, 4) Understand your rights and obligations."
        ai_confidence_score = 0.85
        
        case.ai_summary = ai_summary
        case.ai_recommendations = ai_recommendations
        case.ai_confidence_score = ai_confidence_score
        
        db.session.commit()

    @staticmethod
    def upload_document(case_id, user_id, file):
        """Upload and process a document for a case."""
        if not file or file.filename == '':
            raise ValueError("No file selected")
        
        if not LegalCaseService.allowed_file(file.filename):
            raise ValueError("File type not allowed")
        
        if len(file.read()) > LegalCaseService.MAX_FILE_SIZE:
            raise ValueError("File too large")
        
        file.seek(0)  # Reset file pointer
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join('uploads', 'legal_cases', unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        file.save(file_path)
        
        # Create document record
        document = LegalCaseDocument(
            case_id=case_id,
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
        LegalCaseService.process_document(document.id)
        
        return document

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in LegalCaseService.ALLOWED_EXTENSIONS

    @staticmethod
    def process_document(document_id):
        """Process uploaded document and extract text."""
        document = LegalCaseDocument.query.get(document_id)
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
            system_message = LegalCaseMessage(
                case_id=document.case_id,
                user_id=document.user_id,
                content=f"I've received and processed your document '{document.original_filename}'. I can now reference this document in our conversation. The document appears to contain relevant information for your case. What specific aspects would you like me to analyze?",
                message_type="system",
                ai_confidence=1.0
            )
            db.session.add(system_message)
            db.session.commit()
            
        except Exception as e:
            document.ai_summary = f"Error processing document: {str(e)}"
            db.session.commit()

    @staticmethod
    def request_lawyer(case_id, user_id, reason):
        """Request a lawyer for a case."""
        case = LegalCase.query.filter_by(id=case_id, user_id=user_id).first()
        if not case:
            return None
        
        case.lawyer_requested = True
        case.lawyer_request_reason = reason
        case.status = "lawyer_assigned"
        
        db.session.commit()
        
        # Add system message
        system_message = LegalCaseMessage(
            case_id=case_id,
            user_id=user_id,
            content=f"Your request for legal representation has been received. Reason: {reason}. A qualified attorney will review your case and contact you shortly. In the meantime, I'm here to continue providing general legal information and guidance.",
            message_type="system",
            ai_confidence=1.0
        )
        db.session.add(system_message)
        db.session.commit()
        
        return case

    @staticmethod
    def share_case(case_id, user_id, shared_with_user_id=None, permission_level="view", message=None, allow_public=False):
        """Share a case with another user or make it public."""
        case = LegalCase.query.filter_by(id=case_id, user_id=user_id).first()
        if not case:
            return None
        
        if allow_public:
            case.is_shared = True
            case.allow_public_view = True
        elif shared_with_user_id:
            # Share with specific user
            existing_share = LegalCaseShare.query.filter_by(
                case_id=case_id,
                shared_with_user_id=shared_with_user_id
            ).first()
            
            if not existing_share:
                share = LegalCaseShare(
                    case_id=case_id,
                    shared_by_user_id=user_id,
                    shared_with_user_id=shared_with_user_id,
                    permission_level=permission_level,
                    message=message
                )
                db.session.add(share)
            
            case.is_shared = True
        
        db.session.commit()
        return case

    @staticmethod
    def get_case_messages(case_id, user_id=None):
        """Get all messages for a case."""
        case = LegalCaseService.get_case(case_id, user_id)
        if not case:
            return []
        
        return LegalCaseMessage.query.filter_by(case_id=case_id)\
            .order_by(LegalCaseMessage.created_at.asc()).all()

    @staticmethod
    def get_case_documents(case_id, user_id=None):
        """Get all documents for a case."""
        case = LegalCaseService.get_case(case_id, user_id)
        if not case:
            return []
        
        return LegalCaseDocument.query.filter_by(case_id=case_id).all()

    @staticmethod
    def get_shared_cases(user_id):
        """Get all cases shared with a user."""
        shared_cases = db.session.query(LegalCase).join(LegalCaseShare).filter(
            LegalCaseShare.shared_with_user_id == user_id
        ).all()
        
        return shared_cases
