from tests.test_config import BaseTestCase
from app.models import User # Adjust import based on your app structure

class UserModelTestCase(BaseTestCase):
    def test_password_setter(self):
        u = User(username='testuser')
        u.set_password('cat')
        self.assertTrue(u.password_hash is not None)
        self.assertNotEqual(u.password_hash, 'cat')

    def test_password_verification(self):
        u = User(username='testuser2')
        u.set_password('dog')
        self.assertTrue(u.check_password('dog'))
        self.assertFalse(u.check_password('cat'))
