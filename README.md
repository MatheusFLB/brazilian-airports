# ✈️ Brazilian Airports — Geospatial Data Analysis

## 🌐 Live application 👉 **[brazilaero](https://brazilaero.streamlit.app)**

This project showcases an **end-to-end geospatial data analysis pipeline**, transforming raw government aviation data into a **clean, structured and interactive geospatial product**.

It was designed to demonstrate skills commonly required in **freelance and consulting projects**, such as:

* data cleaning and validation

* geospatial processing

* interactive visualization

* delivery of decision-ready insights

---
---

## 🎯 Project goal

Create a **reliable, interactive map of Brazilian aerodromes** that allows users to:

* explore airports spatially

* filter by operational status and flight rules

* access official regulatory documents directly from the map

This type of solution is applicable to **logistics, aviation, urban planning, mobility, BI dashboards and public data projects**.

---
---

## 🧭 Solution flow

- 📥 Collects raw CSV data from ANAC (Brazilian National Civil Aviation Agency)

- 🧹 Cleans and validates geographic coordinates

- 🗺️ Generates shapefiles for each dataset

- ✈️ Creates an interactive map with filters and clickable popups

- 🔗 Official ordinance links are accessible in airport popups

## 🗺️ Map layers & filters

### Airport categories

* 🟫 Private

* 🟦 Private with IFR

* 🟨 Public

* 🟪 Public with IFR

### Status logic

* ❌ Airports marked as *“Interditado”* (closed) are visually flagged with a red **X**

### Interactive controls

* 🎛️ Toggle layers by airport type

* 🖱️ Click markers to view metadata and official documentation

### ✈️ VFR vs IFR (context)

* **VFR (Visual Flight Rules):** operations under visual conditions

* **IFR (Instrument Flight Rules):** allows flight under low visibility using instruments

---
---

## 📦 Deliverables

This project generates assets commonly requested in freelance contracts:

* ✅ Cleaned and standardized CSV datasets

* ✅ Shapefiles ready for GIS tools (QGIS, ArcGIS, etc.)

* ✅ Interactive web map (HTML / Streamlit)

* ✅ Reproducible data pipeline in Python

---
---

## 🔗 Official data sources

* 🌐 **[Public Aerodromes](https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Aer%C3%B3dromos%20P%C3%BAblicos/Lista%20de%20aer%C3%B3dromos%20p%C3%BAblicos/)**

* 🌐 **[Private Aerodromes](https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Aer%C3%B3dromos%20Privados/Lista%20de%20aer%C3%B3dromos%20privados/Aerodromos%20Privados/)**

---
---

## 🧰 Tech stack

- 🐍 Python — main language and scripts for the data pipeline and app.
- 📊 Pandas — reads CSVs and handles tabular cleaning/processing.
- 🧭 GeoPandas — builds GeoDataFrames and exports shapefiles.
- 📐 Shapely — creates point geometries from lat/lon.
- 🧭 PyProj — manages CRS and ensures EPSG:4326 output.
- 🗃️ Fiona — writes geospatial files (shapefiles) on disk.
- 🗺️ Folium — generates the interactive HTML map with markers and layers.
- 🌐 Streamlit — serves the web app UI and interactions.

## 💼 Use cases

This project reflects real-world scenarios such as:

* Geospatial dashboards

* Public data analysis

* Infrastructure mapping

* BI tools with spatial components

---
---

## 👤 Author

Developed by **[Matheus Bissoli](https://www.linkedin.com/in/matheusbissoli/)**
