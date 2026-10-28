install.packages("httr")
install.packages("jsonlite")
install.packages("dplyr")

library("httr")
library("jsonlite")
library("dplyr")



meses <- seq.Date(
         from = as.Date("2020-11-01"),
         to = as.Date("2026-09-02"),
         by="month"
)

meses <- format(meses, "%Y%m")

  
lista_meses <- lapply(meses, function(m){
  chamada <- paste0(
    "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/",
    "TransacoesPixPorMunicipio(DataBase=@DataBase)",
    "?@DataBase='", m, "'",
    "&$top=10000",
    "&$filter=Estado_Ibge%20eq%2033",
    "&$format=json",
    "&$select=AnoMes,Municipio_Ibge,Municipio,Estado_Ibge,VL_PagadorPF,QT_PagadorPF,QT_PES_PagadorPF"
  )
  resposta <- GET(chamada)
  stop_for_status(resposta)
  status_code(resposta)
  
  conteudo <- content(resposta, as="text", encoding = "UTF-8")
  dados_json <- fromJSON(conteudo)
  tabela_dados_pix <- as.data.frame(dados_json$value)
  
  tabela_dados_pix <- tabela_dados_pix[
    tabela_dados_pix$AnoMes == as.integer(m),
  ]
  
  tabela_dados_pix
  
})



dados_pix <- dplyr::bind_rows(lista_meses)

dados_pix <- dados_pix |>
  dplyr::arrange(Municipio_Ibge, AnoMes)

write.csv(
  dados_pix,
  "pix_municipios_rj.csv",
  row.names = FALSE,
  fileEncoding = "UTF-8"
)


