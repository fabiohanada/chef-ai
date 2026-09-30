from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # 1. Adiciona esta importação aqui

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 2. Adiciona esta linha para redirecionar a raiz "/" para "/login/"
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    
    # As tuas rotas que já lá estão:
    path('', include('accounts.urls')),
    path('', include('menu.urls')), 
]