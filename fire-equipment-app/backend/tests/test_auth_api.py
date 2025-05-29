import json
from tests.test_config import BaseTestCase
from app.models import User, db # Adjust import

class AuthApiTestCase(BaseTestCase):
    def test_user_registration(self):
        # Test successful registration
        response = self.client.post('/auth/register', 
                                   data=json.dumps({'username': 'newuser', 'password': 'password'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('User registered successfully', response.get_data(as_text=True))
        
        # Test registration of existing user
        response = self.client.post('/auth/register',
                                   data=json.dumps({'username': 'newuser', 'password': 'password'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('User already exists', response.get_data(as_text=True))

    def test_user_login(self):
        # First, register a user to ensure they exist
        self.client.post('/auth/register', 
                         data=json.dumps({'username': 'loginuser', 'password': 'loginpass'}),
                         content_type='application/json')
        
        # Test successful login
        response = self.client.post('/auth/login',
                                   data=json.dumps({'username': 'loginuser', 'password': 'loginpass'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertTrue('token' in data)

        # Test login with wrong password
        response = self.client.post('/auth/login',
                                   data=json.dumps({'username': 'loginuser', 'password': 'wrongpassword'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid username or password', response.get_data(as_text=True))

    def test_logout(self):
        # Register and login a user first
        self.client.post('/auth/register', 
                         data=json.dumps({'username': 'logoutuser', 'password': 'logoutpass'}),
                         content_type='application/json')
        login_response = self.client.post('/auth/login',
                                          data=json.dumps({'username': 'logoutuser', 'password': 'logoutpass'}),
                                          content_type='application/json')
        self.assertEqual(login_response.status_code, 200)
        token = json.loads(login_response.get_data(as_text=True))['token']

        # Test logout with token (for API consistency, though Flask-Login handles session)
        response = self.client.post('/auth/logout',
                                   headers={'x-access-token': token})
        self.assertEqual(response.status_code, 200)
        self.assertIn('logged out successfully', response.get_data(as_text=True))

        # Verify that a protected route now denies access (if we had one that solely relied on Flask-Login session)
        # For now, we'll check the /auth/status route
        status_response = self.client.get('/auth/status')
        self.assertEqual(status_response.status_code, 401) # Unauthorized, as user is logged out

    def test_status_route_authenticated(self):
        # Register and login a user
        self.client.post('/auth/register', 
                         data=json.dumps({'username': 'statususer', 'password': 'statuspass'}),
                         content_type='application/json')
        login_response = self.client.post('/auth/login',
                                          data=json.dumps({'username': 'statususer', 'password': 'statuspass'}),
                                          content_type='application/json')
        self.assertEqual(login_response.status_code, 200)
        # Flask-Login handles session, so no token needed for '/auth/status' if it uses @login_required

        response = self.client.get('/auth/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['username'], 'statususer')
        self.assertFalse(data['is_admin'])
