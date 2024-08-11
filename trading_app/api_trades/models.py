'''Models for api_trades app'''
from django.db import models
from django.contrib.auth.models import User


class Stock(models.Model):
    """The stock model"""
    name = models.CharField(max_length=100, blank=False, null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)

    def __str__(self):
        return f'{self.name}'


class Order(models.Model):
    """The order model"""
    ORDER_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, blank=False, null=False)
    order_type = models.CharField(max_length=4, choices=ORDER_CHOICES, null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=False)
    date_time_placed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.stock.name} - {self.order_type} - {self.quantity}"
