from django.contrib import admin
from .models import Category, Product, Order, OrderItem, DeliveryFee

class ProductInline(admin.TabularInline):
    model = Product
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'order')
    list_filter = ('restaurant',)
    inlines = [ProductInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price', 'is_available')
    list_filter = ('restaurant', 'category', 'is_available')
    search_fields = ('name', 'description')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'restaurant', 'customer_name', 'status', 'total_amount', 'created_at')
    list_filter = ('restaurant', 'status', 'created_at')
    inlines = [OrderItemInline]
    
@admin.register(DeliveryFee)
class DeliveryFeeAdmin(admin.ModelAdmin):
    list_display = ('neighborhood', 'restaurant', 'fee')
    list_filter = ('restaurant',)
    search_fields = ('neighborhood',)