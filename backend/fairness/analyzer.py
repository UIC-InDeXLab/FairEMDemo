import pandas as pd
from sklearn.metrics import recall_score, precision_score, f1_score

from enums import DisparityCalculationType, FairnessMeasure, PerformanceMetric
from fairness.experiments import calculate_fairness_df


class FairnessAnalyzer:
    def __init__(self, test_df: pd.DataFrame, sensitive_attribute: str):
        self._test_df = test_df
        self._sensitive_attribute = sensitive_attribute

    def __call__(self, prediction_df: pd.DataFrame, disparity_calculation_type: DisparityCalculationType,
                 measures: list[FairnessMeasure],
                 fairness_threshold: float = 0.5,
                 group_acceptance_count: int = 1,
                 *args, **kwargs):
        fairness_types = {"single_fairness": True, "pairwise_fairness": False}
        results = {}
        for name, single_fairness in fairness_types.items():
            df = calculate_fairness_df(test_df=self._test_df, prediction_df=prediction_df,
                                       left_sens_attribute='left_' + self._sensitive_attribute,
                                       right_sens_attribute='right_' + self._sensitive_attribute,
                                       measures=[measure.value for measure in measures],
                                       aggregate=disparity_calculation_type.value,
                                       threshold=fairness_threshold,
                                       single_fairness=single_fairness)
            df['disparities'] = df['disparities'].abs()
            df = df[df['counts'] >= group_acceptance_count]
            grouped_df = df.groupby('measure')
            result_dict = {}

            # Iterating through each group and converting to the desired format
            for fairness_measure, group in grouped_df:
                result_dict[fairness_measure] = group.to_dict(orient="records")
            results[name] = result_dict

        return results


class PerformanceAnalyzer:
    def __init__(self, test_df: pd.DataFrame):
        self._test_df = test_df

    def __call__(self, prediction_df: pd.DataFrame, metrics: list[PerformanceMetric], *args, **kwargs):
        y_true = self._test_df['label']
        y_pred = prediction_df['label']

        recall = recall_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)

        return {
            'recall': recall,
            'precision': precision,
            'f1-score': f1
        }
