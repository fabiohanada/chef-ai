from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redireciona a raiz "/" para "/login/"
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    
    # 1º LÊ O ACCOUNTS: Para o resto das rotas de autenticação (como /login/)
    path('', include('accounts.urls')),
    
    # 2º LÊ O MENU: Assim o nosso onboarding e a rota /cadastro/ assumem o controlo
        path('', include('menu.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)