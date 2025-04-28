# estrutura_projeto.py
# Esqueleto profissional para seu projeto de leadscore VHE

from pathlib import Path
import sys

# === CONFIGURAR CAMINHO PARA src ===
SRC_PATH = Path(__file__).resolve().parent / "notebooks" / "src"
sys.path.append(str(SRC_PATH))

# === IMPORTS PADRÕES ===
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from cycler import cycler
from datetime import datetime
from io import BytesIO

# === IMPORTS DO MÓDULO src ===
from leadscore_profile import gerar_leadscore_profile, calcular_pesos_por_variavel
from leadscore_plot import plot_distribuicao_barra, plot_histograma_leadscore_alunos
from freq_variavel import gerar_freq_variavel
from score_map import gerar_score_map
from leadscore_final import (
    calcular_leadscore_total,
    detalhar_score_por_variavel,
    calcular_score_total_ponderado
)

# Paleta de cores
cores = plt.get_cmap('Accent').colors
ciclo_cores = cycler('color', cores)
plt.rc('axes', prop_cycle=ciclo_cores)

# === CARREGAR ARQUIVO ===
caminho_csv = Path("dados/pesquisa_alunos_leadscore.csv")
try:
    df = pd.read_csv(caminho_csv)
except FileNotFoundError:
    st.error(f"Arquivo não encontrado: {caminho_csv}")
    st.stop()

# === CONFIGURAÇÃO DO GRÁFICO ===
def plot_distribuicao_barra(df):
    """
    Plota a distribuição percentual de faixas de leadscore.
    """
    distrib = df["leadscore_faixa"].value_counts(normalize=True).sort_index() * 100

    plt.figure(figsize=(8, 5))
    ax = sns.barplot(x=distrib.index, y=distrib.values, color=cores[0])

    for i, val in enumerate(distrib.values):
        ax.text(i, val + 1, f"{val:.1f}%", ha='center', fontsize=10)

    plt.ylim(0, distrib.max() + 10)
    plt.title("Distribuição (%) Faixas de Leadscore")
    plt.ylabel("")
    plt.yticks([])
    plt.xlabel("")
    plt.tick_params(axis='x', length=0)

    for spine in ["top", "right", "left", "bottom"]:
        plt.gca().spines[spine].set_visible(False)

    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.clf()  # limpa o gráfico para evitar sobreposição

# === CONFIGURAÇÃO PÁGINA ===
st.set_page_config(page_title="Leadscore Alunos", layout="wide")

# === PARTE 1: RESUMO DOS LIMITES E DISTRIBUIÇÃO ===
left, center, right = st.columns([0.1, 0.8, 0.1])
with center:
    st.title("📊 Leadscore Alunos - Portal VHE")
    st.markdown(f"**Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    st.markdown("### Classificação dos Alunos por Faixa")
    
    media_compradores = df["leadscore_total"].mean()
    limite_a = media_compradores * 1.10
    limite_b = media_compradores * 0.90
    limite_c = media_compradores * 0.70
    limite_d = media_compradores * 0.50
    
    def classificar_faixa_por_media(score):
        if score >= limite_a:
            return "A"
        elif score >= limite_b:
            return "B"
        elif score >= limite_c:
            return "C"
        else:
            return "D"
    
    if "leadscore_total" in df.columns:
        df["leadscore_faixa"] = df["leadscore_total"].apply(classificar_faixa_por_media)
        dist_faixa = df["leadscore_faixa"].value_counts().sort_index()
    
        resumo_df = pd.DataFrame({
            "faixa": dist_faixa.index,
            "quantidade de alunos em cada faixa": dist_faixa.values
        })
        
        # Adiciona a linha "Total"
        total = resumo_df["quantidade de alunos em cada faixa"].sum()
        resumo_df.loc[len(resumo_df.index)] = ["Total de Alunos", total]

        col1, col2 = st.columns([1, 1.3])
    
        with col1:
            st.dataframe(resumo_df, use_container_width=True, hide_index=True)
            st.markdown("**As faixas de leadscore foram definidas com base na média dos scores dos alunos, criando limites proporcionais (110%, 90%, 70% e 50%) para classificar os perfis em (A, B, C e D).**")
            st.markdown(
                f"""
                <span style='background-color: #fff3cd; color: #000; padding: 4px 8px; border-radius: 4px; font-weight: bold;'>
                    Média Score: {round(media_compradores)}
                </span><br><br>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"Limite A (>= 110%): {round(limite_a)}")
            st.markdown(f"Limite B (>=  90%): {round(limite_b)}")
            st.markdown(f"Limite C (>=  70%): {round(limite_c)}")
            st.markdown(f"Limite D (>=  50%): {round(limite_d)}")
    
        with col2:
            if "leadscore_faixa" in df.columns:
                plot_distribuicao_barra(df)
            else:
                st.warning("Coluna 'leadscore_faixa' ausente no CSV.")


# === PARTE 2: DETALHAMENTO POR ALUNO + TABELA DE PESOS ===
left, center, right = st.columns([0.1, 0.8, 0.1])
with center:
    st.markdown("---")
    st.markdown("### Análise do Modelo Implementado")
    st.markdown("**O leadscore de cada aluno é obtido a partir da multiplicação entre o valor base da resposta `score_base` e o `peso` atribuído à variável. O somatório dos valores ponderados de todas as variáveis resulta no `score_final` do aluno.**")
    
    pesos_manualmente_definidos = {
        "renda_media": {
            "Não tenho renda.": 0,
            "Até 1.500": 1,
            "De 1.500 a 2.500": 2,
            "De 2.500 a 5.000": 4,
            "Mais de 10.000": 7,
            "De 5.000 a 10.000": 10
        },
        "escolaridade_categoria": {
            "Fundamental completo": 0,
            "Médio incompleto": 1,
            "Médio completo": 2,
            "Superior incompleto": 4,
            "Superior completo": 7,
            "Pós-graduação completa": 10
        }
    }
    
    cols_to_analyze = [
        "genero", "faixa_etaria", "escolaridade_categoria", "renda_media",
        "tempo_antes_portal", "nivel_idioma", "motivo_fluencia_espanhol_categoria"
    ]
    
    leadscore_df = gerar_leadscore_profile(
        df,
        colunas=cols_to_analyze,
        pesos_manualmente_definidos=pesos_manualmente_definidos
    )
    leadscore_df = pd.concat([leadscore_df], axis=0)
    
    peso_variavel = calcular_pesos_por_variavel(leadscore_df)
    peso_variavel["renda_media"] = 2.0
    peso_variavel["escolaridade_categoria"] = 2.0
    
    df_pesos = pd.DataFrame.from_dict(peso_variavel, orient="index", columns=["peso_calculado"]).reset_index()
    df_pesos = df_pesos.rename(columns={"index": "variavel"}).sort_values(by="peso_calculado", ascending=False)
   
    col1, col2 = st.columns([1.5, 0.5])

    with col1:    
        score_map = gerar_score_map(leadscore_df, df)
        df["leadscore_total"] = calcular_leadscore_total(df, score_map, peso_variavel)
    
        indice = st.number_input("**Selecione o ID do aluno para ver o seu Leadscore**", min_value=0, max_value=len(df)-1, value=0, step=1)
        detalhes = detalhar_score_por_variavel(df, indice, score_map, peso_variavel)
                
        st.dataframe(detalhes, use_container_width=True, hide_index=True)
        
        score_calc = detalhes["score_final"].sum()
        score_base = df.loc[indice, "leadscore_total"]
        
        st.markdown(
            f"""
            <span style='background-color: #fff3cd; color: #000; padding: 4px 8px; border-radius: 4px; font-weight: bold;'>
                Score Total Calculado: {int(score_calc)}
            </span>
            """,
            unsafe_allow_html=True
        )

    
    with col2:
        st.markdown("\n")
        st.markdown("\n")
        st.markdown("\n**Pesos das Variáveis**")
        st.dataframe(df_pesos, use_container_width=True, hide_index=True)


# === PARTE 3: EXIBIR HISTOGRAMA DO LEADSCORE TOTAL ===
left, center, right = st.columns([0.1, 0.8, 0.1])
with center:
    st.markdown("---")
    st.markdown("### Distribuição do Leadscore Total")
    st.markdown("**Visualize a concentração dos scores totais e os limites de classificação.**")

left, center, right = st.columns([0.4, 0.8, 0.4])
with center:
    fig = plot_histograma_leadscore_alunos(df, limite_a, limite_b, limite_c, limite_d)
    st.pyplot(fig)



# === PARTE 4: DISTRIBUIÇÃO PERCENTUAL ENTRE FAIXA E VARIÁVEL ===
left, center, right = st.columns([0.1, 0.8, 0.1])
with center:
    st.markdown("---")
    st.markdown("### Distribuição Percentual das Categorias por Faixa de Leadscore")
    st.markdown("**Aqui podemos ver como as respostas dos alunos se distribuem proporcionalmente em cada faixa de score de acordo com a categoria. Isso permite visualizar, por exemplo, quais características são mais comuns entre os alunos com score mais alto (Faixa A) ou mais baixo (Faixa D).**")
    
    resumo_faixas = []
    
    for var in cols_to_analyze:
        dist = pd.crosstab(
            df["leadscore_faixa"],
            df[var],
            normalize='index'
        ) * 100
    
        dist = dist.round(2)
    
        for faixa in dist.index:
            for categoria in dist.columns:
                resumo_faixas.append({
                    "faixa": faixa,
                    "variavel": var,
                    "categoria": categoria,
                    "percentual (%)": dist.loc[faixa, categoria]
                })
    
    df_resumo_faixas = pd.DataFrame(resumo_faixas)
    
    df_resumo_pivot = df_resumo_faixas.pivot_table(
        index=["variavel", "categoria"],
        columns="faixa",
        values="percentual (%)"
    ).reset_index()
    
    df_resumo_pivot = df_resumo_pivot[["variavel", "categoria", "A", "B", "C", "D"]]
    df_resumo_pivot = df_resumo_pivot.sort_values(by=["variavel", "A"], ascending=[True, False])
    
    st.dataframe(df_resumo_pivot, use_container_width=True, hide_index=True)


# === PARTE 5: COMPARAÇÃO ENTRE FAIXAS ===
left, center, right = st.columns([0.1, 0.8, 0.1])
with center:
    st.markdown("---")
    st.markdown("### Comparação entre Faixas de Leadscore")
    st.markdown("**Abaixo temos os destaques das principais diferenças percentuais entre duas faixas de leadscore. Para cada variável e categoria, é mostrada a proporção de alunos pertencentes a cada faixa (`faixa_origem` e `faixa_destino`), seguida pela diferença entre elas.**")
    
    # Função auxiliar
    def comparar_faixas(df, colunas, faixa1, faixa2):
        resultados = []
        for col in colunas:
            dist1 = df[df["leadscore_faixa"] == faixa1][col].value_counts(normalize=True) * 100
            dist2 = df[df["leadscore_faixa"] == faixa2][col].value_counts(normalize=True) * 100
            todas_categorias = set(dist1.index).union(dist2.index)
    
            for cat in todas_categorias:
                pct1 = dist1.get(cat, 0)
                pct2 = dist2.get(cat, 0)
                diff = round(pct1 - pct2, 2)
                resultados.append({
                    "faixa_origem": faixa1,
                    "faixa_destino": faixa2,
                    "variavel": col,
                    "categoria": cat,
                    f"% {faixa1}": round(pct1, 2),
                    f"% {faixa2}": round(pct2, 2),
                    f"diferença entre {faixa1} e {faixa2}": diff
                })
    
        return pd.DataFrame(resultados).sort_values(
            by=f"diferença entre {faixa1} e {faixa2}", key=abs, ascending=False
        )
    
    def colorir_diferenca(val):
        if val > 0:
            return "color: green"
        elif val < 0:
            return "color: red"
        else:
            return "color: gray"

    comparacao_ab = comparar_faixas(df, cols_to_analyze, "A", "B")
    comparacao_bc = comparar_faixas(df, cols_to_analyze, "B", "C")
    comparacao_cd = comparar_faixas(df, cols_to_analyze, "C", "D")
    
    st.markdown("🟢 **Diferenças entre Faixa A e B**")
    st.dataframe(
        comparacao_ab.head(15)
        .reset_index(drop=True)
        .style
        .format({
            "% A": "{:.1f}",
            "% B": "{:.1f}",
            "diferença entre A e B": "{:.2f}"
        })
        .applymap(colorir_diferenca, subset=["diferença entre A e B"]),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("🟡 **Diferenças entre Faixa B e C**")
    st.dataframe(
        comparacao_bc.head(15)
        .reset_index(drop=True)
        .style
        .format({
            "% B": "{:.1f}",
            "% C": "{:.1f}",
            "diferença entre B e C": "{:.2f}"
        })
        .applymap(colorir_diferenca, subset=["diferença entre B e C"]),
        use_container_width=True,
        hide_index=True
    )    
    
    st.markdown("🔴 **Diferenças entre Faixa C e D**")
    st.dataframe(
        comparacao_cd.head(15)
        .reset_index(drop=True)
        .style
        .format({
            "% C": "{:.1f}",
            "% D": "{:.1f}",
            "diferença entre C e D": "{:.2f}"
        })
        .applymap(colorir_diferenca, subset=["diferença entre C e D"]),
        use_container_width=True,
        hide_index=True
    )



# === PARTE FINAL: Download da Base Atual ===
left, center, right = st.columns([0.1, 0.8, 0.1])
with center:
    st.markdown("---")
    st.markdown("### 📥 Download da Base Atualizada (.xlsx)")
    
    # Criar um buffer em memória
    buffer = BytesIO()
    
    # Exportar o dataframe para Excel
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leadscore")
    
    # Posicionar o cursor no início
    buffer.seek(0)
    
    # Botão de download
    st.download_button(
        label="📥 Baixar arquivo Excel",
        data=buffer,
        file_name="pesquisa_alunos_leadscore.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
