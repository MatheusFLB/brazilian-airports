from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List
import logging
import math
import re

logger = logging.getLogger(__name__)

LAT_MIN, LAT_MAX = -35.0, 6.0
LON_MIN, LON_MAX = -75.0, -30.0
LAT_CENTER = (LAT_MIN + LAT_MAX) / 2.0
LON_CENTER = (LON_MIN + LON_MAX) / 2.0


@dataclass(frozen=True)
class CleanResult:
    lat: Optional[float]
    lon: Optional[float]
    status: str
    swapped: bool = False
    scale_lat: int = 0
    scale_lon: int = 0


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip() == ""


def parse_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    s = str(value).strip()
    if not s:
        return None

    # Accept comma as decimal separator and strip internal whitespace
    s = re.sub(r"[\s\u00A0]+", "", s)
    s = s.replace(",", ".")

    if not re.fullmatch(r"[-+]?\d*\.?\d+", s):
        m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
        if not m:
            return None
        s = m.group(0)

    try:
        return float(s)
    except ValueError:
        return None


def scaled_candidates(value: float) -> List[Tuple[float, int]]:
    return [(value / (10 ** p), p) for p in range(0, 7)]


def in_range(value: float, vmin: float, vmax: float) -> bool:
    return vmin <= value <= vmax


def clean_lat_lon(raw_lat: object, raw_lon: object) -> CleanResult:
    lat_missing = _is_blank(raw_lat)
    lon_missing = _is_blank(raw_lon)

    lat_val = parse_float(raw_lat)
    lon_val = parse_float(raw_lon)

    if lat_missing and lon_missing:
        return CleanResult(None, None, "missing_lat_lon")
    if lat_missing:
        return CleanResult(None, None, "missing_lat")
    if lon_missing:
        return CleanResult(None, None, "missing_lon")

    if lat_val is None:
        return CleanResult(None, None, "invalid_lat")
    if lon_val is None:
        return CleanResult(None, None, "invalid_lon")

    best: Optional[Tuple[int, float, bool, float, float, int, int]] = None

    # Try normal orientation first, then swapped, and fix by scaling if needed
    for swapped in (False, True):
        lat_raw, lon_raw = (lat_val, lon_val) if not swapped else (lon_val, lat_val)
        for lat_candidate, p_lat in scaled_candidates(lat_raw):
            if not in_range(lat_candidate, LAT_MIN, LAT_MAX):
                continue
            for lon_candidate, p_lon in scaled_candidates(lon_raw):
                if not in_range(lon_candidate, LON_MIN, LON_MAX):
                    continue
                score = p_lat + p_lon + (1 if swapped else 0)
                dist = abs(lat_candidate - LAT_CENTER) + abs(lon_candidate - LON_CENTER)
                candidate = (score, dist, swapped, lat_candidate, lon_candidate, p_lat, p_lon)
                if best is None or candidate < best:
                    best = candidate

    if best is None:
        return CleanResult(None, None, "out_of_range")

    _, _, swapped, lat_best, lon_best, p_lat, p_lon = best
    return CleanResult(lat_best, lon_best, "ok", swapped=swapped, scale_lat=p_lat, scale_lon=p_lon)


def resolve_lat_lon_columns(df, lat_col: Optional[str] = None, lon_col: Optional[str] = None) -> Tuple[str, str]:
    if lat_col and lon_col:
        return lat_col, lon_col

    def normalize(name: str) -> str:
        return re.sub(r"[\s_\-\.]+", "", name.strip().lower())

    name_map = {normalize(c): c for c in df.columns}
    lat_candidates = ["latgeopoint", "latitude", "lat", "latgeo"]
    lon_candidates = ["longeopoint", "longgeopoint", "longitude", "lon", "lng", "long", "longeo"]

    if not lat_col:
        for c in lat_candidates:
            if c in name_map:
                lat_col = name_map[c]
                break
    if not lon_col:
        for c in lon_candidates:
            if c in name_map:
                lon_col = name_map[c]
                break

    if not lat_col or not lon_col:
        raise ValueError("Could not find latitude/longitude columns. Use --lat-col and --lon-col.")
    return lat_col, lon_col


def clean_dataframe(df, lat_col: str, lon_col: str):
    results: List[CleanResult] = []
    lat_dec: List[Optional[float]] = []
    lon_dec: List[Optional[float]] = []
    status: List[str] = []

    for _, row in df.iterrows():
        res = clean_lat_lon(row.get(lat_col), row.get(lon_col))
        results.append(res)
        lat_dec.append(res.lat)
        lon_dec.append(res.lon)
        status.append(res.status)

    out = df.copy()
    out["LAT_DEC"] = lat_dec
    out["LON_DEC"] = lon_dec
    out["STATUS"] = status
    return out, results
