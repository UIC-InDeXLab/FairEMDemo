import copy
import os.path
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type

import pandas as pd

from enums import MatcherAlgorithm


def split(df, train_ratio=0.7, val_ratio=0.15) -> dict[str, pd.DataFrame]:
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
        self.__init_dirs__()

    def __init_dirs__(self) -> None:
        Path(self.output_dir_name).mkdir(parents=True, exist_ok=True)

    def save_df_as_csv(self, df, name: str) -> None:
        df.to_csv(os.path.join(self.output_dir_name, f"{name}.csv"), index=False)

    @abstractmethod
    def convert(self) -> None:
        pass

    @staticmethod
    @abstractmethod
    def get_dir_name() -> str:
        pass

    @property
    def output_dir_name(self) -> str:
        return os.path.join(os.getenv("PREPROCESS_PATH", "./preprocess"), self.get_dir_name(), self.dataset_id)

    @property
    def splits(self) -> dict[str, pd.DataFrame]:
        return copy.deepcopy(self.__splits__)

    @property
    def test_path(self) -> str:
        return os.path.join(self.output_dir_name, "test.csv")

    @property
    def validation_path(self) -> str:
        return os.path.join(self.output_dir_name, "valid.csv")

    @property
    def train_path(self) -> str:
        return os.path.join(self.output_dir_name, "train.csv")


class StandardConvertor(Convertor):
    @staticmethod
    def get_dir_name() -> str:
        return "standard"

    def convert(self):
        for name, df in self.splits.items():
            self.save_df_as_csv(df, name)


class DittoConvertor(Convertor):
    @staticmethod
    def get_dir_name() -> str:
        return MatcherAlgorithm.DITTO.value

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


class MCANConvertor(Convertor):
    @staticmethod
    def get_dir_name() -> str:
        return MatcherAlgorithm.MCAN.value

    def convert(self):
        for name, df in self.splits.items():
            df.rename(columns=lambda x: x.replace('left_', 'ltable_'), inplace=True)
            df.rename(columns=lambda x: x.replace('right_', 'rtable_'), inplace=True)
            self.save_df_as_csv(df, name)


class NonNeuralConvertor(Convertor):
    @staticmethod
    def get_dir_name() -> str:
        return MatcherAlgorithm.NONNEURAL.value

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
    _mappings = {
        MatcherAlgorithm.DITTO: DittoConvertor,
        MatcherAlgorithm.MCAN: MCANConvertor,
        MatcherAlgorithm.DEEPMATCHER: StandardConvertor,
        MatcherAlgorithm.HIERMATCHER: StandardConvertor,
        MatcherAlgorithm.NONNEURAL: NonNeuralConvertor
    }

    @staticmethod
    def get_convertor(matcher_name: str) -> Type[Convertor]:
        return ConvertorManager._mappings[MatcherAlgorithm(matcher_name.strip().lower())]


    @staticmethod
    def get_all_convertors() -> list[Type[Convertor]]:
        return list(ConvertorManager._mappings.values())
