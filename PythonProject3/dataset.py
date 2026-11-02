import os
import re
import pandas as pd

ARQUIVO_PNAD = "pnad_trabalho_uf_trimestre.csv"
ARQUIVO_SFN = "sfn_credito_trimestre.csv"
ARQUIVO_DESENROLA = "desenrola_uf_trimestre_faixa.csv"

# 1. Carregar as três bases
df_pnad = pd.read_csv(ARQUIVO_PNAD, dtype={"codigo_uf": str})
df_sfn = pd.read_csv(ARQUIVO_SFN)
df_desenrola = pd.read_csv(ARQUIVO_DESENROLA, dtype={"codigo_uf": str})


# Função de padronização de trimestre (Converte '2023Q01' -> '2023Q1')
def padronizar_trimestre(val):
    s = str(val).strip().upper()
    m = re.match(r"^(\d{4})[-_]?Q?0?(\d)$", s)
    if m:
        return f"{m.group(1)}Q{m.group(2)}"
    return s


# 2. Padronização estrita de chaves de junção
df_pnad["codigo_uf"] = df_pnad["codigo_uf"].astype(str).str.zfill(2).str.strip()
df_desenrola["codigo_uf"] = (
    df_desenrola["codigo_uf"].astype(str).str.zfill(2).str.strip()
)

df_pnad["ano_trimestre"] = df_pnad["ano_trimestre"].apply(padronizar_trimestre)
df_sfn["ano_trimestre"] = df_sfn["ano_trimestre"].apply(padronizar_trimestre)
df_desenrola["ano_trimestre"] = df_desenrola["ano_trimestre"].apply(
    padronizar_trimestre
)

# 3. Expansão pelas 4 faixas estruturais da análise (216 x 4 = 864 linhas)
faixas_estudo = pd.DataFrame(
    {
        "faixa_renda": [
            "Faixa 1",
            "Faixa 2",
            "Pequenos Negócios",
            "Sem Operação Desenrola",
        ]
    }
)
df_painel_base = df_pnad.merge(faixas_estudo, how="cross")

# 4. Merge 1: Desenrola Brasil
df_painel_completo = df_painel_base.merge(
    df_desenrola,
    on=["codigo_uf", "ano_trimestre", "faixa_renda"],
    how="left",
)

# 5. Merge 2: Sistema Financeiro Nacional (SFN)
df_painel_final = df_painel_completo.merge(
    df_sfn, on="ano_trimestre", how="left"
)

# 6. Preenchimento de zeros para trimestres/faixas sem renegociação
df_painel_final["volume_renegociado_bruto"] = df_painel_final[
    "volume_renegociado_bruto"
].fillna(0.0)
df_painel_final["qtd_contratos_renegociados"] = df_painel_final[
    "qtd_contratos_renegociados"
].fillna(0)

# 7. Arredondamento dos valores decimais para 2 casas
colunas_decimais = [
    "taxa_desocupacao",
    "taxa_informalidade",
    "pessoas_desocupadas_mil",
    "rendimento_medio",
    "volume_renegociado_bruto",
    "taxa_inadimplencia_pf",
    "saldo_credito_pf_milhoes",
]

for col in colunas_decimais:
    if col in df_painel_final.columns:
        df_painel_final[col] = df_painel_final[col].round(2)

# 8. Ordenar dataset
df_painel_final = df_painel_final.sort_values(
    ["codigo_uf", "ano_trimestre", "faixa_renda"]
).reset_index(drop=True)

# 9. Exportar base final
df_painel_final.to_csv("painel_tri_dimensional_final.csv", index=False)

print(f"Dimensões finais: {df_painel_final.shape} (Linhas x Colunas)")
print("\nVerificação de valores nulos por coluna (deve ser 0 em todas):")
print(df_painel_final.isna().sum())
print("\nAmostra de dados com operações registradas:")
print(
    df_painel_final[
        df_painel_final["volume_renegociado_bruto"] > 0
    ].head()
)