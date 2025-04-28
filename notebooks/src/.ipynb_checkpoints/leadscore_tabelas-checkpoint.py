import pandas as pd
import streamlit as st

def gerar_tabela_faixas_leads_alunos(df_leads, df_alunos):
    total_leads = df_leads.groupby("leadscore_faixa").size()
    total_alunos = df_alunos.groupby("leadscore_faixa").size()

    tabela = pd.DataFrame({
        "Total Leads": total_leads,
        "Alunos": total_alunos
    }).fillna(0).astype(int)

    tabela["Taxa de Conversao (%)"] = (
        (tabela["Alunos"] / tabela["Total Leads"]) * 100
    ).round(1)

    tabela = tabela.reset_index().rename(columns={"leadscore_faixa": "Faixa"})

    faixa_ordem = ["A", "B", "C", "D"]
    tabela["Faixa"] = pd.Categorical(tabela["Faixa"], categories=faixa_ordem, ordered=True)
    tabela = tabela.sort_values("Faixa")

    total_leads_sum = tabela["Total Leads"].sum()
    total_alunos_sum = tabela["Alunos"].sum()
    taxa_total = (total_alunos_sum / total_leads_sum) * 100

    linha_total = pd.DataFrame({
        "Faixa": ["Total"],
        "Total Leads": [total_leads_sum],
        "Alunos": [total_alunos_sum],
        "Taxa de Conversao (%)": [round(taxa_total, 1)]
    })

    tabela = pd.concat([tabela, linha_total], ignore_index=True)

    tabela["Total Leads"] = tabela["Total Leads"].apply(lambda x: f"{x:,}".replace(",", "."))
    tabela["Alunos"] = tabela["Alunos"].apply(lambda x: f"{x:,}".replace(",", "."))
    tabela["Taxa de Conversao (%)"] = tabela["Taxa de Conversao (%)"].apply(lambda x: f"{x:.1f}%")

    return tabela


def destacar_total_linha(df):
    def style_rows(row):
        if row["Faixa"] == "Total":
            return ['background-color: #262730'] * len(row)
        else:
            return [''] * len(row)
    return df.style.apply(style_rows, axis=1)


def top1_utms_por_leads_A(df_leads, colunas_utm=["utm source", "utm campaign", "utm medium", "utm content"]):
    resultados = {}
    for coluna in colunas_utm:
        if coluna in df_leads.columns:
            ranking = (
                df_leads[df_leads["leadscore_faixa"] == "A"]
                .groupby(coluna)
                .size()
                .sort_values(ascending=False)
                .head(1)
                .reset_index()
            )
            ranking.columns = [coluna, "Total Leads A"]
            resultados[coluna] = ranking
    return resultados


def analisar_utms(df_leads, df_invest_trafego=None):
    colunas_utm = ["utm source", "utm campaign", "utm medium", "utm content"]

    for coluna in colunas_utm:
        st.markdown(coluna.upper())

        if coluna not in df_leads.columns:
            st.warning(f"⚠️ Atenção: coluna '{coluna}' não encontrada no DataFrame!")
            continue

        tabela_utm = (
            df_leads
            .groupby([coluna, "leadscore_faixa"])
            .size()
            .unstack(fill_value=0)
        )

        df_leads_compradores = df_leads[df_leads["comprou"] == 1]

        tabela_utm_compradores = (
            df_leads_compradores
            .groupby([coluna, "leadscore_faixa"])
            .size()
            .unstack(fill_value=0)
        ).reindex(tabela_utm.index, fill_value=0)

        taxa_conversao = (tabela_utm_compradores / tabela_utm).fillna(0) * 100
        percentuais_utm = (tabela_utm.T / tabela_utm.sum(axis=1)).T * 100

        # FILTRAR AQUI ANTES de misturar
        filtro_valido = (tabela_utm["A"] >= 10) & (tabela_utm["B"] >= 10) & (tabela_utm["C"] >= 10) & (tabela_utm["D"] >= 10)
        tabela_utm = tabela_utm[filtro_valido]
        tabela_utm_compradores = tabela_utm_compradores.reindex(tabela_utm.index, fill_value=0)
        taxa_conversao = taxa_conversao.reindex(tabela_utm.index, fill_value=0)
        percentuais_utm = percentuais_utm.reindex(tabela_utm.index, fill_value=0)

        tabela_final = pd.concat(
            [tabela_utm, percentuais_utm.add_suffix(" (%)"), taxa_conversao.add_suffix(" (tx conv)")],
            axis=1
        )

        # Combinar quantidade + percentual
        for faixa in ["A", "B", "C", "D"]:
            if faixa in tabela_final.columns and f"{faixa} (%)" in tabela_final.columns:
                tabela_final[faixa] = tabela_final.apply(
                    lambda row: f"{int(row[faixa]):,}".replace(",", ".") + f" ({row[f'{faixa} (%)']:.1f}%)", axis=1
                )
                tabela_final.drop(columns=[f"{faixa} (%)"], inplace=True)

        total_leads = tabela_utm.sum(axis=1)
        total_alunos = tabela_utm_compradores.sum(axis=1)
        tabela_final['conversao_final'] = (total_alunos / total_leads * 100).round(2)

        if coluna != "utm source" and df_invest_trafego is not None:
            spend_total = df_invest_trafego.groupby(coluna)['spend'].sum()
            tabela_final['spend_total'] = tabela_final.index.map(spend_total)
            tabela_final['spend_total'] = tabela_final['spend_total'].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else x
            )
        
        rename_dict = {
            'A_conversao': 'A (tx conv)',
            'B_conversao': 'B (tx conv)',
            'C_conversao': 'C (tx conv)',
            'D_conversao': 'D (tx conv)',
        }
        tabela_final = tabela_final.rename(columns=rename_dict)

        nova_ordem = [
            "A", "A (tx conv)",
            "B", "B (tx conv)",
            "C", "C (tx conv)",
            "D", "D (tx conv)",
            "conversao_final", "spend_total"
        ]
        colunas_existentes = [col for col in nova_ordem if col in tabela_final.columns]
        tabela_final = tabela_final[colunas_existentes]

        # Formatar colunas de taxa de conversão (%) para o formato percentual com vírgula
        for faixa in ["A", "B", "C", "D"]:
            col_tx_conv = f"{faixa} (tx conv)"
            if col_tx_conv in tabela_final.columns:
                tabela_final[col_tx_conv] = tabela_final[col_tx_conv].apply(
                    lambda x: f"{x:.2f}".replace(".", ",") + "%"
                )

        if "A (tx conv)" in tabela_final.columns:
            tabela_final = tabela_final.sort_values("A (tx conv)", ascending=False)

        styled = tabela_final.style.format(
            {col: "{:.2f}" for col in tabela_final.select_dtypes(include=['float', 'float64']).columns if col != 'spend_total'}
        )

        # Aplicar cores verdes nas melhores taxas
        for col in ["A (tx conv)", "B (tx conv)"]:
            if col in tabela_final.columns:
                styled = styled.apply(
                    lambda col_vals: [
                        'color: green;' if v.replace(",", ".").replace("%", "") and float(v.replace(",", ".").replace("%", "")) >= 
                        pd.Series([float(x.replace(",", ".").replace("%", "")) for x in col_vals]).quantile(0.70)
                        else ''
                        for v in col_vals
                    ],
                    subset=[col]
                )

        if 'spend_total' in tabela_final.columns:
            styled = styled.applymap(lambda v: 'color: red;' if isinstance(v, str) and v.startswith('R$') else '', subset=['spend_total'])

        st.dataframe(styled, use_container_width=True)


def gerar_tabela_estatisticas_leadscore(df_leads):
    if "leadscore_mapeado" not in df_leads.columns or "comprou" not in df_leads.columns:
        st.error("Erro: coluna 'leadscore_mapeado' ou 'comprou' não encontrada no DataFrame.")
        return

    leads = df_leads[df_leads["comprou"] == 0]
    alunos = df_leads[df_leads["comprou"] == 1]

    resumo = {
        "Categoria": ["Leads", "Alunos"],
        "Mínimo": [
            leads["leadscore_mapeado"].min(),
            alunos["leadscore_mapeado"].min()
        ],
        "Máximo": [
            leads["leadscore_mapeado"].max(),
            alunos["leadscore_mapeado"].max()
        ],
        "Média": [
            leads["leadscore_mapeado"].mean(),
            alunos["leadscore_mapeado"].mean()
        ],
    }

    resumo_df = pd.DataFrame(resumo)

    resumo_df["Mínimo"] = resumo_df["Mínimo"].round(2)
    resumo_df["Máximo"] = resumo_df["Máximo"].round(2)
    resumo_df["Média"] = resumo_df["Média"].round(2)

    st.markdown("#### Estatísticas do Leadscore")
    st.dataframe(resumo_df, hide_index=True, use_container_width=True)
    

def detalhar_leadscore_por_variavel(df, indice, score_map):
    row = df.iloc[indice]
    detalhes = []
    for var in score_map.keys():
        resposta = str(row.get(var)).strip()
        score = score_map[var].get(resposta, 0)
        detalhes.append({
            "Variável": var,
            "Resposta": resposta,
            "Score": round(score, 2)
        })
    return pd.DataFrame(detalhes)


def gerar_comparativo_faixas(df_leads):
    st.markdown("---")
    st.markdown("### Comparação entre Faixas de Leadscore")
    st.markdown("""
    **Abaixo destacamos as diferenças percentuais entre faixas consecutivas de leadscore (A vs B, B vs C, C vs D).**
    Assim você visualiza em quais características cada faixa se destaca.
    """)

    cols_to_analyze = ["renda", "escolaridade", "idade", "nível", "situação profissional"]

    # Função auxiliar para comparar faixas
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

    # Função para colorir diferença
    def colorir_diferenca(val):
        if val > 0:
            return "color: green"
        elif val < 0:
            return "color: red"
        else:
            return "color: gray"

    # Comparacoes
    comparacao_ab = comparar_faixas(df_leads, cols_to_analyze, "A", "B")
    comparacao_bc = comparar_faixas(df_leads, cols_to_analyze, "B", "C")
    comparacao_cd = comparar_faixas(df_leads, cols_to_analyze, "C", "D")

    # Mostrar resultados
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


def gerar_tabela_distribuicao_categorias(df_leads):
    """
    Gera uma tabela com a distribuicao percentual das categorias em cada faixa de leadscore.
    """
    resumo_faixas = []

    features = ["renda", "escolaridade", "idade", "nível", "situação profissional"]

    for var in features:
        if var in df_leads.columns and "leadscore_faixa" in df_leads.columns:
            dist = pd.crosstab(
                df_leads["leadscore_faixa"],
                df_leads[var],
                normalize='index'
            ) * 100

            dist = dist.round(2)

            for faixa in dist.index:
                for categoria in dist.columns:
                    resumo_faixas.append({
                        "Faixa": faixa,
                        "Variável": var,
                        "Categoria": categoria,
                        "Percentual (%)": dist.loc[faixa, categoria]
                    })

    if not resumo_faixas:
        st.warning("Nenhuma informação encontrada para gerar a tabela de distribuição.")
        return

    df_resumo_faixas = pd.DataFrame(resumo_faixas)

    df_resumo_pivot = df_resumo_faixas.pivot_table(
        index=["Variável", "Categoria"],
        columns="Faixa",
        values="Percentual (%)"
    ).reset_index()

    df_resumo_pivot = df_resumo_pivot[["Variável", "Categoria", "A", "B", "C", "D"]]
    df_resumo_pivot = df_resumo_pivot.sort_values(by=["Variável", "A"], ascending=[True, False])

    st.dataframe(df_resumo_pivot, use_container_width=True, hide_index=True)


def mostrar_lift_e_calculo_individual(tabelas_lift, df_leads, score_map, limites):
    col1, col2 = st.columns(2)

    with col1:
        variavel_selecionada = st.selectbox(
            "Escolha a variável para ver o Lift calculado:",
            options=list(tabelas_lift.keys())
        )

        if variavel_selecionada:
            tabela = tabelas_lift[variavel_selecionada]

            # Apenas exibindo a tabela já salva, sem modificar nada
            st.dataframe(tabela.reset_index(), use_container_width=True, hide_index=True)

    with col2:
        indice = st.number_input(
            "Selecione o ID do Lead para visualizar o cálculo de Leadscore sendo aplicado:",
            min_value=0, max_value=len(df_leads)-1, value=0, step=1
        )

        detalhes = detalhar_leadscore_por_variavel(df_leads, indice, score_map)
        st.dataframe(detalhes, use_container_width=True, hide_index=True)

        score_calc = detalhes["Score"].sum()

        if score_calc >= limites["limite_a"]:
            faixa = "A"
        elif score_calc >= limites["limite_b"]:
            faixa = "B"
        elif score_calc >= limites["limite_c"]:
            faixa = "C"
        else:
            faixa = "D"

        st.markdown(
            f"""
            <div style='background-color: #fff3cd; color: #000; display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 16px; line-height: 1.2;'>
                Score Total Calculado: {int(score_calc)} | Faixa: {faixa}
            </div>
            """,
            unsafe_allow_html=True
        )
