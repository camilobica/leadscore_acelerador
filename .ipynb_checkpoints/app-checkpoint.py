import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import os

st.set_page_config(page_title="Lead Scoring Automático", layout="wide")
st.title("📊 Dashboard de Lead Scoring - Lançamento Automático")

# === Detectar caminho absoluto do projeto e do CSV
current_path = Path(__file__).resolve()
base_path = current_path.parent

# Procurar pela pasta 'dados' subindo na hierarquia
while not (base_path / "dados" / "leads_monitorados.csv").exists() and base_path != base_path.parent:
    base_path = base_path.parent

csv_path = base_path / "dados" / "leads_monitorados.csv"

if not csv_path.exists():
    st.error("❌ O arquivo 'leads_monitorados.csv' não foi encontrado em nenhuma pasta 'dados' acima.")
    st.info("Execute o script monitoramento_leads.py para gerar o arquivo.")
else:
    df = pd.read_csv(csv_path)
    data_modificacao = os.path.getmtime(csv_path)
    from datetime import datetime
    st.caption(f"📅 Última atualização: {datetime.fromtimestamp(data_modificacao).strftime('%d/%m/%Y %H:%M:%S')}")

    # ===== SIDEBAR - FILTROS =====
    st.sidebar.header("Filtros")

    lancamentos = df["lancamentos"].dropna().unique().tolist()
    lancamento_selecionado = st.sidebar.multiselect("Selecionar Lançamentos:", lancamentos, default=lancamentos)

    faixa_foco = st.sidebar.multiselect(
        "Filtrar por Faixa:",
        ["A", "B", "C", "D"],
        default=["A", "B", "C", "D"]
    )

    # Aplicar filtros
    df_filtrado = df[df["lancamentos"].isin(lancamento_selecionado)]
    df_filtrado = df_filtrado[df_filtrado["faixa_predita_por_regressao"].isin(faixa_foco)]

    # ===== COLUNAS PRINCIPAIS =====
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuição de Faixas Previstas")
        dist = df_filtrado["faixa_predita_por_regressao"].value_counts(normalize=True).sort_index() * 100
        fig, ax = plt.subplots()
        dist.plot(kind="bar", ax=ax)
        ax.set_ylabel("% de leads")
        ax.set_xlabel("Faixa")
        st.pyplot(fig)

    with col2:
        st.subheader("Score Estimado Médio por Lançamento")
        media_lancamento = df_filtrado.groupby("lancamentos")["leadscore_estimado_total"].mean().round(2)
        st.dataframe(media_lancamento)

    # ===== TABELA DE LEADS =====
    st.subheader("🧠 Leads Filtrados")
    st.dataframe(
        df_filtrado.sort_values(by="leadscore_estimado_total", ascending=False),
        use_container_width=True
    )

    # Botão para download
    st.download_button(
        "📥 Baixar leads filtrados",
        df_filtrado.to_csv(index=False).encode("utf-8"),
        "leads_filtrados.csv",
        "text/csv"
    )