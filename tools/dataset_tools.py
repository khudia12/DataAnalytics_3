import pandas as pd
import numpy as np


def load_dataset(file_path: str):
    if file_path.endswith(".csv"):
        return pd.read_csv(file_path)

    if file_path.endswith(".xlsx"):
        return pd.read_excel(file_path)

    raise ValueError("Поддерживаются только CSV и XLSX")


def get_dataset_schema(df):
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict()
    }


def sample_dataset(df, rows: int = 5):
    return df.sample(
        min(rows, len(df)),
        random_state=42
    ).to_dict("records")


def get_missing_values(df):
    missing = df.isna().sum()

    return {
        col: {
            "count": int(count),
            "percent": round(
                count / len(df) * 100,
                2
            )
        }
        for col, count in missing.items()
    }


def get_numeric_summary(df):
    numeric_df = df.select_dtypes(include=["number"])

    if numeric_df.empty:
        return {}

    return numeric_df.describe().to_dict()


def get_categorical_summary(df):
    result = {}

    categorical = df.select_dtypes(
        include=["object", "category"]
    )

    for col in categorical.columns:
        result[col] = {
            "unique": int(df[col].nunique()),
            "top_values":
                df[col]
                .value_counts()
                .head(10)
                .to_dict()
        }

    return result


def get_correlations(df):
    numeric = df.select_dtypes(include=["number"])

    if numeric.shape[1] < 2:
        return {}

    corr = numeric.corr()

    pairs = []

    for col1 in corr.columns:
        for col2 in corr.columns:
            if col1 >= col2:
                continue

            value = corr.loc[col1, col2]

            if abs(value) >= 0.5:
                pairs.append({
                    "column_1": col1,
                    "column_2": col2,
                    "correlation": round(float(value), 3)
                })

    return sorted(
        pairs,
        key=lambda x: abs(x["correlation"]),
        reverse=True
    )


def detect_outliers(df):
    result = {}

    numeric = df.select_dtypes(include=["number"])

    for col in numeric.columns:

        q1 = numeric[col].quantile(0.25)
        q3 = numeric[col].quantile(0.75)

        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        count = ((numeric[col] < lower) | (numeric[col] > upper)).sum()

        result[col] = int(count)

    return result