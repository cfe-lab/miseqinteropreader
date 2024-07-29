import logging
from enum import Enum
from io import BufferedReader
from pathlib import Path
from typing import Callable, Iterable, Iterator

import pandas as pd
from pydantic import BaseModel

from .models import (
    BaseMetricRecord,
    BaseRecord,
    CollapsedQRecord,
    CorrectedIntensityRecord,
    ErrorRecord,
    ExtractionRecord,
    ImageRecord,
    IndexRecord,
    PhasingRecord,
    QualityMetricsSummary,
    QualityRecord,
    TileMetricCodes,
    TileMetricRecord,
    TileMetricSummary,
)
from .read_records import (
    read_collapsed_q_metric,
    read_corrected_intensities,
    read_errors,
    read_extractions,
    read_images,
    read_index,
    read_phasing,
    read_quality,
    read_tiles,
)


class Metric(BaseModel):
    """
    Class that holds the valid filenames, the model that should be used
    to hold data, and the method which to read the data into the model.
    """

    files: list[str]
    model: type[BaseRecord]
    read_method: Callable[[BufferedReader], Iterator[BaseRecord]] | None = None

    def get_file(self, interop_dir: Path) -> Path:
        for filename in self.files:
            if (interop_dir / filename).exists():
                return interop_dir / filename
        raise FileNotFoundError(
            f"Could not find {'/'.join(self.files)} in {interop_dir}"
        )

    def read_file(self, interop_dir: Path) -> list[BaseRecord]:
        if self.read_method is None:
            raise ReferenceError("No associated read method for this type!")
        with open(self.get_file(interop_dir), mode="rb") as f:
            return list(self.read_method(f))


class MetricFile(Enum):
    """
    Enum class pointing to Metric models.
    """

    CORRECTED_INTENSITY_METRICS = Metric(
        files=[
            "CorrectedIntMetrics.bin",
            "CorrectedIntMetricsOut.bin",
        ],
        model=CorrectedIntensityRecord,
        read_method=read_corrected_intensities,
    )
    ERROR_METRICS = Metric(
        files=["ErrorMetrics.bin", "ErrorMetricsOut.bin"],
        model=ErrorRecord,
        read_method=read_errors,
    )
    EXTENDED_TILE_METRICS = Metric(
        files=["ExtendedTileMetrics.bin", "ExtendedTileMetricsOut.bin"],
        model=TileMetricRecord,
        read_method=read_tiles,
    )
    EXTRACTION_METRICS = Metric(
        files=["ExtractionMetrics.bin", "ExtractionMetricsOut.bin"],
        model=ExtractionRecord,
        read_method=read_extractions,
    )
    IMAGE_METRICS = Metric(
        files=["ImageMetrics.bin", "ImageMetricsOut.bin"],
        model=ImageRecord,
        read_method=read_images,
    )
    PHASING_METRICS = Metric(
        files=["EmpiricalPhasingMetrics.bin", "EmpiricalPhasingMetricsOut.bin"],
        model=PhasingRecord,
        read_method=read_phasing,
    )
    QUALITY_METRICS = Metric(
        files=["QMetrics.bin", "QMetricsOut.bin"],
        model=QualityRecord,
        read_method=read_quality,
    )
    TILE_METRICS = Metric(
        files=["TileMetrics.bin", "TileMetricsOut.bin"],
        model=TileMetricRecord,
        read_method=read_tiles,
    )
    COLLAPSED_Q_METRICS = Metric(
        files=["QMetrics2030.bin", "QMetrics2030Out.bin"],
        model=CollapsedQRecord,
        read_method=read_collapsed_q_metric,
    )
    INDEX_METRICS = Metric(
        files=["IndexMetrics.bin", "IndexMetricsOut.bin"],
        model=IndexRecord,
        read_method=read_index,
    )
    SUMMARY_RUN = Metric(
        files=["SummaryRun.bin", "SummaryRunOut.bin"],
        model=BaseMetricRecord,
    )


class InterOpReader:
    """
    MiSeq Run InterOp reader, this class reads files stored in the ./InterOp
    folder of a run.

    When initialized this object performs some checks to ensure that its pointed
    at the correct folder.

    It checks that:
    - An "InterOp" folder exists in the run folder,
    - A SampleSheet.csv exists in the run folder,
    - `qc_uploaded` and `needsprocessing` markers are present
    """

    def __init__(self, run_dir: str | Path):
        if isinstance(run_dir, str):
            run_dir = Path(run_dir)

        if not run_dir.exists():
            raise FileNotFoundError("Filepath does not exist.")
        if not run_dir.is_dir():
            raise NotADirectoryError("Filepath provided is not a directory.")

        samplesheet_path = run_dir / "SampleSheet.csv"
        if not samplesheet_path.exists():
            raise FileNotFoundError(f"SampleSheet.csv does not exist in {run_dir}")

        interop_dir = run_dir / "InterOp"
        if interop_dir.exists() and interop_dir.is_dir():
            self.interop_dir = interop_dir
        else:
            raise FileNotFoundError(f"InterOp directory does not exist in {run_dir}")

        needsprocessing_marker = run_dir / "needsprocessing"
        qc_uploaded_marker = run_dir / "qc_uploaded"

        self.run_name = run_dir.name
        self.needsprocessing = needsprocessing_marker.exists()
        self.qc_uploaded = qc_uploaded_marker.exists()

    def check_files_present(self, metric_files: Iterable[MetricFile]) -> bool:
        """
        Checks that all desired metric files are present in the InterOp directory.
        """
        try:
            for metric in metric_files:
                metric.value.get_file(self.interop_dir)
            return True
        except FileNotFoundError as e:
            logging.error(e)
            return False

    def read_file(self, metric: MetricFile) -> list[BaseRecord]:
        """
        Reads specified Metric file and returns a list of *MetricRecords, the
        type of which is defiend in `MetricFile.model`.
        """
        return metric.value.read_file(self.interop_dir)

    def read_file_to_dataframe(self, metric: MetricFile) -> pd.DataFrame:
        """
        Reads the specified Metric file and returns a dataframe, based on the
        `MetricFile.model`.
        """
        data = metric.value.read_file(self.interop_dir)
        return pd.DataFrame(data=[el.model_dump() for el in data])

    def summarize_tile_records(
        self, records: list[TileMetricRecord]
    ) -> TileMetricSummary:
        """Summarize the records from a tile metrics file.

        :param records: a sequence of dictionaries from read_tiles()
        :param dict summary: a dictionary to hold the summary values:
        cluster_density and pass_rate.
        """
        density_sum = 0.0
        density_count = 0
        total_clusters = 0.0
        passing_clusters = 0.0

        for record in records:
            if record.metric_code == TileMetricCodes.CLUSTER_DENSITY:
                density_sum += record.metric_value
                density_count += 1
            elif record.metric_code == TileMetricCodes.CLUSTER_COUNT:
                total_clusters += record.metric_value
            elif record.metric_code == TileMetricCodes.CLUSTER_COUNT_PASSING_FILTERS:
                passing_clusters += record.metric_value

        return TileMetricSummary(
            density_count=density_count,
            density_sum=density_sum,
            total_clusters=total_clusters,
            passing_clusters=passing_clusters,
        )

    def summarize_quality_records(
        self,
        records: list[QualityRecord],
        read_lengths: tuple[int, int, int] | None = None,
    ) -> QualityMetricsSummary:
        """Calculate the portion of clusters and cycles with quality >= 30
        (`quality_bins[29:]`).

        :param records: a sequence of dictionaries like those yielded from
        read_quality().
        :param dict summary: a dictionary to hold the summary values:
        q30_fwd and q30_rev. If read_lengths is None, only fwd_q30 will be set.
        :param tuple read_lengths: a tuple of lengths for each type of read: forward,
        indexes, and reverse.
        """
        total_count = 0
        total_reverse = 0
        good_count = 0
        good_reverse = 0
        last_forward_cycle = None
        first_reverse_cycle = None
        if read_lengths is not None:
            last_forward_cycle = read_lengths[0]
            first_reverse_cycle = sum(read_lengths[:-1]) + 1
        for record in records:
            cycle = record.cycle
            cycle_clusters = sum(record.quality_bins)
            cycle_good = sum(record.quality_bins[29:])

            if last_forward_cycle is None or cycle <= last_forward_cycle:
                total_count += cycle_clusters
                good_count += cycle_good
            elif first_reverse_cycle is not None and cycle >= first_reverse_cycle:
                total_reverse += cycle_clusters
                good_reverse += cycle_good

        return QualityMetricsSummary(
            total_count=total_count,
            total_reverse=total_reverse,
            good_count=good_count,
            good_reverse=good_reverse,
        )
