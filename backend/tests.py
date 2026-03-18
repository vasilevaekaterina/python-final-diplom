import json

from django.test import TestCase
from rest_framework.test import APIClient

from backend.models import (
    Category,
    ConfirmEmailToken,
    Product,
    ProductInfo,
    Shop,
    User,
)


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


class FullBuyerScenarioTest(TestCase):
    """
    Сценарий: регистрация → подтверждение → логин → корзина (2 магазина)
    → контакт → оформление заказа → список заказов.
    """

    def setUp(self):
        self.client = APIClient()
        cat = Category.objects.create(name='Тест-категория')
        su1 = User.objects.create_user(
            email='shop_a@test.com',
            password='pass',
            username='shop_a@test.com',
            type='shop',
            first_name='A',
            last_name='Shop',
            company='',
            position='',
        )
        su2 = User.objects.create_user(
            email='shop_b@test.com',
            password='pass',
            username='shop_b@test.com',
            type='shop',
            first_name='B',
            last_name='Shop',
            company='',
            position='',
        )
        shop_a = Shop.objects.create(name='Магазин A', user=su1, state=True)
        shop_b = Shop.objects.create(name='Магазин B', user=su2, state=True)
        p1 = Product.objects.create(name='Товар A', category=cat)
        p2 = Product.objects.create(name='Товар B', category=cat)
        self.info_a = ProductInfo.objects.create(
            product=p1,
            shop=shop_a,
            external_id=9001,
            model='m-a',
            quantity=10,
            price=100,
            price_rrc=110,
        )
        self.info_b = ProductInfo.objects.create(
            product=p2,
            shop=shop_b,
            external_id=9002,
            model='m-b',
            quantity=10,
            price=200,
            price_rrc=220,
        )

    def test_full_scenario_basket_two_shops_order_list(self):
        reg = {
            'first_name': 'Buyer',
            'last_name': 'E2E',
            'email': 'buyer_e2e@test.com',
            'password': 'SecurePass123!',
            'company': 'Co',
            'position': 'Pos',
        }
        r = self.client.post('/api/v1/user/register', reg, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get('Status'))

        user = User.objects.get(email='buyer_e2e@test.com')
        token_confirm = ConfirmEmailToken.objects.get(user=user)
        r = self.client.post(
            '/api/v1/user/confirm',
            {'email': user.email, 'token': token_confirm.key},
            format='json',
        )
        self.assertEqual(r.status_code, 200)

        r = self.client.post(
            '/api/v1/user/login',
            {'email': user.email, 'password': 'SecurePass123!'},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        auth_token = r.json()['Token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {auth_token}')

        basket_items = json.dumps(
            [
                {'product_info': self.info_a.id, 'quantity': 1},
                {'product_info': self.info_b.id, 'quantity': 2},
            ],
        )
        r = self.client.post('/api/v1/basket', {'items': basket_items})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get('Status'))

        r = self.client.post(
            '/api/v1/user/contact',
            {
                'city': 'Москва',
                'street': 'Ленина 1',
                'phone': '+79990001122',
            },
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        contact_id = User.objects.get(email='buyer_e2e@test.com').contacts.first().id

        r = self.client.get('/api/v1/basket')
        self.assertEqual(r.status_code, 200)
        baskets = r.json()
        self.assertEqual(len(baskets), 1)
        basket_id = baskets[0]['id']

        r = self.client.post(
            '/api/v1/order',
            {'id': basket_id, 'contact': contact_id},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get('Status'))

        r = self.client.get('/api/v1/order')
        self.assertEqual(r.status_code, 200)
        orders = r.json()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['state'], 'new')
        item_ids = {
            oi['product_info']['id']
            for oi in orders[0]['ordered_items']
        }
        self.assertEqual(item_ids, {self.info_a.id, self.info_b.id})
