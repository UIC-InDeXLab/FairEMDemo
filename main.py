import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Type

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Query

from convertors import split, ConvertorManager, StandardConvertor
from enums import DisparityCalculationType, FairnessMeasure, MatcherAlgorithm
from fairness.analyzer import FairnessAnalyzer
from matchers import MatcherManager
from predictors import PredictorManager, Predictor
from utils import load_dataset_as_df

load_dotenv()


def startup():
    Path(os.getenv("DATASET_UPLOAD_PATH", "./datasets")).mkdir(parents=True, exist_ok=True)


app = FastAPI(on_startup=[startup])


@app.post("/v1/datasets/")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        return {"message": "Please upload a CSV file."}

    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        return {"message": f"Error reading CSV file: {str(e)}"}

    # TODO: add a random hash id to end of filename
    df.to_csv(os.path.join(os.getenv("DATASET_UPLOAD_PATH", "./datasets"), file.filename), index=False)

    return {
        "id": file.filename.replace(".csv", ""),
    }


@app.get("/v1/datasets/{dataset_id}/preprocess/")
async def preprocess(dataset_id: str):
    datasets_splits = split(load_dataset_as_df(dataset_id))
    for convertor_class in ConvertorManager.get_all_convertors():
        convertor_class(dataset_id=dataset_id, splits=datasets_splits).convert()

    return {"successful": True}


@app.get("/v1/datasets/{dataset_id}/match/")
async def find_scores(dataset_id: str, matchers: List[MatcherAlgorithm] = Query(None), epochs: int = 1):
    manager: MatcherManager = MatcherManager.instance()
    matcher_classes = set()
    with ThreadPoolExecutor() as executor:
        futures = []
        for matcher in matchers:
            matcher_class = manager.get_matcher(matcher.value)

            if matcher_class in matcher_classes:
                continue

            matcher_classes.add(matcher_class)
            matcher = matcher_class(dataset_id=dataset_id, epochs=epochs)
            future = executor.submit(matcher.find_scores)  # Run matcher in a thread
            futures.append(future)

        for future in futures:
            future.result()

    return {"successful": True}


@app.get("/v1/datasets/{dataset_id}/fairness/")
async def calculate_fairness_metrics(dataset_id: str,
                                     sensitive_attribute: str,
                                     disparity_calculation_type: DisparityCalculationType,
                                     fairness_metrics: List[FairnessMeasure] = Query(None),
                                     matchers: List[MatcherAlgorithm] = Query(None),
                                     matching_threshold: float = 0.5,
                                     fairness_threshold: float = 0.2):
    test_df = pd.read_csv(StandardConvertor(dataset_id=dataset_id, splits=None).test_path)
    fairness_analyzer = FairnessAnalyzer(sensitive_attribute=sensitive_attribute, test_df=test_df)

    results = {}
    for matcher in matchers:
        predictor_class: Type[Predictor] = PredictorManager.instance().get_predictor(predictor_name=matcher.value)
        prediction_df = predictor_class(dataset_id=dataset_id, matching_threshold=matching_threshold).predict()
        results[matcher.value] = fairness_analyzer(prediction_df=prediction_df,
                                                   disparity_calculation_type=disparity_calculation_type,
                                                   measures=fairness_metrics, fairness_threshold=fairness_threshold)

    return results
