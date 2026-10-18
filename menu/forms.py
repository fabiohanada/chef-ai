from django import forms
from .models import Category, Product

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'border rounded-lg p-2.5 text-sm w-full outline-none focus:ring-2 focus:ring-red-500', 'placeholder': 'Nome da Categoria (ex: Sobremesas)'})
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'border rounded-lg p-2.5 text-sm w-full outline-none focus:ring-2 focus:ring-red-500'}),
            'description': forms.Textarea(attrs={'class': 'border rounded-lg p-2.5 text-sm w-full outline-none focus:ring-2 focus:ring-red-500', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'border rounded-lg p-2.5 text-sm w-full outline-none focus:ring-2 focus:ring-red-500', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'border rounded-lg p-2.5 text-sm w-full bg-white'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-red-600 rounded border-gray-300 focus:ring-red-500'}),
        }