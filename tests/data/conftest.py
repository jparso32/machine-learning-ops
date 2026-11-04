"""Load the project's feature table for the Week 4 data checks."""

import pandas as pd
import pytest

from src.experiment import feature_table_path, load_week3_config


@pytest.fixture(scope="session")
def features() -> pd.DataFrame:
    path = feature_table_path(load_week3_config())
    if not path.is_file():
        pytest.skip(f"feature table missing: {path}")
    return pd.read_parquet(path)
