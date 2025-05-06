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


def exibir_tabela_faixa_origem(df_filtrado, df_leads, df_alunos):
    st.subheader("Distribuição de Leads por Faixa com Origem")

    total_geral = len(df_filtrado)
    faixas = df_filtrado['leadscore_faixa'].dropna().unique()
    linhas_1 = []
    linhas_2 = []

    # Garantir datetime
    df_leads["data"] = pd.to_datetime(df_leads["data"], errors='coerce')
    df_alunos["data"] = pd.to_datetime(df_alunos["data"], errors='coerce')

    # Conversão histórica
    leads_por_faixa_hist = df_leads['leadscore_faixa'].value_counts()
    alunos_por_faixa_hist = df_alunos['leadscore_faixa'].value_counts()
    taxa_conversao_por_faixa = (alunos_por_faixa_hist / leads_por_faixa_hist).fillna(0)

    for faixa in sorted(faixas):
        df_faixa = df_filtrado[df_filtrado['leadscore_faixa'] == faixa]
        total_faixa = len(df_faixa)
        perc_faixa = (total_faixa / total_geral * 100) if total_geral else 0

        # UTM Source
        if not df_faixa['utm_source'].dropna().empty:
            top_source = df_faixa['utm_source'].value_counts(normalize=True).idxmax()
            top_source_perc = df_faixa['utm_source'].value_counts(normalize=True).max() * 100
        else:
            top_source = "-"
            top_source_perc = 0

        # UTM Content
        if not df_faixa['utm_content'].dropna().empty:
            top_content = df_faixa['utm_content'].value_counts(normalize=True).idxmax()
            top_content_perc = df_faixa['utm_content'].value_counts(normalize=True).max() * 100
        else:
            top_content = "-"
            top_content_perc = 0

        # Conversão e Projeção
        conversao_proj = taxa_conversao_por_faixa.get(faixa, 0)
        projecao_vendas = round(total_faixa * conversao_proj)

        # Coluna 1
        linhas_1.append({
            "Faixa": faixa,
            "Total Leads (%)": f"{total_faixa} ({perc_faixa:.0f}%)",
            "Histórico de Conversão (%)": f"{conversao_proj * 100:.1f}%",
            "Projeção de Vendas": projecao_vendas
        })

        # Coluna 2
        linhas_2.append({
            "Faixa": faixa,
            "UTM Source (Top 1)": f"{top_source} ({top_source_perc:.0f}%)",
            "UTM Content (Top 1)": f"{top_content} ({top_content_perc:.0f}%)"
        })

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📊 Conversão e Projeção**")
        df1 = pd.DataFrame(linhas_1)
        st.dataframe(df1, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**📍 Principais Origens (UTMs)**")
        df2 = pd.DataFrame(linhas_2)
        st.dataframe(df2, use_container_width=True, hide_index=True)



def top1_utms_por_leads_A(df_leads, colunas_utm=["utm_source", "utm_campaign", "utm_medium", "utm_content"]):
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


def analisar_utms(df_base_filtrado):
    colunas_utm = ["utm_source", "utm_campaign", "utm_medium", "utm_content"]

    st.markdown("""
        <style>
            div[data-testid="stSelectbox"] {
                width: 250px;
            }
        </style>
    """, unsafe_allow_html=True)

    df_filtrado = df_base_filtrado.copy()

    for coluna in colunas_utm:
        if coluna not in df_filtrado.columns:
            st.warning(f"⚠️ Atenção: coluna '{coluna}' não encontrada no DataFrame!")
            continue

        valores_unicos = df_filtrado[coluna].dropna().unique()
        valores_opcoes = ["Todos"] + sorted(valores_unicos.tolist())

        col1, _ = st.columns([1.5, 4.5])
        with col1:
            st.markdown(
                f"<div style='font-size:16px; margin-top: 20px; margin-bottom: -30px;'>Selecione qual <b>{coluna.replace('_', ' ').title()}</b> deseja filtrar:</div>",
                unsafe_allow_html=True
            )
            filtro_selecionado = st.selectbox("\u2800", valores_opcoes, key=f"select_{coluna}")

        if filtro_selecionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado[coluna] == filtro_selecionado]

        tabela_utm = (
            df_filtrado
            .groupby([coluna, "leadscore_faixa"])
            .size()
            .unstack(fill_value=0)
        )

        df_leads_compradores = df_filtrado[df_filtrado["comprou"] == 1]
        tabela_utm_compradores = (
            df_leads_compradores
            .groupby([coluna, "leadscore_faixa"])
            .size()
            .unstack(fill_value=0)
        ).reindex(tabela_utm.index, fill_value=0)

        percentuais_utm = tabela_utm.div(tabela_utm.sum(axis=1), axis=0) * 100  # ← POR LINHA (correto pra você)
        filtro_valido = (tabela_utm.sum(axis=1) >= 5)

        tabela_utm = tabela_utm[filtro_valido]
        percentuais_utm = percentuais_utm.reindex(tabela_utm.index, fill_value=0)

        tabela_final = pd.DataFrame(index=tabela_utm.index)

        for faixa in ["A", "B", "C", "D"]:
            if faixa in tabela_utm.columns:
                tabela_final[faixa] = tabela_utm.apply(
                    lambda row: f"{int(row[faixa]):,}".replace(",", ".") + f" ({percentuais_utm.loc[row.name, faixa]:.1f}%)",
                    axis=1
                )

        if tabela_final.empty:
            st.info(f"Nenhum dado encontrado para a UTM **{coluna}** com os filtros aplicados.")
            continue

        # Ordenar pela coluna A (valor absoluto antes do parêntese)
        if "A" in tabela_final.columns:
            tabela_final["_sort"] = tabela_final["A"].str.extract(r"(\d+)\s+\(")[0].astype(int)
            tabela_final = tabela_final.sort_values("_sort", ascending=False).drop(columns=["_sort"])

        def destacar_top_15_absolutos(col_vals):
            # Extrai apenas o número antes do parêntese
            valores = col_vals.str.extract(r'(\d+)\s+\(')[0].astype(int)
            limiar = valores.quantile(0.85)
        
            return ['color: green;' if v >= limiar else '' for v in valores]

        styled = tabela_final.style
        for col in ["A", "B"]:
            if col in tabela_final.columns:
                styled = styled.apply(destacar_top_15_absolutos, subset=[col])

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
    st.dataframe(
        resumo_df.style.format({
            "Mínimo": "{:.2f}",
            "Máximo": "{:.2f}",
            "Média": "{:.2f}"
        }),
        hide_index=True,
        use_container_width=True
    )


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

    # Função para formatar e exibir
    def formatar_e_mostrar(df, faixa1, faixa2, cor_emoji):
        col_diff = f"diferença entre {faixa1} e {faixa2}"
        st.markdown(f"{cor_emoji} **Diferenças entre Faixa {faixa1} e {faixa2}**")

        df_temp = df.copy().head(15).reset_index(drop=True)

        styled = (
            df_temp
            .style
            .format({
                f"% {faixa1}": "{:.1f}",
                f"% {faixa2}": "{:.1f}",
                col_diff: "{:.2f}"
            })
            .applymap(colorir_diferenca, subset=[col_diff])
        )

        st.dataframe(styled, use_container_width=True, hide_index=True)

    # Comparações
    comparacao_ab = comparar_faixas(df_leads, cols_to_analyze, "A", "B")
    comparacao_bc = comparar_faixas(df_leads, cols_to_analyze, "B", "C")
    comparacao_cd = comparar_faixas(df_leads, cols_to_analyze, "C", "D")

    # Mostrar
    formatar_e_mostrar(comparacao_ab, "A", "B", "🟢")
    formatar_e_mostrar(comparacao_bc, "B", "C", "🟡")
    formatar_e_mostrar(comparacao_cd, "C", "D", "🔴")


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
            tabela = tabelas_lift[variavel_selecionada].copy()

            # Calcular totais das colunas numéricas (ignorando percentual e lift/score)
            colunas_soma = ["qtd_leads", "qtd_alunos"]
            totais = tabela[colunas_soma].sum().to_frame().T
            totais.index = ["Total"]

            # Preencher as demais colunas com "-"
            for col in tabela.columns:
                if col not in totais.columns:
                    totais[col] = "-"

            # Concatenar total
            tabela_total = pd.concat([tabela, totais], axis=0)

            # Mostrar no Streamlit
            st.dataframe(tabela_total, use_container_width=True)

    with col2:
        lancamentos = ["Todos"] + sorted(df_leads["lancamentos"].dropna().unique())
        filtro_lancamento = st.selectbox("Selecione o Lançamento para visualizar os Leads:", lancamentos)

        df_filtrado = df_leads if filtro_lancamento == "Todos" else df_leads[df_leads["lancamentos"] == filtro_lancamento]

        if df_filtrado.empty:
            st.warning("⚠️ Nenhum lead disponível para esse lançamento.")
            return

        st.caption(f"📊 Total de leads disponíveis: {len(df_filtrado):,}")

        indice = st.number_input(
            "Selecione o ID do Lead para visualizar o cálculo de Leadscore sendo aplicado:",
            min_value=0, max_value=len(df_filtrado) - 1,
            value=0, step=1
        )

        detalhes = detalhar_leadscore_por_variavel(df_filtrado, indice, score_map)
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