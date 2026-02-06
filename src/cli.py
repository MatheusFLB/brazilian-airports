from __future__ import annotations

import argparse
import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd

from .clean_coords import clean_dataframe, resolve_lat_lon_columns
from .convert_to_shapefile import convert_to_shapefile
from .datasets import DatasetConfig, match_dataset_config
from .make_map import DatasetLayer, make_combined_map

logger = logging.getLogger(__name__)


def sniff_sep(path: Path) -> str:
    sample = path.read_text(encoding="utf-8", errors="ignore")[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";\t,|")
        return dialect.delimiter
    except csv.Error:
        return ";"


def detect_header_index(text: str, sep: str) -> int:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if "atualizado em" in lower and sep not in line:
            continue
        if sep in line:
            return idx
    return 0


def detect_encoding(path: Path, preferred: Optional[str]) -> str:
    data = path.read_bytes()[:10000]
    utf_enc: Optional[str] = None
    for enc in ("utf-8-sig", "utf-8"):
        try:
            data.decode(enc)
            utf_enc = enc
            break
        except UnicodeDecodeError:
            continue

    if preferred:
        pref = preferred.strip()
        pref_norm = re.sub(r"[^a-zA-Z0-9_\-]+", "", pref).lower()
        if pref_norm in ("utf8", "utf-8"):
            return "utf-8"
        if pref_norm in ("utf8sig", "utf-8-sig"):
            return "utf-8-sig"

        if utf_enc:
            # If UTF-8 decodes cleanly, prefer it even when user forces latin1/cp1252.
            # This prevents mojibake in Brazilian government datasets that are UTF-8.
            return utf_enc

        return pref

    if utf_enc:
        return utf_enc

    return "cp1252"


def read_csv_guess(path: Path, sep: Optional[str], encoding: Optional[str]) -> pd.DataFrame:
    if sep is None:
        sep = sniff_sep(path)

    enc = detect_encoding(path, encoding)
    try:
        sample = path.read_text(encoding=enc, errors="ignore")[:10000]
        skiprows = detect_header_index(sample, sep)
        df = pd.read_csv(
            path,
            sep=sep,
            encoding=enc,
            dtype=str,
            keep_default_na=False,
            skiprows=skiprows,
        )
        logger.info("CSV loaded with sep='%s' encoding='%s'", sep, enc)
        return df
    except UnicodeDecodeError:
        fallback = "latin1"
        logger.warning("Encoding '%s' failed for %s. Falling back to '%s'.", enc, path.name, fallback)
        sample = path.read_text(encoding=fallback, errors="ignore")[:10000]
        skiprows = detect_header_index(sample, sep)
        df = pd.read_csv(
            path,
            sep=sep,
            encoding=fallback,
            dtype=str,
            keep_default_na=False,
            skiprows=skiprows,
        )
        logger.info("CSV loaded with sep='%s' encoding='%s'", sep, fallback)
        return df


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean airport coordinates and generate outputs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--in", dest="input_path", help="Input CSV path")
    group.add_argument("--in-dir", dest="input_dir", help="Directory with CSV files")
    parser.add_argument("--outdir", required=True, help="Output directory")
    parser.add_argument("--sep", default=None, help="CSV separator (default: sniff or ';')")
    parser.add_argument("--encoding", default=None, help="CSV encoding (default: utf-8, fallback latin1)")
    parser.add_argument("--lat-col", default=None, help="Latitude column name")
    parser.add_argument("--lon-col", default=None, help="Longitude column name")
    parser.add_argument("--log-level", default="INFO", help="Logging level (INFO, DEBUG, etc)")
    return parser


@dataclass(frozen=True)
class DatasetResult:
    config: DatasetConfig
    df: pd.DataFrame


def _generic_config_for_path(path: Path) -> DatasetConfig:
    label = path.stem
    return DatasetConfig(
        key=label.lower(),
        label=label,
        filename_hints=[],
        popup_fields=["UF"],
        default_color="#4C78A8",
        alt_color="#4C78A8",
        night_ops_field="Operação Noturna",
    )


def _collect_inputs(args: argparse.Namespace) -> List[Tuple[Path, Optional[DatasetConfig]]]:
    if args.input_dir:
        input_dir = Path(args.input_dir)
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        files = sorted(input_dir.glob("*.csv"))
        result: List[Tuple[Path, Optional[DatasetConfig]]] = []
        for path in files:
            cfg = match_dataset_config(path)
            if not cfg:
                logger.warning("Skipping unknown dataset file: %s", path.name)
                continue
            result.append((path, cfg))
        return result

    path = Path(args.input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    return [(path, match_dataset_config(path))]


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s - %(message)s",
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        inputs = _collect_inputs(args)
        if not inputs:
            logger.error("No input CSV files found to process.")
            return 1

        dataset_results: List[DatasetResult] = []

        for input_path, cfg in inputs:
            use_sep = args.sep if args.input_path else None
            df = read_csv_guess(input_path, use_sep, args.encoding)
            lat_col, lon_col = resolve_lat_lon_columns(df, args.lat_col, args.lon_col)
            logger.info("Using columns for %s: lat='%s' lon='%s'", input_path.name, lat_col, lon_col)

            clean_df, results = clean_dataframe(df, lat_col, lon_col)

            total = len(results)
            ok_count = sum(r.status == "ok" for r in results)
            swapped_count = sum((r.status == "ok" and r.swapped) for r in results)
            scaled_count = sum((r.status == "ok" and (r.scale_lat > 0 or r.scale_lon > 0)) for r in results)

            logger.info("Total records (%s): %d", input_path.name, total)
            logger.info("Valid records (%s): %d", input_path.name, ok_count)
            logger.info("Swapped pairs (%s): %d", input_path.name, swapped_count)
            logger.info("Scaled coords (%s): %d", input_path.name, scaled_count)

            clean_csv_path = outdir / f"{input_path.stem}_clean.csv"
            clean_df.to_csv(clean_csv_path, index=False)
            logger.info("Clean CSV saved: %s", clean_csv_path)

            if ok_count == 0:
                logger.error("No valid records in %s. Skipping shapefile and map layer.", input_path.name)
                continue

            convert_to_shapefile(clean_df, outdir / f"{input_path.stem}.shp")

            if cfg is None:
                cfg = _generic_config_for_path(input_path)
                logger.warning("Unknown dataset for %s. Using generic popup fields.", input_path.name)

            dataset_results.append(DatasetResult(cfg, clean_df))

        if not dataset_results:
            logger.error("No datasets with valid records. Skipping map.")
            return 2

        layers = [DatasetLayer(r.config, r.df) for r in dataset_results]
        make_combined_map(layers, outdir / "airports_map.html")
        return 0

    except Exception as exc:
        logger.exception("Error: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
