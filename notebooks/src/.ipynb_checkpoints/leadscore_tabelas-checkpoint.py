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
    import pandas as pd
    import streamlit as st

    st.subheader("Distribuição de Leads por Faixa com Origem")

    colunas_leadscore = ["renda", "escolaridade", "idade", "nível", "situação profissional"]

    # Garantir datetime
    df_leads["data"] = pd.to_datetime(df_leads["data"], errors='coerce')
    df_alunos["data"] = pd.to_datetime(df_alunos["data"], errors='coerce')

    # Conversão histórica sem leads do lançamento atual
    df_leads_filtrado = df_leads[~df_leads['utm_campaign'].astype(str).str.contains("SSP-L13", case=False, na=False)]
    leads_por_faixa_hist = df_leads_filtrado['leadscore_faixa'].value_counts()
    alunos_por_faixa_hist = df_alunos['leadscore_faixa'].value_counts()
    taxa_conversao_por_faixa = (alunos_por_faixa_hist / leads_por_faixa_hist).fillna(0)

    total_geral = len(df_filtrado)
    faixas = df_filtrado['leadscore_faixa'].dropna().unique()
    linhas_1 = []
    linhas_2 = []

    for faixa in sorted(faixas):
        df_faixa = df_filtrado[df_filtrado['leadscore_faixa'] == faixa]
        total_faixa = len(df_faixa)
        perc_faixa = (total_faixa / total_geral * 100) if total_geral else 0

        conversao_proj = taxa_conversao_por_faixa.get(faixa, 0)
        projecao_vendas = round(total_faixa * conversao_proj)

        # Tabela da esquerda
        linha_1 = {
            "Faixa": faixa,
            "Total Leads (%)": f"{total_faixa} ({perc_faixa:.0f}%)",
            "Histórico de Conversão (%)": f"{conversao_proj * 100:.1f}%",
            "Projeção de Vendas": projecao_vendas
        }
        linhas_1.append(linha_1)

        # Tabela da direita
        linha_2 = {"Faixa": faixa}
        for col in colunas_leadscore:
            if col in df_faixa.columns:
                valor_top = df_faixa[col].value_counts(normalize=False).idxmax()
                valor_total = df_faixa[col].value_counts().max()
                perc = (valor_total / total_faixa * 100) if total_faixa else 0
                linha_2[f"{col.title()} (Top 1)"] = f"{valor_top} ({perc:.0f}%)"
        linhas_2.append(linha_2)

    df_1 = pd.DataFrame(linhas_1)
    df_2 = pd.DataFrame(linhas_2)

    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        st.markdown("**📊 Conversão e Projeção**")
        st.dataframe(df_1, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**🧩 Características Principais por Faixa**")
        st.dataframe(df_2, use_container_width=True, hide_index=True)


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


def exibir_tabela_utms_por_source(df_base):
    import streamlit as st
    colunas_utm = ["utm_source", "utm_campaign", "utm_medium", "utm_content"]
    colunas_utm_sem_source = ["utm_campaign", "utm_medium", "utm_content"]

    filtro_por_source = {
        "Facebook-Ads": "utm_campaign",
        "Instagram": "utm_medium",
        "Youtube": "utm_medium",
        "Tiktok": "utm_medium"
    }

    # Remover linhas onde todos os campos utm_campaign, utm_medium, utm_content estão vazios ou nulos
    df_base = df_base[~df_base[colunas_utm_sem_source].apply(lambda row: row.isna().all() or row.eq('').all(), axis=1)]
    # Remover linhas com placeholders do Meta (ex: {{campaign.name}})
    df_base = df_base[~df_base[colunas_utm_sem_source].apply(lambda row: row.astype(str).str.contains(r"\{\{.*?\}\}").any(), axis=1)]
    
    df_base = df_base.copy()
    df_base['Campanhas'] = df_base[colunas_utm_sem_source] \
        .fillna('') \
        .applymap(lambda x: '' if str(x).strip().lower() == "nan" else str(x).strip()) \
        .agg(' | '.join, axis=1)

    fontes = df_base["utm_source"].dropna().astype(str)
    fontes = fontes[~fontes.str.strip().isin(["", "nan", "fb"])]
    fontes = fontes.unique().tolist()

    # Priorizar metaads no topo
    fontes = ["Facebook-Ads"] + sorted([f for f in fontes if f != "Facebook-Ads"])
        
    def destacar_maiores_com_ponderacao(col_vals, cor="green", minimo_absoluto=3):
        import numpy as np
        import pandas as pd
    
        pct_vals = col_vals.str.extract(r"\(([\d.]+)%\)")[0]
        abs_vals = col_vals.str.extract(r"^(\d+)\s+\(")[0]
    
        pct_vals = pd.to_numeric(pct_vals, errors='coerce').fillna(0)
        abs_vals = pd.to_numeric(abs_vals, errors='coerce').fillna(0)
    
        # Evita log(0)
        abs_log = np.log1p(abs_vals)
    
        # Score ponderado: z-score * log do volume
        pct_zscore = (pct_vals - pct_vals.mean()) / (pct_vals.std() + 1e-6)
        score = pct_zscore * abs_log
    
        # Definir limite como o percentil 95 dos scores positivos
        limiar = score[abs_vals >= minimo_absoluto].quantile(0.70)
    
        return [f'color: {cor};' if s >= limiar and a >= minimo_absoluto else ''
                for s, a in zip(score, abs_vals)]

    for fonte in fontes:
        st.markdown(f"### 🔹 UTM Source: `{fonte}`")
        df_grupo = df_base[df_base["utm_source"] == fonte]

        coluna_filtro = filtro_por_source.get(fonte)

        if coluna_filtro and coluna_filtro in df_grupo.columns:
            st.markdown(f"Filtrar por `{coluna_filtro}` em {fonte}:")
            col_filtro, _ = st.columns([4, 5])
            with col_filtro:
                opcoes = df_grupo[coluna_filtro].dropna().unique()
                filtro_valor = st.selectbox(
                    label="",
                    options=["Todas"] + sorted(opcoes),
                    key=f"{fonte}_{coluna_filtro}"
                )

            if filtro_valor != "Todas":
                df_grupo = df_grupo[df_grupo[coluna_filtro] == filtro_valor]

        if df_grupo.empty:
            st.info("Nenhum dado para esta combinação.")
            continue

        dist = df_grupo.groupby(["Campanhas", "leadscore_faixa"]).size().unstack(fill_value=0)
        dist["Total"] = dist.sum(axis=1)

        percentuais = (dist.drop(columns="Total").T / dist["Total"]).T * 100
        combinado = dist.drop(columns="Total").astype(str) + " (" + percentuais.round(1).astype(str) + "%)"
        combinado["Total"] = dist["Total"]

        # Ordenar por A
        if "A" in combinado.columns:
            combinado["_ordem"] = combinado["A"].str.extract(r"(\d+)\s+\(")[0].fillna(0).astype(float)
            combinado = combinado.sort_values(by="_ordem", ascending=False)
            combinado.drop(columns=["_ordem"], inplace=True)

        # Linha TOTAL GERAL
        soma_col = dist.sum()
        linha_total = soma_col.drop("Total").astype(int).astype(str) + " (" + \
                      (soma_col.drop("Total") / soma_col["Total"] * 100).round(1).astype(str) + "%)"
        linha_total["Total"] = int(soma_col["Total"])
        combinado_sem_total = combinado.loc[combinado.index != "TOTAL GERAL"]
        combinado_sem_total = combinado_sem_total.sort_values(by="Total", ascending=False)
        combinado = pd.concat([combinado_sem_total, pd.DataFrame([linha_total], index=["TOTAL GERAL"])])

        # Separar total geral
        linha_total = combinado.loc[["TOTAL GERAL"]]
        combinado_sem_total = combinado.drop(index="TOTAL GERAL")
        
        # Aplicar estilo apenas no corpo
        styled = combinado.style
        for col in ["A", "B"]:
            if col in combinado.columns:
                styled = styled.apply(destacar_maiores_com_ponderacao, subset=[col], axis=0, cor="green")
        if "D" in combinado.columns:
            styled = styled.apply(destacar_maiores_com_ponderacao, subset=["D"], axis=0, cor="red")
        
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