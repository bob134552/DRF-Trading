from django.contrib import admin

from .models import Stock, Order
# Register your models here.

admin.site.register(Stock)
admin.site.register(Order)
