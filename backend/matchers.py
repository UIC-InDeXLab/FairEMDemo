import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type

import docker
import pandas as pd

import convertors
from enums import MatcherAlgorithm
from singleton import Singleton


class Matcher(ABC):

    def __init__(self, dataset_id: str, epochs: int = 1):
        self.dataset_id = dataset_id
        self.epochs = epochs
        self.scores = []
        self.client = docker.from_env()
        self.output = None
        self.__init_dirs__()

    def __init_dirs__(self):
        Path(self.scores_dir).mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def find_scores(self):
        pass

    def extract_scores(self) -> iter(list[float], str):
        def is_float(str):
            try:
                float(str)
                return True
            except ValueError:
                return False

        assert self.output is not None
        in_data = self.output.splitlines()
        data = []
        is_results = False
        is_columns = False
        data_batch_finished = True
        title = ""

        for line in in_data:
            if line.startswith("==========") and line.endswith("=========="):
                is_results = not is_results
                data_batch_finished = not data_batch_finished
                title = str(line).replace("==========", "")
                if data_batch_finished and len(data) > 0:
                    yield title, data
                    data = []
                    is_columns = False

            elif is_results:
                if not is_columns:
                    is_columns = True
                    if is_float(line.strip()):
                        data.append(float(line.strip()))
                else:
                    data.append(float(line))

        if data_batch_finished and len(data) > 0:
            yield title, data

    def docker_run(self, envs: dict, volumes: dict):
        container = self.client.containers.run(
            image=self.image_name,
            detach=True,
            remove=True,
            stdout=True,
            stderr=True,
            environment=envs,
            volumes=volumes,
            device_requests=[
                docker.types.DeviceRequest(device_ids=["all"], capabilities=[['gpu']])]
        )

        output = container.logs(stdout=True, stderr=True, follow=True).decode()
        # container.wait()
        self.output = output

    @property
    def scores_exist(self) -> bool:
        return os.path.isfile(os.path.join(self.scores_dir, "preds.csv"))

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass

    @property
    def image_name(self) -> str:
        manager: MatcherManager = MatcherManager.instance()
        return manager.get_matcher_image(self.get_name())

    @property
    def preprocess_dir(self) -> str:
        dir_name = convertors.ConvertorManager.get_convertor(self.get_name()).get_dir_name()
        return os.path.join(os.getenv("PREPROCESS_PATH", "./preprocess"), dir_name, self.dataset_id)

    @property
    def scores_dir(self) -> str:
        return os.path.join(os.getenv("SCORES_PATH", "./scores"), self.get_name(), self.dataset_id)


class DeepMatcher(Matcher):
    def find_scores(self):
        self.docker_run(
            volumes={os.getenv("FASTTEXT_PATH", "./fasttext"): {'bind': '/root/.vector_cache', 'mode': 'rw'},
                     self.preprocess_dir: {'bind': f'/app/deepmatcher/data/{self.dataset_id}/', 'mode': 'rw'}},
            envs={"TASK": self.dataset_id, "EPOCHS": self.epochs})

        title, self.scores = next(self.extract_scores())
        df = pd.DataFrame(self.scores, columns=["scores"])
        df.to_csv(os.path.join(self.scores_dir, "preds.csv"), index=False)

    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.DEEPMATCHER.value.lower()


class HierMatcher(Matcher):
    def find_scores(self):
        self.docker_run(
            volumes={os.getenv("FASTTEXT_PATH", "./fasttext/"): {'bind': '/app/HierMatcher/embedding/', 'mode': 'rw'},
                     self.preprocess_dir: {'bind': f'/app/HierMatcher/data/{self.dataset_id}/', 'mode': 'rw'}},
            envs={"TASK": self.dataset_id, "EPOCHS": self.epochs})

        title, self.scores = next(self.extract_scores())
        df = pd.DataFrame(self.scores, columns=["scores"])
        df.to_csv(os.path.join(self.scores_dir, "preds.csv"), index=False)

    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.HIERMATCHER.value.lower()


class MCANMatcher(Matcher):
    def find_scores(self):
        self.docker_run(
            volumes={
                os.getenv("FASTTEXT_PATH", "./fasttext/"): {'bind': '/app/MCAN/embedding/', 'mode': 'rw'},
                self.preprocess_dir: {'bind': f'/app/MCAN/data/Structural/{self.dataset_id}/', 'mode': 'rw'}},
            envs={"TASK": self.dataset_id, "EPOCHS": self.epochs})

        title, self.scores = next(self.extract_scores())
        df = pd.DataFrame(self.scores, columns=["scores"])
        df.to_csv(os.path.join(self.scores_dir, "preds.csv"), index=False)

    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.MCAN.value.lower()


class DittoMatcher(Matcher):
    def find_scores(self):
        self.docker_run(
            volumes={self.preprocess_dir: {'bind': f'/app/ditto/data/{self.dataset_id}/', 'mode': 'rw'}},
            envs={"TASK": self.dataset_id, "EPOCHS": self.epochs})

        title, self.scores = next(self.extract_scores())
        df = pd.DataFrame(self.scores, columns=["scores"])
        df.to_csv(os.path.join(self.scores_dir, "preds.csv"), index=False)

    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.DITTO.value.lower()


class NonNeuralMatcher(Matcher, ABC):

    def find_scores(self):
        self.docker_run(
            volumes={self.preprocess_dir: {'bind': f'/app/non-neural/data/{self.dataset_id}/', 'mode': 'rw'}},
            envs={"TASK": self.dataset_id, "MODEL": self.get_name()})

        title, self.scores = next(self.extract_scores())
        df = pd.DataFrame(self.scores, columns=["scores"])
        df.to_csv(os.path.join(self.scores_dir, "preds.csv"), index=False)

    @property
    def preprocess_dir(self) -> str:
        dir_name = convertors.ConvertorManager.get_convertor(MatcherAlgorithm.NONNEURAL.value).get_dir_name()
        return os.path.join(os.getenv("PREPROCESS_PATH", "./preprocess"), dir_name, self.dataset_id)

    @property
    def image_name(self) -> str:
        manager: MatcherManager = MatcherManager.instance()
        return manager.get_matcher_image(MatcherAlgorithm.NONNEURAL.value)


class RandomForestMatcher(NonNeuralMatcher):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.RFMATCHER.value.lower()


class DecisionTreeMatcher(NonNeuralMatcher):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.DTMATCHER.value.lower()


class LinearRegressionMatcher(NonNeuralMatcher):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.LINREGMATCHER.value.lower()


class LogisticRegressionMatcher(NonNeuralMatcher):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.LOGREGMATCHER.value.lower()


class SVMMatcher(NonNeuralMatcher):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.SVMMATCHER.value.lower()


class NaiveBayesMatcher(NonNeuralMatcher):
    @staticmethod
    def get_name() -> str:
        return MatcherAlgorithm.NBMATCHER.value.lower()


@Singleton
class MatcherManager:
    def __init__(self):
        self.matchers = self.__init_matchers__()
        self.mappings = self.__init_mappings__()

    @staticmethod
    def __init_mappings__():
        return {
            MatcherAlgorithm.DITTO: DittoMatcher,
            MatcherAlgorithm.MCAN: MCANMatcher,
            MatcherAlgorithm.DEEPMATCHER: DeepMatcher,
            MatcherAlgorithm.HIERMATCHER: HierMatcher,
            MatcherAlgorithm.DTMATCHER: DecisionTreeMatcher,
            MatcherAlgorithm.LOGREGMATCHER: LogisticRegressionMatcher,
            MatcherAlgorithm.LINREGMATCHER: LinearRegressionMatcher,
            MatcherAlgorithm.NBMATCHER: NaiveBayesMatcher,
            MatcherAlgorithm.RFMATCHER: RandomForestMatcher,
            MatcherAlgorithm.SVMMATCHER: SVMMatcher
        }

    @staticmethod
    def __init_matchers__():
        with open(os.getenv("CONFIG_PATH", "./config.json"), 'r+') as f:
            config = json.load(f)
            return config["matchers"]

    def get_matcher(self, matcher_name: str) -> Type[Matcher]:
        return self.mappings[MatcherAlgorithm(matcher_name.strip())]

    def get_all_matchers(self):
        return self.mappings.values()

    def get_matcher_image(self, name: str):
        return [m["image"] for m in self.matchers if m["name"].strip().lower() == name.strip().lower()].pop()
