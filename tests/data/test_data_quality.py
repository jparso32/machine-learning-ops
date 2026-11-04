"""Check the Week 4 assumptions on the generated feature table."""

import pandas as pd
from pandas.api.types import is_numeric_dtype

REQUIRED_NUMERIC = ("SK_ID_CURR", "TARGET", "AMT_INCOME_TOTAL", "AMT_CREDIT",
                    "DAYS_BIRTH", "EXT_SOURCE_2")
REQUIRED_COMPLETE = ("AMT_INCOME_TOTAL", "AMT_CREDIT", "DAYS_BIRTH", "TARGET")


def test_one_row_per_applicant(features: pd.DataFrame) -> None:
    ids = features["SK_ID_CURR"]
    assert ids.notna().all(), "Some applicant IDs are missing"
    assert ids.is_unique, "The feature table contains duplicate applicant IDs"


def test_schema(features: pd.DataFrame) -> None:
    missing = set(REQUIRED_NUMERIC) - set(features.columns)
    assert not missing, f"Missing columns: {sorted(missing)}"
    nonnumeric = [name for name in REQUIRED_NUMERIC if not is_numeric_dtype(features[name])]
    assert not nonnumeric, f"Expected numeric columns: {nonnumeric}"
    assert features["TARGET"].isin([0, 1]).all(), "TARGET must contain only 0 or 1"


def test_value_ranges(features: pd.DataFrame) -> None:
    age_years = -features["DAYS_BIRTH"] / 365.25
    assert age_years.between(18, 70).all(), "Applicant age is outside 18–70 years"
    assert features["AMT_INCOME_TOTAL"].gt(0).all(), "Applicant income must be positive"
    for name in features.filter(regex=r"_(RATE|SHARE)$"):
        assert features[name].dropna().between(0, 1).all(), f"{name} is outside [0, 1]"


def test_missing_values(features: pd.DataFrame) -> None:
    missing = features[list(REQUIRED_COMPLETE)].isna().any()
    assert not missing.any(), f"Missing values in {missing[missing].index.tolist()}"
    external_missing = features["EXT_SOURCE_2"].isna().mean()
    assert external_missing < 0.01, f"EXT_SOURCE_2 missing rate is {external_missing:.2%}"
    empty = features.isna().all()
    assert not empty.any(), f"Entirely missing columns: {empty[empty].index.tolist()}"


def test_default_rate(features: pd.DataFrame) -> None:
    rate = features["TARGET"].mean()
    assert 0.06 <= rate <= 0.10, f"Default rate {rate:.2%} is outside 6%–10%"
