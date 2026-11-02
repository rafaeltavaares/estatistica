
import pandas as pd
import requests


def extrair_serie_bcb(codigo_serie, nome_coluna, agregacao="media"):
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs."
        f"{codigo_serie}/dados"
    )

    print(f"Baixando série {codigo_serie} ({nome_coluna})...")

    response = requests.get(
        url,
        params={
            "formato": "json",
            "dataInicial": "01/01/2023",
            "dataFinal": "31/12/2024"
        },
        timeout=30
    )

    response.raise_for_status()

    df = pd.DataFrame(response.json())

    if df.empty:
        raise ValueError(f"A série {codigo_serie} não retornou dados.")

    df["data"] = pd.to_datetime(
        df["data"], format="%d/%m/%Y"
    )

    df["valor"] = pd.to_numeric(
        df["valor"].astype(str).str.replace(",", "."),
        errors="coerce"
    )

    # Criar chave trimestral
    df["ano_trimestre"] = (
        df["data"].dt.year.astype(str)
        + "Q"
        + df["data"].dt.quarter.astype(str)
    )

    if agregacao == "media":
        # Média dos três meses do trimestre
        df_trimestral = (
            df.groupby("ano_trimestre")["valor"]
            .mean()
            .reset_index()
        )

    elif agregacao == "ultimo":
        # Saldo no último mês de cada trimestre
        df_fim_trimestre = df[
            df["data"].dt.month.isin([3, 6, 9, 12])
        ].copy()

        df_fim_trimestre = df_fim_trimestre.sort_values("data")

        df_trimestral = (
            df_fim_trimestre.groupby("ano_trimestre")
            .tail(1)[["ano_trimestre", "valor"]]
            .reset_index(drop=True)
        )

    else:
        raise ValueError("Agregação deve ser 'media' ou 'ultimo'.")

    df_trimestral.rename(
        columns={"valor": nome_coluna},
        inplace=True
    )

    return df_trimestral


# Séries do Banco Central
# 21082 = Inadimplência das pessoas físicas (%)
# 22050 = Saldo total das operações de crédito PF (R$ milhões)

print("Extraindo indicadores do Sistema Financeiro Nacional...")

df_inadimplencia = extrair_serie_bcb(
    21082,
    "taxa_inadimplencia_pf",
    agregacao="media"
)

df_saldo_credito = extrair_serie_bcb(
    22050,
    "saldo_credito_pf_milhoes",
    agregacao="ultimo"
)


# Cruzar as duas séries pela chave trimestral
df_sfn = df_inadimplencia.merge(
    df_saldo_credito,
    on="ano_trimestre",
    validate="one_to_one"
)


# Ordenar os trimestres
df_sfn = df_sfn.sort_values("ano_trimestre").reset_index(drop=True)


# Exportar CSV
df_sfn.to_csv(
    "sfn_credito_trimestre.csv",
    index=False
)

print("Base Banco Central gerada com sucesso!")
print(df_sfn.head())
print("Dimensões da base:", df_sfn.shape)
