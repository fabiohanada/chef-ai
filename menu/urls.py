from django.urls import path
from . import views, views_webhook

urlpatterns = [
    # ==========================================
    # 0. REGISTO / ONBOARDING (DEVE VIR SEMPRE ANTES DO SLUG)
    # ==========================================
    path('cadastro/', views.merchant_register, name='merchant_register'),

    # ==========================================
    # 1. ÁREA PÚBLICA (Cliente Final)
    # ==========================================
    path('<slug:slug>/', views.restaurant_menu, name='restaurant_menu'),
    path('<slug:slug>/api/order/', views.create_order_api, name='create_order_api'),

    # ==========================================
    # 2. COZINHA / KDS & WEBHOOKS
    # ==========================================
    path('<slug:slug>/cozinha/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('<slug:slug>/api/check-new-orders/', views.check_new_orders, name='check_new_orders'), # <-- ADICIONA ESTA LINHA
    path('api/order/<uuid:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('<slug:slug>/webhook/whatsapp/', views_webhook.whatsapp_webhook, name='whatsapp_webhook'),

    # ==========================================
    # 3. PAINEL DO LOJISTA (Administração)
    # ==========================================
    path('<slug:slug>/admin-cardapio/', views.restaurant_admin, name='restaurant_admin'),
    path('<slug:slug>/dashboard/', views.financial_dashboard, name='financial_dashboard'),
    
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
    # 4. PAINEL DO SUPERADMIN (Global)
    # ==========================================
    path('painel-geral/mensalidades/', views.superadmin_subscriptions_view, name='superadmin_subscriptions'),
]