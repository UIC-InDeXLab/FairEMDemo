import os

import pandas as pd


def load_dataset_as_df(dataset_id) -> pd.DataFrame:
    return pd.read_csv(os.path.join(os.getenv("DATASET_UPLOAD_PATH", "./datasets"), f"{dataset_id}.csv"))


def get_ds_path(dataset_id: str):
    return os.path.join(os.getenv("DATASET_UPLOAD_PATH", "./datasets"), f"{dataset_id}.csv")