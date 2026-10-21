import uuid
from django.db import models
from tenants.models import Restaurant

class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField('Nome da Categoria', max_length=100)
    order = models.PositiveIntegerField('Ordem de Exibição', default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

class Product(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField('Nome do Produto', max_length=150)
    description = models.TextField('Descrição', blank=True)
    price = models.DecimalField('Preço (R$)', max_digits=10, decimal_places=2)
    image_url = models.URLField('URL da Imagem', blank=True, null=True)
    is_available = models.BooleanField('Disponível', default=True)
    image = models.ImageField("Foto do Produto", upload_to='product_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} (R$ {self.price})"

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('PREPARING', 'Em Preparo'),
        ('DISPATCHED', 'Saiu para Entrega'),
        ('COMPLETED', 'Concluído'),
        ('CANCELED', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.PositiveIntegerField('Número do Pedido', blank=True, null=True) # <--- NOVO CAMPO
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    customer_name = models.CharField('Nome do Cliente', max_length=100)
    customer_phone = models.CharField('WhatsApp do Cliente', max_length=20, blank=True)
    address = models.TextField('Endereço de Entrega')
    payment_method = models.CharField('Forma de Pagamento', max_length=50, default='PIX')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField('Total (R$)', max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Lógica para gerar o número sequencial do pedido por restaurante (#1, #2, #3...)
        if not self.order_number:
            last_order = Order.objects.filter(restaurant=self.restaurant).order_by('-order_number').first()
            if last_order and last_order.order_number:
                self.order_number = last_order.order_number + 1
            else:
                self.order_number = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido #{self.order_number} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    unit_price = models.DecimalField('Preço Unitário (R$)', max_digits=10, decimal_places=2)

    def get_subtotal(self):
        return self.quantity * self.unit_price

class DeliveryFee(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='delivery_fees')
    neighborhood = models.CharField('Bairro', max_length=100)
    fee = models.DecimalField('Taxa de Entrega (R$)', max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = 'Taxa de Entrega'
        verbose_name_plural = 'Taxas de Entrega'

    def __str__(self):
        return f"{self.neighborhood} - R$ {self.fee}"
    
class Subscription(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('ACTIVE', 'Ativa'),
        ('CANCELED', 'Cancelada'),
    ]

    # Alterado para apontar diretamente para a classe Restaurant (com R maiúsculo)
    restaurant = models.OneToOneField(Restaurant, on_delete=models.CASCADE, related_name='subscription')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    mercadopago_preference_id = models.CharField(max_length=255, blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Assinatura de {self.restaurant.name} - {self.status}"