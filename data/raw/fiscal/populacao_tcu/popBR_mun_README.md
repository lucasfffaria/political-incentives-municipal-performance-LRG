# popBR_mun

## Brazilian municipalities population estimates from 2000 to 2025

These estimates were made for the DATASUS from the Brazilian Ministry of Health 
by the CGI Demográfico/[RIPSA](https://www.ripsa.org.br/) e CGIAE/SVSA/Ministério da Saúde.

I gather the brute data available at the datasus ftp [ftp://ftp.datasus.gov.br/dissemin/publicos/IBGE/POPSVS/], also available at [TABNET](http://tabnet.datasus.gov.br/cgi/tabcgi.exe?ibge/cnv/popsvs2024br.def). 
The long file `popBR2000-2025.long.csv` contains the population for each municipality (with name and IBGE 6-digit code) by year. 
The columns are

-   `MUNCOD` - Municipality IBGE 6-digit code
-   `MUN` - Municicipality name
-   `Ano` - Year of the estimate
-   `POP` - Estimated population. For years 2000, 2010 and 2022 data came from IBGE census.

This code allows you to download the file directly from my github:

```
pop.git <- read.csv("https://raw.githubusercontent.com/lsbastos/popBR_mun/refs/heads/master/popBR2000-2025.long.csv")
```

All brute files are available at the folder `brute/`.
