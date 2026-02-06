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
    st.set_page_config(page_title="Brazilian Airports", page_icon=":flag-br:", layout="wide")
    st.markdown(
        """
<style>
.main .block-container {
  max-width: 980px;
  margin: 0 auto;
  padding-top: 2rem;
}
.page-title {
  text-align: center;
  font-size: 34px;
  font-weight: 700;
  margin-bottom: 6px;
  color: #0f172a;
  line-height: 1.25;
  padding-top: 10px;
  padding-bottom: 10px;
}
.page-subtitle {
  text-align: center;
  color: #334155;
  margin-bottom: 18px;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
.stMarkdownContainer h1, .stMarkdownContainer h2, .stMarkdownContainer h3 {
  line-height: 1.4;
  padding-top: 10px;
  padding-bottom: 10px;
  overflow: visible;
}
.stMarkdown h1 span, .stMarkdown h2 span, .stMarkdown h3 span,
.stMarkdownContainer h1 span, .stMarkdownContainer h2 span, .stMarkdownContainer h3 span,
.stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a,
.stMarkdownContainer h1 a, .stMarkdownContainer h2 a, .stMarkdownContainer h3 a {
  line-height: inherit;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
@media (prefers-color-scheme: dark) {
  .page-title { color: #f8fafc; }
  .page-subtitle { color: #cbd5e1; }
}
</style>
<div class="page-title">✈️ Brazilian Airports</div>
<div class="page-subtitle">
  Projeto de portfólio para analise de dados geoespaciais.<br>
  Demonstra o fluxo completo: CSV bruto → limpeza → shapefile → mapa interativo.
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Fontes oficiais dos dados (CSV bruto): "
        f"[Aerodromos Publicos]({PUBLICOS_URL}) | "
        f"[Aerodromos Privados]({PRIVADOS_URL})"
    )

    st.markdown(
        """
### 🧭 Fluxo da solução
- 📥 Coleta dados brutos em CSV do site governamental da ANAC (Agência Nacional de Aviação Civil)
- 🧹 Limpa e valida coordenadas geográficas
- 🗺️ Gera shapefiles para cada dataset
- ✈️ Cria mapa interativo com filtros e popups clicaveis para cada aeroporto
- 🔗 Links da documentação de portaria ficam clicáveis nos popups dos aeroportos
"""
    )

    st.markdown(
        """
### 🗺️ Mapa interativo e filtros
- 🟫 Privados
- 🟦 Privados com IFR
- 🟨 Públicos
- 🟪 Públicos com IFR
- ❌ Se "Situação" contém "Interditado", o ícone recebe um X vermelho
- 🎛️ Filtros: Privados, Privados com IFR, Públicos, Públicos com IFR

### **O que é VFR e IFR?**
VFR (Visual Flight Rules) = operação visual.  
IFR (Instrument Flight Rules) = operação por instrumentos, permite voos com baixa visibilidade.
"""
    )

    st.markdown("### Entrada de dados")
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
            key="uploads",
        )
    run = st.button("Processar")

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
