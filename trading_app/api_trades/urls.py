"""
url mappings for the api_trades app
"""
from django.urls import (
    path,
)

from rest_framework.routers import DefaultRouter

from api_trades import views

router = DefaultRouter()
router.register('', views.OrdersViewSet, basename='orders')

urlpatterns = router.urls

urlpatterns += [
    path(
        'total_value_invested/<int:stock_id>/',
        views.TotalValueInvestedView.as_view(),
        name='total_value_invested'),
    path('portfolio/', views.PortfolioView.as_view(), name='user-portfolio'),
]

app_name = 'orders'
