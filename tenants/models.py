import uuid
from django.db import models
from django.contrib.auth.models import User

class Restaurant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='restaurants')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome do Restaurante', max_length=120)
    slug = models.SlugField('Slug / Subdomínio URL', unique=True, help_text='Ex: pizzaria-do-mario')
    whatsapp_number = models.CharField('WhatsApp para Pedidos', max_length=20, help_text='DDD + Número sem espaços')
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.CharField("Endereço", max_length=255, blank=True, null=True)
    city = models.CharField("Cidade", max_length=100, blank=True, null=True)
    state = models.CharField("Estado", max_length=2, blank=True, null=True)
    zip_code = models.CharField("CEP", max_length=9, blank=True, null=True)
    minimum_order_value = models.DecimalField("Pedido Mínimo", max_digits=6, decimal_places=2, default=0.00)

class OperatingHours(models.Model):
    DAYS_OF_WEEK = [
        ('0', 'Segunda-feira'),
        ('1', 'Terça-feira'),
        ('2', 'Quarta-feira'),
        ('3', 'Quinta-feira'),
        ('4', 'Sexta-feira'),
        ('5', 'Sábado'),
        ('6', 'Domingo'),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='hours')
    day = models.CharField("Dia da Semana", max_length=1, choices=DAYS_OF_WEEK)
    opening_time = models.TimeField("Abertura")
    closing_time = models.TimeField("Fechamento")
    is_closed = models.BooleanField("Fechado o dia todo", default=False)

class Meta:
    ordering = ['day', 'opening_time']


class PaymentMethod(models.Model):
    CATEGORIES = [
        ('ONLINE', 'Pagamento online'),
        ('DELIVERY', 'Pagamento na entrega'),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='payment_methods')
    name = models.CharField("Forma de Pagamento", max_length=50)  # Ex: Pix, Visa Crédito, Dinheiro
    category = models.CharField("Tipo", max_length=10, choices=CATEGORIES)
    is_active = models.BooleanField("Ativo na loja", default=True)

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"