import enum


class DisparityCalculationType(enum.Enum):
    SUBTRACTION = "distribution-subtraction"
    DIVISION = "distribution-division"


class MatcherAlgorithm(enum.Enum):
    DITTO = "ditto"
    MCAN = "mcan"
    DEEPMATCHER = "deepmatcher"
    HIERMATCHER = "hiermatcher"
    NONNEURAL = "non-neural"
    DECISION_TREE = "dt"
    LOGISTIC_REGRESSION = "lg"
    LINEAR_REGRESSION = "ln"
    NAIVE_BAYES = "nb"
    RANDOM_FOREST = "rf"
    SVM = "svm"


class FairnessMeasure(enum.Enum):
    ACCURACY_PARITY = "accuracy_parity"
    TRUE_POSITIVE_RATE_PARITY = "true_positive_rate_parity"
    FALSE_POSITIVE_RATE_PARITY = "false_positive_rate_parity"
    NEGATIVE_PREDICTIVE_VALUE_PARITY = "negative_predictive_value_parity"
    POSITIVE_PREDICTIVE_VALUE_PARITY = "positive_predictive_value_parity"
