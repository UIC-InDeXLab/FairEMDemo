import math


class FairEM:
    # the input is a list of objects of class Workload
    # alpha is used for the Z-Test
    def __init__(
            self,
            workloads,
            threshold,
    ):
        self.workloads = workloads
        self.threshold = threshold
        self.distances_unfaired = {}
        self.distances_all = {}

        self.TP = 0
        self.FP = 1
        self.TN = 2
        self.FN = 3

    # creates a two dimensional matrix, subgroups x workload fairness value
    # used only for distribution
    # true would mean something is good, i.e. is fair
    # so for accuracy if x0 - avg(x) > -threshold, this is good
    # if we want a measure to be as low as possible,
    # then x0 - avg(x) < threshold
    def is_fair_measure_specific(self, measure, workload_fairness):
        # if (
        #         measure == "accuracy_parity"
        #         or measure == "statistical_parity"
        #         or measure == "true_positive_rate_parity"
        #         or measure == "true_negative_rate_parity"
        #         or measure == "positive_predictive_value_parity"
        #         or measure == "negative_predictive_value_parity"
        # ):
        #     return workload_fairness >= -self.threshold
        # if (
        #         measure == "false_positive_rate_parity"
        #         or measure == "false_negative_rate_parity"
        #         or measure == "false_discovery_rate_parity"
        #         or measure == "false_omission_rate_parity"
        # ):
        return math.fabs(workload_fairness) <= self.threshold

    def is_fair(self, measure, aggregate, real_distr=False):
        workload_fairness, counts = self.workloads[0].fairness(
            self.workloads[0].k_combs, measure, aggregate
        )
        if aggregate not in ["subtraction based", "division based"]:
            return self.is_fair_measure_specific(measure, workload_fairness)
        else:
            if real_distr:
                return workload_fairness
            else:
                return [
                    self.is_fair_measure_specific(measure, subgroup_fairness)
                    for subgroup_fairness in workload_fairness
                ], counts, workload_fairness
