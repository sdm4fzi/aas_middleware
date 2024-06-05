from typing import Literal, Union, Optional, List

from enum import Enum

from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection

class DistributionTypeEnum(str, Enum):
    NORMAL = "normal"
    TRIANGULAR = "traingular"
    BINOMIAL = "binomial"
    EXPONENTIAL = "exponential"
    LOGNORMAL = "lognormal"
    UNIFORM = "uniform"

class BinomialDistribution(SubmodelElementCollection):
    type: Literal[DistributionTypeEnum.BINOMIAL]
    trials: int
    probability: float

class TriangularDistribution(SubmodelElementCollection):
    type: Literal[DistributionTypeEnum.TRIANGULAR]
    lowerBound: float
    upperBound: float
    mode: float

class NormalDistribution(SubmodelElementCollection):
    type: Literal[DistributionTypeEnum.NORMAL]
    mean: float
    std: float

class ExponentialDistribution(SubmodelElementCollection):
    type: Literal[DistributionTypeEnum.EXPONENTIAL]
    mean: float

class LognormalDistribution(SubmodelElementCollection):
    type: Literal[DistributionTypeEnum.LOGNORMAL]
    mean: float
    std: float

class UniformDistribution(SubmodelElementCollection):
    type: Literal[DistributionTypeEnum.UNIFORM]
    mean: float


ABSTRACT_INTEGER_DISTRIBUTION = BinomialDistribution
ABSTRACT_REAL_DISTRIBUTION = Union[TriangularDistribution, NormalDistribution, ExponentialDistribution, LognormalDistribution, UniformDistribution]