from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from .core.config import Config
from .core.extensions import db, migrate, jwt
from .core.logging_config import init_logging
from .api.routes.auth_routes import auth_bp
from .api.routes.user_routes import user_bp
from .api.routes.legal_aid_routes import legal_aid_bp
from .api.routes.appointment_routes import appointment_bp
from .api.routes.health_routes import health_bp
from .api.routes.lawyer_profile_routes import lawyer_profile_bp
from .api.routes.case_assignment_routes import case_assignment_bp
from .api.routes.case_comment_routes import case_comment_bp
from .api.routes.case_document_routes import case_document_bp
from .api.routes.payment_routes import payment_bp
from .api.routes.notification_routes import notification_bp
# Temporarily disable old routes
# from .api.routes.legal_case_routes import legal_case_bp
# from .api.routes.legal_chat_routes import legal_chat_bp
# from .api.routes.case_routes import case_bp
# Temporarily disable AI routes to debug
# from .api.routes.ai_routes import ai_bp

from .models.user import User
from .models.appointment import Appointment
from .models.lawyer_profile import LawyerProfile
from .models.case_assignment import CaseAssignment
from .models.case_comment import CaseComment
from .models.case_document import CaseDocument
from .models.payment import Payment
from .models.notification import Notification
from .models.case_ai_suggestion import CaseAISuggestion
# New simplified legal aid models
from .models.legal_aid_conversation import LegalAidConversation
from .models.legal_aid_message import LegalAidMessage
from .models.legal_aid_document import LegalAidDocument
# Temporarily disable old models
# from .models.legal_case import LegalCase
# from .models.legal_case_message import LegalCaseMessage
# from .models.legal_case_document import LegalCaseDocument
# from .models.legal_case_share import LegalCaseShare
# from .models.legal_aid_request import LegalAidRequest
# from .models.legal_aid_document import LegalAidDocument
# from .models.legal_chat import LegalChat
# from .models.legal_chat_message import LegalChatMessage
# from .models.legal_chat_document import LegalChatDocument
# from .models.case import Case


def create_app(testing: bool = False):
    # Load environment variables from .env file
    load_dotenv()
    
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    if testing:
        app.config["SQLALCHEMY_DATABASE_URI"] = Config.DATABASE_URL
        app.config["TESTING"] = True

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(legal_aid_bp, url_prefix="/api")
    app.register_blueprint(appointment_bp, url_prefix="/api/appointments")
    app.register_blueprint(health_bp)
    app.register_blueprint(lawyer_profile_bp, url_prefix="/api/lawyer-profiles")
    app.register_blueprint(case_assignment_bp, url_prefix="/api/assignments")
    app.register_blueprint(case_comment_bp, url_prefix="/api")
    app.register_blueprint(case_document_bp, url_prefix="/api")
    app.register_blueprint(payment_bp, url_prefix="/api/payments")
    app.register_blueprint(notification_bp, url_prefix="/api/notifications")
    # Temporarily disable old routes
    # app.register_blueprint(legal_case_bp, url_prefix="/api")
    # app.register_blueprint(legal_chat_bp, url_prefix="/api/legal-chat")
    # app.register_blueprint(case_bp, url_prefix="/api/cases")
    # app.register_blueprint(ai_bp, url_prefix="/api/ai")

    init_logging(app)
    return app