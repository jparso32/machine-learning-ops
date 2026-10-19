"""Loading the sampled tables and the fixed train/validation split."""

from __future__ import annotations

from typing import Any

import pandas as pd


# PROVIDED
def load_table(name: str, config: dict[str, Any]) -> pd.DataFrame:
    """Read one sampled table from data/sample/ with pandas' default type inference.

    Args:
        name: A table name from ``config["tables"]``, for example ``"bureau"``.
        config: The loaded config (see ``src.utils.load_config``).

    Returns:
        The table as a DataFrame.
    """
    if name not in config["tables"]:
        raise KeyError(f"Unknown table '{name}'. Known tables: {list(config['tables'])}")
    path = config["paths"]["sample_dir"] / config["tables"][name]
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run `python run.py sample` first.")
    return pd.read_csv(path)


# PROVIDED
def load_application(config: dict[str, Any]) -> pd.DataFrame:
    """Return the sampled application_train table (one row per applicant)."""
    return load_table("application_train", config)


# TODO(student)
def load_split(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the sampled application table into train and validation rows.

    Use the fixed split in ``config["paths"]["split_file"]`` (columns SK_ID_CURR and
    ``split``, where ``split`` is ``"train"`` or ``"valid"``). Never create your own split.

    Args:
        config: The loaded config.

    Returns:
        ``(train_df, valid_df)``: application rows, with all their original columns,
        for the train ids and the valid ids. Each has a fresh 0..n-1 index.

    Raises:
        ValueError: if the split file lists an id twice, uses a split value other than
            train/valid, or does not match the applicants in the sample one-to-one.

    Hints:
        - Read the id column so it has the same type as the id column in the application table.
        - Every applicant must land in exactly one of the two frames: no overlap, none missing.
        - Check the split file before you trust it, and fail loudly if it looks wrong.
        - Use ``config["id_col"]`` instead of typing the column name.
    """
    app = load_application(config)
    id_col = config["id_col"]
    split_file = config["paths"]["split_file"]

    split_df = pd.read_csv(split_file, dtype={id_col: app[id_col].dtype})

    if split_df[id_col].duplicated().any():
        raise ValueError("Split file contains duplicate applicant IDs.")

    if not split_df["split"].isin(["train", "valid"]).all():
        raise ValueError("Split file contains invalid split values.")

    if (
        len(split_df) != len(app)
        or set(split_df[id_col]) != set(app[id_col])
    ):
        raise ValueError("Split file IDs do not match the application sample one-to-one.")

    split_ids = split_df.set_index(id_col)["split"]
    app_splits = app[id_col].map(split_ids)

    train_df = app.loc[app_splits == "train"].reset_index(drop=True)
    valid_df = app.loc[app_splits == "valid"].reset_index(drop=True)

    return train_df, valid_df
