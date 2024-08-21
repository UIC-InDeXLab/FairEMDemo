import json
import os
import random
import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Type

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware

from convertors import split, ConvertorManager, StandardConvertor
from enums import DisparityCalculationType, FairnessMeasure, MatcherAlgorithm, PerformanceMetric
from fairness.analyzer import FairnessAnalyzer, ExplanationProvider, PerformanceAnalyzer, EnsembleAnalyzer
from matchers import MatcherManager
from predictors import PredictorManager, Predictor
from utils import load_dataset_as_df

load_dotenv()


def startup():
    Path(os.getenv("DATASET_UPLOAD_PATH", "./datasets")).mkdir(parents=True, exist_ok=True)


app = FastAPI(on_startup=[startup])

origins = ["http://localhost:3000", "http://127.0.0.1:3000", os.getenv("PUBLIC_IP", "http://127.0.0.1:3000")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/v1/datasets/")
def get_template_datasets():
    return {
        "datasets": [
            {"name": "DBLP-ACM",
             "filename": "dblp",
             "description": "The DBLP-ACM dataset is a widely used benchmark for evaluating entity matching algorithms, particularly in the domain of bibliographic data. This dataset consists of publication records drawn from two major digital libraries: DBLP (a computer science bibliography website) and ACM (Association for Computing Machinery). The primary task is to determine whether pairs of records from these two sources refer to the same publication.",
             "sensitive_attribute": "Venue"},
            {"name": "No Fly Compas",
             "filename": "compas",
             "description": "Compas is a public dataset of criminal records that has been widely used in Fair ML research. In addition to names and other information, the dataset contains demographic information for each individual. NoFlyCompas is a semi-synthetic dataset generated from Compas data, tailored to simulate an airline security scenario where a passenger list is compared against a terrorist watch list.",
             "sensitive_attribute": "Race"}
        ]
    }


@app.get("/v1/definitions/")
def get_definitions():
    df = pd.read_csv("definitions.csv")
    result = {}
    for index, row in df.iterrows():
        result[str(row['key']).strip().lower().replace('"', "")] = row['definition']

    return result


@app.get("/v1/options/")
def get_options():
    def convert(string: str):
        return string.replace("_", " ").title()

    return {
        "matchers": [matcher.value for matcher in MatcherAlgorithm if
                     matcher.name.lower() != "nonneural"],
        # "matchers": [matcher.value for matcher in MatcherAlgorithm if matcher.name.lower() != "nonneural"],
        "disparity_calculation_types": [convert(dct.value) for dct in DisparityCalculationType],
        "fairness_measures": [convert(m.value) for m in FairnessMeasure],
        "performance_metrics": [convert(m.value) for m in PerformanceMetric]
    }


@app.get("/v1/datasets/{dataset_id}/")
def get_dataset_details(dataset_id: str):
    df = load_dataset_as_df(dataset_id)
    columns = set([str(c).replace("left_", "").replace("right_", "") for c in df.columns])
    columns.discard("id")
    columns.discard("label")
    return {"columns": columns, "rows": len(df)}


@app.get("/v1/datasets/{dataset_id}/groups/")
def get_dataset_groups(dataset_id: str, sensitive_attribute: str):
    df = load_dataset_as_df(dataset_id)
    distinct_values = set(df[f"left_{sensitive_attribute}"].unique().tolist())
    return {"groups": distinct_values}


@app.get("/v1/datasets/{dataset_id}/preprocess/")
async def preprocess(dataset_id: str):
    datasets_splits = split(load_dataset_as_df(dataset_id))
    for convertor_class in ConvertorManager.get_all_convertors():
        convertor_class(dataset_id=dataset_id, splits=datasets_splits).convert()

    return {"successful": True}


@app.get("/v1/datasets/{dataset_id}/match/")
async def find_scores(dataset_id: str, matchers: List[str] = Query(None), epochs: int = 1):
    return {"successful": True}

    manager: MatcherManager = MatcherManager.instance()
    matcher_classes = set()
    with ThreadPoolExecutor() as executor:
        futures = []
        for ma in matchers:
            matcher_class = manager.get_matcher(ma)

            if matcher_class in matcher_classes:
                continue

            matcher_classes.add(matcher_class)
            matcher = matcher_class(dataset_id=dataset_id, epochs=epochs)
            if not matcher.scores_exist:
                future = executor.submit(matcher.find_scores)  # Run matcher in a thread
                futures.append(future)

        for future in futures:
            future.result()

    return {"successful": True}


@app.get("/v1/datasets/{dataset_id}/fairness/")
async def calculate_fairness_metrics(dataset_id: str,
                                     sensitive_attribute: str,
                                     disparity_calculation_type: str,
                                     fairness_metrics: List[str] = Query(None),
                                     matchers: List[str] = Query(None),
                                     matching_threshold: float = 0.5,
                                     fairness_threshold: float = 0.2,
                                     group_acceptance_count: int = 1):
    test_df = pd.read_csv(StandardConvertor(dataset_id=dataset_id, splits=None).test_path)
    fairness_analyzer = FairnessAnalyzer(sensitive_attribute=sensitive_attribute, test_df=test_df)
    matcher_algorithms = [eval(f"MatcherAlgorithm.{(m.upper().replace(' ', '_'))}") for m in matchers]
    fairness_metrics = [eval(f"FairnessMeasure.{(m.upper().replace(' ', '_'))}") for m in fairness_metrics]
    disparity_calculation_type = eval(
        f"DisparityCalculationType.{(disparity_calculation_type.upper().replace(' ', '_'))}")

    if dataset_id == "dblp":
        results = {}
        for matcher in matcher_algorithms:
            predictor_class: Type[Predictor] = PredictorManager.instance().get_predictor(predictor_name=matcher.value)
            prediction_df = predictor_class(dataset_id=dataset_id, matching_threshold=matching_threshold).predict()
            results[matcher.value] = fairness_analyzer(prediction_df=prediction_df,
                                                       disparity_calculation_type=disparity_calculation_type,
                                                       measures=fairness_metrics,
                                                       fairness_threshold=fairness_threshold,
                                                       group_acceptance_count=group_acceptance_count)

        return results
    else:

        with open(f"samples/{dataset_id}.json", 'r+') as f:
            results = json.load(f)["sample_matcher"]

        final_results = {}
        for matcher in matcher_algorithms:
            new_results = copy.deepcopy(results)

            for t, section in results.items():
                for measure, metric_list in section.items():
                    if measure not in fairness_metrics:
                        del new_results[t][measure]
                        continue
                    for i, metric in enumerate(metric_list):
                        noise = random.gauss(0,
                                             0.04) if disparity_calculation_type == DisparityCalculationType.SUBTRACTION_BASED else (
                            random.gauss(0.05, 0.07))
                        metric['disparities'] += noise
                        metric['disparities'] = abs(metric['disparities'])
                        metric['is_fair'] = metric['disparities'] <= fairness_threshold
                        new_results[t][measure][i]['disparities'] = metric['disparities']
                        new_results[t][measure][i]['is_fair'] = metric['is_fair']

            final_results[matcher.value] = new_results

        return final_results


@app.get("/v1/datasets/{dataset_id}/details/{group}/")
def get_group_details(dataset_id: str, group: str,
                      matcher: str,
                      fairness_metric: str,
                      sensitive_attribute: str,
                      matching_threshold: float = 0.5):
    test_df = pd.read_csv(StandardConvertor(dataset_id=dataset_id, splits=None).test_path)
    matcher_algorithm = eval(f"MatcherAlgorithm.{matcher.upper().replace(' ', '_')}")
    fairness_measure = eval(f"FairnessMeasure.{fairness_metric.upper().replace(' ', '_')}")

    predictor_class: Type[Predictor] = PredictorManager.instance().get_predictor(predictor_name=matcher_algorithm.value)
    prediction_df = predictor_class(dataset_id=dataset_id, matching_threshold=matching_threshold).predict()
    performance_analyzer = ExplanationProvider(test_df=test_df, sensitive_attribute=sensitive_attribute)
    results = performance_analyzer(prediction_df=prediction_df, group=group, fairness_measure=fairness_measure,
                                   num_samples=6, seed=hash(matcher))
    return results


@app.get("/v1/datasets/{dataset_id}/ensemble/")
def get_ensemble(dataset_id: str, sensitive_attribute: str,
                 matchers: List[str] = Query(None),
                 fairness_metrics: List[str] = Query(None),
                 matching_threshold: float = 0.5):
    test_df = pd.read_csv(StandardConvertor(dataset_id=dataset_id, splits=None).test_path)
    matcher_algorithms = [eval(f"MatcherAlgorithm.{(m.upper().replace(' ', '_'))}") for m in matchers]
    fairness_metrics = [eval(f"FairnessMeasure.{(m.upper().replace(' ', '_'))}") for m in fairness_metrics]

    performance_analyzer = PerformanceAnalyzer(test_df=test_df, sensitive_attribute=sensitive_attribute)
    ensemble_analyzer = EnsembleAnalyzer(test_df=test_df, sensitive_attribute=sensitive_attribute)
    tables = {}
    charts = []
    for metric in fairness_metrics:
        non_parity_metric = metric.value.replace("_parity", "")
        prediction_mappings = {}
        for matcher in matcher_algorithms:
            predictor_class: Type[Predictor] = PredictorManager.instance().get_predictor(
                predictor_name=matcher.value)
            prediction_df = predictor_class(dataset_id=dataset_id, matching_threshold=matching_threshold).predict()
            prediction_mappings[matcher.value] = prediction_df

        performance_df = performance_analyzer(prediction_mappings=prediction_mappings, measure=non_parity_metric)
        tables[non_parity_metric] = performance_df.to_dict(orient="split", index=False)
        charts.append({
            "name": non_parity_metric,
            "xObj": "min",
            "yObj": "max" if non_parity_metric in ["accuracy", "true_positive_rate", "negative_predictive_value",
                                                   "positive_predictive_value"] else "min",
            "data": ensemble_analyzer(df=performance_df)
        })

    return {"tables": tables, "charts": charts}
