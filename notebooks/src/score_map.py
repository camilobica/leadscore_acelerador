import pandas as pd

def gerar_score_map(df_leadscore, df_base=None):
    """
    Cria um dicionário {variável: {categoria: score}} a partir do leadscore_df.
    Também completa com score 0 para categorias presentes no df_base e ausentes no modelo.

    Parâmetros:
    ----------
    df_leadscore : pd.DataFrame
        DataFrame com colunas ['variavel', 'categoria', 'score'].
    df_base : pd.DataFrame, opcional
        DataFrame com os dados reais (para garantir que todas as categorias tenham score).

    Retorno:
    -------
    dict
        Dicionário score_map: {variável: {categoria: score}}.
    """
    score_map = {}

    for _, row in df_leadscore.iterrows():
        var = row["variavel"]
        cat = str(row["categoria"]).strip()
        score = row["score"]

        if var not in score_map:
            score_map[var] = {}

        score_map[var][cat] = score

    # Completar com categorias da base real que não estão no modelo
    if df_base is not None:
        for var in score_map:
            if var in df_base.columns:
                categorias_df = df_base[var].dropna().astype(str).str.strip().unique()
                for cat in categorias_df:
                    if cat not in score_map[var]:
                        score_map[var][cat] = 0  # score neutro

    return score_map
