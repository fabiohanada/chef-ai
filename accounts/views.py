from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from menu.models import Restaurant
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from menu.models import Restaurant  # Importa o modelo do Restaurante (ajusta o import se estiver em tenants.models)
from django.utils.text import slugify

def login_view(request):
    # Lógica para usuário que já está logado na sessão
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')
            
        restaurants = Restaurant.objects.filter(user=request.user)
        
        if restaurants.count() == 1:
            return redirect(f'/{restaurants.first().slug}/cozinha/')
        elif restaurants.count() > 1:
            # Se tem mais de 1 loja, manda para o Seletor
            return render(request, 'accounts/select_store.html', {'restaurants': restaurants})
        else:
            return redirect('/cadastro/') 

    if request.method == 'POST':
        email_or_username = request.POST.get('username')
        password = request.POST.get('password')

        # 🚀 NOVA LÓGICA: Se o texto tiver '@', é um e-mail! Vamos descobrir o username dele.
        if '@' in email_or_username:
            user_obj = User.objects.filter(email=email_or_username).first()
            if user_obj:
                email_or_username = user_obj.username  # Troca o e-mail pelo username real para o Django aceitar

        # Agora o Django faz a autenticação com o username correto
        user = authenticate(request, username=email_or_username, password=password)
        
        if user is not None:
            login(request, user)
            
            if user.is_superuser:
                return redirect('/admin/')
            
            restaurants = Restaurant.objects.filter(user=user)
            if restaurants.count() == 1:
                return redirect(f'/{restaurants.first().slug}/cozinha/')
            elif restaurants.count() > 1:
                return render(request, 'accounts/select_store.html', {'restaurants': restaurants})
            else:
                return redirect('/cadastro/')
        else:
            messages.error(request, 'E-mail, usuário ou senha inválidos.')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    # Se já estiver autenticado, redireciona para a cozinha
    if request.user.is_authenticated:
        restaurant = Restaurant.objects.filter(user=request.user).first()
        if restaurant:
            return redirect(f'/{restaurant.slug}/cozinha/')

    if request.method == 'POST':
        # 1. Obter os dados do formulário
        first_name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone') # Vamos usar depois, se tiveres campo no User/Restaurant
        restaurant_name = request.POST.get('restaurant_name')
        password = request.POST.get('password')
        
        # 2. Validar se o e-mail já existe
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já está cadastrado.')
            return render(request, 'accounts/register.html')

        # 3. Criar o Utilizador no Django
        user = User.objects.create_user(
            username=email,  # Usamos o email como username para facilitar o login
            email=email,
            password=password,
            first_name=first_name
        )

        # 4. Gerar o slug do restaurante (ex: "Pizza do Chef" -> "pizza-do-chef")
        base_slug = slugify(restaurant_name)
        slug = base_slug
        count = 1
        while Restaurant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{count}"
            count += 1

        # 5. Criar o Restaurante ligado ao Utilizador criado
        restaurant = Restaurant.objects.create(
            name=restaurant_name,
            slug=slug,
            user=user,
            whatsapp_number=phone
        )

        # 6. Fazer login automático e redirecionar
        login(request, user)
        messages.success(request, f'Bem-vindo(a)! O restaurante {restaurant.name} foi criado com sucesso.')
        
        return redirect(f'/{restaurant.slug}/cozinha/')

    return render(request, 'accounts/register.html')