"""Joining per-applicant feature tables onto the application table.

The application table has exactly one row per applicant, and so must the result. A join that
silently adds rows (because a child table was not aggregated) or drops rows (because of an
inner join) still runs without an error, and the model then trains on the wrong data. The
functions here make that mistake fail loudly instead.
"""

from __future__ import annotations

import pandas as pd

# PROVIDED: a feature whose name ends with this is a count, so "no records" means 0.
COUNT_SUFFIX = "_COUNT"



def assert_one_row_per_applicant(
    df: pd.DataFrame, expected_ids: pd.Series, id_col: str = "SK_ID_CURR"
) -> None:
    """Raise a ValueError unless ``df`` has exactly one row for each id in ``expected_ids``.

    Args:
        df: The table to check (for example the joined feature table).
        expected_ids: The applicant ids that must each appear exactly once.
        id_col: The applicant id column.

    Raises:
        ValueError: if the row count differs, any id appears twice, or the set of ids is not
            exactly ``expected_ids``. The message must say which problem it found and give
            the numbers (for example "24,395 rows for 5,000 applicants").

    Hints:
        - Equal row counts are not enough on their own: one duplicated id plus one missing id
          keeps the count the same.
    """
    expected_count = len(expected_ids)
    actual_count = len(df)

    if actual_count != expected_count:
        raise ValueError(
            f"{actual_count:,} rows for {expected_count:,} applicants"
        )

    if id_col not in df.columns:
        raise ValueError(f"Missing applicant id column: {id_col}")

    if df[id_col].duplicated().any():
        raise ValueError(f"Duplicate applicant IDs in {actual_count:,} rows")

    expected_set = set(expected_ids)
    actual_set = set(df[id_col])

    if actual_set != expected_set:
        missing = len(expected_set - actual_set)
        unexpected = len(actual_set - expected_set)
        raise ValueError(
            f"Applicant IDs do not match: {missing:,} missing, "
            f"{unexpected:,} unexpected"
        )



def join_features(
    app: pd.DataFrame, feature_tables: dict[str, pd.DataFrame], id_col: str = "SK_ID_CURR"
) -> pd.DataFrame:
    """Left-join each per-applicant feature table onto the application table.

    Args:
        app: The application table, one row per applicant.
        feature_tables: Table name -> aggregated table (the output of an ``aggregate_*``
            function), for example ``{"bureau": aggregate_bureau(bureau)}``.
        id_col: The applicant id column.

    Returns:
        A new DataFrame with the same rows in the same order as ``app``, every column of
        ``app`` unchanged, plus every feature column. For applicants missing from a feature
        table, columns ending in ``_COUNT`` are 0 and every other new column is NaN.

    Raises:
        ValueError: before joining, if a feature table has the same id twice (name the table:
            it was probably not aggregated), or if a feature column name is already taken.
            After joining, through ``assert_one_row_per_applicant``.

    Hints:
        - Which ``how=`` keeps every applicant, including the ones with no history at all?
        - ``pd.merge`` has a ``validate=`` argument that can raise on duplicate keys for you.
        - Why 0 for counts but NaN for averages? Be ready to explain it at the checkpoint.
    """
    assert_one_row_per_applicant(app, app[id_col], id_col)

    result = app.copy()

    for table_name, features in feature_tables.items():
        if id_col not in features.columns:
            raise ValueError(f"{table_name} is missing {id_col}")

        if features[id_col].duplicated().any():
            raise ValueError(
                f"{table_name} has duplicate applicant IDs; "
                "the table may not have been aggregated"
            )

        feature_columns = [col for col in features.columns if col != id_col]
        conflicts = [col for col in feature_columns if col in result.columns]

        if conflicts:
            raise ValueError(
                f"{table_name} has feature columns already present: {conflicts}"
            )

        result = result.merge(
            features,
            on=id_col,
            how="left",
            sort=False,
            validate="one_to_one",
        )

        count_columns = [
            col for col in feature_columns if col.endswith(COUNT_SUFFIX)
        ]
        result[count_columns] = result[count_columns].fillna(0)

    assert_one_row_per_applicant(result, app[id_col], id_col)

    return result
