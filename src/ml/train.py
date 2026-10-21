"""Train and tune heart-disease classifiers on the cleaned Cleveland dataset.

Run from the repository root:
    python -m src.ml.train

The held-out test set is not used for hyperparameter selection. All imputation,
encoding, and scaling are fitted inside cross-validation pipelines.
"""
from __future__ import annotations
from typing import Any

import argparse
import json
import logging
import pickle
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV, train_test_split, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier

LOGGER = logging.getLogger("heart_disease.train")
RANDOM_STATE = 42

FEATURE_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal",
]
NUMERIC_FEATURES = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL_FEATURES = [
    "sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"
]


def load_clean_dataset(path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """Load and validate the output of src.ml.preprocess."""
    if not path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {path.resolve()}. "
            "Run `python -m src.ml.preprocess` first."
        )
    df = pd.read_csv(path)
    missing = [c for c in FEATURE_COLUMNS + ["target"] if c not in df.columns]
    if missing:
        raise ValueError(f"Cleaned dataset is missing required columns: {missing}")

    X = df[FEATURE_COLUMNS].copy()
    y_numeric = pd.to_numeric(df["target"], errors="coerce")
    if y_numeric.isna().any():
        raise ValueError("Target contains missing or non-numeric values.")
    if not set(y_numeric.unique()).issubset({0, 1}):
        raise ValueError(f"Target must be binary 0/1; got {sorted(y_numeric.unique())}.")
    y = y_numeric.astype(int)

    # Convert expected features to numeric values; invalid values become NaN
    # and are handled by fold-fitted imputers. Completely empty features are rejected.
    for col in FEATURE_COLUMNS:
        X[col] = pd.to_numeric(X[col], errors="coerce")
        if X[col].notna().sum() == 0:
            raise ValueError(f"Feature {col!r} contains no usable numeric values.")

    if y.nunique() != 2:
        raise ValueError("Both target classes must be present.")
    if len(df) < 30:
        raise ValueError(f"Only {len(df)} rows found; too few for this training workflow.")

    return X, y


def make_preprocessor(scale_numeric: bool = True) -> ColumnTransformer:
    """Build preprocessing that is fitted only on the training fold."""
    numeric_steps: list[tuple[str, Any]] = [
    ("imputer", SimpleImputer(strategy="median"))
    ]

    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    numeric_pipe = Pipeline(numeric_steps)

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    return ColumnTransformer([
        ("numeric", numeric_pipe, NUMERIC_FEATURES),
        ("categorical", categorical_pipe, CATEGORICAL_FEATURES),
    ])


def build_searches() -> dict[str, tuple[Pipeline, dict[str, Any], int]]:
    """Return model pipelines, bounded parameter spaces, and iteration counts."""
    searches: dict[str, tuple[Pipeline, dict[str, Any], int]] = {}

    lr = Pipeline([
        ("preprocess", make_preprocessor(scale_numeric=True)),
        ("model", LogisticRegression(max_iter=3000, random_state=RANDOM_STATE)),
    ])
    searches["logistic_regression"] = (
        lr,
        {
            "model__C": np.logspace(-3, 2, 20),
            "model__class_weight": [None, "balanced"],
            "model__solver": ["lbfgs"],
        },
        20,
    )

    rf = Pipeline([
        ("preprocess", make_preprocessor(scale_numeric=False)),
        ("model", RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=1)),
    ])
    searches["random_forest"] = (
        rf,
        {
            "model__n_estimators": [100, 200, 300, 500],
            "model__max_depth": [None, 3, 5, 8, 12],
            "model__min_samples_split": [2, 4, 6, 10],
            "model__min_samples_leaf": [1, 2, 3, 5],
            "model__max_features": ["sqrt", 0.7, 1.0],
            "model__class_weight": [None, "balanced", "balanced_subsample"],
        },
        30,
    )

    try:
        from xgboost import XGBClassifier
        xgb = Pipeline([
            ("preprocess", make_preprocessor(scale_numeric=False)),
            ("model", XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=RANDOM_STATE,
                n_jobs=1,
                verbosity=0,
            )),
        ])
        searches["xgboost"] = (
            xgb,
            {
                "model__n_estimators": [100, 150, 250, 350],
                "model__max_depth": [2, 3, 4, 5],
                "model__learning_rate": [0.01, 0.03, 0.05, 0.1, 0.15],
                "model__subsample": [0.7, 0.85, 1.0],
                "model__colsample_bytree": [0.7, 0.85, 1.0],
                "model__min_child_weight": [1, 3, 5],
                "model__reg_lambda": [1, 3, 5, 10],
            },
            30,
        )
    except ImportError:
        LOGGER.warning("xgboost is not installed; skipping XGBoost. Install with `pip install xgboost`.")

    return searches


def evaluate_model(name: str, estimator: Any, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    """Evaluate a selected estimator once on the held-out test set."""
    predictions = estimator.predict(X_test)
    probabilities = estimator.predict_proba(X_test)[:, 1]
    return {
        "model": name,
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=[0, 1]).tolist(),
        "classification_report": classification_report(
            y_test, predictions, labels=[0, 1],
            target_names=["absence", "presence"], zero_division=0, output_dict=True
        ),
    }


def train(
    data_path: Path,
    output_dir: Path,
    cv_splits: int = 5,
    n_jobs: int = -1,
    refit_metric: str = "roc_auc",
) -> dict[str, Any]:
    """Tune candidate models, compare CV scores, evaluate the winner, and save artifacts."""
    X, y = load_clean_dataset(data_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )
    min_class_count = int(y_train.value_counts().min())
    actual_splits = min(cv_splits, min_class_count)
    if actual_splits < 2:
        raise ValueError("Not enough examples per class for stratified cross-validation.")
    cv = StratifiedKFold(n_splits=actual_splits, shuffle=True, random_state=RANDOM_STATE)

    cv_rows: list[dict[str, Any]] = []
    fitted_searches: dict[str, RandomizedSearchCV] = {}

    for name, (pipeline, param_distributions, n_iter) in build_searches().items():
        LOGGER.info("Tuning %s (%d randomized candidates, %d-fold CV)", name, n_iter, actual_splits)
        search = RandomizedSearchCV(
            estimator=pipeline,
            param_distributions=param_distributions,
            n_iter=n_iter,
            scoring={"roc_auc": "roc_auc", "recall": "recall", "f1": "f1"},
            refit=refit_metric,
            cv=cv,
            random_state=RANDOM_STATE,
            n_jobs=n_jobs,
            verbose=1,
            return_train_score=True,
            error_score="raise",
        )
        with warnings.catch_warnings():
            warnings.simplefilter("default")
            search.fit(X_train, y_train)

        fitted_searches[name] = search
        best_index = search.best_index_
        results = search.cv_results_
        cv_rows.append({
            "model": name,
            "best_cv_roc_auc": float(results["mean_test_roc_auc"][best_index]),
            "std_cv_roc_auc": float(results["std_test_roc_auc"][best_index]),
            "best_cv_recall": float(results["mean_test_recall"][best_index]),
            "std_cv_recall": float(results["std_test_recall"][best_index]),
            "best_cv_f1": float(results["mean_test_f1"][best_index]),
            "best_params": json.dumps(search.best_params_, default=str, sort_keys=True),
        })
        pd.DataFrame(search.cv_results_).to_csv(
            output_dir / f"{name}_cv_results.csv", index=False
        )

    cv_results = pd.DataFrame(cv_rows).sort_values(
        by=["best_cv_roc_auc", "best_cv_recall"], ascending=False
    ).reset_index(drop=True)
    cv_results.to_csv(output_dir / "tuning_results.csv", index=False)

    winner_name = str(cv_results.iloc[0]["model"])
    winner_search = fitted_searches[winner_name]
    winner = winner_search.best_estimator_

    test_metrics = evaluate_model(winner_name, winner, X_test, y_test)
    test_metrics["selection_metric"] = refit_metric
    test_metrics["best_params"] = winner_search.best_params_
    test_metrics["train_rows"] = int(len(X_train))
    test_metrics["test_rows"] = int(len(X_test))
    test_metrics["cv_splits"] = int(actual_splits)

    # Save the entire fitted pipeline so inference reproduces preprocessing.
    model_path = output_dir / "heart_model.pkl"
    with model_path.open("wb") as f:
        pickle.dump(winner, f)

    metrics_path = output_dir / "evaluation_metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(test_metrics, f, indent=2, default=str)

    best_params_path = output_dir / "best_params.json"
    with best_params_path.open("w", encoding="utf-8") as f:
        json.dump(winner_search.best_params_, f, indent=2, default=str)

    LOGGER.info("Selected model: %s", winner_name)
    LOGGER.info("Best CV ROC-AUC: %.4f", float(cv_results.iloc[0]["best_cv_roc_auc"]))
    LOGGER.info("Held-out test metrics: %s", {
        k: round(v, 4) for k, v in test_metrics.items()
        if isinstance(v, (int, float)) and k not in {"train_rows", "test_rows", "cv_splits"}
    })
    LOGGER.info("Saved fitted pipeline to %s", model_path.resolve())
    LOGGER.info("Saved tuning results to %s", (output_dir / "tuning_results.csv").resolve())
    LOGGER.info("Saved evaluation metrics to %s", metrics_path.resolve())

    return {"winner": winner_name, "cv_results": cv_results, "test_metrics": test_metrics}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed/cleveland_clean.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("models"))
    parser.add_argument("--cv-splits", type=int, default=5)
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument(
        "--refit-metric", choices=["roc_auc", "recall", "f1"], default="roc_auc",
        help="Metric used to select best hyperparameters within CV (default: roc_auc).",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    train(args.data, args.output_dir, args.cv_splits, args.n_jobs, args.refit_metric)


if __name__ == "__main__":
    main()
