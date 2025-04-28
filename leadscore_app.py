# === Imports Padrões ===
import joblib
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from cycler import cycler
from pathlib import Path
from datetime import datetime

# === Imports dos módulos internos ===
from notebooks.src.leadscore_plot_app import (
    plot_comparativo_leads_alunos,
    plot_histograma_leadscore,
    plot_stacked_100_percent
)
from notebooks.src.leadscore_tabelas import (
    gerar_tabela_faixas_leads_alunos,
    destacar_total_linha,
    top1_utms_por_leads_A,
    analisar_utms,
    gerar_tabela_estatisticas_leadscore,
    detalhar_leadscore_por_variavel,
    gerar_comparativo_faixas,
    mostrar_lift_e_calculo_individual
)

# === Configuração Inicial ===
st.set_page_config(page_title="Leadscore Acelerador", layout="wide")

# === Caminho base ===
base_path = Path("dados")

# === Carregar Dados ===
try:
    df_leads = pd.read_csv(base_path / "leadscore_implementado.csv")
    df_invest_trafego = pd.read_csv(base_path / "invest_trafego.csv")
    
    # Garantir que tenham as mesmas colunas (no futuro)
    #colunas_ambas = list(set(df_leads_antigos.columns) | set(df_leads_novos.columns))
    #df_leads_antigos = df_leads_antigos.reindex(columns=colunas_ambas)
    #df_leads_novos = df_leads_novos.reindex(columns=colunas_ambas)

    # Unir os leads
    #df_leads = pd.concat([df_leads_antigos, df_leads_novos], ignore_index=True)

except FileNotFoundError:
    st.error("Erro ao carregar os dados. Verifique o caminho base.")
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

# === Interface ===
aba1, aba2 = st.tabs(["📈 Leadscore Acelerador", "🧮 Como Calculamos o Leadscore"])

# === Aba 1: Lançamentos Anteriores ===
with aba1:
    st.title("📈 Leadscore Acelerador")
    st.markdown(f"**Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    filtros_col1, filtros_col2, filtros_col5  = st.columns(3)
    filtros_col3, filtros_col4= st.columns(2)
    
    with filtros_col1:
        lancamentos = ["Todos"] + sorted(df_leads["lancamentos"].dropna().unique().tolist())
        filtro_lancamento = st.selectbox("Selecione o Lançamento:", lancamentos)
    with filtros_col2:
        utm_sources = ["Todos"] + sorted(df_leads["utm source"].dropna().unique().tolist())
        filtro_utm_source = st.selectbox("Selecione a UTM Source:", utm_sources)
    with filtros_col3:
        utm_campaigns = ["Todos"] + sorted(df_leads["utm campaign"].dropna().unique().tolist())
        filtro_utm_campaign = st.selectbox("Selecione a UTM Campaign:", utm_campaigns)
    with filtros_col4:
        utm_mediums = ["Todos"] + sorted(df_leads["utm medium"].dropna().unique().tolist())
        filtro_utm_medium = st.selectbox("Selecione a UTM Medium:", utm_mediums)
    with filtros_col5:
        utm_contents = ["Todos"] + sorted(df_leads["utm content"].dropna().unique().tolist())
        filtro_utm_content = st.selectbox("Selecione a UTM Content:", utm_contents)

    df_filtrado = df_leads.copy()
    if filtro_lancamento != "Todos":
        df_filtrado = df_filtrado[df_filtrado["lancamentos"] == filtro_lancamento]
    if filtro_utm_source != "Todos":
        df_filtrado = df_filtrado[df_filtrado["utm source"] == filtro_utm_source]
    if filtro_utm_campaign != "Todos":
        df_filtrado = df_filtrado[df_filtrado["utm campaign"] == filtro_utm_campaign]
    if filtro_utm_medium != "Todos":
        df_filtrado = df_filtrado[df_filtrado["utm medium"] == filtro_utm_medium]
    if filtro_utm_content != "Todos":
        df_filtrado = df_filtrado[df_filtrado["utm content"] == filtro_utm_content]

    df_alunos_filtrado = df_filtrado[df_filtrado["comprou"] == 1]

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum lead encontrado para os filtros selecionados. Tente mudar os filtros.")
        st.stop()
    
    if df_alunos_filtrado.empty:
        st.info("ℹ️ Nenhum aluno encontrado para este filtro. Mostrando apenas dados de leads.")

    
    st.markdown("---")
    col1, col2 = st.columns([0.5, 0.5])
    
    with col1:
        st.subheader("Distribuição de Leads e Alunos")
        tabela_faixas = gerar_tabela_faixas_leads_alunos(df_filtrado, df_alunos_filtrado)
        st.dataframe(destacar_total_linha(tabela_faixas), use_container_width=True, hide_index=True)

        st.subheader("UTM's que mais trouxeram Leads A")
        tops_utms = top1_utms_por_leads_A(df_filtrado)
        dados_top = []
        for coluna, df_ranking in tops_utms.items():
            if not df_ranking.empty:
                nome_coluna = coluna.replace("utm ", "").capitalize()
                utm_value = df_ranking.iloc[0, 0]
                total_a = df_ranking.iloc[0, 1]
                total_a_formatado = f"{total_a:,}".replace(",", ".")
                dados_top.append({"UTM's": nome_coluna, "Melhor Resultado": utm_value, "Total Leads A": total_a_formatado})
        df_top_utms = pd.DataFrame(dados_top)
        st.dataframe(df_top_utms, use_container_width=True, hide_index=True)

    with col2:
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        plot_comparativo_leads_alunos(df_filtrado, df_alunos_filtrado)

    st.markdown("---")
    st.subheader("Análises Detalhadas da Conversão UTM's")
    analisar_utms(df_filtrado, df_invest_trafego)

# === Aba 2: Como Calculamos ===
with aba2:
    st.title("🧮 Como Calculamos o Leadscore")
    st.markdown(f"**Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
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
            media_score = df_leads["leadscore_mapeado"].mean()
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
    st.markdown("## Análise do Lift (peso) por Variável")
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