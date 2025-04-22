import pandas as pd

def calcular_leadscore_total(df, score_map, peso_map):
    """
    Aplica o cálculo do leadscore total ponderado por linha.

    Parâmetros:
    ----------
    df : pd.DataFrame
        Base com os leads.
    score_map : dict
        Dicionário com os scores por variável e categoria.
    peso_map : dict
        Dicionário com os pesos por variável.

    Retorno:
    -------
    pd.Series
        Coluna com o score total calculado para cada linha.
    """
    def calcular_linha(linha):
        total_score = 0
        for var in score_map:
            valor = linha.get(var)
            if pd.notna(valor):
                valor = str(valor).strip()
                base_score = score_map[var].get(valor, 0)
                peso = peso_map.get(var, 1.0)
                total_score += base_score * peso
        return round(total_score)

    return df.apply(calcular_linha, axis=1)


def detalhar_score_por_variavel(df, lead_index, score_map, peso_map):
    """
    Mostra a contribuição de cada variável para o score total de um lead.

    Parâmetros:
    ----------
    df : pd.DataFrame
        Base com os leads.
    lead_index : int
        Índice do lead na base.
    score_map : dict
        Dicionário de scores por variável e categoria.
    peso_map : dict
        Dicionário de pesos por variável.

    Retorno:
    -------
    pd.DataFrame
        Tabela com score base, peso e score final de cada variável.
    """
    linha = df.iloc[lead_index]
    detalhes = []

    for var in score_map:
        valor = linha.get(var)
        if pd.notna(valor):
            valor = str(valor).strip()
            base_score = score_map[var].get(valor, 0)
            peso = peso_map.get(var, 1.0)
            score_final = round(base_score * peso)
            detalhes.append({
                "variavel": var,
                "resposta": valor,
                "score_base": base_score,
                "peso": peso,
                "score_final": score_final
            })

    return pd.DataFrame(detalhes).sort_values(by="score_final", ascending=False)

def calcular_score_total_ponderado(linha, score_map, peso_map):
    """
    Calcula o score ponderado total de um lead com base em score por categoria e peso por variável.

    Parâmetros:
    ----------
    linha : pd.Series
        Linha do DataFrame contendo as variáveis do lead.
    score_map : dict
        Dicionário com os scores por categoria de cada variável.
    peso_map : dict
        Dicionário com os pesos por variável.

    Retorna:
    -------
    float
        Score total ponderado daquele lead.
    """
    total_score = 0
    for var in score_map:
        valor = linha.get(var)
        if pd.notna(valor):
            valor = str(valor).strip()
            base_score = score_map[var].get(valor, 0)
            peso = peso_map.get(var, 1.0)
            total_score += base_score * peso
    return round(total_score)
