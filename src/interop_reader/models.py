from datetime import datetime
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


class BaseMetric(BaseModel):
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


class BaseCycleMetric(BaseMetric):
    cycle: uint


class CorrectedIntensityRecord(BaseCycleMetric):
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


class ExtractionRecord(BaseCycleMetric):
    focus_a: float
    focus_c: float
    focus_g: float
    focus_t: float
    max_intensity_a: uint
    max_intensity_c: uint
    max_intensity_g: uint
    max_intensity_t: uint
    datestamp: uint

    @computed_field
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.datestamp)


class ImageRecord(BaseCycleMetric):
    channel_number: uint
    min_contrast: uint
    max_contrast: uint


class IndexRecord(BaseCycleMetric):
    pass


class PhasingRecord(BaseCycleMetric):
    phasing_weight: float
    prephasing_weight: float


class ErrorRecord(BaseCycleMetric):
    error_rate: float
    num_0_errors: uint
    num_1_errors: uint
    num_2_errors: uint
    num_3_errors: uint
    num_4_errors: uint


def check_quality_record_length(v: list[int]) -> list[int]:
    assert len(v) == 50, "Length mismatch!"
    return v


class QualityRecord(BaseCycleMetric):
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
            **{f"{k:02}": v for k, v in enumerate(self.quality_bins)},
        }


class TileMetricRecord(BaseMetric):
    metric_code: uint
    metric_value: float
