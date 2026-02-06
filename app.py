from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import io
import tempfile
import zipfile
from typing import List

import pandas as pd
import streamlit as st

from src.clean_coords import clean_dataframe, resolve_lat_lon_columns
from src.convert_to_shapefile import convert_to_shapefile
from src.datasets import DatasetConfig, match_dataset_config
from src.make_map import DatasetLayer, make_combined_map
from src.cli import read_csv_guess

BASE_DIR = Path(__file__).resolve().parent

PUBLICOS_URL = (
    "https://sistemas.anac.gov.br/dadosabertos/Aerodromos/"
    "Aer%C3%B3dromos%20P%C3%BAblicos/Lista%20de%20aer%C3%B3dromos%20p%C3%BAblicos/"
)
PRIVADOS_URL = (
    "https://sistemas.anac.gov.br/dadosabertos/Aerodromos/"
    "Aer%C3%B3dromos%20Privados/Lista%20de%20aer%C3%B3dromos%20privados/Aerodromos%20Privados/"
)


@dataclass(frozen=True)
class DatasetResult:
    name: str
    stem: str
    config: DatasetConfig
    df: pd.DataFrame
    valid: int


def _generic_config_for_path(path: Path) -> DatasetConfig:
    label = path.stem
    return DatasetConfig(
        key=label.lower(),
        label=label,
        filename_hints=[],
        popup_fields=["UF"],
        default_color="#4C78A8",
        alt_color="#4C78A8",
        night_ops_field="Operacao Noturna",
    )


def _hash_path(path: Path) -> tuple:
    stat = path.stat()
    return (str(path), stat.st_mtime, stat.st_size)


@st.cache_data(show_spinner=False, hash_funcs={Path: _hash_path})
def _prepare_results(paths: List[Path]) -> List[DatasetResult]:
    results: List[DatasetResult] = []
    for path in paths:
        cfg = match_dataset_config(path) or _generic_config_for_path(path)
        df = read_csv_guess(path, None, None)
        lat_res, lon_res = resolve_lat_lon_columns(df, None, None)
        clean_df, clean_results = clean_dataframe(df, lat_res, lon_res)
        valid = sum(r.status == "ok" for r in clean_results)
        results.append(
            DatasetResult(
                name=path.name,
                stem=path.stem,
                config=cfg,
                df=clean_df,
                valid=valid,
            )
        )
    return results


@st.cache_data(show_spinner=False)
def _build_outputs_zip(results: List[DatasetResult]) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        outdir = Path(tmpdir) / "out"
        outdir.mkdir(parents=True, exist_ok=True)

        for result in results:
            clean_csv_path = outdir / f"{result.stem}_clean.csv"
            result.df.to_csv(clean_csv_path, index=False)
            if result.valid > 0:
                convert_to_shapefile(result.df, outdir / f"{result.stem}.shp")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(outdir.iterdir()):
                zf.write(file, arcname=file.name)
        return zip_buffer.getvalue()


def _render_map(results: List[DatasetResult], outdir: Path) -> Path:
    layers = [DatasetLayer(r.config, r.df) for r in results if r.valid > 0]
    map_path = outdir / "mapa_aeroportos.html"
    make_combined_map(layers, map_path)
    return map_path


def main() -> None:
    st.set_page_config(page_title="Aeroportos Geo", page_icon=":flag-br:", layout="wide")
    st.markdown(
        """
<style>
.hero-card {
  background: linear-gradient(120deg, #f7f9fc, #eef3ff);
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.hero-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0;
}
.hero-sub {
  margin-top: 6px;
  font-size: 15px;
  color: #2f3640;
}
.badges {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.badge {
  background: #ffffff;
  border: 1px solid #d7e0ee;
  color: #2d3748;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
}
</style>
<div class="hero-card">
  <div class="hero-title">✈️ Aeroportos Geo</div>
  <div class="hero-sub">
    Projeto de portfólio para analista de dados geoespaciais. Demonstra o fluxo completo:
    CSV bruto → limpeza → shapefile → mapa interativo.
  </div>
  <div class="badges">
    <span class="badge">CSV → Shapefile</span>
    <span class="badge">EPSG:4326</span>
    <span class="badge">Folium + Streamlit</span>
    <span class="badge">Filtros e popups</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Fontes oficiais dos dados (CSV bruto): "
        f"[Aerodromos Publicos]({PUBLICOS_URL}) | "
        f"[Aerodromos Privados]({PRIVADOS_URL})"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
### 🧭 Fluxo da solução
- 📥 Coleta dados brutos em CSV (ANAC)
- 🧹 Limpa e valida coordenadas geográficas
- 🗺️ Gera shapefiles por dataset (EPSG:4326)
- ✈️ Cria mapa interativo com filtros e popups
- 🔗 Links de portaria ficam clicáveis
"""
        )
    with col2:
        st.markdown(
            """
### 🧠 Regras de qualidade de coordenadas
- Remove espaços/tabs e aceita vírgula decimal
- Corrige números sem ponto decimal (ex: -22175 → -22.175)
- Tenta inverter LAT/LON quando fora das faixas do Brasil
- Faixas Brasil: Latitude [-35, 6]
- Faixas Brasil: Longitude [-75, -30]
"""
        )

    st.markdown(
        """
### 🗺️ Mapa interativo e filtros
- 🟫 Privados (terracota) e 🟦 ciano quando "Operação Noturna" contém "VFR / IFR"
- 🟨 Públicos (amarelo) e 🟪 violeta quando "Operação Noturna" contém "VFR / IFR"
- ❌ Se "Situação" contém "Interditado", o ícone recebe um X vermelho
- 🎛️ Filtros: Privados, Privados com IFR, Públicos, Públicos com IFR
"""
    )

    st.markdown("### Entrada de dados")
    with st.form("input_form"):
        source = st.radio(
            "Fonte",
            ["Usar CSVs do projeto", "Upload de CSVs"],
            horizontal=True,
        )
        uploads = []
        if source == "Upload de CSVs":
            uploads = st.file_uploader(
                "Envie 1 ou 2 CSVs",
                type=["csv"],
                accept_multiple_files=True,
            )
        run = st.form_submit_button("Processar")

    if "results" not in st.session_state:
        st.session_state.results = None
    if "map_html" not in st.session_state:
        st.session_state.map_html = None
    if "outputs_zip" not in st.session_state:
        st.session_state.outputs_zip = None

    if run:
        with st.spinner("Processando..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)

                if source == "Usar CSVs do projeto":
                    csv_dir = BASE_DIR / "csv-base"
                    paths = sorted(csv_dir.glob("*.csv"))
                    if not paths:
                        st.error("Nenhum CSV encontrado em csv-base.")
                        return
                else:
                    if not uploads:
                        st.error("Envie pelo menos um CSV.")
                        return
                    paths = []
                    for up in uploads:
                        target = tmpdir_path / up.name
                        target.write_bytes(up.getvalue())
                        paths.append(target)

                results = _prepare_results(paths)
                outdir = tmpdir_path / "out"
                outdir.mkdir(parents=True, exist_ok=True)
                map_path = _render_map(results, outdir)

                st.session_state.results = results
                st.session_state.map_html = map_path.read_text(encoding="utf-8", errors="ignore")
                st.session_state.outputs_zip = None

    if st.session_state.map_html is None:
        st.info("Configure a entrada e clique em Processar.")
        return

    st.subheader("Mapa")
    st.info("Para visualizar os aeroportos, marque as camadas na legenda do mapa.")
    try:
        st.components.v1.html(st.session_state.map_html, height=800, scrolling=True, key="map")
    except TypeError:
        # Older Streamlit versions don't support the "key" argument here.
        st.components.v1.html(st.session_state.map_html, height=800, scrolling=True)

    st.markdown("### Outputs")
    if st.button("Gerar outputs para download"):
        if st.session_state.results:
            st.session_state.outputs_zip = _build_outputs_zip(st.session_state.results)
    if st.session_state.outputs_zip:
        st.download_button(
            label="Baixar outputs (CSV + Shapefiles + HTML)",
            data=st.session_state.outputs_zip,
            file_name="aeroportos_outputs.zip",
            mime="application/zip",
        )


if __name__ == "__main__":
    main()

