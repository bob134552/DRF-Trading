"""
Tests for api_trades app
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from api_trades.models import Order, Stock
from api_trades.serializers import OrderSerializer

ORDERS_URL = reverse('orders:orders-list')
PORTFOLIO_URL = reverse('orders:user-portfolio')


def total_invested_value_url(stock_id):
    """create and return a total invested value for a stock URL"""
    return reverse('orders:total_value_invested', kwargs={'stock_id': stock_id})

def create_user(**params):
    """create and return a new user"""
    return get_user_model().objects.create_user(**params)

def create_stock(**params):
    """Create and return a sample stock"""
    defaults = {
        'name': 'default stock',
        'price': Decimal('5.99')
    }
    defaults.update(params)

    stock = Stock.objects.create(**defaults)
    return stock

def create_order(user, stock, **params):
    """Create and return an order"""
    defaults = {
        'order_type': 'buy',
        'quantity': '10'
    }
    defaults.update(params)

    order = Order.objects.create(user=user, stock=stock, **defaults)
    return order


class PublicOrdersAPITests(TestCase):
    """test unauthorized API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(ORDERS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateOrdersAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            username='Testusername',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Name'
        )
        self.stock1 = create_stock(name='Stock 1',)
        self.stock2 = create_stock(name='Stock 2', price=Decimal('10'))
        self.client.force_authenticate(self.user)

    def test_retrieve_orders(self):
        """Test retrieving a list of orders"""
        create_order(user=self.user, stock=self.stock1)
        create_order(user=self.user, stock=self.stock2)

        res= self.client.get(ORDERS_URL)

        orders = Order.objects.filter(user=self.user)
        serializer = OrderSerializer(orders, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_placing_a_trade_order(self):
        """Test POST to api creates an order"""
        payload = {
            'stock': self.stock1.id,
            'order_type': 'buy',
            'quantity': 5,
        }

        res = self.client.post(ORDERS_URL, payload)

        # Check that the order was created successfully
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Verify that the order was created with the correct data
        order = Order.objects.get(id=res.data['id'])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.stock.id, payload['stock'])
        self.assertEqual(order.order_type, payload['order_type'])
        self.assertEqual(order.quantity, payload['quantity'])

    def test_retrieve_orders_limited_to_user(self):
        """Test that only orders belonging to the authenticated user are returned"""
        other_user = create_user(
            username='OtherUser',
            email='other@example.com',
            password='testpass123'
        )
        create_order(user=other_user, stock=self.stock1)
        create_order(user=self.user, stock=self.stock2)

        res = self.client.get(ORDERS_URL)

        orders = Order.objects.filter(user=self.user)
        serializer = OrderSerializer(orders, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_create_order_with_negative_quantity(self):
        """Test creating an order with negative quantity fails"""
        payload = {
            'stock': self.stock1.id,
            'order_type': 'buy',
            'quantity': -10,  # Invalid negative quantity
        }
        res = self.client.post(ORDERS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_with_large_quantity(self):
        """Test creating an order with a large quantity succeeds"""
        payload = {
            'stock': self.stock1.id,
            'order_type': 'buy',
            'quantity': 1000000000,  # Large quantity
        }
        res = self.client.post(ORDERS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_order_with_invalid_order_type(self):
        """Test creating an order with invalid order_type fails"""
        payload = {
            'stock': self.stock1.id,
            'order_type': 'invalid_type',  # Invalid order type
            'quantity': 10,
        }
        res = self.client.post(ORDERS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)



class PortfolioAPITests(TestCase):
    """Tests to check users portfolio"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            username='Testusername',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Name'
        )
        self.stock1 = create_stock(name='Stock 1',)
        self.stock2 = create_stock(name='Stock 2', price=Decimal('10'))
        self.order1 = create_order(user=self.user, stock=self.stock1)
        self.order2 = create_order(user=self.user, stock=self.stock2)
        self.client.force_authenticate(self.user)

    def test_portfolio_contains_orders(self):
        """
        Test that portfolio contains both stocks and match
        the values of each.
        """
        res = self.client.get(PORTFOLIO_URL)
        self.assertEqual(res.status_code, 200)

        # Check if the response contains the correct data
        expected_data = [
            {
                'stock_name': 'Stock 1',
                'quantity': 10,
                'total_value': '59.90'
            },
            {
                'stock_name': 'Stock 2',
                'quantity': 10,
                'total_value': '100.00'
            }
        ]
        self.assertEqual(res.data, expected_data)

    def test_adjusted_portfolio(self):
        """
        Test that portfolio is updated when a new buy/sell
        order is made
        """
        create_order(
            user=self.user,
            stock=self.stock2,
            order_type='sell',
            quantity=10
            )
        res = self.client.get(PORTFOLIO_URL)
        self.assertEqual(res.status_code, 200)

        # Check if the response contains the correct data
        # Stock2 shouldn't appear
        expected_data = [
            {
                'stock_name': 'Stock 1',
                'quantity': 10,
                'total_value': '59.90'
            },
        ]
        self.assertEqual(res.data, expected_data)

    def test_empty_portfolio(self):
        """Test portfolio response when there are no orders"""
        Order.objects.all().delete()  # Ensure no orders exist for this user
        res = self.client.get(PORTFOLIO_URL)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {'message': 'You currently have no stocks in your portfolio'})


class TotalValueInvestedViewTest(TestCase):
    """Testing the total value invested api view for single stocks"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            username='Testusername',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Name'
        )
        self.client.force_authenticate(self.user)
        self.stock = Stock.objects.create(name='AAPL', price=150.00)

        # Create some buy and sell orders
        Order.objects.create(user=self.user, stock=self.stock, order_type='buy', quantity=10)
        Order.objects.create(user=self.user, stock=self.stock, order_type='sell', quantity=2)

    def test_total_value_invested(self):
        """Test the correct value of total stock"""
        url = total_invested_value_url(stock_id=self.stock.id)
        response = self.client.get(url)

        expected_total_value = (10 * 150.00) - (2 * 150.00)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_value'], expected_total_value)

    def test_stock_not_found(self):
        """Test trying to check total value of a non existant stock"""
        url = total_invested_value_url(stock_id=999)  # Non-existent stock ID
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
