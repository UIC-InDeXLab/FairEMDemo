import pandas as pd

from fairness import fair_em as fem
from fairness import workloads as wl


def run_one_workload(
        predictions_df,
        test_df,
        left_sens_attribute,
        right_sens_attribute,
        single_fairness=True,
        k_combinations=1,
        delimiter=",",
):
    pred_list = predictions_df.values.tolist()

    workload = wl.Workload(
        test_df,
        left_sens_attribute,
        right_sens_attribute,
        pred_list,
        label_column="label",
        multiple_sens_attr=True,
        delimiter=delimiter,
        single_fairness=single_fairness,
        k_combinations=k_combinations,
    )
    return [workload]


def calculate_fairness_df(
        test_df,
        prediction_df,
        left_sens_attribute,
        right_sens_attribute,
        measures,
        aggregate,
        threshold,
        single_fairness=True,
):
    workloads = run_one_workload(
        predictions_df=prediction_df,
        test_df=test_df,
        left_sens_attribute=left_sens_attribute,
        right_sens_attribute=right_sens_attribute,
        single_fairness=single_fairness
    )

    fairEM = fem.FairEM(
        workloads,
        threshold=threshold,
    )

    binary_fairness = []

    attribute_names = []
    for k_comb in workloads[0].k_combs_to_attr_names:
        curr_attr_name = workloads[0].k_combs_to_attr_names[k_comb]
        attribute_names.append(curr_attr_name)

    df = pd.DataFrame(columns=["measure", "sens_attr", "is_fair"])

    for measure in measures:
        temp_df = pd.DataFrame(columns=["measure", "sens_attr", "is_fair"])
        is_fair, counts, disparities = fairEM.is_fair(measure, aggregate)
        binary_fairness.append(is_fair)
        temp_df["measure"] = [measure] * len(is_fair)
        temp_df["sens_attr"] = attribute_names
        temp_df["is_fair"] = is_fair
        temp_df["counts"] = counts
        temp_df["disparities"] = disparities
        df = pd.concat([temp_df, df])

    return df
