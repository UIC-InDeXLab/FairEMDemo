import itertools

import pandas as pd
from sklearn.metrics import recall_score, precision_score, f1_score, confusion_matrix

from enums import DisparityCalculationType, FairnessMeasure, PerformanceMetric
from fairness.experiments import calculate_fairness_df

from abc import ABC, abstractmethod
from enums import MatcherAlgorithm


class Analyzer(ABC):
    def __init__(self, test_df: pd.DataFrame, sensitive_attribute: str):
        self._test_df = test_df
        self._sensitive_attribute = sensitive_attribute

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class FairnessAnalyzer(Analyzer):
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

            for fairness_measure, group in grouped_df:
                result_dict[fairness_measure] = group.to_dict(orient="records")
            results[name] = result_dict

        return results


class ExplanationProvider(Analyzer):
    def __call__(self, prediction_df: pd.DataFrame, group: str, fairness_measure: FairnessMeasure,
                 num_samples: int = 10, *args, **kwargs):
        combined_df = pd.merge(self._test_df, prediction_df, left_index=True, right_index=True)

        y_true = combined_df['label']
        y_pred = combined_df['preds']

        conf_matrix = confusion_matrix(y_true, y_pred)
        conf_matrix = conf_matrix.transpose()
        conf_matrix_df = pd.DataFrame(conf_matrix,
                                      index=['Non-Match', 'Match'],
                                      columns=['Actual Non-Match', 'Actual Match'])

        conf_matrix_df.insert(0, 'Predicted', ['Non-Match', 'Match'])

        filtered_df = self._test_df[self._test_df[f"left_{self._sensitive_attribute}"] == group]

        match_count_group = (filtered_df['label'] == 1).sum()
        non_match_count_group = (filtered_df['label'] == 0).sum()
        total_count_group = len(filtered_df)

        match_count_total = (self._test_df['label'] == 1).sum()
        non_match_count_total = (self._test_df['label'] == 0).sum()
        total_count_total = len(self._test_df)

        coverage_df = pd.DataFrame({
            'Group': [group, 'Total'],
            'Match': [match_count_group, match_count_total],
            'Non-match': [non_match_count_group, non_match_count_total],
            'Total': [total_count_group, total_count_total]
        })

        incorrect_preds_df = combined_df[combined_df['label'] != combined_df['preds']]
        incorrect_preds_group_df = incorrect_preds_df[incorrect_preds_df[f"left_{self._sensitive_attribute}"] == group]

        if len(incorrect_preds_group_df) > 0:
            sample_df = incorrect_preds_group_df.sample(n=min(num_samples, len(incorrect_preds_group_df)))
        else:
            sample_df = pd.DataFrame(columns=combined_df.columns)  # Return empty DataFrame if no samples

        results = {
            "confusion_matrix": conf_matrix_df.to_dict(orient="split", index=False),
            "coverage": coverage_df.to_dict(orient="split", index=False),
            f"{group}_samples": sample_df.to_dict(orient="split", index=False)
        }
        return results


class PerformanceAnalyzer(Analyzer):
    def __call__(self, prediction_mappings: dict[MatcherAlgorithm, pd.DataFrame], measure: FairnessMeasure, *args,
                 **kwargs):
        def calculate_metric(df_group, matcher):
            if measure == "accuracy":
                metric_value = (df_group["label"] == df_group["preds"]).mean()
            elif measure == "true_positive_rate":
                tp = ((df_group["label"] == 1) & (df_group["preds"] == 1)).sum()
                fn = ((df_group["label"] == 1) & (df_group["preds"] == 0)).sum()
                metric_value = tp / (tp + fn) if (tp + fn) > 0 else "-"
            elif measure == "false_positive_rate":
                fp = ((df_group["label"] == 0) & (df_group["preds"] == 1)).sum()
                tn = ((df_group["label"] == 0) & (df_group["preds"] == 0)).sum()
                metric_value = fp / (fp + tn) if (fp + tn) > 0 else "-"
            elif measure == "negative_predictive_value":
                tn = ((df_group["label"] == 0) & (df_group["preds"] == 0)).sum()
                fn = ((df_group["label"] == 1) & (df_group["preds"] == 0)).sum()
                metric_value = tn / (tn + fn) if (tn + fn) > 0 else "-"
            elif measure == "positive_predictive_value":
                tp = ((df_group["label"] == 1) & (df_group["preds"] == 1)).sum()
                fp = ((df_group["label"] == 0) & (df_group["preds"] == 1)).sum()
                metric_value = tp / (tp + fp) if (tp + fp) > 0 else "-"
            else:
                raise ValueError(f"Unsupported metric: {measure}")

            return pd.Series({matcher: metric_value})

        dfs = []
        for matcher_name, pred_df in prediction_mappings.items():
            # Merge the test DataFrame with the predictions DataFrame
            df = pd.merge(self._test_df, pred_df, left_index=True, right_index=True)

            # Group by the sensitive attribute and calculate the metric
            df_grouped = df.groupby(f"left_{self._sensitive_attribute}").apply(
                lambda group: calculate_metric(group, matcher_name)).reset_index()
            reshaped_df = df_grouped.set_index(df_grouped.columns[0]).T.reset_index()
            first_column_name = reshaped_df.columns[0]
            reshaped_df = reshaped_df.rename(columns={first_column_name: 'matcher'})
            dfs.append(reshaped_df)

        combined_df = pd.concat(dfs, ignore_index=True)

        return combined_df


class EnsembleAnalyzer(Analyzer):
    def __call__(self, df: pd.DataFrame, *args, **kwargs):
        matchers = df['matcher'].tolist()
        groups = df.columns[1:]

        combinations = list(itertools.product(matchers, repeat=len(groups)))
        results = []

        for combo in combinations:
            performance_list = []
            matchers_dict = {}

            # Assign matchers to groups and calculate performance
            for i, group in enumerate(groups):
                matcher = combo[i]
                performance = df.loc[df['matcher'] == matcher, group].values[0]
                performance_list.append(performance)
                matchers_dict[group] = matcher

            # Calculate worst performance and max disparity
            worst_performance = min(performance_list)
            max_disparity = max(performance_list) - min(performance_list)

            # Append the result
            results.append({
                'disparity': max_disparity,
                'performance': worst_performance,
                'matchers': matchers_dict
            })

        return results
