from django.urls import path
from . import views, views_webhook

urlpatterns = [
    path('<slug:slug>/', views.restaurant_menu, name='restaurant_menu'),
    path('<slug:slug>/api/order/', views.create_order_api, name='create_order_api'),
    path('<slug:slug>/cozinha/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('api/order/<uuid:order_id>/status/', views.update_order_status, name='update_order_status'),
    # Rota do Webhook do Bot do WhatsApp
    path('<slug:slug>/webhook/whatsapp/', views_webhook.whatsapp_webhook, name='whatsapp_webhook'),
]