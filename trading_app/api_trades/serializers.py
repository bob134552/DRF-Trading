"""Serializers for api_trades app"""
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


from django.db.models import Sum

from .models import Order, Stock

class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""

    class Meta:
        """ Meta for order serializer"""
        model = Order
        fields = [
            'id',
            'order_type',
            'stock',
            'quantity',
            'date_time_placed'
        ]

    def create(self, validated_data):
        """Create a trade order, ensuring that a sell order does not exceed the user's holdings."""
        user = self.context['request'].user
        stock = validated_data['stock']
        order_type = validated_data['order_type']
        quantity = validated_data['quantity']

        if order_type == 'sell':
            # Calculate the user's total holdings of the stock
            total_buy_quantity = Order.objects.filter(
                user=user,
                stock=stock,
                order_type='buy'
            ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
            total_sell_quantity = Order.objects.filter(
                user=user,
                stock=stock,
                order_type='sell'
            ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

            # Calculate net available quantity
            net_quantity = total_buy_quantity - total_sell_quantity

            if quantity > net_quantity:
                raise ValidationError(
                    f"You cannot sell more than your current holdings. "
                    f"Available quantity: {net_quantity}"
                )


        # Create the order
        order = Order.objects.create(**validated_data)
        return order


class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model"""

    class Meta:
        model = Stock
        fields = [
            'id',
            'name',
            'price'
        ]
        read_only_fields = ['id']


class PortfolioSerializer(serializers.Serializer):
    stock_name = serializers.CharField()
    quantity = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=10, decimal_places=2)


class EmptySerializer(serializers.Serializer):
    pass
