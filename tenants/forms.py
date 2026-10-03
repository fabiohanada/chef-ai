from django import forms
from .models import Restaurant

class RestaurantProfileForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        # 1. Adicionamos o 'logo' aqui na lista:
        fields = ['name', 'logo', 'address', 'city', 'state', 'zip_code', 'minimum_order_value']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500'}),
            # 2. Adicionamos o estilo do campo de upload de ficheiro:
            'logo': forms.ClearableFileInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none'}),
            'address': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500', 'placeholder': 'Ex: Rua das Flores, 123'}),
            'city': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500'}),
            'state': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500', 'placeholder': 'SP'}),
            'zip_code': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500', 'placeholder': '00000-000'}),
            'minimum_order_value': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500'}),
        }