"""
url mappings for the api_trades app
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('trades', views.OrdersViewSet)

urlpatterns = router.urls

urlpatterns += [
    path('total_value_invested/<int:stock_id>/', views.TotalValueInvestedView.as_view(), name='total_value_invested'),
    path('portfolio/', views.PortfolioView.as_view(), name='user-portfolio'),
]