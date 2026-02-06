# ✈️ Brazilian Airports

## 🌐 Aplicação publicada
- https://brazilaero.streamlit.app

Projeto para analise de dados geoespaciais.\
Demonstra o fluxo completo: CSV bruto → limpeza → shapefile → mapa interativo.

## 🧭 Fluxo da solução
- 📥 Coleta dados brutos em CSV do site governamental da ANAC (Agência Nacional de Aviação Civil)
- 🧹 Limpa e valida coordenadas geográficas
- 🗺️ Gera shapefiles para cada dataset
- ✈️ Cria mapa interativo com filtros e popups clicaveis para cada aeroporto
- 🔗 Links da documentação de portaria ficam clicáveis nos popups dos aeroportos

## 🗺️ Mapa interativo e filtros
- 🟫 Privados
- 🟦 Privados com IFR
- 🟨 Públicos
- 🟪 Públicos com IFR
- ❌ Se "Situação" contém "Interditado", o ícone recebe um X vermelho
- 🎛️ Filtros: Privados, Privados com IFR, Públicos, Públicos com IFR

**O que é VFR e IFR?**
VFR (Visual Flight Rules) = operação visual.  
IFR (Instrument Flight Rules) = operação por instrumentos, permite voos com baixa visibilidade.

## 📦 Saídas geradas
- CSVs limpos
- Shapefiles por dataset
- Mapa HTML com filtros

## 🔗 Fontes oficiais (CSV bruto)
- 🌐 Aeródromos Públicos: https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Aer%C3%B3dromos%20P%C3%BAblicos/Lista%20de%20aer%C3%B3dromos%20p%C3%BAblicos/
- 🌐 Aeródromos Privados: https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Aer%C3%B3dromos%20Privados/Lista%20de%20aer%C3%B3dromos%20privados/Aerodromos%20Privados/

## 🧰 Tecnologias
- 🐍 Python
- 📊 Pandas / GeoPandas
- 🧭 Shapely / PyProj / Fiona
- 🗺️ Folium
- 🌐 Streamlit
