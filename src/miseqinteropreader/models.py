from datetime import datetime, timedelta
from functools import cached_property
from math import isclose
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    computed_field,
    model_serializer,
)


def assert_unsigned(v: int) -> int:
    assert v >= 0, "Integer must be >=0"
    return v


uint = Annotated[int, AfterValidator(assert_unsigned)]


###### Row record models


class BaseMetricRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    lane: uint
    tile: uint

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            other_dict = other.model_dump()
            self_dict = self.model_dump()
            comparison_array = []
            for k, info in self.model_fields.items():
                if info.annotation is float:
                    # we get into floating point innacuracies after 1e-7
                    close_enough = isclose(self_dict[k], other_dict[k], rel_tol=1e-7)
                    comparison_array.append(close_enough)
                else:
                    comparison_array.append(self_dict[k] == other_dict[k])
            return all(comparison_array)
        return False


class BaseCycleMetricRecord(BaseMetricRecord):
    cycle: uint


class CorrectedIntensityRecord(BaseCycleMetricRecord):
    avg_cycle_intensity: uint
    avg_corrected_intensity_a: uint
    avg_corrected_intensity_c: uint
    avg_corrected_intensity_g: uint
    avg_corrected_intensity_t: uint
    avg_corrected_cluster_intensity_a: uint
    avg_corrected_cluster_intensity_c: uint
    avg_corrected_cluster_intensity_g: uint
    avg_corrected_cluster_intensity_t: uint
    num_base_calls_none: uint
    num_base_calls_a: uint
    num_base_calls_c: uint
    num_base_calls_g: uint
    num_base_calls_t: uint
    snr: float


class ExtractionRecord(BaseCycleMetricRecord):
    focus_a: float
    focus_c: float
    focus_g: float
    focus_t: float
    max_intensity_a: uint
    max_intensity_c: uint
    max_intensity_g: uint
    max_intensity_t: uint
    datestamp: uint

    @computed_field  # type: ignore
    @cached_property
    def datetime(self) -> datetime:
        """
        this is a 64 bit integer,
        - the first 2 bits are 'kind', we just discard these bits.
        - the last 62 bits are the number of 100ns since midnight Jan 1, 0001
        (0001 is not a typo)

        Reference: https://github.com/nthmost/illuminate/blob/master/illuminate/extraction_metrics.py#L83C42-L83C53
        """
        bitmask = sum([2**i for i in range(62)])
        ns100intervals = self.datestamp & bitmask
        microseconds = timedelta(microseconds=ns100intervals / 10)
        datetime_of_record = datetime(1, 1, 1) + microseconds
        return datetime_of_record


class ImageRecord(BaseCycleMetricRecord):
    channel_number: uint
    min_contrast: uint
    max_contrast: uint


class IndexRecord(BaseCycleMetricRecord):
    pass


class PhasingRecord(BaseCycleMetricRecord):
    phasing_weight: float
    prephasing_weight: float


class ErrorRecord(BaseCycleMetricRecord):
    error_rate: float
    num_0_errors: uint
    num_1_errors: uint
    num_2_errors: uint
    num_3_errors: uint
    num_4_errors: uint


def check_quality_record_length(v: list[int]) -> list[int]:
    assert len(v) == 50, "Length mismatch!"
    return v


class QualityRecord(BaseCycleMetricRecord):
    quality_bins: Annotated[list[int], AfterValidator(check_quality_record_length)]

    @model_serializer
    def custom_serializer(self):
        """
        Since this has a list, it complicates the eventual pandas
        dataframe transformation. To that end we turn it into a flat dict
        with a custom serializer function.
        """
        return {
            "lane": self.lane,
            "tile": self.tile,
            "cycle": self.cycle,
            **{f"q{k:02}": v for k, v in enumerate(self.quality_bins, start=1)},
        }


class TileMetricRecord(BaseMetricRecord):
    metric_code: uint
    metric_value: float


### Summary models


class TileMetricCodes(object):
    """Constants for metric codes used in a tile metrics data file.

    Other codes:
    (200 + (N - 1) * 2): phasing for read N
    (201 + (N - 1) * 2): prephasing for read N
    (300 + N - 1): percent aligned for read N
    """

    CLUSTER_DENSITY = 100  # K/mm2
    CLUSTER_DENSITY_PASSING_FILTERS = 101  # K/mm2
    CLUSTER_COUNT = 102
    CLUSTER_COUNT_PASSING_FILTERS = 103


class TileMetricSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    density_count: int = 0
    density_sum: float
    total_clusters: float = 0.0
    passing_clusters: float

    @computed_field  # type: ignore
    @cached_property
    def pass_rate(self) -> float:
        if self.total_clusters == 0:
            return 0.0
        return self.passing_clusters / self.total_clusters

    @computed_field  # type: ignore
    @cached_property
    def cluster_density(self) -> float:
        if self.density_count == 0:
            return 0.0
        return self.density_sum / self.density_count


class QualityMetricsRunLengths(BaseModel):
    last_forward_cycle: int
    first_forward_cycle: int


class QualityMetricsSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_count: int = 0
    total_reverse: int = 0
    good_count: int
    good_reverse: int

    @computed_field  # type: ignore
    @cached_property
    def q30_forward(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.good_count / float(self.total_count)

    @computed_field  # type: ignore
    @cached_property
    def q30_reverse(self) -> float:
        if self.total_reverse == 0:
            return 0.0
        return self.good_reverse / float(self.total_reverse)


class ErrorMetricsRunLengths(BaseModel):
    last_forward_cycle: int
    first_forward_cycle: int


class ErrorMetricsSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    error_sum_forward: float
    error_count_forward: int

    error_sum_reverse: float
    error_count_reverse: int

    @computed_field  # type: ignore
    @cached_property
    def error_rate_forward(self) -> float:
        if self.error_count_forward == 0:
            return 0.0
        return self.error_sum_forward / float(self.error_count_forward)

    @computed_field  # type: ignore
    @cached_property
    def error_rate_reverse(self) -> float:
        if self.error_count_reverse == 0:
            return 0.0
        return self.error_sum_reverse / float(self.error_count_reverse)
