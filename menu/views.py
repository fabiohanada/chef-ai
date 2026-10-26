# 1. Biblioteca Padrão do Python
import json
import os
from datetime import datetime, time, timedelta

# 2. Bibliotecas de Terceiros
import mercadopago
import requests
from dotenv import load_dotenv
from twilio.rest import Client

# 3. Django
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# 4. Aplicações do Projeto (Tenants e Menu)
from menu.forms import CategoryForm, ProductForm
from menu.models import Category, DeliveryFee, Order, OrderItem, Product, Subscription
from tenants.forms import RestaurantProfileForm
from tenants.models import OperatingHours, PaymentMethod, Restaurant

from datetime import datetime
from django.utils import timezone

load_dotenv()
# ==========================================
# 1. VISÃO DO CLIENTE (Cardápio Digital)
# ==========================================
def restaurant_menu(request, slug):
    # Procura o restaurante pelo slug sem filtrar is_active na query para evitar erro 404 técnico
    restaurant = get_object_or_404(Restaurant, slug=slug)
    
    # --- BLOQUEIO SE A LOJA ESTIVER INATIVA OU EM ATRASO ---
    if not restaurant.is_active or restaurant.subscription_status == 'OVERDUE':
        return render(request, 'menu/loja_indisponivel.html', {'restaurant': restaurant})
    # -----------------------------------------------------
    
    categories = Category.objects.filter(restaurant=restaurant).prefetch_related('products')
    delivery_fees = DeliveryFee.objects.filter(restaurant=restaurant)
    
    is_open = is_restaurant_open(restaurant)
    
    current_time = timezone.localtime(timezone.now())
    current_day_str = str(current_time.weekday())
    today_hours = restaurant.hours.filter(day=current_day_str).first()
    all_hours = restaurant.hours.all().order_by('day')
    
    context = {
        'restaurant': restaurant,
        'categories': categories,
        'delivery_fees': delivery_fees,
        'is_open': is_open,
        'today_hours': today_hours,
        'all_hours': all_hours,
    }
    return render(request, 'menu/cardapio.html', context)

# ==========================================
# 2. PAINEL DA COZINHA (KDS)
# ==========================================
def kitchen_dashboard(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug)
    
    # --- BLOQUEIO NO PAINEL DO LOJISTA ---
    if restaurant.subscription_status == 'OVERDUE':
        # Renderiza a tela de pagamento pendente em vez da cozinha
        return render(request, 'menu/pagamento_pendente.html', {'restaurant': restaurant})
    
    # Conta quantas lojas o utilizador dono deste restaurante possui
    user_stores_count = Restaurant.objects.filter(user=restaurant.user).count()
    has_multiple_stores = user_stores_count > 1
    
    orders = Order.objects.filter(restaurant=restaurant).exclude(status__in=['concluido', 'cancelado', 'COMPLETED', 'CANCELED']).order_by('created_at')
    all_orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')
    
    latest_time = timezone.now().isoformat()
    
    context = {
        'restaurant': restaurant,
        'orders': orders,
        'all_orders': all_orders,
        'has_multiple_stores': has_multiple_stores, # <--- Variável de controlo
        'latest_time': latest_time, # Passamos a data para o ecrã
    }
    return render(request, 'menu/kitchen.html', context)

@csrf_exempt
def update_order_status(request, order_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        order = get_object_or_404(Order, id=order_id)
        novo_status = data.get('status')
        
        # Só envia a mensagem se o status realmente mudou
        if order.status != novo_status:
            order.status = novo_status
            order.save()
            
            # Chama a nossa função de disparo de WhatsApp
            enviar_notificacao_whatsapp(order)
            
        return JsonResponse({'success': True, 'status': order.status})
    return JsonResponse({'error': 'Método não permitido'}, status=405)

# --- NOVA FUNÇÃO DE DISPARO ---
def enviar_notificacao_whatsapp(order):
    # Dicionário de mensagens
    mensagens = {
        'PREPARING': f"👨‍🍳 Olá {order.customer_name}! O seu pedido na {order.restaurant.name} já está na cozinha a ser preparado. Avisamos quando sair!",
        'DISPATCHED': f"🛵 Boas notícias, {order.customer_name}! O seu pedido acabou de sair para entrega. Prepare a mesa!",
        'COMPLETED': f"✅ Pedido entregue! A {order.restaurant.name} agradece a preferência. Bom apetite!",
        'CANCELED': f"❌ Olá {order.customer_name}, o seu pedido teve de ser cancelado. Por favor, entre em contacto com a loja para mais detalhes."
    }
    
    mensagem_texto = mensagens.get(order.status)
    telefone_cliente = order.customer_phone
    
    if mensagem_texto and telefone_cliente:
        try:
            # CREDENCIAIS DO TWILIO (Substitui pelos teus dados reais do painel do Twilio)
            TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
            TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
            TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886' # Exemplo do número Sandbox
            
            # Formata o número do cliente para o padrão internacional do WhatsApp (ex: +5511999999999)
            # Retira qualquer traço ou espaço que possa ter vindo do formulário
            telefone_limpo = ''.join(filter(str.isdigit, telefone_cliente))
            
            # Garante que tem o código do Brasil (+55) se o cliente não o tiver colocado
            if not telefone_limpo.startswith('55'):
                telefone_limpo = f"55{telefone_limpo}"
                
            numero_destino = f"whatsapp:+{telefone_limpo}"
            
            # Inicializa o cliente e envia a mensagem
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=mensagem_texto,
                to=numero_destino
            )
            
            print(f"Mensagem enviada com sucesso! SID: {message.sid}")
            
        except Exception as e:
            print(f"Erro ao enviar WhatsApp pelo Twilio: {e}")

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
    delivery_fees = restaurant.delivery_fees.all()
    
    # Instanciamos o formulário base para quando a página é apenas carregada (GET)
    profile_form = RestaurantProfileForm(instance=restaurant)

    # 3. Processamento de todos os botões "Guardar" (POST)
    if request.method == 'POST':
        
        # A. Guardar Perfil
        if 'update_profile' in request.POST:
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
        'delivery_fees': delivery_fees,
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

@csrf_exempt
def create_order_api(request, slug):
    if request.method == 'POST':
        try:
            restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
            data = json.loads(request.body)
            
            # --- VALIDAÇÃO DE HORÁRIO ---
            if not is_restaurant_open(restaurant):
                return JsonResponse({
                    'success': False, 
                    'error': 'A loja encontra-se encerrada no momento e não está a aceitar novos pedidos.'
                }, status=400)
            
            # Cria o pedido principal associado ao restaurante com status em minúsculas ou compatível com a cozinha
            order = Order.objects.create(
                restaurant=restaurant,
                customer_name=data.get('customer_name'),
                customer_phone=data.get('customer_phone', ''),
                address=data.get('address'),
                payment_method=data.get('payment_method', 'PIX'),
                total_amount=data.get('total_amount'),
                status='PENDING' # Garante que fica em maiúsculas para o template reconhecer
            )
            
            # Criar os itens do pedido associados
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
def create_delivery_fee(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    
    if request.method == 'POST':
        neighborhood = request.POST.get('neighborhood')
        fee = request.POST.get('fee')
        if neighborhood and fee:
            DeliveryFee.objects.create(
                restaurant=restaurant,
                neighborhood=neighborhood,
                fee=fee
            )
    return redirect('restaurant_admin', slug=slug)

@login_required
def delete_delivery_fee(request, slug, fee_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    fee = get_object_or_404(DeliveryFee, id=fee_id, restaurant=restaurant)
    fee.delete()
    return redirect('restaurant_admin', slug=slug)

@login_required
def edit_delivery_fee(request, slug, fee_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    fee_obj = get_object_or_404(DeliveryFee, id=fee_id, restaurant=restaurant)
    
    if request.method == 'POST':
        neighborhood = request.POST.get('neighborhood')
        fee = request.POST.get('fee')
        if neighborhood and fee:
            fee_obj.neighborhood = neighborhood
            fee_obj.fee = fee
            fee_obj.save()
            return redirect('restaurant_admin', slug=slug)
            
    context = {'fee': fee_obj, 'restaurant': restaurant}
    return render(request, 'menu/edit_delivery_fee.html', context)

@staff_member_required
def superadmin_subscriptions_view(request):
    restaurants = Restaurant.objects.all().select_related('user').order_by('-id')
    
    # --- VERIFICAÇÃO AUTOMÁTICA DE VENCIMENTO ---
    hoje = timezone.now().date()
    for rest in restaurants:
        if rest.due_date and rest.due_date < hoje and rest.subscription_status != 'OVERDUE':
            rest.subscription_status = 'OVERDUE'
            rest.save(update_fields=['subscription_status'])
    # ---------------------------------------------
    
    # Métricas globais do SaaS para o topo do painel
    total_lojas = restaurants.count()
    lojas_ativas = restaurants.filter(subscription_status='ACTIVE').count()
    lojas_atrasadas = restaurants.filter(subscription_status='OVERDUE').count()
    
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant_id')
        action = request.POST.get('action') # 'update_sub' ou 'toggle_block'
        
        rest_obj = get_object_or_404(Restaurant, id=restaurant_id)
        
        if action == 'update_sub':
            # --- PROTEÇÃO DA MENSALIDADE ---
            monthly_fee_str = request.POST.get('monthly_fee')
            if not monthly_fee_str:
                rest_obj.monthly_fee = 0.00  # Se vier vazio, guarda 0
            else:
                rest_obj.monthly_fee = monthly_fee_str
            # -------------------------------
            
            due_date_str = request.POST.get('due_date')
            if due_date_str:
                try:
                    rest_obj.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                except ValueError:
                    rest_obj.due_date = None
            else:
                rest_obj.due_date = None
            
            if rest_obj.due_date and rest_obj.due_date >= hoje and rest_obj.subscription_status == 'OVERDUE':
                rest_obj.subscription_status = 'ACTIVE'
                
            rest_obj.save()
            
        elif action == 'toggle_block':
            # AGORA BLOQUEIA APENAS ESTE RESTAURANTE INDIVIDUALMENTE
            rest_obj.is_active = not rest_obj.is_active
            rest_obj.save(update_fields=['is_active'])
            
        return redirect('superadmin_subscriptions')

    context = {
        'restaurants': restaurants,
        'total_lojas': total_lojas,
        'lojas_ativas': lojas_ativas,
        'lojas_atrasadas': lojas_atrasadas,
    }
    return render(request, 'menu/superadmin_subscriptions.html', context)

# ==========================================
# FUNÇÃO DE VERIFICAÇÃO DE HORÁRIO LIMPA
# ==========================================
def is_restaurant_open(restaurant):
    # Obtém a hora e o dia atual com base no fuso horário configurado no Django
    current_time = timezone.localtime(timezone.now())
    current_day_str = str(current_time.weekday())  # '0' a '6' (Segunda a Domingo)
    current_time_only = current_time.time()
    
    today_hours = restaurant.hours.filter(day=current_day_str).first()
    
    if not today_hours or today_hours.is_closed:
        return False
        
    if today_hours.opening_time <= current_time_only <= today_hours.closing_time:
        return True
        
    return False

from django.utils.text import slugify

def merchant_register(request):
    if request.method == 'POST':
        owner_name = request.POST.get('name') # "Nome do usuario"
        email = request.POST.get('email')
        whatsapp_number = request.POST.get('whatsapp') # "Celular"
        restaurant_name = request.POST.get('restaurant_name') # "Nome do seu delivery"
        password = request.POST.get('password')
        
        # Gera o slug automaticamente através do nome do delivery
        base_slug = slugify(restaurant_name)
        slug = base_slug
        counter = 1
        # Garante que o slug é único na base de dados
        while Restaurant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        # Define um username temporário baseado no email ou slug
        username = email.split('@')[0]
        if User.objects.filter(username=username).exists():
            username = f"{username}_{slug}"

        if User.objects.filter(email=email).exists():
            context = {'error': 'Este e-mail já está a ser utilizado.'}
            return render(request, 'menu/merchant_register.html', context)
            
        # 1. Cria o Utilizador
        user = User.objects.create_user(username=username, email=email, password=password, first_name=owner_name)
        
        # 2. Cria o Restaurante
        restaurant = Restaurant.objects.create(
            user=user,
            name=restaurant_name,
            slug=slug,
            whatsapp_number=whatsapp_number,
            plan='PRO',
            subscription_status='ACTIVE',
            monthly_fee=99.90
        )
        
        # 3. Cria formas de pagamento padrão
        default_methods = [
            ('Pix', 'ONLINE'),
            ('Cartão de Crédito', 'DELIVERY'),
            ('Dinheiro (Necessita Troco)', 'DELIVERY'),
        ]
        for name, category in default_methods:
            PaymentMethod.objects.create(restaurant=restaurant, name=name, category=category, is_active=True)
            
        # 4. Cria horários padrão
        for day_code, day_name in OperatingHours.DAYS_OF_WEEK:
            OperatingHours.objects.create(
                restaurant=restaurant,
                day=day_code,
                opening_time=time(11, 0),
                closing_time=time(23, 0),
                is_closed=False
            )
            
        # 5. Faz login automático e redireciona para o painel da loja
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return redirect('restaurant_admin', slug=restaurant.slug)
        
    return render(request, 'menu/merchant_register.html')

@login_required
def financial_dashboard(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, user=request.user)
    
    # === LÓGICA FINANCEIRA FICA TODA AQUI ===
    current_filter = request.GET.get('filter', 'all')
    now = timezone.now()
    completed_orders = restaurant.orders.filter(status='COMPLETED')
    
    if current_filter == 'today':
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        completed_orders = completed_orders.filter(created_at__gte=start_of_day)
    elif current_filter == '7days':
        start_of_week = now - timedelta(days=7)
        completed_orders = completed_orders.filter(created_at__gte=start_of_week)
    elif current_filter == 'month':
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_orders = completed_orders.filter(created_at__gte=start_of_month)

    total_orders_count = completed_orders.count()
    total_revenue = completed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    average_ticket = completed_orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0.00
    
    context = {
        'restaurant': restaurant,
        'current_filter': current_filter,
        'total_orders_count': total_orders_count,
        'total_revenue': total_revenue,
        'average_ticket': average_ticket,
    }
    return render(request, 'menu/financial_dashboard.html', context)

def check_new_orders(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug)
    last_time_str = request.GET.get('last_time')
    has_new = False
    
    if last_time_str:
        try:
            # Converte a string de volta para data
            last_time = datetime.fromisoformat(last_time_str)
            # Verifica se existe algum pedido criado DEPOIS dessa data
            has_new = Order.objects.filter(restaurant=restaurant, created_at__gt=last_time).exists()
        except ValueError:
            pass
            
    return JsonResponse({'has_new_orders': has_new})

from datetime import timedelta
from django.utils import timezone

def criar_pagamento_mensalidade(request, restaurant_id):
    # Procura o restaurante pelo ID
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    # Identifica qual plano o lojista escolheu através do link (?plano=teste, ?plano=plus, ou ?plano=premium)
    tipo_plano = request.GET.get('plano', 'plus') # 'plus' é o valor padrão se não vier nada
    
    # --- SIMULAÇÃO INSTANTÂNEA PARA O PLANO TESTE ---
    if tipo_plano == 'teste':
        restaurant.subscription_status = 'ACTIVE'
        restaurant.plan = 'BASIC' # Ou o plano correspondente ao teste
        restaurant.monthly_fee = 1.00
        # Define a nova data de vencimento para daqui a 30 dias a contar de hoje
        restaurant.due_date = timezone.now().date() + timedelta(days=30)
        restaurant.save()
        
        # Redireciona de volta para o admin do cardápio com o painel já atualizado
        return redirect('restaurant_admin', slug=restaurant.slug)
    # -----------------------------------------------

    # Se não for o plano de teste, continua o fluxo normal do Mercado Pago para Plus / Premium:
    if tipo_plano == 'premium':
        titulo = f"Mensalidade Plano Premium - {restaurant.name}"
        valor = 79.90
    else:
        titulo = f"Mensalidade Plano Plus - {restaurant.name}"
        valor = 39.90

    # Inicia o Mercado Pago usando a chave do teu ficheiro .env
    mp_token = os.environ.get('MP_ACCESS_TOKEN')
    sdk = mercadopago.SDK(mp_token)
    
    # Cria o "boleto/Pix" digital com o valor dinâmico do plano escolhido
    preference_data = {
        "items": [
            {
                "title": titulo,
                "quantity": 1,
                "unit_price": float(valor)
            }
        ],
        "back_urls": {
            "success": "https://www.google.com",
            "failure": "https://www.google.com",
            "pending": "https://www.google.com",
        },
        "auto_return": "approved"
    }

    result = sdk.preference().create(preference_data)
    preference = result.get("response")
    
    print("RESPOSTA MERCADO PAGO:", result) 
    
    if preference and 'id' in preference:
        sub, created = Subscription.objects.get_or_create(restaurant=restaurant)
        sub.mercadopago_preference_id = preference['id']
        sub.save()
        
        url_pagamento = preference.get('init_point') or preference.get('sandbox_init_point')
        return redirect(url_pagamento)
    else:
        print("FALHA AO CRIAR PREFERÊNCIA. Verifique o token ou os dados enviados.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
@csrf_exempt
def mercadopago_webhook(request):
    if request.method == 'POST':
        try:
            # Lê os dados que o Mercado Pago enviou
            data = json.loads(request.body)
            print("WEBHOOK RECEBIDO DO MERCADO PAGO:", data)
            
            # Aqui vamos colocar a lógica para ler o ID do pagamento 
            # e atualizar a Subscription para 'ACTIVE' na base de dados
            
            # Respondemos sempre com status 200 para o Mercado Pago saber que recebemos
            return JsonResponse({'status': 'sucesso'}, status=200)
            
        except Exception as e:
            return JsonResponse({'erro': str(e)}, status=400)
            
    return JsonResponse({'erro': 'Método inválido'}, status=405)