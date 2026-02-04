# ✈️ Aeroportos Geo

Projeto de portfólio para analista de dados geoespaciais. Demonstra o fluxo
completo de dados: CSV bruto → limpeza → shapefile → mapa interativo.

## 🧭 Fluxo da solução
- 📥 Coleta dados brutos em CSV (ANAC)
- 🧹 Limpa e valida coordenadas geográficas
- 🗺️ Gera shapefiles por dataset (EPSG:4326)
- ✈️ Cria mapa interativo com filtros e popups
- 🔗 Links de portaria ficam clicáveis

## 🧠 Regras de qualidade de coordenadas
- Remove espaços/tabs e aceita vírgula decimal
- Corrige números sem ponto decimal (ex: -22175 → -22.175)
- Tenta inverter LAT/LON quando fora das faixas do Brasil
- Faixas Brasil: Latitude [-35, 6]
- Faixas Brasil: Longitude [-75, -30]

## 🗺️ Mapa interativo e filtros
- 🟫 Privados (terracota) e 🟦 ciano quando "Operação Noturna" contém "VFR / IFR"
- 🟨 Públicos (amarelo) e 🟪 violeta quando "Operação Noturna" contém "VFR / IFR"
- ❌ Se "Situação" contém "Interditado", o ícone recebe um X vermelho
- 🎛️ Filtros: Privados, Privados com IFR, Públicos, Públicos com IFR

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
