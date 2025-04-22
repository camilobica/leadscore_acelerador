import pandas as pd

def gerar_freq_variavel(df, colunas, corte_percentual=5):
    """
    Gera um resumo do perfil comprador com base na distribuição percentual das respostas.

    Parâmetros:
    ----------
    df : pd.DataFrame
        DataFrame com a base de leads ou compradores.
    colunas : list
        Lista de colunas categóricas a serem analisadas.
    corte_percentual : float, opcional
        Limite mínimo de representatividade (%) para uma categoria ser exibida. Default = 5.

    Retorno:
    -------
    pd.DataFrame
        DataFrame com colunas: 'variavel', 'categoria', 'percentual (%)', ordenado por relevância.
    """
    perfil = []

    for col in colunas:
        counts = df[col].value_counts(normalize=True).round(3) * 100
        top_values = counts[counts > corte_percentual]
        if not top_values.empty:
            for cat, pct in top_values.items():
                perfil.append({
                    "variavel": col,
                    "categoria": cat,
                    "percentual (%)": pct
                })

    return pd.DataFrame(perfil).sort_values(by=["variavel", "percentual (%)"], ascending=[True, False])
