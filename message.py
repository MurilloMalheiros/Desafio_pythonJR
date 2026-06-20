# message.py
import os
import sys
import requests
from dotenv import load_dotenv
from connection import get_supabase_client

# Garante que a saída no terminal use UTF-8 para evitar UnicodeEncodeError no Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Carrega as variáveis de ambiente
load_dotenv()

ZAPI_INSTANCE = os.environ.get("ZAPI_INSTANCE")
ZAPI_TOKEN = os.environ.get("ZAPI_TOKEN")
ZAPI_CLIENT_TOKEN = os.environ.get("ZAPI_CLIENT_TOKEN")

def enviar_mensagens_clientes():
    # 1. Importa e inicializa a conexão com o banco
    db = get_supabase_client()
    
    # 2. Busca os clientes no Supabase
    response = db.table('cliente').select("*").execute()
    clientes = response.data

    if not clientes:
        print("Nenhum cliente encontrado na tabela.")
        return

    # 3. Configura o endpoint padrão da Z-API para envio de texto
    url_zapi = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    
    headers = {
        "Client-Token": ZAPI_CLIENT_TOKEN,
        "Content-Type": "application/json"
    }

    print(f"Iniciando envio para {len(clientes)} clientes...\n")
    print("-" * 30)

    # 4. Itera sobre cada cliente e envia a mensagem
    for cliente in clientes:
        nome = cliente.get("name")
        telefone = cliente.get("telefone") # Mude aqui se a coluna no banco tiver outro nome

        if not telefone:
            print(f"⚠️ O cliente {nome} não tem um telefone cadastrado. Pulando...")
            continue

        # Monta a mensagem personalizada
        mensagem = f"Olá, {nome}! Tudo bem com você?"

        # Payload exigido pela documentação da Z-API
        payload = {
            "phone": telefone, 
            "message": mensagem
        }

        # 5. Faz a requisição (disparo)
        try:
            resposta = requests.post(url_zapi, headers=headers, json=payload)
            
            # Log detalhado da resposta (arquivo + console)
            log_entry = (
                f"CLIENTE={nome} PHONE={telefone} STATUS={resposta.status_code} RESPONSE={resposta.text}\n"
            )
            try:
                with open('zapi_debug.log', 'a', encoding='utf-8') as f:
                    f.write(log_entry)
            except Exception:
                pass

            # Verifica se o disparo foi aceito pela API
            if resposta.status_code == 200:
                print(f"✅ Enviado com sucesso para: {nome} ({telefone})")
                print('DEBUG-ZAPI:', resposta.text)
            else:
                print(f"❌ Erro ao enviar para {nome}. Detalhes: {resposta.text}")
                print('DEBUG-ZAPI:', resposta.status_code, resposta.text)
                
        except Exception as e:
            print(f"❌ Erro de rede ao tentar enviar para {nome}: {e}")
            try:
                with open('zapi_debug.log', 'a', encoding='utf-8') as f:
                    f.write(f"CLIENTE={nome} PHONE={telefone} EXCEPTION={e}\n")
            except Exception:
                pass


def debug_query():
    """Função de debug: apenas consulta a tabela 'cliente' e mostra resposta/detalhes."""
    db = get_supabase_client()
    response = db.table('cliente').select("*").execute()
    print('DEBUG: response repr ->', repr(response))
    try:
        print('DEBUG: data ->', response.data)
        print('DEBUG: error ->', getattr(response, 'error', None))
        print('DEBUG: count ->', getattr(response, 'count', None))
    except Exception as e:
        print('DEBUG: erro ao acessar atributos do response:', e)
    return response

if __name__ == "__main__":
    # Para rodar em modo debug sem enviar mensagens, exporte DEBUG_SUPABASE=1
    if os.environ.get('DEBUG_SUPABASE') == '1':
        debug_query()
    else:
        enviar_mensagens_clientes()