import pandas

from enums import DisparityCalculationType, FairnessMeasure
from fairness.experiments import calculate_fairness_df


class FairnessAnalyzer:
    def __init__(self, test_df: pandas.DataFrame, sensitive_attribute: str):
        self._test_df = test_df
        self._sensitive_attribute = sensitive_attribute

    def __call__(self, prediction_df: pandas.DataFrame, disparity_calculation_type: DisparityCalculationType,
                 measures: list[FairnessMeasure],
                 fairness_threshold: float = 0.5,
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

            results[name] = df.to_dict(orient="records")

        return results
