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
    # Se já estiver logado, redireciona para a cozinha do restaurante dele
    if request.user.is_authenticated:
        restaurant = Restaurant.objects.filter(user=request.user).first()
        if restaurant:
            return redirect(f'/{restaurant.slug}/cozinha/')
        return redirect('/cadastro/')  # Redirecionamento padrão caso não tenha restaurante associado

    if request.method == 'POST':
        email_or_username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=email_or_username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login efetuado com sucesso!')
            
            # Procura o restaurante do utilizador logado
            restaurant = Restaurant.objects.filter(user=user).first()
            if restaurant:
                return redirect(f'/{restaurant.slug}/cozinha/')
            
            # Se for um superuser sem restaurante específico, pode redirecionar para um padrão
            return redirect('/restaurante-demo/cozinha/')
        else:
            messages.error(request, 'E-mail, chave ou senha inválidos.')

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
            user=user
        )

        # 6. Fazer login automático e redirecionar
        login(request, user)
        messages.success(request, f'Bem-vindo(a)! O restaurante {restaurant.name} foi criado com sucesso.')
        
        return redirect(f'/{restaurant.slug}/cozinha/')

    return render(request, 'accounts/register.html')