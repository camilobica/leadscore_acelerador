import os
from dotenv import load_dotenv
import requests
import pandas as pd

# === CARREGAR VARIÁVEIS DO .env ===
load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# === FUNÇÃO PARA OBTER O TOKEN ===
def obter_token(client_id, client_secret):
    url = "https://api-sec.hotmart.com/security/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()["access_token"]

# === FUNÇÃO PARA OBTER VENDAS ===
def obter_vendas(token, pagina=1):
    url = f"https://api-sec.hotmart.com/v1/sales?page={pagina}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# === FUNÇÃO PARA CONVERTER DADOS EM DATAFRAME ===
def vendas_para_dataframe(dados):
    if 'items' in dados:
        return pd.json_normalize(dados['items'])
    return pd.DataFrame()

# === EXECUÇÃO ===
try:
    token = obter_token(CLIENT_ID, CLIENT_SECRET)
    dados_vendas = obter_vendas(token, pagina=1)
    df_vendas = vendas_para_dataframe(dados_vendas)

    # Visualiza os dados
    print(df_vendas.head())

    # Exporta para CSV
    df_vendas.to_csv("vendas_hotmart.csv", index=False)
    print("Arquivo 'vendas_hotmart.csv' salvo com sucesso!")

except requests.HTTPError as e:
    print("Erro na requisição HTTP:", e)
except Exception as e:
    print("Erro geral:", e)
