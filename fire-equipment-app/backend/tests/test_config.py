import unittest
from app import create_app, db

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Use an in-memory SQLite database for testing
        config_overrides = {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", # Override DB URI for tests
            "WTF_CSRF_ENABLED": False, # Disable CSRF for forms if you have them
            "JWT_SECRET_KEY": "test-jwt-secret", # Use a fixed JWT secret for tests
            "SERVER_NAME": "localhost.localdomain" # Often needed for url_for in tests
        }
        self.app = create_app(config_overrides=config_overrides)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all() # Create all tables for the in-memory SQLite DB

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all() # Drop all tables after each test
