# ✈️ Brazilian Airports

## 🌐 Live app
- https://brazilaero.streamlit.app

Portfolio project for **geospatial data analysis**. It demonstrates the full pipeline:
raw CSV → cleaning → shapefile → interactive map.

## 🧭 Solution flow
- 📥 Collects raw CSV data from ANAC (Brazilian National Civil Aviation Agency)
- 🧹 Cleans and validates geographic coordinates
- 🗺️ Generates shapefiles for each dataset
- ✈️ Creates an interactive map with filters and clickable popups
- 🔗 Official ordinance links are accessible in airport popups

## 🗺️ Interactive map and filters
- 🟫 Private
- 🟦 Private with IFR
- 🟨 Public
- 🟪 Public with IFR
- ❌ If "Status" contains "Interditado" (Closed), the icon shows a red X
- 🎛️ Filters: Private, Private with IFR, Public, Public with IFR

**What are VFR and IFR?**  
VFR (Visual Flight Rules) = visual operations.  
IFR (Instrument Flight Rules) = instrument operations, allows low-visibility flights.

## 📦 Outputs
- Cleaned CSVs
- Shapefiles by dataset
- Interactive HTML map with filters

## 🔗 Official sources (raw CSV)
- 🌐 Public Aerodromes: https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Aer%C3%B3dromos%20P%C3%BAblicos/Lista%20de%20aer%C3%B3dromos%20p%C3%BAblicos/
- 🌐 Private Aerodromes: https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Aer%C3%B3dromos%20Privados/Lista%20de%20aer%C3%B3dromos%20privados/Aerodromos%20Privados/

## 🧰 Tech stack
- 🐍 Python — main language and scripts for the data pipeline and app.
- 📊 Pandas — reads CSVs and handles tabular cleaning/processing.
- 🧭 GeoPandas — builds GeoDataFrames and exports shapefiles.
- 📐 Shapely — creates point geometries from lat/lon.
- 🧭 PyProj — manages CRS and ensures EPSG:4326 output.
- 🗃️ Fiona — writes geospatial files (shapefiles) on disk.
- 🗺️ Folium — generates the interactive HTML map with markers and layers.
- 🌐 Streamlit — serves the web app UI and interactions.

# 👤 Author

Project created by **[Matheus Bissoli](https://www.linkedin.com/in/matheusbissoli/)**
