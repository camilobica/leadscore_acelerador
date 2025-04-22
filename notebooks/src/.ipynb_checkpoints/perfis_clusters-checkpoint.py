import pandas as pd
from IPython.display import display, HTML


def exibir_perfis_clusters(df_clusterizado, col_cluster="cluster_kmeans"):
    """
    Exibe tabelas HTML estilizadas com perfil simplificado por cluster.
    """

    # Variáveis a ignorar
    colunas_excluir = [
        'email', 'data_inscricao', 'data_nascimento',
        'pais_categoria', 'estado_categoria', 'como_comprou_portal', 'lancamentos'
    ]

    # Seleciona colunas categóricas válidas
    cols_to_analyze = [
        col for col in df_clusterizado.columns
        if df_clusterizado[col].dtype == "object" and col not in colunas_excluir
    ]

    # CSS customizado
    css = """
    <style>
    td {
        white-space: pre-wrap;
        vertical-align: top;
    }
    </style>
    """

    # Para cada cluster
    for i, cluster_id in enumerate(sorted(df_clusterizado[col_cluster].unique()), start=1):
        subset = df_clusterizado[df_clusterizado[col_cluster] == cluster_id]
        n = len(subset)

        perfil_data = []

        # 1. Média do leadscore
        media_score = subset["leadscore_total"].mean()
        perfil_data.append({
            "variavel": "leadscore_total (média)",
            "valor": f"{media_score:.2f}"
        })

        # 2. Variáveis categóricas
        for col in cols_to_analyze:
            top_cat = subset[col].value_counts(normalize=True).head(3)
            valor = "<br>".join([f"{k} ({v*100:.1f}%)" for k, v in top_cat.items()])
            perfil_data.append({"variavel": col, "valor": valor})

        # 3. Faixa (sempre 100%)
        faixa = subset["leadscore_faixa"].value_counts(normalize=True).index[0]
        faixa_pct = subset["leadscore_faixa"].value_counts(normalize=True).values[0] * 100
        perfil_data.append({
            "variavel": "leadscore_faixa",
            "valor": f"{faixa} ({faixa_pct:.1f}%)"
        })

        # DataFrame final
        df_formatado = pd.DataFrame(perfil_data)

        # Título atualizado
        display(HTML(f"<h3 style='margin-top: 40px;'>🔹 Cluster {i} — Total de {n} alunos</h3>"))

        # Exibe tabela com CSS
        html = df_formatado.to_html(escape=False, index=False)
        display(HTML(css + html))
