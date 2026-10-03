import json
from datetime import time

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Importações dos teus modelos
from tenants.models import Restaurant, PaymentMethod, OperatingHours
from .models import Category, Product, Order, OrderItem, DeliveryFee
from tenants.forms import RestaurantProfileForm

from django.utils import timezone

# Adicione esta linha junto aos outros imports no topo:
from .forms import CategoryForm, ProductForm

# ==========================================
# 1. VISÃO DO CLIENTE (Cardápio Digital)
# ==========================================
def restaurant_menu(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    categories = Category.objects.filter(restaurant=restaurant).prefetch_related('products')
    delivery_fees = DeliveryFee.objects.filter(restaurant=restaurant)
    
    # --- LÓGICA DE ABERTO / FECHADO ---
    # Pegamos a hora atual no fuso horário do servidor (Brasil)
    current_time = timezone.localtime(timezone.now())
    # datetime.weekday() retorna 0 para Segunda e 6 para Domingo (bate certinho com o nosso banco!)
    current_day_str = str(current_time.weekday())
    current_time_only = current_time.time()
    
    is_open = False
    # Buscamos os horários de HOJE no banco de dados
    today_hours = restaurant.hours.filter(day=current_day_str).first()
    
    if today_hours and not today_hours.is_closed:
        # Se a hora atual estiver entre a hora de abrir e fechar, a loja está aberta
        if today_hours.opening_time <= current_time_only <= today_hours.closing_time:
            is_open = True
    # ----------------------------------
    all_hours = restaurant.hours.all().order_by('day')
    
    context = {
        'restaurant': restaurant,
        'categories': categories,
        'delivery_fees': delivery_fees,
        'is_open': is_open,            # Enviamos o status de aberto/fechado para a tela
        'today_hours': today_hours,    # Enviamos os horários de hoje para mostrar no texto
        'all_hours': all_hours,
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


# ==========================================
# 2. PAINEL DA COZINHA (KDS)
# ==========================================
def kitchen_dashboard(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug)
    
    # 1. Pedidos ATIVOS
    active_orders = Order.objects.filter(restaurant=restaurant).exclude(status__in=['concluido', 'cancelado', 'COMPLETED', 'CANCELED']).order_by('created_at')
    
    # 2. TODOS os pedidos
    all_orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')
    
    context = {
        'restaurant': restaurant,
        'active_orders': active_orders,
        'all_orders': all_orders,
    }
    return render(request, 'menu/kitchen.html', context)


@csrf_exempt
def update_order_status(request, order_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        order = get_object_or_404(Order, id=order_id)
        order.status = data.get('status')
        order.save()
        return JsonResponse({'success': True, 'status': order.status})
    return JsonResponse({'error': 'Método não permitido'}, status=405)


# ==========================================
# 3. PAINEL DO GESTOR (Configurações)
# ==========================================
@login_required
def restaurant_admin(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    categories = Category.objects.filter(restaurant=restaurant).prefetch_related('products')
    
    # 1. Garante que as formas de pagamento padrão existem
    if not restaurant.payment_methods.exists():
        default_methods = [
            ('Pix', 'ONLINE'),
            ('Cartão de Crédito', 'DELIVERY'),
            ('Cartão de Débito', 'DELIVERY'),
            ('Dinheiro (Necessita Troco)', 'DELIVERY'),
            ('Vale Refeição (VR/Alelo/Ticket)', 'DELIVERY'),
        ]
        for name, category in default_methods:
            PaymentMethod.objects.create(restaurant=restaurant, name=name, category=category, is_active=False)
            
    # 2. Garante que os horários padrão existem para a semana toda
    if not restaurant.hours.exists():
        for day_code, day_name in OperatingHours.DAYS_OF_WEEK:
            OperatingHours.objects.create(
                restaurant=restaurant, 
                day=day_code, 
                opening_time=time(11, 0),
                closing_time=time(23, 0),
                is_closed=False
            )
            
    payment_methods = restaurant.payment_methods.all()
    operating_hours = restaurant.hours.all()
    
    # Instanciamos o formulário base para quando a página é apenas carregada (GET)
    profile_form = RestaurantProfileForm(instance=restaurant)

    # 3. Processamento de todos os botões "Guardar" (POST)
    if request.method == 'POST':
        
        # A. Guardar Perfil
        if 'update_profile' in request.POST:
            # ADICIONAMOS O request.FILES AQUI:
            profile_form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
            if profile_form.is_valid():
                profile_form.save()
                return redirect('restaurant_admin', slug=slug)
                
        # B. Guardar Pagamentos
        elif 'update_payments' in request.POST:
            active_payment_ids = request.POST.getlist('payments')
            for pm in payment_methods:
                pm.is_active = str(pm.id) in active_payment_ids
                pm.save()
            return redirect('restaurant_admin', slug=slug)
            
        # C. Guardar Horários
        elif 'update_hours' in request.POST:
            for hour in operating_hours:
                is_closed = request.POST.get(f'is_closed_{hour.id}') == 'on'
                opening_time = request.POST.get(f'opening_{hour.id}')
                closing_time = request.POST.get(f'closing_{hour.id}')
                
                hour.is_closed = is_closed
                if opening_time:
                    hour.opening_time = opening_time
                if closing_time:
                    hour.closing_time = closing_time
                hour.save()
            return redirect('restaurant_admin', slug=slug)
            
    # 4. Montar a resposta para o ecrã
    context = {
        'restaurant': restaurant,
        'categories': categories,
        'profile_form': profile_form,
        'payment_methods': payment_methods,
        'operating_hours': operating_hours,
    }
    return render(request, 'menu/admin_cardapio.html', context)

@login_required
def create_category(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.restaurant = restaurant # Associa a categoria à loja correta
            category.save()
            return redirect('restaurant_admin', slug=slug)
    else:
        form = CategoryForm()
        
    context = {'form': form, 'restaurant': restaurant, 'title': 'Nova Categoria'}
    return render(request, 'menu/form_generico.html', context)

@login_required
def create_product(request, slug, category_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    category = get_object_or_404(Category, id=category_id, restaurant=restaurant)
    
    if request.method == 'POST':
        # request.FILES é obrigatório aqui por causa da foto do produto!
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.restaurant = restaurant
            product.category = category # Associa o produto à categoria escolhida
            product.save()
            return redirect('restaurant_admin', slug=slug)
    else:
        form = ProductForm()
        
    context = {'form': form, 'restaurant': restaurant, 'title': f'Novo Produto em {category.name}'}
    return render(request, 'menu/form_generico.html', context)

# ==========================================
# EDIÇÃO E EXCLUSÃO (Categorias e Produtos)
# ==========================================
@login_required
def edit_category(request, slug, category_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    category = get_object_or_404(Category, id=category_id, restaurant=restaurant)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('restaurant_admin', slug=slug)
    else:
        form = CategoryForm(instance=category)
        
    context = {'form': form, 'restaurant': restaurant, 'title': f'Editar Categoria'}
    return render(request, 'menu/form_generico.html', context)

@login_required
def delete_category(request, slug, category_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    category = get_object_or_404(Category, id=category_id, restaurant=restaurant)
    category.delete()
    return redirect('restaurant_admin', slug=slug)

@login_required
def edit_product(request, slug, product_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    product = get_object_or_404(Product, id=product_id, restaurant=restaurant)
    
    if request.method == 'POST':
        # request.FILES obrigatório para não perder a foto ao editar!
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('restaurant_admin', slug=slug)
    else:
        form = ProductForm(instance=product)
        
    context = {'form': form, 'restaurant': restaurant, 'title': f'Editar Produto'}
    return render(request, 'menu/form_generico.html', context)

@login_required
def delete_product(request, slug, product_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    product = get_object_or_404(Product, id=product_id, restaurant=restaurant)
    product.delete()
    return redirect('restaurant_admin', slug=slug)