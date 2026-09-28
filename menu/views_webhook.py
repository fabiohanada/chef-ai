import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from tenants.models import Restaurant
from .models import Order

# Token de verificação padrão para configuração do Webhook (Meta / Cloud API)
VERIFY_TOKEN = "chef_ai_webhook_token_123"

@csrf_exempt
def whatsapp_webhook(request, slug):
    restaurant = Restaurant.objects.filter(slug=slug, is_active=True).first()
    if not restaurant:
        return JsonResponse({'error': 'Restaurante não encontrado'}, status=404)

    # 1. Validação inicial do Webhook (GET)
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)
        return HttpResponse('Token de verificação inválido', status=403)

    # 2. Processamento das mensagens recebidas (POST)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8', errors='ignore'))
            
            # Extração de dados da mensagem recebida
            phone_number = data.get('phone') or data.get('from')
            customer_name_in_msg = data.get('name', 'Cliente')
            
            # Se vier no formato oficial da Meta Cloud API
            if not phone_number and 'entry' in data:
                try:
                    entry = data['entry'][0]
                    changes = entry['changes'][0]
                    value = changes['value']
                    messages = value.get('messages', [])
                    if messages:
                        phone_number = messages[0].get('from')
                        contacts = value.get('contacts', [])
                        if contacts:
                            customer_name_in_msg = contacts[0].get('profile', {}).get('name', 'Cliente')
                except (IndexError, KeyError):
                    pass

            if phone_number:
                # Limpar caracteres não numéricos do telefone
                clean_phone = ''.join(filter(str.isdigit, str(phone_number)))
                
                # Buscar o último pedido do cliente pelo número de WhatsApp (últimos 8 dígitos)
                last_order = Order.objects.filter(
                    restaurant=restaurant,
                    customer_phone__icontains=clean_phone[-8:]
                ).order_by('-created_at').first()

                # Construir o link do cardápio digital
                menu_url = f"http://{request.get_host()}/{restaurant.slug}/"

                # Montagem da mensagem automática de resposta (Réplica Anota AI)
                if last_order:
                    response_text = (
                        f"Olá, Bom dia {last_order.customer_name}! 👋\n\n"
                        f"Há quanto tempo! 👏 Bem-vindo(a) de volta ao nosso autoatendimento! 🤖 No que posso ajudar você hoje?\n\n"
                        f"🌟 *Da última vez que nos encontramos, você pediu:*\n\n"
                    )
                    for item in last_order.items.all():
                        response_text += f"• *{item.product.name if item.product else 'Item'}*\n"

                    response_text += (
                        f"\nSe quiser repetir esse pedido ou fazer um novo, é só clicar no link abaixo e **finalizar pelo cardápio digital** 🍽️:\n\n"
                        f"👉 {menu_url}"
                    )
                else:
                    response_text = (
                        f"Olá {customer_name_in_msg}, seja muito bem-vindo(a) ao *{restaurant.name}*! 🤖\n\n"
                        f"Nada melhor do que boas escolhas, né? Veja o nosso cardápio digital e faça o seu pedido rápido por aqui 👇:\n\n"
                        f"👉 {menu_url}"
                    )

                # Log de simulação no console do Django
                print("\n==================================================")
                print(f"📱 MENSAGEM RECEBIDA DE: {clean_phone}")
                print("--------------------------------------------------")
                print("🤖 RESPOSTA GERADA PELO BOT CHEF AI:")
                print(response_text)
                print("==================================================\n")

                return JsonResponse({
                    'status': 'success',
                    'phone': clean_phone,
                    'bot_response': response_text
                }, status=200)

            return JsonResponse({'status': 'EVENT_RECEIVED'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método não permitido'}, status=405)