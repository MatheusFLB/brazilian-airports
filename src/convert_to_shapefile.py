from __future__ import annotations

from pathlib import Path
import logging
import pandas as pd
import geopandas as gpd

logger = logging.getLogger(__name__)


def convert_to_shapefile(df: pd.DataFrame, out_path: Path, lat_col: str = "LAT_DEC", lon_col: str = "LON_DEC") -> Path:
    out_path = Path(out_path)
    if out_path.suffix.lower() != ".shp":
        out_path = out_path.with_suffix(".shp")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df_ok = df[df["STATUS"] == "ok"].copy()
    df_ok = df_ok.dropna(subset=[lat_col, lon_col])
    if df_ok.empty:
        raise ValueError("No valid records to export to shapefile.")

    gdf = gpd.GeoDataFrame(
        df_ok,
        geometry=gpd.points_from_xy(df_ok[lon_col].astype(float), df_ok[lat_col].astype(float)),
        crs="EPSG:4326",
    )
    gdf.to_file(out_path, driver="ESRI Shapefile", index=False)
    logger.info("Shapefile saved: %s", out_path)
    return out_path
