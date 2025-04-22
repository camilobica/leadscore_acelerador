import pandas as pd

def tabela_comparativa_por_lancamento(df_leads, df_alunos):
    """
    Compara a distribuição percentual por faixa de score em cada lançamento,
    usando projeção dos leads e realidade dos alunos.
    """

    # Projeção (leads): distribuição prevista por faixa e lançamento
    previsto = (
        df_leads.groupby(["lancamentos", "faixa_predita_por_regressao"])
        .size()
        .groupby(level=0)
        .apply(lambda x: (x / x.sum() * 100).round(1))
        .unstack(fill_value=0)
    )
    previsto.columns = [f"{col}_previsto" for col in previsto.columns]

    # Realidade (alunos): distribuição real por faixa e lançamento
    real = (
        df_alunos.groupby(["lancamentos", "leadscore_faixa"])
        .size()
        .groupby(level=0)
        .apply(lambda x: (x / x.sum() * 100).round(1))
        .unstack(fill_value=0)
    )
    real.columns = [f"{col}_real" for col in real.columns]

    # Junta as duas tabelas
    comparativo = previsto.join(real, how="outer").fillna(0)

    # Calcula variação percentual (previsto - real)
    for faixa in ["A", "B", "C", "D"]:
        comparativo[f"{faixa}_variação"] = (
            comparativo.get(f"{faixa}_previsto", 0) - comparativo.get(f"{faixa}_real", 0)
        ).round(1)

    # Ordenação das colunas
    def ordena(col):
        faixa_ordem = {"A": 0, "B": 1, "C": 2, "D": 3}
        base, tipo = col.split("_")
        return faixa_ordem.get(base, 99), tipo

    comparativo = comparativo[sorted(comparativo.columns, key=ordena)]

    # Estilização
    def color_variacao(val):
        if abs(val) == 0:
            return "color: gray"
        elif val > 0:
            return "color: green"
        else:
            return "color: red"

    styled = comparativo.style.format("{:.1f}%")
    for col in comparativo.columns:
        if col.endswith("_variação"):
            styled = styled.map(color_variacao, subset=[col])

    return styled
