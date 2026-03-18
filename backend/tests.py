from django.test import TestCase
from rest_framework.test import APIClient

from backend.models import User


class ApiRootTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_api_root_returns_200(self):
        response = self.client.get('/api/v1/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('Status'))
        self.assertIn('Endpoints', data)


class RegisterConfirmLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/v1/user/register'
        self.confirm_url = '/api/v1/user/confirm'
        self.login_url = '/api/v1/user/login'

    def test_register_creates_user_and_returns_token(self):
        payload = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'company': 'Company',
            'position': 'Manager',
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('Status'))
        self.assertIn('Token', data)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_confirm_activates_user(self):
        payload = {
            'first_name': 'Confirm',
            'last_name': 'User',
            'email': 'confirm@example.com',
            'password': 'SecurePass123!',
            'company': 'Co',
            'position': 'Pos',
        }
        self.client.post(self.register_url, payload, format='json')
        user = User.objects.get(email='confirm@example.com')
        from backend.models import ConfirmEmailToken
        token_obj = ConfirmEmailToken.objects.get(user=user)
        response = self.client.post(
            self.confirm_url,
            {'email': user.email, 'token': token_obj.key},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('Status'))
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_login_returns_token_for_active_user(self):
        payload = {
            'first_name': 'Login',
            'last_name': 'User',
            'email': 'login@example.com',
            'password': 'SecurePass123!',
            'company': 'C',
            'position': 'P',
        }
        self.client.post(self.register_url, payload, format='json')
        user = User.objects.get(email='login@example.com')
        user.is_active = True
        user.save()
        response = self.client.post(
            self.login_url,
            {'email': 'login@example.com', 'password': 'SecurePass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('Status'))
        self.assertIn('Token', data)


class CatalogTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_categories_get_returns_200(self):
        response = self.client.get('/api/v1/categories')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_shops_get_returns_200(self):
        response = self.client.get('/api/v1/shops')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_products_get_returns_200(self):
        response = self.client.get('/api/v1/products')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
