import pandas as pd
import sidrapy


def extrair_variavel_sidra(
    tabela, codigo_variavel, nome_coluna, classificacoes=None
):
    print(f"Extraindo {nome_coluna} (Tabela {tabela})...")
    df = sidrapy.get_table(
        table_code=tabela,
        territorial_level="3",
        ibge_territorial_code="all",
        variable=codigo_variavel,
        period="202301,202302,202303,202304,202401,202402,202403,202404",
        classifications=classificacoes,
    )

    df_limpo = df[["D1C", "D2C", "V"]].iloc[1:].copy()
    df_limpo.columns = ["codigo_uf", "ano_trimestre", nome_coluna]

    df_limpo["codigo_uf"] = df_limpo["codigo_uf"].astype(str).str.zfill(2)
    df_limpo["ano_trimestre"] = df_limpo["ano_trimestre"].apply(
        lambda x: f"{str(x)[:4]}Q{int(str(x)[4:])}"
    )
    df_limpo[nome_coluna] = pd.to_numeric(
        df_limpo[nome_coluna].astype(str).str.replace(",", "."), errors="coerce"
    )

    return df_limpo


classificacao_total = {"2": "6794"}  # Sexo: Total

df_desocupacao = extrair_variavel_sidra(
    "4093", "4099", "taxa_desocupacao", classificacao_total
)
df_informalidade = extrair_variavel_sidra(
    "4093", "12466", "taxa_informalidade", classificacao_total
)
df_qtd_desocupados = extrair_variavel_sidra(
    "4093", "4092", "pessoas_desocupadas_mil", classificacao_total
)
df_rendimento = extrair_variavel_sidra(
    "5436", "5932", "rendimento_medio", classificacao_total
)

chaves = ["codigo_uf", "ano_trimestre"]
df_pnad = df_desocupacao.merge(
    df_informalidade, on=chaves, validate="one_to_one"
)
df_pnad = df_pnad.merge(df_qtd_desocupados, on=chaves, validate="one_to_one")
df_pnad_final = df_pnad.merge(df_rendimento, on=chaves, validate="one_to_one")

df_pnad_final.to_csv("pnad_trabalho_uf_trimestre.csv", index=False)
print(f"Base PNAD salva com sucesso! Linhas: {len(df_pnad_final)}")