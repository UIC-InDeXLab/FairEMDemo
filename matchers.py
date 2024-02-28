import os
from abc import ABC, abstractmethod
import docker
import json

import pandas as pd

import convertors
from singleton import Singleton


# Commands :
# Deepmatcher: docker run -v ./fasttext/:/root/.vector_cache/ -v ./train_1/:/app/deepmatcher/data/train_1/ -e TASK=train_1 merfanian/fair-entity-matching:demo-deepmatcher-0.1.0
# HierMatcher: docker run -v ./fasttext/:/app/HierMatcher/embedding/ -v ./train_1/:/app/HierMatcher/data/train_1/ -e TASK=train_1 merfanian/fair-entity-matching:demo-hiermatcher-0.1.0
# Non-Neural:  docker run  -v ./train_1/:/app/non-neural/data/train_1/ -e TASK=train_1  merfanian/fair-entity-matching:demo-nonneural-0.1.0
# MCAN:  docker run -v ./fasttext/:/app/MCAN/embedding/ -v ./train_1/:/app/MCAN/data/Structural/train_1/ -e TASK=train_1 merfanian/fair-entity-matching:demo-mcan-0.1.0

@Singleton
class MatcherConfigManager:
    def __init__(self):
        self.matchers = self.__init_matchers__()

    @staticmethod
    def __init_matchers__():
        with open(os.getenv("CONFIG_PATH", "./config.json"), 'r+') as f:
            config = json.load(f)
            return config["matchers"]

    def get_matcher_image(self, name: str):
        return [m["image"] for m in self.matchers if m["name"].strip().lower() == name.strip().lower()].pop()


class Matcher(ABC):

    def __init__(self, dataset_id: str, matching_threshold: float = 0.5, epochs: int = 1):
        self.dataset_id = dataset_id
        self.matching_threshold = matching_threshold
        self.epochs = epochs
        self.scores = []
        self.client = docker.from_env()
        self.output = None

    @abstractmethod
    def match(self):
        pass

    def extract_scores(self):
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

        for line in in_data:
            if line.startswith("==========") and line.endswith("=========="):
                is_results = not is_results
            elif is_results:
                if not is_columns:
                    is_columns = True
                    if is_float(line.strip()):
                        data.append(float(line.strip()))
                else:
                    data.append(float(line))
        self.scores = data

        df = pd.DataFrame(self.scores, columns=["scores"])
        df.to_csv(os.path.join(self.scores_dir, "preds.csv"), index=False)

    def docker_run(self, envs: dict, volumes: dict):
        container = self.client.containers.run(
            image=self.image_name,
            detach=True,
            remove=True,
            stdout=True,
            stderr=True,
            environment=envs,
            volumes=volumes
        )

        output = container.logs(stdout=True, stderr=True, follow=True).decode()
        container.wait()
        self.output = output

    @property
    @abstractmethod
    def name(self) -> str:
        # TODO: Change this method to static method
        pass

    @property
    def image_name(self) -> str:
        manager: MatcherConfigManager = MatcherConfigManager.instance()
        return manager.get_matcher_image(self.name)

    @property
    def preprocess_dir(self) -> str:
        dir_name = convertors.ConvertorManager.get_convertor(self.name).dir_name()
        return os.path.join(os.getenv("PREPROCESS_PATH", "./preprocess"), dir_name, self.dataset_id)

    @property
    def scores_dir(self) -> str:
        return os.path.join(os.getenv("SCORES_PATH", "./scores"), self.name, self.dataset_id)


class DeepMatcher(Matcher):

    def match(self):
        self.docker_run(
            volumes={os.getenv("FASTTEXT_PATH", "./fasttext"): {'bind': '/root/.vector_cache', 'mode': 'rw'},
                     self.preprocess_dir: {'bind': f'/app/deepmatcher/data/{self.dataset_id}/', 'mode': 'rw'}},
            envs={"TASK": self.dataset_id, "EPOCHS": self.epochs})

        self.extract_scores()

    @property
    def name(self) -> str:
        return "deepmatcher"
