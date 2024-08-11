'''Views for api trades'''
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema_view, extend_schema

from rest_framework import generics, viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from api_trades.models import Order, Stock
from api_trades.serializers import (
    OrderSerializer,
    StockSerializer,
    EmptySerializer,
    PortfolioSerializer
)

@extend_schema_view(
    list=extend_schema(
        summary="List all orders",
        description="Retrieve a list of all orders placed by the authenticated user."
    ),
    create=extend_schema(
        summary="Create a new order",
        description="Place a new order for a stock by the authenticated user."
    ),
)
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


@extend_schema_view(
    list=extend_schema(
        summary="List all stocks",
        description="Retrieve a list of all available stocks."
    ),
    retrieve=extend_schema(
        summary="Retrieve a stock",
        description="Retrieve details of a specific stock by its ID."
    ),
    create=extend_schema(
        summary="Create a new stock",
        description="Create a new stock with the provided data."
    ),
    update=extend_schema(
        summary="Update an existing stock",
        description="Update the details of an existing stock."
    ),
    partial_update=extend_schema(
        summary="Partially update a stock",
        description="Partially update the details of an existing stock."
    ),
    destroy=extend_schema(
        summary="Delete a stock",
        description="Delete an existing stock."
    ),
)
class StockViewSet(viewsets.ModelViewSet):
    '''viewset for the stock endpoints'''
    serializer_class = StockSerializer
    queryset = Stock.objects.all()
    authentication_classes =[TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        return queryset

    def perform_create(self, serializer):
        """Handle the creation of a new Stock instance."""
        if self.request.user.is_superuser:
            serializer.save()
        else:
            raise PermissionDenied("Only superusers can create stocks.")

    def perform_update(self, serializer):
        """Handle the update of an existing Stock instance."""
        if self.request.user.is_superuser:
            serializer.save()
        else:
            raise PermissionDenied("Only superusers can update stocks.")

    def perform_destroy(self, instance):
        """Handle the deletion of a Stock instance."""
        if self.request.user.is_superuser:
            instance.delete()
        else:
            raise PermissionDenied("Only superusers can update stocks.")

class TotalValueInvestedView(
    generics.GenericAPIView
):
    """
    API view to get the total value invested in a specific stock by the authenticated user.
    """
    authentication_classes =[TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer # prevents throwing error in console.

    @extend_schema(
        summary="Get total value invested in a stock",
        description="Retrieve the net total value invested by \
            the authenticated user\
            in a specific stock, considering buy and sell orders."
    )
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

    @extend_schema(
        summary="Get user's portfolio",
        description="Retrieve the portfolio of the authenticated user,\
            showing the total quantity and value of each stock they hold."
    )
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
