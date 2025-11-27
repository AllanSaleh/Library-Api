from app import create_app
from app.models import Users, db
import unittest
from werkzeug.security import check_password_hash, generate_password_hash
from app.util.auth import encode_token

# Ren Script: python -m unittest discover tests

class TestUsers(unittest.TestCase):

    #Runs before each test_method
    def setUp(self):
        self.app = create_app('TestingConfig') #Create a testing version of my app for these testcases
        self.user = Users(first_name="Test", last_name="Lasttest", email="tester@email.com", password=generate_password_hash('12345'), role="user")
        with self.app.app_context():
            db.drop_all() #removing any lingering tables
            db.create_all() #creating fresh tables for another round of testing
            db.session.add(self.user)
            db.session.commit()
        self.token = encode_token(1, 'user') #encoding a token for my starter degined user above ^
        self.client = self.app.test_client() #creates a test client that will send requests to our API
    
    #test creating a user (IMPORTANT all test functions need to start with test)
    def test_create_user(self):
        user_payload = {
            "email": "test@email.com",
            "first_name": "Test",
            "last_name": "Lasttest",
            "password": "12345",
            "role": "user"
        }

        response = self.client.post('/users', json=user_payload) #sending a test POST request using our test_client and includeing a JSON body
        self.assertEqual(response.status_code, 201) #checking if I got a 201 status code
        self.assertEqual(response.json['first_name'], "Test") #checking to make sure the data that I sent in, is part of the response
        self.assertTrue(check_password_hash(response.json['password'], '12345'))
        self.assertEqual(response.json['last_name'], "Lasttest")
        self.assertEqual(response.json['email'], "test@email.com")
        self.assertEqual(response.json['role'], "user")
        self.assertIsNone(response.json['DOB'])
        self.assertIsNone(response.json['address'])

    #Negative check: See what happens when we intentionally try and break our endpoint
    def test_invalid_create(self):
        user_payload = { #Missing email which shoule be required
            "first_name": "Test",
            "last_name": "Lasttest",
            "password": "12345",
            "role": "user"
        }

        response = self.client.post('/users', json=user_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json)

    def test_get_users(self):
        response = self.client.get('/users')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]['email'], 'tester@email.com')
    
    def test_login(self):
        login_creds = {
            "email": "tester@email.com",
            "password": "12345"
        }

        response = self.client.post("/users/login", json=login_creds)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], "Welcome Test")
        self.assertIn("token", response.json)

    def test_delete(self):
        headers = {"Authorization": "Bearer " + self.token}

        response = self.client.delete("/users", headers=headers) #Sending delete request to /users with my Authorization headers
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'],"Successfully deleted user 1")

    def test_unauthorized_delete(self):
        response = self.client.delete("/users")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], "token missing from authorization headers")

    def test_update(self):
        headers = {"Authorization": "Bearer " + self.token}

        update_payload = {
            "email": "NEW_EMAIL@email.com",
            "first_name": "Tester",
            "last_name": "Lasttest",
            "password": "12345",
            "role": "user"
        }

        response = self.client.put("/users", headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["email"], "NEW_EMAIL@email.com")
        self.assertEqual(response.json["first_name"], "Tester")

    def test_nonunique_email(self):
        user_payload = {
            "email": "tester@email.com",
            "first_name": "Test",
            "last_name": "Lasttest",
            "password": "12345",
            "role": "user"
        }

        response = self.client.post ('/users', json=user_payload)
        self.assertEqual(response.status_code, 400)
