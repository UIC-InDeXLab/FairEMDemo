import enum
from enum import Enum


class CaseInsensitiveEnum(str, Enum):
    @classmethod
    def _missing_(cls, value):
        value = value.lower().replace(" ", "_")
        for member in cls:
            if member.lower() == value:
                return member
        return None


class DisparityCalculationType(CaseInsensitiveEnum):
    SUBTRACTION_BASED = "subtraction based"
    DIVISION_BASED = "division based"


class MatcherAlgorithm(CaseInsensitiveEnum):
    DITTO = "Ditto"
    MCAN = "MCAN"
    DEEPMATCHER = "DeepMatcher"
    HIERMATCHER = "HierMatcher"
    NONNEURAL = "non-neural"
    DTMATCHER = "DTMatcher"
    LOGREGMATCHER = "LogRegMatcher"
    LINREGMATCHER = "LinRegMatcher"
    NBMATCHER = "NBMatcher"
    RFMATCHER = "RFMatcher"
    SVMMATCHER = "SVMMatcher"


class FairnessMeasure(CaseInsensitiveEnum):
    ACCURACY_PARITY = "accuracy_parity"
    TRUE_POSITIVE_RATE_PARITY = "true_positive_rate_parity"
    FALSE_POSITIVE_RATE_PARITY = "false_positive_rate_parity"
    NEGATIVE_PREDICTIVE_VALUE_PARITY = "negative_predictive_value_parity"
    POSITIVE_PREDICTIVE_VALUE_PARITY = "positive_predictive_value_parity"


class PerformanceMetric(CaseInsensitiveEnum):
    PRECISION = "precision"
    RECALL = "recall"
    F1 = "f1"
