# tests/conftest.py
import pytest
from app import create_app
from app.core.extensions import db


class _SessionProxy:
    """Proxy so db.session is both callable (session()) and attribute-delegating (session.add)."""

    def __init__(self, session):
        self._session = session

    def __call__(self):
        return self._session

    def __getattr__(self, name):
        return getattr(self._session, name)


@pytest.fixture(scope="session")
def app():
    """Create Flask app for tests using main DB"""
    app = create_app(testing=True)
    app.config['TESTING'] = True
    return app

@pytest.fixture(scope="function", autouse=True)
def session(app):
    """
    Create a new DB session for each test, roll back after test.
    Works with Flask-SQLAlchemy v3+.
    """
    with app.app_context():
        # Ensure tables exist (e.g. in-memory SQLite)
        db.create_all()
        # Connect to main DB and start a transaction
        connection = db.engine.connect()
        transaction = connection.begin()

        # Bind a new session to the connection
        test_session = db.create_session(bind=connection)
        original_session = db.session
        db.session = _SessionProxy(test_session)

        yield test_session  # <-- the test runs here

        # Rollback and cleanup
        test_session.close()
        transaction.rollback()
        connection.close()
        # Restore original session so Flask-SQLAlchemy teardown doesn't call .remove() on our session
        db.session = original_session