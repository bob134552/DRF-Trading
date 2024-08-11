'''Views for api trades'''
from django.shortcuts import get_object_or_404

from rest_framework import generics, viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from api_trades.models import Order, Stock
from api_trades.serializers import OrderSerializer, EmptySerializer, PortfolioSerializer


class OrdersViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
):
    """View for managing orders"""
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    authentication_classes =[TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Adds the user to the create.
        serializer.save(user=self.request.user)


class TotalValueInvestedView(
    generics.GenericAPIView
):
    """
    API view to get the total value invested in a specific stock by the authenticated user.
    """
    authentication_classes =[TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer # prevents throwing error in console.

    def get(self, request, stock_id):
        """
        gets stocks overall invested value.
        """
        stock = get_object_or_404(Stock, id=stock_id)

        # Get all buy orders
        buy_orders = Order.objects.filter(
            user=request.user, stock=stock, order_type='buy')
        total_buy_value = sum(order.quantity * stock.price for order in buy_orders)

        # Get all sell orders
        sell_orders = Order.objects.filter(
            user=request.user, stock=stock, order_type='sell')
        total_sell_value = sum(order.quantity * stock.price for order in sell_orders)

        # Calculate net total value invested
        net_total_value = total_buy_value - total_sell_value

        return Response({'total_value': net_total_value})


class PortfolioView(APIView):
    """
    API view to return the user's portfolio with the total quantity and value of each stock.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PortfolioSerializer

    def get(self, request):
        """
        Gets portfolio of user
        """
        user = request.user

        # Retrieve all orders for the user
        orders = Order.objects.filter(user=user)

        # Dictionary to store total quantities and values for each stock
        stock_summary = {}

        # Process each order
        for order in orders:
            stock_id = order.stock.id
            stock_name = order.stock.name
            quantity = order.quantity

            if stock_id not in stock_summary:
                stock_summary[stock_id] = {
                    'stock_name': stock_name,
                    'total_buy_quantity': 0,
                    'total_sell_quantity': 0,
                    'net_quantity': 0,
                    'total_value': 0
                }

            if order.order_type == 'buy':
                stock_summary[stock_id]['total_buy_quantity'] += quantity
            elif order.order_type == 'sell':
                stock_summary[stock_id]['total_sell_quantity'] += quantity

        # Compute net quantities and values
        for stock_id, summary in stock_summary.items():
            summary['net_quantity'] = summary['total_buy_quantity'] - summary['total_sell_quantity']
            if summary['net_quantity'] > 0:
                summary['total_value'] = summary['net_quantity'] * Stock.objects.get(id=stock_id).price
            else:
                # If no net quantity, set total value to 0
                summary['total_value'] = 0

        # Filter out stocks with no net quantity
        portfolio_with_value = [
            {
                'stock_name': summary['stock_name'],
                'quantity': summary['net_quantity'],
                'total_value': summary['total_value']
            }
            for summary in stock_summary.values()
            if summary['net_quantity'] > 0
        ]

        if not portfolio_with_value:
            return Response({
                'message': 'You currently have no stocks in your portfolio'}, status=200)

        # Serialize the data
        serializer = self.serializer_class(portfolio_with_value, many=True)
        return Response(serializer.data)
