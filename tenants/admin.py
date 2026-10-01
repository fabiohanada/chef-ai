from django.contrib import admin
from .models import Restaurant

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    # Define as colunas que você quer ver de cara no painel admin
    list_display = ('name', 'user', 'whatsapp_number', 'slug', 'is_active')
    
    # Adiciona uma barra de pesquisa
    search_fields = ('name', 'slug', 'whatsapp_number')
