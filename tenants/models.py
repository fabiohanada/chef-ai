import uuid
from django.db import models

class Restaurant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome do Restaurante', max_length=120)
    slug = models.SlugField('Slug / Subdomínio URL', unique=True, help_text='Ex: pizzaria-do-mario')
    whatsapp_number = models.CharField('WhatsApp para Pedidos', max_length=20, help_text='DDD + Número sem espaços')
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name