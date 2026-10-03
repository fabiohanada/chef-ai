from django import forms
from .models import Category, Product

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500', 'placeholder': 'Ex: Hambúrgueres, Bebidas, Sobremesas'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500', 'placeholder': 'Ex: X-Bacon Artesanal'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500', 'rows': 3, 'placeholder': 'Descreva os ingredientes...'}),
            'price': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500', 'placeholder': '0.00'}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded'}),
        }