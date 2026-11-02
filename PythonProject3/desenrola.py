import pandas as pd


# 1. Carregar arquivo bruto (CSV do BCB utiliza separador ';')
arquivo = "dados_desenrola.csv"

try:
    df_desenrola = pd.read_csv(arquivo, sep=";", encoding="utf-8")
except FileNotFoundError:
    raise FileNotFoundError(
        f"Arquivo '{arquivo}' não encontrado. "
        "Verifique se salvou o CSV do BCB nesta pasta com esse nome."
    )

# 2. Renomear as colunas oficiais do BCB (Atribuição direta para evitar Warning de inplace)
renomear_bcb = {
    "UNIDADE_FEDERACAO": "codigo_uf",
    "DATA_BASE": "periodo_referencia",
    "TIPO_DESENROLA": "faixa_programa",
    "VOLUME_OPERACOES": "valor_renegociado",
    "NUMERO_OPERACOES": "qtd_contratos",
}
df_desenrola = df_desenrola.rename(columns=renomear_bcb)

# 3. Verificar colunas necessárias
colunas_necessarias = [
    "codigo_uf",
    "periodo_referencia",
    "faixa_programa",
    "valor_renegociado",
    "qtd_contratos",
]

colunas_ausentes = [
    coluna
    for coluna in colunas_necessarias
    if coluna not in df_desenrola.columns
]

if colunas_ausentes:
    raise ValueError(f"Colunas ausentes no arquivo: {colunas_ausentes}")

# 4. Mapear sigla de UF para código IBGE de 2 dígitos
uf_para_codigo = {
    "RO": "11",
    "AC": "12",
    "AM": "13",
    "RR": "14",
    "PA": "15",
    "AP": "16",
    "TO": "17",
    "MA": "21",
    "PI": "22",
    "CE": "23",
    "RN": "24",
    "PB": "25",
    "PE": "26",
    "AL": "27",
    "SE": "28",
    "BA": "29",
    "MG": "31",
    "ES": "32",
    "RJ": "33",
    "SP": "35",
    "PR": "41",
    "SC": "42",
    "RS": "43",
    "MS": "50",
    "MT": "51",
    "GO": "52",
    "DF": "53",
}

df_desenrola["codigo_uf"] = df_desenrola["codigo_uf"].map(
    lambda x: uf_para_codigo.get(str(x), str(x))
)
df_desenrola["codigo_uf"] = (
    df_desenrola["codigo_uf"]
    .astype(str)
    .str.replace(r"\.0$", "", regex=True)
    .str.zfill(2)
)

# Filtrar apenas UFs válidas
df_desenrola = df_desenrola[
    df_desenrola["codigo_uf"].isin(uf_para_codigo.values())
].copy()

# 5. Converter período mensal (AAAAMM) para trimestre (YYYYQ#)
data_temp = pd.to_datetime(
    df_desenrola["periodo_referencia"].astype(str),
    format="%Y%m",
    errors="coerce",
)

if data_temp.isna().any():
    raise ValueError("Existem períodos de referência inválidos no arquivo.")

df_desenrola["ano_trimestre"] = (
    data_temp.dt.year.astype(str) + "Q" + data_temp.dt.quarter.astype(str)
)

# 6. Mapear a faixa do programa (evitando incompatibilidade de tipos no fillna)
mapeamento_faixas = {
    1: "Faixa 1",
    2: "Faixa 2",
    3: "Pequenos Negócios",
    "1": "Faixa 1",
    "2": "Faixa 2",
    "3": "Pequenos Negócios",
}
df_desenrola["faixa_programa"] = (
    df_desenrola["faixa_programa"]
    .map(mapeamento_faixas)
    .astype(str)
    .fillna("Outros")
)

# 7. Tratamento Numérico Rígido (Substituição de vírgula decimal e conversão segura)
df_desenrola["valor_renegociado"] = (
    df_desenrola["valor_renegociado"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)
df_desenrola["valor_renegociado"] = pd.to_numeric(
    df_desenrola["valor_renegociado"], errors="coerce"
).fillna(0.0)

df_desenrola["qtd_contratos"] = pd.to_numeric(
    df_desenrola["qtd_contratos"], errors="coerce"
).fillna(0)

# 8. Consolidar por UF, trimestre e faixa
df_desenrola_por_faixa = (
    df_desenrola.groupby(
        ["codigo_uf", "ano_trimestre", "faixa_programa"], as_index=False
    )
    .agg(
        volume_renegociado_bruto=("valor_renegociado", "sum"),
        qtd_contratos_renegociados=("qtd_contratos", "sum"),
    )
    .rename(columns={"faixa_programa": "faixa_renda"})
)

# 9. Consolidar por UF e trimestre (total do programa)
df_desenrola_limpo = df_desenrola_por_faixa.groupby(
    ["codigo_uf", "ano_trimestre"], as_index=False
).agg(
    volume_renegociado_bruto=("volume_renegociado_bruto", "sum"),
    qtd_contratos_renegociados=("qtd_contratos_renegociados", "sum"),
)

# 10. Ordenar os dados
df_desenrola_por_faixa = df_desenrola_por_faixa.sort_values(
    ["codigo_uf", "ano_trimestre", "faixa_renda"]
).reset_index(drop=True)

df_desenrola_limpo = df_desenrola_limpo.sort_values(
    ["codigo_uf", "ano_trimestre"]
).reset_index(drop=True)

# 11. Exportar as duas bases
df_desenrola_por_faixa.to_csv("desenrola_uf_trimestre_faixa.csv", index=False)
df_desenrola_limpo.to_csv("desenrola_uf_trimestre.csv", index=False)

print("\nBases do Desenrola geradas com sucesso!")
print("\nBase consolidada (Primeiras linhas):")
print(df_desenrola_limpo.head())

print("\nDimensões da base consolidada:", df_desenrola_limpo.shape)
print("Dimensões da base por faixa:", df_desenrola_por_faixa.shape)