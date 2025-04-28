from cycler import cycler
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# Definição das paletas de cores
cores = plt.get_cmap('tab20b').colors
ciclo_cores = cycler('color', cores)
plt.rc('axes', prop_cycle=ciclo_cores)

# Definição do layout dos gráficos
LIGHT_DARK_COLOR = '#262730' 

plt.rcParams['figure.facecolor'] = LIGHT_DARK_COLOR
plt.rcParams['axes.facecolor'] = LIGHT_DARK_COLOR

plt.rcParams['text.color'] = 'white'
plt.rcParams['axes.labelcolor'] = 'white'
plt.rcParams['xtick.color'] = 'white'
plt.rcParams['ytick.color'] = 'white'
plt.rcParams['axes.titlecolor'] = 'white'
plt.rcParams['legend.labelcolor'] = 'white'



def plot_comparativo_leads_alunos(df_leads, df_alunos):
    contagem_prevista = df_leads["leadscore_faixa"].value_counts(normalize=True).sort_index() * 100
    contagem_real = df_alunos["leadscore_faixa"].value_counts(normalize=True).sort_index() * 100

    comparativo_perc = pd.DataFrame({
        "Leads (%)": contagem_prevista,
        "Alunos (%)": contagem_real
    }).fillna(0).round(1)

    comparativo_perc["Variação (p.p.)"] = (
        comparativo_perc["Leads (%)"] - comparativo_perc["Alunos (%)"]
    ).round(1)

    plt.figure(figsize=(8, 5))
    labels = comparativo_perc.index
    x = np.arange(len(labels))
    width = 0.35

    bars1 = plt.bar(x - width/2, comparativo_perc["Leads (%)"], width, label="Leads (%)", color=cores[1])
    bars2 = plt.bar(x + width/2, comparativo_perc["Alunos (%)"], width, label="Alunos (%)", color=cores[4])

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, height + 1, f"{height:.1f}%", ha='center', va='bottom')

    plt.ylabel("")
    plt.title("Leads vs Alunos por Faixa", pad=20)
    plt.xticks(x, labels)
    plt.tick_params(axis='x', length=0)
    plt.yticks([])
    plt.legend()

    for spine in ["top", "right", "left", "bottom"]:
        plt.gca().spines[spine].set_visible(False)

    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.clf()
    

def plot_histograma_leadscore(df, limite_a, limite_b, limite_c, limite_d):
    bins_leadscore = np.histogram_bin_edges(df["leadscore_mapeado"], bins="sturges")
    bins_leadscore = np.round(bins_leadscore).astype(int)

    interval_labels = [f"{bins_leadscore[i]}–{bins_leadscore[i+1]}" for i in range(len(bins_leadscore) - 1)]
    bin_centers = (bins_leadscore[:-1] + bins_leadscore[1:]) / 2

    fig, ax = plt.subplots(figsize=(12, 5))  # <== cria fig corretamente
    sns.histplot(df["leadscore_mapeado"], bins=bins_leadscore, color=cores[1], ax=ax)

    ax.axvline(limite_a, color=cores[6], linestyle="--", label="Limite A")
    ax.axvline(limite_b, color=cores[18], linestyle="--", label="Limite B")
    ax.axvline(limite_c, color=cores[10], linestyle="--", label="Limite C")
    ax.axvline(limite_d, color=cores[14], linestyle="--", label="Limite D")

    ymax = ax.get_ylim()[1]
    ax.text(limite_a, ymax * 1.02, "Limite A >", color=cores[6], ha="center", fontsize=10)
    ax.text(limite_b, ymax * 1.02, "Limite B >", color=cores[18], ha="center", fontsize=10)
    ax.text(limite_c, ymax * 1.02, "Limite C >", color=cores[10], ha="center", fontsize=10)
    ax.text(limite_d, ymax * 1.02, "Limite D >", color=cores[14], ha="center", fontsize=10)

    ax.set_xticks(bin_centers)
    ax.set_xticklabels(interval_labels, rotation=30, ha="right")

    ax.set_title("Distribuição das Faixas no Leadscore", y=1.1)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_yticks([])

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.legend()
    plt.tight_layout()

    return fig  # <<< RETORNA fig

def plot_stacked_100_percent(df, variavel):
    if "leadscore_faixa" not in df.columns:
        st.error("leadscore_faixa não encontrado no DataFrame!")
        return

    # Calcula a distribuição
    dist = pd.crosstab(df[variavel], df["leadscore_faixa"], normalize='index') * 100
    dist = dist.fillna(0)

    # Paleta de cores local
    cores_local = plt.get_cmap('Accent').colors

    # Plot
    fig, ax = plt.subplots(figsize=(15, 5))
    bottom = pd.Series([0] * len(dist), index=dist.index)

    for i, faixa in enumerate(dist.columns):
        bars = ax.bar(dist.index, dist[faixa], label=faixa, bottom=bottom, color=cores_local[i])

        # Inserir os valores no centro das barras
        for bar in bars:
            height = bar.get_height()
            if height > 5:  # Só escreve se a barra tiver tamanho razoável
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + height / 2,
                    f'{height:.1f}%',
                    ha='center',
                    va='center',
                    color='black',
                    fontsize=9
                )
        bottom += dist[faixa]

    ax.set_ylabel("Percentual (%)")
    ax.set_ylim(0, 100)
    ax.set_title(f"Distribuição de Faixa - {variavel.capitalize()}", fontsize=14, pad=10)
    ax.set_ylabel("")
    ax.set_yticks([])
    ax.legend(title="Faixa", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(ha='center')
    plt.grid(False)

    st.pyplot(fig)