import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

import docker
import pandas as pd

import convertors
from singleton import Singleton


class Matcher(ABC):

    def __init__(self, dataset_id: str, matching_threshold: float = 0.5, epochs: int = 1):
        self.dataset_id = dataset_id
        self.matching_threshold = matching_threshold
        self.epochs = epochs
        self.scores = []
        self.client = docker.from_env()
        self.output = None
        self.__init_dirs__()

    def __init_dirs__(self):
        Path(self.scores_dir).mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def match(self):
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
    def match(self):
        self.docker_run(
            volumes={os.getenv("FASTTEXT_PATH", "./fasttext"): {'bind': '/root/.vector_cache', 'mode': 'rw'},
                     self.preprocess_dir: {'bind': f'/app/deepmatcher/data/{self.dataset_id}/', 'mode': 'rw'}},
            envs={"TASK": self.dataset_id, "EPOCHS": self.epochs})

        title, self.scores = next(self.extract_scores())
        df = pd.DataFrame(self.scores, columns=["scores"])
        df.to_csv(os.path.join(self.scores_dir, "preds.csv"), index=False)

    @staticmethod
    def get_name() -> str:
        return "deepmatcher"


class HierMatcher(Matcher):
    def match(self):
        self.docker_run(
            volumes={os.getenv("FASTTEXT_PATH", "./fasttext/"): {'bind': '/app/HierMatcher/embedding/', 'mode': 'rw'},
                     self.preprocess_dir: {'bind': f'/app/HierMatcher/data/{self.dataset_id}/', 'mode': 'rw'}},
            envs={"TASK": self.dataset_id, "EPOCHS": self.epochs})

        title, self.scores = next(self.extract_scores())
        df = pd.DataFrame(self.scores, columns=["scores"])
        df.to_csv(os.path.join(self.scores_dir, "preds.csv"), index=False)

    @staticmethod
    def get_name() -> str:
        return "hiermatcher"


class MCANMatcher(Matcher):
    def match(self):
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
        return "mcan"


class DittoMatcher(Matcher):
    def match(self):
        self.docker_run(
            volumes={self.preprocess_dir: {'bind': f'/app/ditto/data/{self.dataset_id}/', 'mode': 'rw'}},
            envs={"TASK": self.dataset_id, "EPOCHS": self.epochs})

        title, self.scores = next(self.extract_scores())
        df = pd.DataFrame(self.scores, columns=["scores"])
        df.to_csv(os.path.join(self.scores_dir, "preds.csv"), index=False)

    @staticmethod
    def get_name() -> str:
        return "ditto"


class NonNeuralMatcher(Matcher):

    def match(self):
        self.docker_run(
            volumes={self.preprocess_dir: {'bind': f'/app/non-neural/data/{self.dataset_id}/', 'mode': 'rw'}},
            envs={"TASK": self.dataset_id})

        for title, scores in self.extract_scores():
            print(title)
            df = pd.DataFrame(scores, columns=["scores"])
            dir = self.get_score_dir_by_name(str(title).split("/")[2])
            Path(dir).mkdir(parents=True, exist_ok=True)
            df.to_csv(os.path.join(dir, "preds.csv"), index=False)

    def __init_dirs__(self):
        pass

    @staticmethod
    def get_name() -> str:
        return "nonneural"

    @property
    def scores_dir(self) -> str:
        raise NotImplementedError("don't use this function for non-neural, use get_score_dir_by_name function with "
                                  "method name")

    def get_score_dir_by_name(self, name: str) -> str:
        return os.path.join(os.getenv("SCORES_PATH", "./scores"), name, self.dataset_id)


@Singleton
class MatcherManager:
    def __init__(self):
        self.matchers = self.__init_matchers__()
        self.mappings = self.__init_mappings__()

    @staticmethod
    def __init_mappings__():
        return {
            "ditto": DittoMatcher,
            "mcan": MCANMatcher,
            "deepmatcher": DeepMatcher,
            "hiermatcher": HierMatcher,
            "nonneural": NonNeuralMatcher,
        }

    @staticmethod
    def __init_matchers__():
        with open(os.getenv("CONFIG_PATH", "./config.json"), 'r+') as f:
            config = json.load(f)
            return config["matchers"]

    def get_matcher(self, matcher_name: str) -> Matcher:
        return self.mappings[matcher_name.strip().lower()]

    def get_all_matchers(self):
        return self.mappings.values()

    def get_matcher_image(self, name: str):
        return [m["image"] for m in self.matchers if m["name"].strip().lower() == name.strip().lower()].pop()
