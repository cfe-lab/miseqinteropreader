from datetime import datetime, timedelta
from functools import cached_property
from math import isclose
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_serializer,
)


def assert_uint8(v: int) -> int:
    assert 0 <= v < 2**8, f"Integer must be between 0 and {2**8-1}"
    return v


def assert_uint16(v: int) -> int:
    assert 0 <= v < 2**16, f"Integer must be between 0 and {2**16-1}"
    return v


def assert_uint32(v: int) -> int:
    assert 0 <= v < 2**32, f"Integer must be between 0 and {2**32-1}"
    return v


def assert_uint64(v: int) -> int:
    assert 0 <= v < 2**64, f"Integer must be between 0 and {2**64-1}"
    return v


def value_is_non_negative(v: float | int) -> float | int:
    assert v >= 0, "This value must be positive"
    return v


uint8 = Annotated[int, AfterValidator(assert_uint8)]
uint16 = Annotated[int, AfterValidator(assert_uint16)]
uint32 = Annotated[int, AfterValidator(assert_uint32)]
uint64 = Annotated[int, AfterValidator(assert_uint64)]
float_positive = Annotated[float, AfterValidator(value_is_non_negative)]


###### Row record models


class BaseRecord(BaseModel):
    """Base record for all interop files"""

    model_config = ConfigDict(frozen=True)

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


class BaseMetricRecord(BaseRecord):
    """
    Base class for metrics taken from the Illumina interop folder
    """

    model_config = ConfigDict(frozen=True)
    lane: uint16
    tile: uint16


class BaseCycleMetricRecord(BaseMetricRecord):
    """
    Base class for a cycle metric
    """

    cycle: uint16


class CorrectedIntensityRecord(BaseCycleMetricRecord):
    """
    https://illumina.github.io/interop/corrected_v2.html
    """

    avg_cycle_intensity: uint16
    avg_corrected_intensity_a: uint16
    avg_corrected_intensity_c: uint16
    avg_corrected_intensity_g: uint16
    avg_corrected_intensity_t: uint16
    avg_corrected_cluster_intensity_a: uint16
    avg_corrected_cluster_intensity_c: uint16
    avg_corrected_cluster_intensity_g: uint16
    avg_corrected_cluster_intensity_t: uint16
    num_base_calls_none: uint32
    num_base_calls_a: uint32
    num_base_calls_c: uint32
    num_base_calls_g: uint32
    num_base_calls_t: uint32
    snr: float


class ExtractionRecord(BaseCycleMetricRecord):
    """
    https://illumina.github.io/interop/extraction_v2.html
    """

    focus_a: float
    focus_c: float
    focus_g: float
    focus_t: float
    max_intensity_a: uint16
    max_intensity_c: uint16
    max_intensity_g: uint16
    max_intensity_t: uint16
    datestamp: uint64

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
    """
    https://illumina.github.io/interop/image_v1.html
    """

    channel_number: uint16
    min_contrast: uint16
    max_contrast: uint16


class IndexRecord(BaseRecord):
    lane_number: uint16
    tile_number: uint16
    read_number: uint16
    index_name_length: uint16
    index_cluster_count: uint64
    sample_name_length: uint16
    project_name_length: uint16

    index_name_b: bytes
    sample_name_b: bytes
    project_name_b: bytes

    @computed_field  # type: ignore
    @cached_property
    def index_name(self) -> str:
        return self.index_name_b.decode()

    @computed_field  # type: ignore
    @cached_property
    def sample_name(self) -> str:
        return self.sample_name_b.decode()

    @computed_field  # type: ignore
    @cached_property
    def project_name(self) -> str:
        return self.project_name_b.decode()


class SummaryRecord(BaseRecord):
    """
    https://illumina.github.io/interop/summary_run_v1.html

    Heads up the formatting on this class is broken.
    """

    dummy: uint16
    occupancy_proxy_cluster_count: float
    raw_cluster_count: float
    occupancy_cluster_count: float
    pf_cluster_count: float


class PhasingRecord(BaseCycleMetricRecord):
    """
    https://illumina.github.io/interop/phasing_v1.html
    """

    phasing_weight: float
    prephasing_weight: float


class ErrorRecord(BaseCycleMetricRecord):
    """
    https://illumina.github.io/interop/error_v3.html
    """

    error_rate: float
    num_0_errors: uint32
    num_1_errors: uint32
    num_2_errors: uint32
    num_3_errors: uint32
    num_4_errors: uint32


def check_quality_record_length(v: list[int]) -> list[int]:
    assert len(v) == 50, "Length mismatch!"
    return v


class QualityRecord(BaseCycleMetricRecord):
    """
    https://illumina.github.io/interop/q_v4.html
    """

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
    """
    https://illumina.github.io/interop/tile_v2.html
    https://illumina.github.io/interop/extended_tile_v1.html

    """

    metric_code: uint16
    metric_value: float


class CollapsedQRecord(BaseCycleMetricRecord):
    """
    https://illumina.github.io/interop/q_collapsed_v2.html
    """

    q20: uint32
    q30: uint32
    total_count: uint32
    median_score: uint32


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

    density_count: int = Field(ge=0)
    density_sum: float
    total_clusters: float = Field(ge=0)
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

    total_count: int = Field(ge=0)
    total_reverse: int = Field(ge=0)
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
    error_count_forward: int = Field(ge=0)

    error_sum_reverse: float
    error_count_reverse: int = Field(ge=0)

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
