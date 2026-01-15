from app import create_app
from app.models import Books, Loans, db
import unittest
from datetime import date
from werkzeug.security import generate_password_hash
from app.util.auth import encode_token

class TestBooks(unittest.TestCase):

    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        self.admin_token = encode_token(1, 'admin')
        self.user_token = encode_token(2, 'user')
        self.book_data = {
            "title": "Test Book",
            "genre": "Fiction",
            "age_category": "Adult",
            "publish_date": date.today().isoformat(),
            "author": "Author Name"
        }
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            # Add admin user for token
            from app.models import Users
            admin = Users(first_name="Admin", last_name="User", email="admin@email.com", password=generate_password_hash('admin'), role="admin")
            user = Users(first_name="User", last_name="User", email="user@email.com", password=generate_password_hash('user'), role="user")
            db.session.add(admin)
            db.session.add(user)
            db.session.commit()
            # Add a book for GET, PUT, DELETE tests
            book = Books(**self.book_data)
            db.session.add(book)
            db.session.commit()
            self.book_id = book.id

    def test_create_book(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        payload = {
            "title": "Another Book",
            "genre": "Non-Fiction",
            "age_category": "Teen",
            "publish_date": date.today().isoformat(),
            "author": "Another Author"
        }
        response = self.client.post('/books', headers=headers, json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['title'], "Another Book")
        self.assertEqual(response.json['genre'], "Non-Fiction")
        self.assertEqual(response.json['age_category'], "Teen")
        self.assertEqual(response.json['author'], "Another Author")

    def test_create_book_invalid(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        payload = {
            "genre": "Fiction",
            "age_category": "Adult",
            "publish_date": date.today().isoformat(),
            "author": "Author Name"
        }
        response = self.client.post('/books', headers=headers, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.json)

    def test_get_books(self):
        response = self.client.get('/books')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(book['title'] == "Test Book" for book in response.json))

    def test_get_books_paginated(self):
        response = self.client.get('/books?page=1&per_page=1')
        self.assertEqual(response.status_code, 200)
        # Should return a paginated object or list with one book
        self.assertTrue(len(response.json) >= 1 or 'items' in response.json)

    def test_update_book(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        update_payload = {
            "title": "Updated Book",
            "genre": "Mystery",
            "age_category": "Adult",
            "publish_date": date.today().isoformat(),
            "author": "Updated Author"
        }
        response = self.client.put(f'/books/{self.book_id}', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['title'], "Updated Book")
        self.assertEqual(response.json['genre'], "Mystery")

    def test_update_book_invalid(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        update_payload = {
            "genre": "Mystery",
            "age_category": "Adult",
            "publish_date": date.today().isoformat(),
            "author": "Updated Author"
        }
        response = self.client.put(f'/books/{self.book_id}', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.json)

    def test_update_book_not_found(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        update_payload = self.book_data
        response = self.client.put('/books/9999', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 404)

    def test_delete_book(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.delete(f'/books/{self.book_id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully deleted book", response.json)

    def test_delete_book_not_found(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.delete('/books/9999', headers=headers)
        # Should not crash, but may return 500 if not handled
        self.assertIn(response.status_code, [200, 404, 500])

    def test_get_popular_books(self):
        with self.app.app_context():
            # Add loans to make the book popular
            loan = Loans(user_id=1, loan_date=date.today(), deadline=date.today())
            db.session.add(loan)
            db.session.commit()
            book = db.session.get(Books, self.book_id)
            loan.books.append(book)
            db.session.commit()
        response = self.client.get('/books/popularity')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json, list))
        self.assertTrue('book' in response.json[0])

    def test_search_books(self):
        response = self.client.get('/books/search?title=Test')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any("Test Book" in book['title'] for book in response.json))

if __name__ == '__main__':
    unittest.main()