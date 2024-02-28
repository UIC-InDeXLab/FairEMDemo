import os.path
from abc import ABC, abstractmethod
from pathlib import Path

import copy
import pandas as pd


def split(df, train_ratio=0.7, val_ratio=0.15) -> dict:
    train_size = int(len(df) * train_ratio)
    val_size = int(len(df) * val_ratio)

    return {"train": df[:train_size],
            "valid": df[train_size:train_size + val_size],
            "test": df[train_size + val_size:]
            }


class Convertor(ABC):

    def __init__(self, dataset_id, splits):
        self.dataset_id = dataset_id
        self.__splits__ = splits
        self.create_dir()

    def create_dir(self):
        Path(self.output_dir_name).mkdir(parents=True, exist_ok=True)

    def save_df_as_csv(self, df, name: str):
        df.to_csv(os.path.join(self.output_dir_name, f"{name}.csv"), index=False)

    @abstractmethod
    def convert(self):
        pass

    @staticmethod
    @abstractmethod
    def dir_name() -> str:
        pass

    @property
    def output_dir_name(self) -> str:
        return os.path.join(os.getenv("PREPROCESS_PATH", "./preprocess"), self.dir_name(), self.dataset_id)

    @property
    def splits(self):
        return copy.deepcopy(self.__splits__)


class StandardConvertor(Convertor):

    @staticmethod
    def dir_name() -> str:
        return "standard"

    def convert(self):
        for name, df in self.splits.items():
            self.save_df_as_csv(df, name)


class DittoConvertor(Convertor):

    @staticmethod
    def dir_name() -> str:
        return "ditto"

    def convert(self):
        for name, df in self.splits.items():
            schema = list(df.columns)[0:]
            schema = [x for x in schema if x.lower() != "id"]
            ditto_schema = [x.replace("left_", "").replace("right_", "") for x in schema]
            with open(os.path.join(self.output_dir_name, f"{name}.txt"), "w+") as res_file:
                for idx, row in df.iterrows():
                    label = row["label"]
                    ditto_row = ""
                    for i in range(len(schema)):
                        if ditto_schema[i].lower() == "label":
                            continue
                        ditto_row += "COL " + ditto_schema[i] + " "
                        ditto_row += "VAL " + str(row[schema[i]]) + " "
                        if "left_" in schema[i] and "right_" in schema[i + 1]:
                            ditto_row += "\t"
                    ditto_row += "\t" + str(label)
                    res_file.write(ditto_row)
                    res_file.write("\n")


class GNEMConvertor(Convertor):
    @staticmethod
    def dir_name() -> str:
        return "gnem"

    def convert(self):
        merged_df = pd.concat(self.splits, axis=0, ignore_index=True)

        left_df = pd.DataFrame()
        right_df = pd.DataFrame()

        for column in merged_df.columns:
            if 'left' in column:
                left_df[str(column).replace("left_", "")] = merged_df[column]
            elif 'right' in column:
                right_df[str(column).replace("right_", "")] = merged_df[column]

        self.save_df_as_csv(left_df, "tableA")
        self.save_df_as_csv(right_df, "tableB")

        for name, df in self.splits.items():
            df = df.loc[:, ['left_id', 'right_id', 'label']]
            df = df.rename({'left_id': 'ltable_id', 'right_id': 'rtable_id'}, axis=1)
            self.save_df_as_csv(df, name)


class MCANConvertor(Convertor):
    @staticmethod
    def dir_name() -> str:
        return "mcan"

    def convert(self):
        for name, df in self.splits.items():
            df.rename(columns=lambda x: x.replace('left_', 'ltable_'), inplace=True)
            df.rename(columns=lambda x: x.replace('right_', 'rtable_'), inplace=True)
            self.save_df_as_csv(df, name)


class NonNeuralConvertor(Convertor):
    @staticmethod
    def dir_name() -> str:
        return "non-neural"

    def convert(self):
        merged_df = pd.concat(self.splits, axis=0, ignore_index=True)

        left_df = pd.DataFrame()
        right_df = pd.DataFrame()

        for column in merged_df.columns:
            if 'left' in column:
                left_df[str(column).replace("left_", "")] = merged_df[column]
            elif 'right' in column:
                right_df[str(column).replace("right_", "")] = merged_df[column]

        self.save_df_as_csv(left_df, "tableA")
        self.save_df_as_csv(right_df, "tableB")

        # TODO: Check if validation split must be ignored
        for name, df in self.splits.items():
            self.save_df_as_csv(df, name)


class ConvertorManager:
    __mappings__ = {
        "ditto": DittoConvertor,
        "mcan": MCANConvertor,
        "gnem": GNEMConvertor,
        "nonneural": NonNeuralConvertor,
        "deepmatcher": StandardConvertor,
        "hiermatcher": StandardConvertor
    }

    @staticmethod
    def get_convertor(matcher_name: str) -> Convertor:
        return ConvertorManager.__mappings__[matcher_name.strip().lower()]

    @staticmethod
    def get_all_convertors():
        return ConvertorManager.__mappings__.values()
