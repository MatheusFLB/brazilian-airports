from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import html
import logging
import re
import pandas as pd
import folium
from branca.element import Element

from .datasets import DatasetConfig, normalize_name

logger = logging.getLogger(__name__)

BRAZIL_CENTER = (-14.235, -51.925)

FA_CSS = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
PLANE_CSS = """
<style>
.plane-icon {
  position: relative;
  width: 22px;
  height: 22px;
}
.plane-icon i {
  position: absolute;
  left: 0;
  top: 0;
}
.plane-icon .plane {
  font-size: 20px;
}
.plane-icon .x {
  font-size: 20px;
}
</style>
"""

SIDEBAR_CSS = """
<style>
#filter-sidebar {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 9999;
  background: #ffffff;
  padding: 12px 14px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  width: 230px;
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: 13px;
}
#filter-sidebar h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
}
#filter-sidebar label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 6px 0;
  cursor: pointer;
}
#filter-sidebar .swatch {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid #555;
  flex: 0 0 12px;
}
</style>
"""

LABEL_RENAMES = {
    normalize_name("Nome"): "Aeroporto",
    normalize_name("UF"): "Estado",
    normalize_name("Superfície 1"): "Superfície",
}


@dataclass(frozen=True)
class DatasetLayer:
    config: DatasetConfig
    df: pd.DataFrame


def _normalize_map(df: pd.DataFrame) -> dict[str, str]:
    return {normalize_name(c): c for c in df.columns}


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _find_column(col_map: dict[str, str], target_label: str) -> Optional[str]:
    target_norm = normalize_name(target_label)
    if not target_norm:
        return None
    if target_norm in col_map:
        return col_map[target_norm]

    best_col = None
    best_dist = None
    for norm, col in col_map.items():
        if not norm:
            continue
        dist = _levenshtein(target_norm, norm)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_col = col

    if best_dist is None:
        return None

    threshold = max(2, len(target_norm) // 5)
    return best_col if best_dist <= threshold else None


def _resolve_fields(df: pd.DataFrame, labels: List[str]) -> List[Tuple[str, str]]:
    col_map = _normalize_map(df)
    resolved: List[Tuple[str, str]] = []
    for label in labels:
        col = _find_column(col_map, label)
        if col:
            resolved.append((label, col))
    return resolved


def _fix_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    if "Ã" in text or "Â" in text:
        try:
            text = text.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            pass
    if "�" in text:
        text = text.replace("�", "")
    return text.strip()


def _has_vfr_ifr(value: object) -> bool:
    text = _fix_text(value).lower()
    text = re.sub(r"\s+", "", text)
    return "vfr/ifr" in text


def _has_token(value: object, token: str) -> bool:
    return token.lower() in _fix_text(value).lower()


def _build_popup(row: pd.Series, fields: List[Tuple[str, str]]) -> str:
    lines = ["<table style='border-collapse:collapse; white-space:nowrap;'>"]
    for label, col in fields:
        val = _fix_text(row.get(col, ""))
        if val.strip() == "":
            continue
        display_label = LABEL_RENAMES.get(normalize_name(label), label)
        if normalize_name(label) == normalize_name("Link Portaria"):
            url = html.escape(val)
            link_text = "Abrir link"
            title = html.escape(val)
            lines.append(
                f"<tr><th style='text-align:left;padding-right:6px;white-space:nowrap'>"
                f"{html.escape(display_label)}</th>"
                f"<td style='white-space:nowrap'>"
                f"<a href=\"{url}\" target=\"_blank\" rel=\"noopener\" title=\"{title}\">"
                f"{link_text}</a></td></tr>"
            )
            continue
        lines.append(
            f"<tr><th style='text-align:left;padding-right:6px;white-space:nowrap'>"
            f"{html.escape(display_label)}</th>"
            f"<td style='white-space:nowrap'>{html.escape(val)}</td></tr>"
        )
    lines.append("</table>")
    return "".join(lines)


def _plane_icon_html(color: str, show_x: bool) -> str:
    plane = f"<i class='fa fa-plane plane' style='color:{color}'></i>"
    cross = ""
    if show_x:
        cross = "<i class='fa fa-times x' style='color:#D32F2F'></i>"
    return f"<div class='plane-icon'>{plane}{cross}</div>"


def _pick_color_and_x(row: pd.Series, cfg: DatasetConfig, col_map: dict[str, str]) -> Tuple[str, bool, bool]:
    night_col = _find_column(col_map, cfg.night_ops_field)
    use_alt = False
    if night_col:
        use_alt = _has_vfr_ifr(row.get(night_col))
    color = cfg.alt_color if use_alt else cfg.default_color

    show_x = False
    if cfg.interdicted_field and cfg.interdicted_token:
        interdicted_col = _find_column(col_map, cfg.interdicted_field)
        if interdicted_col:
            show_x = _has_token(row.get(interdicted_col), cfg.interdicted_token)
    return color, show_x, use_alt


def make_combined_map(
    datasets: List[DatasetLayer],
    out_path: Path,
    lat_col: str = "LAT_DEC",
    lon_col: str = "LON_DEC",
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    m = folium.Map(location=BRAZIL_CENTER, zoom_start=4, control_scale=True)
    m.get_root().header.add_child(Element(f"<link rel='stylesheet' href='{FA_CSS}'>"))
    m.get_root().header.add_child(Element(PLANE_CSS))
    m.get_root().header.add_child(Element(SIDEBAR_CSS))

    bounds: Optional[Tuple[float, float, float, float]] = None

    privados_group = folium.FeatureGroup(name="Privados")
    privados_ifr_group = folium.FeatureGroup(name="Privados com IFR")
    publicos_group = folium.FeatureGroup(name="Publicos")
    publicos_ifr_group = folium.FeatureGroup(name="Publicos com IFR")

    group_map = {
        "privados": (privados_group, privados_ifr_group),
        "publicos": (publicos_group, publicos_ifr_group),
    }

    for dataset in datasets:
        df_ok = dataset.df[dataset.df["STATUS"] == "ok"].copy()
        df_ok = df_ok.dropna(subset=[lat_col, lon_col])
        if df_ok.empty:
            logger.warning("No valid points for dataset '%s'", dataset.config.label)
            continue

        df_ok[lat_col] = df_ok[lat_col].astype(float)
        df_ok[lon_col] = df_ok[lon_col].astype(float)

        fields = _resolve_fields(df_ok, dataset.config.popup_fields)
        col_map = _normalize_map(df_ok)

        for _, row in df_ok.iterrows():
            color, show_x, is_ifr = _pick_color_and_x(row, dataset.config, col_map)
            popup_html = _build_popup(row, fields)
            icon = folium.DivIcon(
                html=_plane_icon_html(color, show_x),
                icon_size=(22, 22),
                icon_anchor=(11, 11),
            )
            if dataset.config.key in group_map:
                base_group, ifr_group = group_map[dataset.config.key]
                target_group = ifr_group if is_ifr else base_group
            else:
                target_group = publicos_group
            folium.Marker(
                location=[row[lat_col], row[lon_col]],
                popup=folium.Popup(popup_html, max_width=350),
                icon=icon,
            ).add_to(target_group)

            lat = float(row[lat_col])
            lon = float(row[lon_col])
            if bounds is None:
                bounds = (lat, lon, lat, lon)
            else:
                min_lat, min_lon, max_lat, max_lon = bounds
                bounds = (
                    min(min_lat, lat),
                    min(min_lon, lon),
                    max(max_lat, lat),
                    max(max_lon, lon),
                )

    if bounds:
        min_lat, min_lon, max_lat, max_lon = bounds
        m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
    else:
        logger.warning("No valid points to plot. Map will be centered in Brazil without markers.")

    for group in (privados_group, privados_ifr_group, publicos_group, publicos_ifr_group):
        group.add_to(m)

    privados_cfg = next((d.config for d in datasets if d.config.key == "privados"), None)
    publicos_cfg = next((d.config for d in datasets if d.config.key == "publicos"), None)

    priv_default = privados_cfg.default_color if privados_cfg else "#C46A4A"
    priv_alt = privados_cfg.alt_color if privados_cfg else "#00B6C7"
    pub_default = publicos_cfg.default_color if publicos_cfg else "#F4C430"
    pub_alt = publicos_cfg.alt_color if publicos_cfg else "#7E57C2"

    sidebar_html = f"""
<div id="filter-sidebar">
  <h4>Filtros</h4>
  <label><input type="checkbox" id="flt-privados" checked>
    <span class="swatch" style="background:{priv_default}"></span>
    Privados
  </label>
  <label><input type="checkbox" id="flt-privados-ifr" checked>
    <span class="swatch" style="background:{priv_alt}"></span>
    Privados com IFR
  </label>
  <label><input type="checkbox" id="flt-publicos" checked>
    <span class="swatch" style="background:{pub_default}"></span>
    Publicos
  </label>
  <label><input type="checkbox" id="flt-publicos-ifr" checked>
    <span class="swatch" style="background:{pub_alt}"></span>
    Publicos com IFR
  </label>
</div>
"""

    sidebar_script = f"""
(function() {{
  function initFilters() {{
    var map = {m.get_name()};
    var layers = {{
      privados: {privados_group.get_name()},
      privados_ifr: {privados_ifr_group.get_name()},
      publicos: {publicos_group.get_name()},
      publicos_ifr: {publicos_ifr_group.get_name()}
    }};
    function bind(id, layer) {{
      var cb = document.getElementById(id);
      if (!cb) return;
      cb.addEventListener('change', function() {{
        if (cb.checked) {{
          map.addLayer(layer);
        }} else {{
          map.removeLayer(layer);
        }}
      }});
    }}
    bind('flt-privados', layers.privados);
    bind('flt-privados-ifr', layers.privados_ifr);
    bind('flt-publicos', layers.publicos);
    bind('flt-publicos-ifr', layers.publicos_ifr);
  }}
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initFilters);
  }} else {{
    initFilters();
  }}
}})();
"""

    m.get_root().html.add_child(Element(sidebar_html))
    m.get_root().script.add_child(Element(sidebar_script))

    m.save(out_path)
    logger.info("Map saved: %s", out_path)
    return out_path
