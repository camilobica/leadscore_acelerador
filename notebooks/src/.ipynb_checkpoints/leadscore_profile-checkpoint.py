import pandas as pd
import numpy as np

def gerar_leadscore_profile(df, colunas, variavel_com_pesos=None, pesos_manualmente_definidos=None):
    """
    Gera o score base (0–1000) por categoria de cada variável, com possibilidade de aplicar pesos manuais a uma variável específica.

    Parâmetros:
    ----------
    df : pd.DataFrame
        Base de dados com leads ou compradores.
    colunas : list
        Lista de colunas categóricas para análise de score via estatística.
    variavel_com_pesos : str
        Nome da variável que usará pesos manuais (se houver).
    pesos_manualmente_definidos : dict
        Dicionário com pesos brutos da variável.

    Retorno:
    -------
    pd.DataFrame
        Tabela com variavel, categoria, percentual (%) e score.
    """
    perfil = []

    for col in colunas:
        if col == variavel_com_pesos:
            continue  # será tratado manualmente depois

        dist = df[col].value_counts(normalize=True) * 100
        total_pct = dist.sum()
        for cat, pct in dist.items():
            score = round((pct / total_pct) * 1000)
            perfil.append({
                "variavel": col,
                "categoria": cat,
                "percentual (%)": pct,
                "score": score
            })

    # Adiciona variável com pesos manuais
    if variavel_com_pesos and pesos_manualmente_definidos:
        total_peso = sum(pesos_manualmente_definidos.values())
        score_manual = {k: round((v / total_peso) * 1000) for k, v in pesos_manualmente_definidos.items()}

        for cat, score in score_manual.items():
            pct = (df[variavel_com_pesos] == cat).mean() * 100
            perfil.append({
                "variavel": variavel_com_pesos,
                "categoria": cat,
                "percentual (%)": round(pct, 2),
                "score": score
            })

    return pd.DataFrame(perfil)
    

def calcular_pesos_por_variavel(df_scores, peso_renda_fixo=2.0):
    """
    Calcula os pesos das variáveis com base no desvio padrão dos scores, incluindo peso fixo para a renda.

    Parâmetros:
    ----------
    df_scores : pd.DataFrame
        DataFrame com colunas ['variavel', 'categoria', 'score'].
    peso_renda_fixo : float
        Peso fixo para 'renda_media'.

    Retorno:
    -------
    dict
        Dicionário com os pesos por variável.
    """
    variaveis = df_scores[df_scores["variavel"] != "renda_media"]
    desvios = variaveis.groupby("variavel")["score"].std().reset_index()
    desvios.columns = ["variavel", "desvio_padrao"]

    min_d, max_d = desvios["desvio_padrao"].min(), desvios["desvio_padrao"].max()

    def normalizar(d):
        if max_d == min_d:
            return 1.0
        return round(0.5 + (d - min_d) / (max_d - min_d) * (1.5 - 0.5), 2)

    desvios["peso_calculado"] = desvios["desvio_padrao"].apply(normalizar)

    # Adiciona renda_media com peso fixo
    desvios = pd.concat([
        desvios,
        pd.DataFrame([{"variavel": "renda_media", "desvio_padrao": np.nan, "peso_calculado": peso_renda_fixo}])
    ], ignore_index=True)

    peso_dict = dict(zip(desvios["variavel"], desvios["peso_calculado"]))
    return dict(zip(desvios["variavel"], desvios["peso_calculado"]))
