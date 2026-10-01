import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from tenants.models import Restaurant
from .models import Category, Product, Order, OrderItem, DeliveryFee

# View do Cardápio Digital
def restaurant_menu(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    categories = Category.objects.filter(restaurant=restaurant).prefetch_related('products')
    
    context = {
        'restaurant': restaurant,
        'categories': categories,
    }
    return render(request, 'menu/cardapio.html', context)

# API para salvar o pedido feito no cardápio no banco de dados
@csrf_exempt
def create_order_api(request, slug):
    if request.method == 'POST':
        try:
            restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
            data = json.loads(request.body)
            
            # Criar o pedido principal
            order = Order.objects.create(
                restaurant=restaurant,
                customer_name=data.get('customer_name'),
                customer_phone=data.get('customer_phone', ''),
                address=data.get('address'),
                total_amount=data.get('total_amount'),
                status='PENDING'
            )
            
            # Criar os itens do pedido
            for item in data.get('items', []):
                product = Product.objects.filter(name=item['name'], restaurant=restaurant).first()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item['qty'],
                    unit_price=item['price']
                )
                
            return JsonResponse({'success': True, 'order_id': str(order.id)[:8]})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Método não permitido'}, status=405)

# Painel do Gestor / Cozinha (PDV/KDS)
def kitchen_dashboard(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug)
    
    # 1. Pedidos ATIVOS (Exclui os concluídos e cancelados da tela de produção)
    # ATENÇÃO: Verifique se no seu models.py os status estão em maiúsculas (ex: 'COMPLETED', 'CANCELED') ou minúsculas.
    active_orders = Order.objects.filter(restaurant=restaurant).exclude(status__in=['concluido', 'cancelado', 'COMPLETED', 'CANCELED']).order_by('created_at')
    
    # 2. TODOS os pedidos (Para a tabela de histórico, do mais recente para o mais antigo)
    all_orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')
    
    context = {
        'restaurant': restaurant,
        'active_orders': active_orders, # Passa os ativos para os cartões
        'all_orders': all_orders,       # Passa o histórico para a tabela
    }
    return render(request, 'menu/kitchen.html', context)

# API para atualizar status do pedido na cozinha
@csrf_exempt
def update_order_status(request, order_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        order = get_object_or_404(Order, id=order_id)
        order.status = data.get('status')
        order.save()
        return JsonResponse({'success': True, 'status': order.status})
    return JsonResponse({'error': 'Método não permitido'}, status=405)

def restaurant_menu(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    categories = Category.objects.filter(restaurant=restaurant).prefetch_related('products')
    delivery_fees = DeliveryFee.objects.filter(restaurant=restaurant) # <--- Buscar taxas
    
    context = {
        'restaurant': restaurant,
        'categories': categories,
        'delivery_fees': delivery_fees, # <--- Passar no contexto
    }
    return render(request, 'menu/cardapio.html', context)

@csrf_exempt
def create_order_api(request, slug):
    if request.method == 'POST':
        try:
            restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
            data = json.loads(request.body)
            
            # Criar o pedido principal com o método de pagamento
            order = Order.objects.create(
                restaurant=restaurant,
                customer_name=data.get('customer_name'),
                customer_phone=data.get('customer_phone', ''),
                address=data.get('address'),
                payment_method=data.get('payment_method', 'PIX'),
                total_amount=data.get('total_amount'),
                status='PENDING'
            )
            
            # Criar os itens do pedido
            for item in data.get('items', []):
                product = Product.objects.filter(name=item['name'], restaurant=restaurant).first()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item['qty'],
                    unit_price=item['price']
                )
                
            return JsonResponse({'success': True, 'order_id': str(order.id)[:8]})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
def restaurant_admin(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    categories = Category.objects.filter(restaurant=restaurant).prefetch_related('products')
    
    context = {
        'restaurant': restaurant,
        'categories': categories,
    }
    return render(request, 'menu/admin_cardapio.html', context)