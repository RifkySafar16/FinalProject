"""Load, validate, and clean the UCI Cleveland Heart Disease dataset.

This module performs deterministic data cleaning only. It does not fit imputers,
encoders, or scalers: any transformation that learns parameters from data should
be fitted on training folds inside the model-selection Pipeline to prevent data
leakage.

Default input:  data/raw/processed.cleveland.data
Default output: data/processed/cleveland_clean.csv

Run from the project root:
    python -m src.ml.preprocess
    python -m src.ml.preprocess --input path/to/processed.cleveland.data \
        --output data/processed/cleveland_clean.csv
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH: Final[Path] = PROJECT_ROOT / "data" / "raw" / "processed.cleveland.data"
DEFAULT_OUTPUT_PATH: Final[Path] = PROJECT_ROOT / "data" / "processed" / "cleveland_clean.csv"

# The original processed Cleveland file has no header and contains 13 features
# followed by the original disease-severity target (0 through 4).
FEATURE_COLUMNS: Final[list[str]] = [
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
]
ORIGINAL_TARGET_COLUMN: Final[str] = "target_original"
BINARY_TARGET_COLUMN: Final[str] = "target"
RAW_COLUMNS: Final[list[str]] = FEATURE_COLUMNS + [ORIGINAL_TARGET_COLUMN]

# These fields are discrete categories even though the source stores them as
# numbers. Treating them as categories later avoids implying false ordinality.
CATEGORICAL_FEATURES: Final[list[str]] = [
    "sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"
]
CONTINUOUS_FEATURES: Final[list[str]] = [
    "age", "trestbps", "chol", "thalach", "oldpeak"
]

ALLOWED_CATEGORIES: Final[dict[str, set[int]]] = {
    "sex": {0, 1},
    "cp": {1, 2, 3, 4},
    "fbs": {0, 1},
    "restecg": {0, 1, 2},
    "exang": {0, 1},
    "slope": {1, 2, 3},
    "ca": {0, 1, 2, 3},
    "thal": {3, 6, 7},
}

# Broad sanity bounds catch obvious data corruption without pretending to be
# clinical diagnostic thresholds. Missing values are allowed for features.
NUMERIC_BOUNDS: Final[dict[str, tuple[float, float]]] = {
    "age": (0, 120),
    "trestbps": (0, 400),
    "chol": (0, 1000),
    "thalach": (0, 300),
    "oldpeak": (-10, 20),
}


class DatasetValidationError(ValueError):
    """Raised when the source dataset violates the expected schema or values."""


def load_raw_dataset(input_path: str | Path = DEFAULT_INPUT_PATH) -> pd.DataFrame:
    """Load the headerless Cleveland file and convert missing markers to NA.

    Args:
        input_path: Path to the original processed.cleveland.data file.

    Returns:
        A DataFrame with the expected 14 named columns and numeric values.

    Raises:
        FileNotFoundError: If the input file does not exist.
        DatasetValidationError: If the file has an unexpected number of columns
            or contains non-numeric non-missing values.
    """
    path = Path(input_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Cleveland dataset not found: {path.resolve()}")

    # Read as strings first so malformed text can be distinguished from an
    # intentionally missing marker rather than silently coerced to NA.
    raw = pd.read_csv(
        path,
        header=None,
        dtype=str,
        skipinitialspace=True,
        keep_default_na=False,
    )
    if raw.shape[1] != len(RAW_COLUMNS):
        raise DatasetValidationError(
            f"Expected {len(RAW_COLUMNS)} columns, found {raw.shape[1]}. "
            "Check that the input is the processed Cleveland dataset."
        )
    if raw.empty:
        raise DatasetValidationError("The input dataset contains no rows.")

    raw.columns = RAW_COLUMNS
    for column in RAW_COLUMNS:
        values = raw[column].astype("string").str.strip()
        values = values.replace({"?": pd.NA, "": pd.NA})
        numeric = pd.to_numeric(values, errors="coerce")
        invalid = values.notna() & numeric.isna()
        if invalid.any():
            examples = values[invalid].drop_duplicates().head(5).tolist()
            raise DatasetValidationError(
                f"Column '{column}' contains non-numeric values: {examples}"
            )
        raw[column] = numeric

    return raw


def validate_dataset(df: pd.DataFrame) -> None:
    """Validate schema, target values, categories, and broad numeric bounds.

    Feature missing values are permitted and reported by ``clean_dataset``;
    target missing values are not permitted because they cannot be supervised.
    """
    missing_columns = [column for column in RAW_COLUMNS if column not in df.columns]
    extra_columns = [column for column in df.columns if column not in RAW_COLUMNS]
    if missing_columns or extra_columns:
        raise DatasetValidationError(
            f"Schema mismatch. Missing columns: {missing_columns}; "
            f"unexpected columns: {extra_columns}."
        )
    if df.empty:
        raise DatasetValidationError("The dataset contains no rows.")

    target = df[ORIGINAL_TARGET_COLUMN]
    if target.isna().any():
        rows = (target[target.isna()].index + 1).tolist()[:10]
        raise DatasetValidationError(
            "Target values are missing; cannot train on these rows. "
            f"Example source row numbers (1-based): {rows}"
        )
    if not target.isin([0, 1, 2, 3, 4]).all():
        bad = sorted(target[~target.isin([0, 1, 2, 3, 4])].unique().tolist())
        raise DatasetValidationError(
            f"Original target must contain only integer values 0-4; found {bad}."
        )
    if not (target % 1 == 0).all():
        raise DatasetValidationError("Original target values must be integers.")

    for column, allowed in ALLOWED_CATEGORIES.items():
        observed = df[column].dropna()
        invalid = ~observed.isin(allowed)
        if invalid.any():
            bad = sorted(observed[invalid].unique().tolist())
            raise DatasetValidationError(
                f"Column '{column}' has unexpected category value(s) {bad}; "
                f"expected values from {sorted(allowed)}."
            )
        non_missing = observed.dropna()
        if ((non_missing % 1) != 0).any():
            raise DatasetValidationError(f"Categorical column '{column}' must use integer codes.")

    for column, (minimum, maximum) in NUMERIC_BOUNDS.items():
        observed = df[column].dropna()
        invalid = (observed < minimum) | (observed > maximum)
        if invalid.any():
            bad = observed[invalid].head(5).tolist()
            raise DatasetValidationError(
                f"Column '{column}' contains values outside the broad sanity "
                f"bounds [{minimum}, {maximum}]: {bad}"
            )


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and return a clean dataset with a binary target.

    Missing feature values are retained as pandas NA/NaN and reported, rather
    than imputed globally. The training Pipeline must fit imputers using only
    its training folds. ``target_original`` preserves severity 0-4; ``target``
    maps 0 -> 0 (absence) and 1-4 -> 1 (presence).
    """
    cleaned = df.copy()
    validate_dataset(cleaned)

    # Ensure predictable numeric dtypes. Nullable Float64 preserves missingness
    # and avoids converting an entire column to strings.
    for column in RAW_COLUMNS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="raise").astype("Float64")

    # The original target is semantically an integer, not a continuous value.
    cleaned[ORIGINAL_TARGET_COLUMN] = cleaned[ORIGINAL_TARGET_COLUMN].astype("Int64")
    cleaned[BINARY_TARGET_COLUMN] = (
        cleaned[ORIGINAL_TARGET_COLUMN].gt(0).astype("int8")
    )

    # Stable column order: features, original target for traceability, binary target.
    return cleaned[FEATURE_COLUMNS + [ORIGINAL_TARGET_COLUMN, BINARY_TARGET_COLUMN]]


def save_clean_dataset(
    df: pd.DataFrame,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
) -> Path:
    """Save the cleaned dataset to CSV, creating parent directories as needed."""
    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, na_rep="")
    return path.resolve()


def preprocess_dataset(
    input_path: str | Path = DEFAULT_INPUT_PATH,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
) -> pd.DataFrame:
    """Run the complete load -> validate -> clean -> save workflow."""
    raw = load_raw_dataset(input_path)
    cleaned = clean_dataset(raw)
    saved_path = save_clean_dataset(cleaned, output_path)

    missing_counts = cleaned[FEATURE_COLUMNS].isna().sum()
    missing_counts = missing_counts[missing_counts > 0]
    LOGGER.info("Loaded %d rows and %d columns.", len(cleaned), len(FEATURE_COLUMNS))
    if missing_counts.empty:
        LOGGER.info("No missing feature values found.")
    else:
        LOGGER.warning(
            "Missing feature values retained for fold-safe imputation:\n%s",
            missing_counts.to_string(),
        )
    LOGGER.info(
        "Target distribution (0 = absence, 1 = presence): %s",
        cleaned[BINARY_TARGET_COLUMN].value_counts().sort_index().to_dict(),
    )
    LOGGER.info("Cleaned dataset saved to %s", saved_path)
    return cleaned


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and clean the UCI Cleveland Heart Disease dataset."
    )
    parser.add_argument(
        "--input", type=Path, default=DEFAULT_INPUT_PATH,
        help=f"Input dataset path (default: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT_PATH,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument("--verbose", action="store_true", help="Show informational logs.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    try:
        cleaned = preprocess_dataset(args.input, args.output)
    except (FileNotFoundError, DatasetValidationError, pd.errors.ParserError) as exc:
        raise SystemExit(f"Preprocessing failed: {exc}") from exc

    print(f"Rows: {len(cleaned)}")
    print(f"Columns: {len(cleaned.columns)}")
    print(f"Saved: {Path(args.output).expanduser().resolve()}")
    print("Binary target counts:")
    print(cleaned[BINARY_TARGET_COLUMN].value_counts().sort_index().to_string())
    print("Missing feature values:")
    print(cleaned[FEATURE_COLUMNS].isna().sum().to_string())


if __name__ == "__main__":
    main()
