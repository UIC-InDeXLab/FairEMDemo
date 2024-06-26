import os.path
from abc import ABC, abstractmethod
from typing import Type

import pandas as pd

from enums import MatcherAlgorithm
from matchers import MatcherManager, Matcher
from singleton import Singleton


class Predictor(ABC):
    def __init__(self, dataset_id: str, matching_threshold: float = 0.5):
        self.dataset_id = dataset_id
        self.matching_threshold = matching_threshold

    @abstractmethod
    def predict(self) -> pd.DataFrame:
        pass

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass

    @property
    def scores_dir(self) -> str:
        matcher_class: Type[Matcher] = MatcherManager.instance().get_matcher(self.get_name())
        return matcher_class(dataset_id=self.dataset_id).scores_dir

    @property
    def df(self):
        df = pd.read_csv(os.path.join(self.scores_dir, "preds.csv"))
        return df


class StandardPredictor(Predictor, ABC):
    def predict(self) -> pd.DataFrame:
        return pd.DataFrame({
            'preds': (self.df['scores'] > self.matching_threshold).astype(int)
        })


class DittoPredictor(StandardPredictor):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.DITTO.value


class DeepMatcherPredictor(StandardPredictor):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.DEEPMATCHER.value


class HierMatcherPredictor(StandardPredictor):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.HIERMATCHER.value


class MCANPredictor(StandardPredictor):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.MCAN.value


class DecisionTreePredictor(StandardPredictor):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.DTMATCHER.value


class LogisticRegressionPredictor(StandardPredictor):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.LOGREGMATCHER.value


class LinearRegressionPredictor(StandardPredictor):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.LINREGMATCHER.value


class NaiveBayesPredictor(StandardPredictor):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.NBMATCHER.value


class SVMPredictor(StandardPredictor):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.SVMMATCHER.value


class RandomForestPredictor(StandardPredictor):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.RFMATCHER.value


@Singleton
class PredictorManager:
    def __init__(self):
        self._mappings = self.__init_mapping__()

    @staticmethod
    def __init_mapping__() -> dict[MatcherAlgorithm, Type[Predictor]]:
        return {
            MatcherAlgorithm.DITTO: DittoPredictor,
            MatcherAlgorithm.MCAN: MCANPredictor,
            MatcherAlgorithm.DEEPMATCHER: DeepMatcherPredictor,
            MatcherAlgorithm.HIERMATCHER: HierMatcherPredictor,
            MatcherAlgorithm.DTMATCHER: DecisionTreePredictor,
            MatcherAlgorithm.LOGREGMATCHER: LogisticRegressionPredictor,
            MatcherAlgorithm.LINREGMATCHER: LinearRegressionPredictor,
            MatcherAlgorithm.NBMATCHER: NaiveBayesPredictor,
            MatcherAlgorithm.RFMATCHER: RandomForestPredictor,
            MatcherAlgorithm.SVMMATCHER: SVMPredictor
        }

    def get_predictor(self, predictor_name: str) -> Type[Predictor]:
        return self._mappings[MatcherAlgorithm(predictor_name.strip())]
