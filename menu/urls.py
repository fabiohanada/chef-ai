from django.urls import path
from . import views, views_webhook

urlpatterns = [
    path('<slug:slug>/', views.restaurant_menu, name='restaurant_menu'),
    path('<slug:slug>/api/order/', views.create_order_api, name='create_order_api'),
    path('<slug:slug>/cozinha/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('api/order/<uuid:order_id>/status/', views.update_order_status, name='update_order_status'),
    # Rota do Webhook do Bot do WhatsApp
    path('<slug:slug>/webhook/whatsapp/', views_webhook.whatsapp_webhook, name='whatsapp_webhook'),
    path('<slug:slug>/admin-cardapio/', views.restaurant_admin, name='restaurant_admin'),
    path('<slug:slug>/nova-categoria/', views.create_category, name='create_category'),
    path('<slug:slug>/categoria/<int:category_id>/novo-produto/', views.create_product, name='create_product'),
    # Rotas de Criação
    path('<slug:slug>/nova-categoria/', views.create_category, name='create_category'),
    path('<slug:slug>/categoria/<int:category_id>/novo-produto/', views.create_product, name='create_product'),
    
    # NOVAS Rotas de Edição e Exclusão
    path('<slug:slug>/categoria/<int:category_id>/editar/', views.edit_category, name='edit_category'),
    path('<slug:slug>/categoria/<int:category_id>/excluir/', views.delete_category, name='delete_category'),
    path('<slug:slug>/produto/<int:product_id>/editar/', views.edit_product, name='edit_product'),
    path('<slug:slug>/produto/<int:product_id>/excluir/', views.delete_product, name='delete_product'),
]
