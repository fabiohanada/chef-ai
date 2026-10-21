from django.urls import path
from . import views, views_webhook

urlpatterns = [
    # ==========================================
    # 0. ROTAS GLOBAIS FIXAS (Devem vir SEMPRE no topo)
    # ==========================================
    path('cadastro/', views.merchant_register, name='merchant_register'),
    path('painel-geral/mensalidades/', views.superadmin_subscriptions_view, name='superadmin_subscriptions'),
    path('pagar-mensalidade/<uuid:restaurant_id>/', views.criar_pagamento_mensalidade, name='pagar_mensalidade'),
    
    # Webhooks Globais e APIs genéricas
    path('api/webhook/mercadopago/', views.mercadopago_webhook, name='mercadopago_webhook'),
    path('api/order/<uuid:order_id>/status/', views.update_order_status, name='update_order_status'),

    # ==========================================
    # 1. PAINEL DO LOJISTA (Administração com Slug)
    # ==========================================
    path('<slug:slug>/dashboard/', views.financial_dashboard, name='financial_dashboard'),
    path('<slug:slug>/admin-cardapio/', views.restaurant_admin, name='restaurant_admin'),
    
    # Categorias
    path('<slug:slug>/nova-categoria/', views.create_category, name='create_category'),
    path('<slug:slug>/categoria/<int:category_id>/editar/', views.edit_category, name='edit_category'),
    path('<slug:slug>/categoria/<int:category_id>/excluir/', views.delete_category, name='delete_category'),
    
    # Produtos
    path('<slug:slug>/categoria/<int:category_id>/novo-produto/', views.create_product, name='create_product'),
    path('<slug:slug>/produto/<int:product_id>/editar/', views.edit_product, name='edit_product'),
    path('<slug:slug>/produto/<int:product_id>/excluir/', views.delete_product, name='delete_product'),
    
    # Taxas de Entrega / Bairros
    path('<slug:slug>/admin/taxa/nova/', views.create_delivery_fee, name='create_delivery_fee'),
    path('<slug:slug>/admin/taxa/<int:fee_id>/editar/', views.edit_delivery_fee, name='edit_delivery_fee'),
    path('<slug:slug>/admin/taxa/<int:fee_id>/apagar/', views.delete_delivery_fee, name='delete_delivery_fee'),

    # ==========================================
    # 2. COZINHA / KDS E WEBOOKS DA LOJA
    # ==========================================
    path('<slug:slug>/cozinha/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('<slug:slug>/api/check-new-orders/', views.check_new_orders, name='check_new_orders'),
    path('<slug:slug>/api/order/', views.create_order_api, name='create_order_api'),
    path('<slug:slug>/webhook/whatsapp/', views_webhook.whatsapp_webhook, name='whatsapp_webhook'),

    # ==========================================
    # 3. ÁREA PÚBLICA (Cliente Final) - SEMPRE NO FIM
    # ==========================================
    # Fica no fim para não interferir com rotas como "cadastro", "painel-geral", etc.
    path('<slug:slug>/', views.restaurant_menu, name='restaurant_menu'),
]