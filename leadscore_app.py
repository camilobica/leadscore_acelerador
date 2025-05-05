# === Imports Padrões ===
import os
import joblib
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread

from cycler import cycler
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import service_account
from gspread_dataframe import get_as_dataframe
from pathlib import Path

# === Imports dos módulos internos ===
from notebooks.src.leadscore_plot_app import (
    plot_comparativo_leads_alunos,
    plot_histograma_leadscore,
    plot_stacked_100_percent,
    plot_entrada_leads,
    plot_utm_source_por_faixa
)
from notebooks.src.leadscore_tabelas import (
    gerar_tabela_faixas_leads_alunos,
    destacar_total_linha,
    top1_utms_por_leads_A,
    analisar_utms,
    gerar_tabela_estatisticas_leadscore,
    detalhar_leadscore_por_variavel,
    gerar_comparativo_faixas,
    mostrar_lift_e_calculo_individual,
    exibir_tabela_faixa_origem
)

# === Configuração Inicial do Streamlit ===
st.set_page_config(page_title="Leadscore Acelerador", layout="wide")

# === Carregar variáveis de ambiente ===
load_dotenv()

# === Autenticação Google Sheets via Secrets (sem .json físico) ===
import json

scopes = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=scopes
)
client = gspread.authorize(creds)

# === Função para carregar aba da planilha ===
def carregar_aba(sheet_id, aba_nome="Dados"):
    planilha = client.open_by_key(sheet_id)
    aba = planilha.worksheet(aba_nome)
    dados = aba.get_all_records()
    return pd.DataFrame(dados)

# === IDs das planilhas (fixos) ===
id_leadscore_implementado = "1otpSf30y2iqykxNNiCmN3DjxVDTuHSVZhOpzwi8UBBc"  
id_leadscore_implementado_alunos = "15RQf1wkiafPZftolCIAwcTFE7rv0_zRTB0zDOCkdPRs"
id_invest_trafego = "1477LAemTkMN1YTFdRJkLMaDLPZEiJ3vvtqwduemHXD4"

# === Carregar Dados diretamente do Google Sheets ===
try:
    df_leads = carregar_aba(id_leadscore_implementado)
    df_alunos = carregar_aba(id_leadscore_implementado_alunos)
    df_invest_trafego = carregar_aba(id_invest_trafego)
    df_leads['data'] = pd.to_datetime(df_leads['data'], errors='coerce')

    df_leads_antigos = df_leads[df_leads["lancamentos"] == "SSP-L12"]
    df_leads_novos = df_leads[df_leads["lancamentos"] == "SSP-L13"]
    
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# === Carregar Configurações salvas ===
path_modelos = Path("modelos")
limites = joblib.load(path_modelos / "limites_faixa.pkl")
score_map = joblib.load(path_modelos / "score_map.pkl")
tabelas_lift = joblib.load(path_modelos / "tabelas_lift.pkl")

# === Paleta de cores ===
cores = plt.get_cmap('Accent').colors
ciclo_cores = cycler('color', cores)
plt.rc('axes', prop_cycle=ciclo_cores)

# === Adicionar o horário de atualização do painel ===
from datetime import datetime

try:
    with open("ultima_atualizacao.txt", "r") as f:
        texto = f.read().strip()
        dt = datetime.strptime(texto, "%Y-%m-%d %H:%M:%S")
        data_atualizacao_formatada = dt.strftime("%d/%m/%Y %H:%M")
except Exception as e:
    data_atualizacao_formatada = "Desconhecida"
    st.error(f"[ERRO ao ler data de atualização]: {e}")

# === Interface ===
aba1, aba2 = st.tabs(["📈 Leadscore Acelerador", "🧮 Como Calculamos o Leadscore"])

# === Aba 1: Lançamentos Anteriores ===
with aba1:
    st.title("📈 Leadscore Acelerador")
    st.markdown(f"**Última atualização:** {data_atualizacao_formatada}")

    # Layout compacto: cada filtro ocupa 1/5 da largura
    col_lancamento, col_data, _ = st.columns([1, 1, 3])
    
    with col_lancamento:
        ordem_personalizada = ["SSP-L12", "SSP-L13"]
        lancamentos_unicos = df_leads["lancamentos"].dropna().unique()
        
        # Filtra apenas os que existem no DataFrame e estão na ordem desejada
        lancamentos_ordenados = [l for l in ordem_personalizada if l in lancamentos_unicos]
        lancamentos_todos = lancamentos_ordenados

        filtro_lancamento = st.selectbox(
            "Selecione o Lançamento para filtrar:",
            options=lancamentos_todos,
            index=lancamentos_todos.index("SSP-L13") if "SSP-L13" in lancamentos_todos else 0
        )
    
    # Filtrar dados antes de calcular datas mínimas e máximas
    df_filtrado = df_leads.copy()
    if filtro_lancamento != "Todos":
        df_filtrado = df_filtrado[df_filtrado["lancamentos"] == filtro_lancamento]
    
    # calcular datas do lançamento filtrado
    data_min = df_filtrado['data'].min().date()
    data_max = df_filtrado['data'].max().date()
    
    with col_data:
        intervalo_datas = st.date_input(
            "Selecione o intervalo de datas:",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max,
            format="DD/MM/YYYY"
        )
    
    # Agora sim aplica o filtro final de datas
    if isinstance(intervalo_datas, tuple) and len(intervalo_datas) == 2:
        data_inicio, data_fim = intervalo_datas
        df_filtrado = df_filtrado[
            (df_filtrado['data'].dt.date >= data_inicio) &
            (df_filtrado['data'].dt.date <= data_fim)
        ]

    df_alunos_filtrado = df_alunos.copy()
    if filtro_lancamento != "Todos":
        df_alunos_filtrado = df_alunos_filtrado[df_alunos_filtrado["lancamentos"] == filtro_lancamento]

    if 'data_inscricao' in df_alunos_filtrado.columns:
        df_alunos_filtrado['data'] = pd.to_datetime(df_alunos_filtrado['data'], errors='coerce')
        df_alunos_filtrado = df_alunos_filtrado[
            (df_alunos_filtrado['data'].dt.date >= df_filtrado['data'].min().date()) &
            (df_alunos_filtrado['data'].dt.date <= df_filtrado['data'].max().date())
        ]

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum lead encontrado para os filtros selecionados. Tente mudar os filtros.")
        st.stop()

    st.markdown("---")
    df_filtrado = plot_entrada_leads(df_filtrado)

    st.markdown("---")
    exibir_tabela_faixa_origem(df_filtrado, df_leads, df_alunos)

    st.markdown("---")
    st.subheader("Análise Detalhada de Conversão - UTM's")
    plot_utm_source_por_faixa(df_filtrado)
    analisar_utms(df_filtrado)


# === Aba 2: Como Calculamos ===
with aba2:
    st.title("🧮 Como Calculamos o Leadscore")
    st.markdown(f"**Última atualização:** {data_atualizacao_formatada}")

    st.markdown("""
    O Leadscore foi desenvolvido a partir de variáveis importantes que se correlacionam com a decisão de compra:
    
    - **Renda**
    - **Escolaridade**
    - **Idade**
    - **Nível**
    - **Situação Profissional**

    A partir dessas variáveis, foi criado um `score ponderado` e os leads foram classificados em faixas **A, B, C, D** de acordo com o potencial de conversão.
    """)

    st.markdown("---")
    st.markdown("### Como funcionam os limites de score")

    if "leadscore_mapeado" not in df_leads.columns:
        st.warning("Leadscore ainda não calculado. Execute o cálculo de Leadscore primeiro.")
    else:
        col1, col2 = st.columns([0.7, 1.3])

        with col1:
            st.markdown("""
            **A média foi o ponto de partida para definir as faixas:**
            """)
            media_score = limites["media_compradores"]

            st.markdown(
                f"""
                <div style='background-color: #fff3cd; color: #000; display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 16px; line-height: 1.2;'>
                    Média Geral do Score: {media_score:.2f}
                </div>
                """,
                unsafe_allow_html=True
            )
            st.write("")
            st.markdown(f"🔹 **Faixa A** (≥ 110% da média): {limites['limite_a']:.2f}")
            st.markdown(f"🔹 **Faixa B** (≥  90% da média): {limites['limite_b']:.2f}")
            st.markdown(f"🔹 **Faixa C** (≥  70% da média): {limites['limite_c']:.2f}")
            st.markdown(f"🔹 **Faixa D** (≥  50% da média): {limites['limite_d']:.2f}")

            gerar_tabela_estatisticas_leadscore(df_leads)

        with col2:
            fig = plot_histograma_leadscore(
                df_leads,
                limite_a=limites["limite_a"],
                limite_b=limites["limite_b"],
                limite_c=limites["limite_c"],
                limite_d=limites["limite_d"]
            )
            st.pyplot(fig)

    st.markdown("---")
    st.markdown("### Comparativo das Faixas entre Leads x Alunos")

    plot_comparativo_leads_alunos(df_leads, df_alunos)
    
    st.markdown("---")
    st.markdown("### Análise do Lift (peso) por Variável")
    st.markdown("""
    O `Lift` é obtido dividindo a **porcentagem de alunos** pela **porcentagem de leads** em cada categoria. Já o `Score Final` é o resultado do `Lift` multiplicado pelo número absoluto de alunos na categoria.
    """)
    st.write("")
        
    mostrar_lift_e_calculo_individual(tabelas_lift, df_leads, score_map, limites)
    
    st.markdown("---")
    st.markdown("### Distribuição Percentual das Categorias por Faixa de Leadscore")
    st.markdown("**Aqui podemos ver como as respostas dos alunos se distribuem proporcionalmente em cada faixa de score de acordo com a categoria. Isso permite visualizar, por exemplo, quais características são mais comuns entre os alunos com score mais alto (Faixa A) ou mais baixo (Faixa D).**")

    variavel_selecionada = st.selectbox(
        "Selecione a variável para análise:",
        options=["renda", "escolaridade", "idade", "nível", "situação profissional"],
        key="seletor_plot"
    )
    
    plot_stacked_100_percent(df_leads, variavel_selecionada)

    gerar_comparativo_faixas(df_leads)